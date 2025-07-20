from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, List, Optional
import structlog
from datetime import datetime
import uuid

from auth import get_current_user
from storage_manager import StorageManager
from storage_models import (
    UserStorage, StorageRequest, StorageSelectionRequest,
    StorageListResponse, StorageCreationResponse, StorageUsageStats,
    BucketOperationRequest, StorageMetadata, StorageStatus, StorageType
)
from database import get_database
from config import settings

logger = structlog.get_logger()

router = APIRouter(prefix="/storage", tags=["storage"])

# Global storage manager instance
storage_manager = StorageManager()

@router.get("/list", response_model=StorageListResponse)
async def list_user_storages(current_user: Dict = Depends(get_current_user)):
    """List all storage buckets for the current user"""
    user_id = current_user["sub"]
    
    try:
        db = get_database()
        storages = await db.get_user_storages(user_id)
        
        # Update storage metadata from cloud provider
        updated_storages = []
        total_size = 0
        active_count = 0
        
        for storage in storages:
            # Get fresh metadata from cloud
            bucket_metadata = await storage_manager.get_bucket_metadata(storage.bucket_name)
            if bucket_metadata:
                # Update database with fresh metadata
                await db.update_storage_metadata(
                    storage.id, 
                    bucket_metadata['size_bytes'], 
                    bucket_metadata['object_count']
                )
                
                # Update storage object
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve storage list"
        )

@router.post("/create", response_model=StorageCreationResponse)
async def create_storage(
    request: StorageRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Create a new storage bucket for the user"""
    user_id = current_user["sub"]
    user_email = current_user["email"]
    
    try:
        # Generate storage ID
        storage_id = str(uuid.uuid4())
        
        # Create bucket
        bucket_metadata = await storage_manager.create_user_bucket(
            user_id=user_id,
            bucket_name=request.custom_name,
            storage_class=request.storage_class
        )
        
        # Generate display name
        display_name = storage_manager.get_friendly_display_name(bucket_metadata['bucket_name'])
        
        # Create storage record
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
        
        # Save to database
        db = get_database()
        await db.create_storage(storage)
        
        # Configure permissions in background
        background_tasks.add_task(
            configure_storage_permissions,
            storage.bucket_name,
            storage_id
        )
        
        logger.info("Created user storage", 
                   user_id=user_id, 
                   storage_id=storage_id,
                   bucket_name=storage.bucket_name,
                   display_name=display_name)
        
        return StorageCreationResponse(
            storage=storage,
            bucket_metadata=bucket_metadata,
            permissions_configured=False  # Will be configured in background
        )
        
    except Exception as e:
        logger.error("Failed to create storage", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create storage: {str(e)}"
        )

@router.get("/{storage_id}", response_model=StorageMetadata)
async def get_storage_details(
    storage_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get detailed information about a specific storage bucket"""
    user_id = current_user["sub"]
    
    try:
        db = get_database()
        storage = await db.get_storage_by_id(storage_id)
        
        if not storage or storage.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Storage not found"
            )
        
        # Get fresh metadata from cloud
        bucket_metadata = await storage_manager.get_bucket_metadata(storage.bucket_name)
        
        # Update database if metadata found
        if bucket_metadata:
            await db.update_storage_metadata(
                storage_id,
                bucket_metadata['size_bytes'],
                bucket_metadata['object_count']
            )
            storage.size_bytes = bucket_metadata['size_bytes']
            storage.object_count = bucket_metadata['object_count']
        
        return StorageMetadata(
            storage=storage,
            bucket_metadata=bucket_metadata,
            recent_activity=[],  # TODO: Implement activity tracking
            permissions_valid=bucket_metadata is not None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get storage details", 
                    storage_id=storage_id, 
                    user_id=user_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve storage details"
        )

@router.delete("/{storage_id}")
async def delete_storage(
    storage_id: str,
    request: BucketOperationRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Delete a storage bucket"""
    user_id = current_user["sub"]
    
    try:
        db = get_database()
        storage = await db.get_storage_by_id(storage_id)
        
        if not storage or storage.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Storage not found"
            )
        
        # Update status to deleting
        await db.update_storage_status(storage_id, StorageStatus.DELETING)
        
        # Delete bucket from cloud
        success = await storage_manager.delete_user_bucket(
            storage.bucket_name,
            force=request.force
        )
        
        if success:
            # Remove from database
            await db.delete_storage(storage_id)
            
            logger.info("Deleted user storage", 
                       user_id=user_id, 
                       storage_id=storage_id,
                       bucket_name=storage.bucket_name)
            
            return {"status": "deleted", "message": "Storage deleted successfully"}
        else:
            # Update status back to failed
            await db.update_storage_status(storage_id, StorageStatus.FAILED)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete storage bucket"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete storage", 
                    storage_id=storage_id, 
                    user_id=user_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete storage: {str(e)}"
        )

@router.post("/{storage_id}/operations")
async def perform_storage_operation(
    storage_id: str,
    request: BucketOperationRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Perform operations on storage bucket (backup, download, etc.)"""
    user_id = current_user["sub"]
    
    try:
        db = get_database()
        storage = await db.get_storage_by_id(storage_id)
        
        if not storage or storage.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Storage not found"
            )
        
        if request.operation == "download":
            # TODO: Implement download functionality
            return {"status": "pending", "message": "Download functionality coming soon"}
        
        elif request.operation == "backup":
            # TODO: Implement backup functionality
            return {"status": "pending", "message": "Backup functionality coming soon"}
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown operation: {request.operation}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to perform storage operation", 
                    storage_id=storage_id, 
                    operation=request.operation,
                    user_id=user_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform operation: {str(e)}"
        )

# Background task functions
async def configure_storage_permissions(bucket_name: str, storage_id: str):
    """Configure storage bucket permissions (background task)"""
    try:
        # Get service account email for workload identity
        sa_email = f"{settings.cluster_name}-workload-sa@{settings.project_id}.iam.gserviceaccount.com"
        
        success = await storage_manager.ensure_bucket_permissions(
            bucket_name, 
            sa_email
        )
        
        # Update storage status
        db = get_database()
        if success:
            await db.update_storage_status(storage_id, StorageStatus.ACTIVE)
            logger.info("Storage permissions configured successfully", 
                       storage_id=storage_id, 
                       bucket_name=bucket_name)
        else:
            await db.update_storage_status(storage_id, StorageStatus.FAILED)
            logger.error("Failed to configure storage permissions", 
                        storage_id=storage_id, 
                        bucket_name=bucket_name)
        
    except Exception as e:
        logger.error("Error configuring storage permissions", 
                    storage_id=storage_id, 
                    bucket_name=bucket_name,
                    error=str(e))
        
        # Update status to failed
        try:
            db = get_database()
            await db.update_storage_status(storage_id, StorageStatus.FAILED)
        except:
            pass
