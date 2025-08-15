from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional
import structlog
from datetime import datetime
import uuid
import io
import os

from .auth import get_current_user
from .storage_manager import StorageManager
from .storage_models import (
    UserStorage, StorageRequest, StorageSelectionRequest,
    StorageListResponse, StorageCreationResponse, StorageUsageStats,
    BucketOperationRequest, StorageMetadata, StorageStatus, StorageType
)
from .database import get_database
from .config import settings

logger = structlog.get_logger()

router = APIRouter(prefix="/storage", tags=["storage"])

# Dependency to get the storage manager instance
def get_storage_manager(request: Request) -> StorageManager:
    if not hasattr(request.app.state, "storage_manager"):
        raise HTTPException(status_code=503, detail="Storage service is not available.")
    return request.app.state.storage_manager

@router.get("/list", response_model=StorageListResponse)
async def list_user_storages(
    current_user: Dict = Depends(get_current_user),
    storage_manager: StorageManager = Depends(get_storage_manager)
):
    """List all storage buckets for the current user"""
    user_id = current_user["sub"]
    
    try:
        db = get_database()
        storages = await db.get_user_storages(user_id)
        
        updated_storages = []
        total_size = 0
        active_count = 0
        
        for storage in storages:
            bucket_metadata = await storage_manager.get_bucket_metadata(storage.bucket_name)
            if bucket_metadata:
                await db.update_storage_metadata(
                    storage.id, 
                    bucket_metadata['size_bytes'], 
                    bucket_metadata['object_count']
                )
                storage.size_bytes = bucket_metadata['size_bytes']
                storage.object_count = bucket_metadata['object_count']
                total_size += bucket_metadata['size_bytes']
                if storage.status == StorageStatus.ACTIVE:
                    active_count += 1
            updated_storages.append(storage)
        
        usage_stats = StorageUsageStats(
            total_buckets=len(updated_storages),
            total_size_bytes=total_size,
            active_buckets=active_count,
            last_updated=datetime.utcnow()
        )
        
        return StorageListResponse(
            storages=updated_storages,
            total_count=len(updated_storages),
            usage_stats=usage_stats
        )
        
    except Exception as e:
        logger.error("Failed to list user storages", user_id=user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve storage list")

@router.post("/create", response_model=StorageCreationResponse)
async def create_storage(
    request: StorageRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    storage_manager: StorageManager = Depends(get_storage_manager)
):
    """Create a new storage bucket for the user"""
    user_id = current_user["sub"]
    
    try:
        storage_id = str(uuid.uuid4())
        bucket_metadata = await storage_manager.create_user_bucket(
            user_id=user_id,
            bucket_name=request.custom_name,
            storage_class=request.storage_class
        )
        display_name = storage_manager.get_friendly_display_name(bucket_metadata['bucket_name'])
        
        storage = UserStorage(
            id=storage_id,
            user_id=user_id,
            bucket_name=bucket_metadata['bucket_name'],
            display_name=display_name,
            storage_type=request.storage_type,
            status=StorageStatus.CREATING,
            created_at=bucket_metadata['created_at'],
            size_bytes=bucket_metadata['size_bytes'],
            object_count=0,
            location=bucket_metadata['location'],
            storage_class=bucket_metadata['storage_class'],
            versioning_enabled=bucket_metadata['versioning_enabled']
        )
        
        db = get_database()
        await db.create_storage(storage)
        
        background_tasks.add_task(
            configure_storage_permissions,
            storage_manager,
            storage.bucket_name,
            storage_id
        )
        
        logger.info("Created user storage", user_id=user_id, storage_id=storage_id)
        return StorageCreationResponse(storage=storage, bucket_metadata=bucket_metadata, permissions_configured=False)
        
    except Exception as e:
        logger.error("Failed to create storage", user_id=user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create storage: {str(e)}")

@router.get("/{storage_id}", response_model=StorageMetadata)
async def get_storage_details(
    storage_id: str,
    current_user: Dict = Depends(get_current_user),
    storage_manager: StorageManager = Depends(get_storage_manager)
):
    """Get detailed information about a specific storage bucket"""
    user_id = current_user["sub"]
    db = get_database()
    storage = await db.get_storage_by_id(storage_id)
    
    if not storage or storage.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")

    bucket_metadata = await storage_manager.get_bucket_metadata(storage.bucket_name)
    if bucket_metadata:
        await db.update_storage_metadata(storage_id, bucket_metadata['size_bytes'], bucket_metadata['object_count'])
        storage.size_bytes = bucket_metadata['size_bytes']
        storage.object_count = bucket_metadata['object_count']

    return StorageMetadata(storage=storage, bucket_metadata=bucket_metadata, recent_activity=[], permissions_valid=bucket_metadata is not None)

@router.delete("/{storage_id}")
async def delete_storage(
    storage_id: str,
    request: BucketOperationRequest,
    current_user: Dict = Depends(get_current_user),
    storage_manager: StorageManager = Depends(get_storage_manager)
):
    """Delete a storage bucket"""
    user_id = current_user["sub"]
    db = get_database()
    storage = await db.get_storage_by_id(storage_id)
    
    if not storage or storage.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")

    await db.update_storage_status(storage_id, StorageStatus.DELETING)
    success = await storage_manager.delete_user_bucket(storage.bucket_name, force=request.force)

    if success:
        await db.delete_storage(storage_id)
        logger.info("Deleted user storage", user_id=user_id, storage_id=storage_id)
        return {"status": "deleted", "message": "Storage deleted successfully"}
    else:
        await db.update_storage_status(storage_id, StorageStatus.FAILED)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete storage bucket")

import asyncio

@router.post("/{storage_id}/upload")
async def upload_file_to_storage(
    storage_id: str,
    file: UploadFile = File(...),
    path: str = "",
    current_user: Dict = Depends(get_current_user),
    storage_manager: StorageManager = Depends(get_storage_manager)
):
    """Upload a file to a storage bucket using streaming."""
    user_id = current_user["sub"]
    db = get_database()
    storage = await db.get_storage_by_id(storage_id)
    
    if not storage or storage.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")

    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file name provided.")

    # Sanitize and create the object path
    object_path = f"{path.strip('/')}/{file.filename}" if path else file.filename
    object_path = object_path.lstrip('/')

    content_type = file.content_type or 'application/octet-stream'
    file_size = file.size

    try:
        # Run the synchronous upload method in a thread to avoid blocking the event loop
        success = await asyncio.to_thread(
            storage_manager.upload_object,
            bucket_name=storage.bucket_name,
            object_name=object_path,
            file_obj=file.file,
            file_size=file_size,
            content_type=content_type
        )

        if success:
            logger.info("File stream uploaded successfully", user_id=user_id, storage_id=storage_id, object_path=object_path, size=file_size)
            return {"status": "success", "message": "File uploaded successfully", "object_path": object_path, "size": file_size}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload file")

    except Exception as e:
        logger.error("File upload failed", user_id=user_id, storage_id=storage_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred during file upload: {e}")

@router.get("/{storage_id}/download/{object_path:path}")
async def download_file_from_storage(
    storage_id: str,
    object_path: str,
    current_user: Dict = Depends(get_current_user),
    storage_manager: StorageManager = Depends(get_storage_manager)
):
    """Download a file from storage bucket"""
    user_id = current_user["sub"]
    db = get_database()
    storage = await db.get_storage_by_id(storage_id)
    
    if not storage or storage.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")

    file_data = await storage_manager.download_object(storage.bucket_name, object_path)
    if file_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    filename = os.path.basename(object_path)
    return StreamingResponse(io.BytesIO(file_data), media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={filename}"})

@router.get("/{storage_id}/list")
async def list_storage_objects(
    storage_id: str,
    prefix: str = "",
    current_user: Dict = Depends(get_current_user),
    storage_manager: StorageManager = Depends(get_storage_manager)
):
    """List objects in storage bucket"""
    user_id = current_user["sub"]
    db = get_database()
    storage = await db.get_storage_by_id(storage_id)
    
    if not storage or storage.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")

    objects = await storage_manager.list_objects(storage.bucket_name, prefix=prefix)
    return {"objects": objects, "total_count": len(objects)}

@router.delete("/{storage_id}/objects/{object_path:path}")
async def delete_storage_object(
    storage_id: str,
    object_path: str,
    current_user: Dict = Depends(get_current_user),
    storage_manager: StorageManager = Depends(get_storage_manager)
):
    """Delete an object from storage bucket"""
    user_id = current_user["sub"]
    db = get_database()
    storage = await db.get_storage_by_id(storage_id)
    
    if not storage or storage.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storage not found")
    
    success = await storage_manager.delete_object(storage.bucket_name, object_path)
    if success:
        return {"status": "success", "message": "Object deleted successfully"}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found")

# Background task function
async def configure_storage_permissions(storage_manager: StorageManager, bucket_name: str, storage_id: str):
    """Configure storage bucket permissions"""
    try:
        sa_email = f"{settings.cluster_name}-workload-sa@{settings.project_id}.iam.gserviceaccount.com"
        success = await storage_manager.ensure_bucket_permissions(bucket_name, sa_email)
        
        db = get_database()
        status = StorageStatus.ACTIVE if success else StorageStatus.FAILED
        await db.update_storage_status(storage_id, status)
        logger.info(f"Storage permissions configured: {success}", storage_id=storage_id)
        
    except Exception as e:
        logger.error("Error in background permission configuration", error=str(e))
        db = get_database()
        await db.update_storage_status(storage_id, StorageStatus.FAILED)
