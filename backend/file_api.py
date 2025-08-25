import asyncio
import json
import uuid
import tempfile
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from fastapi.responses import JSONResponse
import structlog

from auth import get_current_user
from database import get_database
from file_models import (
    UserFile, UserFileRequest, UserFileResponse, UserFileUpdate, 
    FileType
)
from file_encryption import get_file_encryption
from models import User

logger = structlog.get_logger()

router = APIRouter(prefix="/files", tags=["user-files"])

# File size limit (1MB)
MAX_FILE_SIZE = 1024 * 1024

@router.post("/upload", response_model=UserFileResponse)
async def upload_user_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    environment_variable_name: str = Form(...),  # Now required
    container_path: Optional[str] = Form(None),
    current_user: Dict = Depends(get_current_user)
):
    """Upload a JSON file with encryption and validation"""
    
    # Get user ID from the token dictionary
    user_id = current_user["sub"]
    
    # Validate file type
    if not file.filename.lower().endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JSON files are allowed"
        )
    
    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size must be less than {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Validate JSON content
    try:
        json_content = content.decode('utf-8')
        parsed_json = json.loads(json_content)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must contain valid JSON"
        )
    
    # Validate file type enum
    try:
        file_type_enum = FileType(file_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Must be one of: {[ft.value for ft in FileType]}"
        )
    
    # Create file request for validation
    try:
        file_request = UserFileRequest(
            file_name=file.filename,
            file_type=file_type_enum,
            content=json_content,
            environment_variable_name=environment_variable_name,
            container_path=container_path
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Check for duplicate environment variable names for this user
    db = get_database()
    existing_files = await db.get_user_files(user_id)
    
    for existing_file in existing_files:
        if (existing_file.environment_variable_name and 
            existing_file.environment_variable_name == file_request.environment_variable_name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Environment variable '{file_request.environment_variable_name}' is already used by another file"
            )
    
    # Encrypt file content
    encryption = get_file_encryption()
    try:
        encrypted_content = encryption.encrypt_content(json_content)
    except Exception as e:
        logger.error("Failed to encrypt file content", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to encrypt file content"
        )
    
    # Create user file record
    user_file = UserFile(
        id=str(uuid.uuid4()),
        user_id=user_id,
        file_name=file_request.file_name,
        file_type=file_request.file_type,
        encrypted_content=encrypted_content,
        environment_variable_name=file_request.environment_variable_name,
        container_path=file_request.container_path,
        file_size=len(content),
        created_at=datetime.utcnow()
    )
    
    # Save to database
    try:
        await db.create_user_file(user_file)
        logger.info("File uploaded successfully", 
                   file_id=user_file.id, 
                   user_id=user_id, 
                   file_name=user_file.file_name,
                   file_type=user_file.file_type.value)
    except Exception as e:
        logger.error("Failed to save file to database", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file"
        )
    
    # Return response without encrypted content
    return UserFileResponse(
        id=user_file.id,
        file_name=user_file.file_name,
        file_type=user_file.file_type,
        environment_variable_name=user_file.environment_variable_name,
        container_path=user_file.container_path,
        file_size=user_file.file_size,
        created_at=user_file.created_at,
        updated_at=user_file.updated_at
    )

@router.get("", response_model=List[UserFileResponse])
async def list_user_files(current_user: Dict = Depends(get_current_user)):
    """List all files for the current user"""
    db = get_database()
    
    # Get user ID from the token dictionary
    user_id = current_user["sub"]
    
    try:
        files = await db.get_user_files(user_id)
        return [
            UserFileResponse(
                id=file.id,
                file_name=file.file_name,
                file_type=file.file_type,
                environment_variable_name=file.environment_variable_name,
                container_path=file.container_path,
                file_size=file.file_size,
                created_at=file.created_at,
                updated_at=file.updated_at
            )
            for file in files
        ]
    except Exception as e:
        logger.error("Failed to list user files", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve files"
        )

@router.get("/{file_id}", response_model=UserFileResponse)
async def get_user_file(
    file_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get details of a specific file"""
    db = get_database()
    
    # Get user ID from the token dictionary
    user_id = current_user["sub"]
    
    try:
        file = await db.get_user_file(user_id, file_id)
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return UserFileResponse(
            id=file.id,
            file_name=file.file_name,
            file_type=file.file_type,
            environment_variable_name=file.environment_variable_name,
            container_path=file.container_path,
            file_size=file.file_size,
            created_at=file.created_at,
            updated_at=file.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user file", error=str(e), user_id=user_id, file_id=file_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve file"
        )

@router.put("/{file_id}", response_model=UserFileResponse)
async def update_user_file(
    file_id: str,
    file_update: UserFileUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Update file metadata and optionally content"""
    db = get_database()
    
    # Get user ID from the token dictionary
    user_id = current_user["sub"]
    
    # Check if file exists and belongs to user
    existing_file = await db.get_user_file(user_id, file_id)
    if not existing_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    updates = {}
    
    # Validate and prepare updates
    if file_update.file_name is not None:
        updates['file_name'] = file_update.file_name
    
    if file_update.environment_variable_name is not None:
        # Check for conflicts with other files
        existing_files = await db.get_user_files(user_id)
        for file in existing_files:
            if (file.id != file_id and 
                file.environment_variable_name and
                file.environment_variable_name == file_update.environment_variable_name):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Environment variable '{file_update.environment_variable_name}' is already used by another file"
                )
        updates['environment_variable_name'] = file_update.environment_variable_name
    
    if file_update.container_path is not None:
        updates['container_path'] = file_update.container_path
    
    if file_update.content is not None:
        # Validate and encrypt new content
        try:
            json.loads(file_update.content)  # Validate JSON
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content must be valid JSON"
            )
        
        # Encrypt new content
        encryption = get_file_encryption()
        try:
            encrypted_content = encryption.encrypt_content(file_update.content)
            updates['encrypted_content'] = encrypted_content
            updates['file_size'] = len(file_update.content.encode('utf-8'))
        except Exception as e:
            logger.error("Failed to encrypt file content", error=str(e), user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to encrypt file content"
            )
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid updates provided"
        )
    
    # Perform update
    try:
        success = await db.update_user_file(user_id, file_id, **updates)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or no changes made"
            )
        
        # Get updated file
        updated_file = await db.get_user_file(user_id, file_id)
        return UserFileResponse(
            id=updated_file.id,
            file_name=updated_file.file_name,
            file_type=updated_file.file_type,
            environment_variable_name=updated_file.environment_variable_name,
            container_path=updated_file.container_path,
            file_size=updated_file.file_size,
            created_at=updated_file.created_at,
            updated_at=updated_file.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update user file", error=str(e), user_id=user_id, file_id=file_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update file"
        )

@router.delete("/{file_id}")
async def delete_user_file(
    file_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete a user file"""
    db = get_database()
    
    # Get user ID from the token dictionary
    user_id = current_user["sub"]
    
    try:
        success = await db.delete_user_file(user_id, file_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        logger.info("File deleted successfully", file_id=file_id, user_id=user_id)
        return {"status": "success", "message": "File deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete user file", error=str(e), user_id=user_id, file_id=file_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )

@router.get("/{file_id}/download")
async def download_user_file(
    file_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Download and decrypt file content (for debugging or backup)"""
    db = get_database()
    
    # Get user ID from the token dictionary
    user_id = current_user["sub"]
    
    try:
        file = await db.get_user_file(user_id, file_id)
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Decrypt content
        encryption = get_file_encryption()
        try:
            decrypted_content = encryption.decrypt_content(file.encrypted_content)
        except Exception as e:
            logger.error("Failed to decrypt file content", error=str(e), user_id=user_id, file_id=file_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to decrypt file content"
            )
        
        # Return as JSON response
        return JSONResponse(
            content={
                "file_name": file.file_name,
                "file_type": file.file_type.value,
                "content": json.loads(decrypted_content)
            },
            headers={
                "Content-Disposition": f"attachment; filename={file.file_name}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to download user file", error=str(e), user_id=user_id, file_id=file_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file"
        )
