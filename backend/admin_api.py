from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, List, Optional
from pydantic import BaseModel
import structlog
from datetime import datetime
import uuid
import os
import aiofiles
from pathlib import Path

from auth import get_current_user, require_role
from models import User, UserRole, ActivityLog
from database import get_database

logger = structlog.get_logger()

router = APIRouter(prefix="/admin", tags=["admin"])

# Import application models from models.py
from models import ApplicationImage

class ApplicationImageRequest(BaseModel):
    name: str
    summary: str
    image_path: str
    port: Optional[int] = 8888
    working_dir: Optional[str] = "/cmbagent"
    icon_url: Optional[str] = None
    category: str = "research"
    tags: List[str] = []

class ApplicationImageRequestWithFile(BaseModel):
    name: str
    summary: str
    image_path: str
    port: Optional[int] = 8888
    category: str = "research"
    tags: str = ""  # Comma-separated string for form data

class ApplicationImageResponse(BaseModel):
    status: str
    message: str
    application: Optional[ApplicationImage] = None

# User Management Models
class UserManagementRequest(BaseModel):
    new_role: UserRole
    reason: Optional[str] = None

class UserWithRole(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    promoted_by: Optional[str] = None
    promoted_at: Optional[datetime] = None

class RoleChangeRecord(BaseModel):
    id: str
    user_id: str
    changed_by: str
    changed_by_name: str
    old_role: str
    new_role: str
    reason: Optional[str]
    changed_at: datetime

# Helper Functions
def require_admin_mode():
    """Decorator to require admin role"""
    return require_role(UserRole.ADMIN)

async def is_project_owner(user_id: str) -> bool:
    """Check if user has project owner permissions"""
    # For now, we'll consider admins as project owners
    # This can be expanded to check specific project ownership logic
    db = get_database()
    user = await db.get_user(user_id)
    return user and user.role == UserRole.ADMIN

async def log_role_change(changed_by: str, user_id: str, old_role: UserRole, new_role: UserRole, reason: Optional[str] = None):
    """Log role change for audit trail"""
    db = get_database()
    change_record = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "changed_by": changed_by,
        "old_role": old_role.value,
        "new_role": new_role.value,
        "reason": reason,
        "changed_at": datetime.utcnow()
    }
    await db.log_role_change(change_record)

# Helper function to save uploaded image
async def save_uploaded_image(file: UploadFile, app_name: str) -> str:
    """Save uploaded image to GCS bucket and return the file path"""
    import os
    
    # Determine the correct upload directory based on environment
    # In production (k8s), use GCS FUSE mount at /app/data
    # In development, use local uploads directory
    if os.path.exists("/app/data"):
        # Production: GCS FUSE mount
        upload_dir = Path("/app/data/uploads/applications")
        url_prefix = "/data"
        logger.info("Using GCS FUSE mount for image storage", upload_dir=str(upload_dir))
    else:
        # Development: Local storage
        upload_dir = Path("./uploads/applications")
        url_prefix = "/uploads"
        logger.info("Using local storage for image storage", upload_dir=str(upload_dir))
    
    try:
        upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Upload directory created/verified", path=str(upload_dir))
    except Exception as e:
        logger.error("Failed to create upload directory", error=str(e), path=str(upload_dir))
        raise
    
    # Generate safe filename
    safe_name = "".join(c for c in app_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
    file_extension = Path(file.filename).suffix if file.filename else '.png'
    filename = f"{safe_name}_{uuid.uuid4().hex[:8]}{file_extension}"
    file_path = upload_dir / filename
    
    logger.info("Saving uploaded image", filename=filename, path=str(file_path), size=file.size)
    
    try:
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Verify file was saved
        if not file_path.exists():
            raise Exception(f"File was not saved successfully: {file_path}")
        
        logger.info("Image saved successfully", filename=filename, size=file_path.stat().st_size)
        
    except Exception as e:
        logger.error("Failed to save image file", error=str(e), filename=filename)
        raise
    
    # Return relative URL path for serving the image
    # This allows the frontend to serve images from the same domain
    return f"{url_prefix}/uploads/applications/{filename}"

# Application/Image Management Endpoints
@router.post("/applications", response_model=ApplicationImageResponse)
async def create_application(
    request: ApplicationImageRequest,
    current_user: Dict = Depends(require_admin_mode())
):
    """Create a new application image (admin only) - for API usage"""
    try:
        db = get_database()
        
        application = ApplicationImage(
            id=str(uuid.uuid4()),
            name=request.name,
            summary=request.summary,
            image_path=request.image_path,
            port=request.port or 8888,
            working_dir=request.working_dir or "/cmbagent",
            icon_url=request.icon_url,
            category=request.category,
            created_at=datetime.utcnow(),
            created_by=current_user["sub"],
            is_active=True,
            tags=request.tags
        )
        
        await db.create_application(application)
        
        logger.info("Application created", 
                   application_id=application.id,
                   name=application.name,
                   created_by=current_user["email"])
        
        return ApplicationImageResponse(
            status="success",
            message="Application created successfully",
            application=application
        )
        
    except Exception as e:
        logger.error("Failed to create application", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create application"
        )

# Test endpoint for debugging
@router.post("/test-form")
async def test_form_submission(
    name: str = Form(...),
    summary: str = Form(...),
    current_user: Dict = Depends(require_admin_mode())
):
    """Test endpoint to verify form submission is working"""
    return JSONResponse({
        "status": "success",
        "message": "Form submission test successful",
        "data": {"name": name, "summary": summary}
    })

@router.post("/applications-with-image", response_model=ApplicationImageResponse)
async def create_application_with_image(
    name: str = Form(...),
    summary: str = Form(...),
    image_path: str = Form(...),
    category: str = Form("research"),
    port: int = Form(8888),
    working_dir: str = Form("/cmbagent"),
    tags: str = Form(""),
    image_file: Optional[UploadFile] = File(None),
    current_user: Dict = Depends(require_admin_mode())
):
    """Create a new application image with optional image upload (admin only)"""
    logger.info("Starting application creation with image", 
                name=name, 
                summary=summary[:50] + "..." if len(summary) > 50 else summary,
                image_path=image_path,
                category=category,
                port=port,
                tags=tags,
                has_image_file=image_file is not None,
                image_file_size=image_file.size if image_file else 0,
                user_id=current_user.get("sub"))
    
    try:
        db = get_database()
        logger.info("Database connection obtained")
        
        # Handle image upload if provided
        icon_url = None
        if image_file and image_file.size > 0:
            # Validate file type
            if not image_file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File must be an image"
                )
            
            # Save uploaded image
            try:
                icon_url = await save_uploaded_image(image_file, name)
                logger.info("Image uploaded successfully", filename=icon_url, app_name=name)
            except Exception as img_error:
                logger.error("Failed to save uploaded image", error=str(img_error), app_name=name)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to save uploaded image: {str(img_error)}"
                )
        
        # Parse tags
        tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
        
        application = ApplicationImage(
            id=str(uuid.uuid4()),
            name=name,
            summary=summary,
            image_path=image_path,
            port=port,
            working_dir=working_dir,
            icon_url=icon_url,
            category=category,
            created_at=datetime.utcnow(),
            created_by=current_user["sub"],
            is_active=True,
            tags=tags_list
        )
        
        await db.create_application(application)
        
        logger.info("Application created with image", 
                   application_id=application.id,
                   name=application.name,
                   has_image=icon_url is not None,
                   created_by=current_user["email"])
        
        return ApplicationImageResponse(
            status="success",
            message="Application created successfully",
            application=application
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error("Failed to create application with image", 
                    error=str(e), 
                    traceback=traceback.format_exc(),
                    name=name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create application: {str(e)}"
        )

@router.get("/applications", response_model=List[ApplicationImage])
async def list_applications(
    current_user: Dict = Depends(require_admin_mode())
):
    """List all applications (admin only)"""
    try:
        db = get_database()
        applications = await db.list_applications()
        return applications
        
    except Exception as e:
        logger.error("Failed to list applications", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list applications"
        )

@router.put("/applications/{application_id}", response_model=ApplicationImageResponse)
async def update_application(
    application_id: str,
    request: ApplicationImageRequest,
    current_user: Dict = Depends(require_admin_mode())
):
    """Update an application (admin only) - for API usage"""
    try:
        db = get_database()
        
        existing_app = await db.get_application(application_id)
        if not existing_app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Update application
        updated_app = ApplicationImage(
            id=application_id,
            name=request.name,
            summary=request.summary,
            image_path=request.image_path,
            port=request.port or 8888,
            working_dir=request.working_dir or "/cmbagent",
            icon_url=request.icon_url,
            category=request.category,
            created_at=existing_app.created_at,
            created_by=existing_app.created_by,
            is_active=existing_app.is_active,
            tags=request.tags
        )
        
        await db.update_application(updated_app)
        
        logger.info("Application updated",
                   application_id=application_id,
                   updated_by=current_user["email"])
        
        return ApplicationImageResponse(
            status="success",
            message="Application updated successfully",
            application=updated_app
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update application", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application"
        )

@router.put("/applications-with-image/{application_id}", response_model=ApplicationImageResponse)
async def update_application_with_image(
    application_id: str,
    name: str = Form(...),
    summary: str = Form(...),
    image_path: str = Form(...),
    category: str = Form("research"),
    port: int = Form(8888),
    working_dir: str = Form("/cmbagent"),
    tags: str = Form(""),
    image_file: Optional[UploadFile] = File(None),
    current_user: Dict = Depends(require_admin_mode())
):
    """Update an application with optional image upload (admin only)"""
    try:
        db = get_database()
        
        existing_app = await db.get_application(application_id)
        if not existing_app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Handle image upload if provided
        icon_url = existing_app.icon_url  # Keep existing image by default
        if image_file and image_file.size > 0:
            # Validate file type
            if not image_file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File must be an image"
                )
            
            # Delete old image file if it exists in GCS storage
            if existing_app.icon_url and existing_app.icon_url.startswith('/data/uploads/'):
                try:
                    # Remove /data prefix to get the actual file path in the mounted GCS bucket
                    relative_path = existing_app.icon_url.replace('/data/', '')
                    old_file_path = Path(f"/app/data/{relative_path}")
                    if old_file_path.exists():
                        old_file_path.unlink()
                except Exception as e:
                    logger.warning("Failed to delete old image file from GCS", error=str(e))
            
            # Save new uploaded image
            try:
                icon_url = await save_uploaded_image(image_file, name)
                logger.info("Image uploaded successfully", filename=icon_url, app_name=name)
            except Exception as img_error:
                logger.error("Failed to save uploaded image", error=str(img_error), app_name=name)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to save uploaded image: {str(img_error)}"
                )
        
        # Parse tags
        tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []
        
        # Update application
        updated_app = ApplicationImage(
            id=application_id,
            name=name,
            summary=summary,
            image_path=image_path,
            port=port,
            working_dir=working_dir,
            icon_url=icon_url,
            category=category,
            created_at=existing_app.created_at,
            created_by=existing_app.created_by,
            is_active=existing_app.is_active,
            tags=tags_list
        )
        
        await db.update_application(updated_app)
        
        logger.info("Application updated with image",
                   application_id=application_id,
                   has_new_image=image_file is not None and image_file.size > 0,
                   updated_by=current_user["email"])
        
        return ApplicationImageResponse(
            status="success",
            message="Application updated successfully",
            application=updated_app
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update application with image", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application"
        )

@router.delete("/applications/{application_id}")
async def delete_application(
    application_id: str,
    current_user: Dict = Depends(require_admin_mode())
):
    """Delete an application (admin only)"""
    try:
        db = get_database()
        
        existing_app = await db.get_application(application_id)
        if not existing_app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        await db.delete_application(application_id)
        
        logger.info("Application deleted",
                   application_id=application_id,
                   deleted_by=current_user["email"])
        
        return {"status": "success", "message": "Application deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete application", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete application"
        )

# User Management Endpoints
@router.get("/users", response_model=List[UserWithRole])
async def list_users(
    current_user: Dict = Depends(require_admin_mode())
):
    """List all users with their roles (admin only)"""
    try:
        db = get_database()
        users = await db.list_all_users()
        
        # Convert to UserWithRole format
        user_list = []
        for user in users:
            user_with_role = UserWithRole(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role,
                created_at=user.created_at,
                last_login=user.last_login,
                is_active=user.is_active,
                promoted_by=getattr(user, 'promoted_by', None),
                promoted_at=getattr(user, 'promoted_at', None)
            )
            user_list.append(user_with_role)
        
        return user_list
        
    except Exception as e:
        logger.error("Failed to list users", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )

@router.post("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    request: UserManagementRequest,
    current_user: Dict = Depends(require_admin_mode())
):
    """Update user role (admin only)"""
    try:
        db = get_database()
        
        # Get target user
        target_user = await db.get_user(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent self-demotion from admin
        if (user_id == current_user["sub"] and 
            target_user.role == UserRole.ADMIN and 
            request.new_role != UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote yourself"
            )
        
        # Check if role is actually changing
        if target_user.role == request.new_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User already has {request.new_role.value} role"
            )
        
        # Update user role
        old_role = target_user.role
        await db.update_user_role(
            user_id, 
            request.new_role, 
            current_user["sub"], 
            datetime.utcnow()
        )
        
        # Log the role change
        await log_role_change(
            current_user["sub"], 
            user_id, 
            old_role, 
            request.new_role, 
            request.reason
        )
        
        logger.info("User role updated",
                   user_id=user_id,
                   user_email=target_user.email,
                   old_role=old_role.value,
                   new_role=request.new_role.value,
                   updated_by=current_user["email"],
                   reason=request.reason)
        
        return {
            "status": "success",
            "message": f"User {target_user.name} role updated to {request.new_role.value} successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update user role", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        )

@router.post("/users/{user_id}/promote")
async def promote_user_to_admin(
    user_id: str,
    request: UserManagementRequest,
    current_user: Dict = Depends(require_admin_mode())
):
    """Promote a user to admin role (admin only)"""
    try:
        db = get_database()
        
        # Get target user
        target_user = await db.get_user(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if target_user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already an admin"
            )
        
        # Update user role
        old_role = target_user.role
        await db.update_user_role(
            user_id, 
            UserRole.ADMIN, 
            current_user["sub"], 
            datetime.utcnow()
        )
        
        # Log the role change
        await log_role_change(
            current_user["sub"], 
            user_id, 
            old_role, 
            UserRole.ADMIN, 
            request.reason
        )
        
        logger.info("User promoted to admin",
                   user_id=user_id,
                   user_email=target_user.email,
                   promoted_by=current_user["email"],
                   reason=request.reason)
        
        return {
            "status": "success",
            "message": f"User {target_user.name} promoted to admin successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to promote user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to promote user"
        )

@router.post("/users/{user_id}/demote")
async def demote_admin_to_user(
    user_id: str,
    request: UserManagementRequest,
    current_user: Dict = Depends(require_admin_mode())
):
    """Demote an admin to user role (admin only)"""
    try:
        db = get_database()
        
        # Prevent self-demotion
        if user_id == current_user["sub"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote yourself"
            )
        
        # Get target user
        target_user = await db.get_user(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if target_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not an admin"
            )
        
        # Update user role
        old_role = target_user.role
        await db.update_user_role(
            user_id, 
            UserRole.USER, 
            current_user["sub"], 
            datetime.utcnow()
        )
        
        # Log the role change
        await log_role_change(
            current_user["sub"], 
            user_id, 
            old_role, 
            UserRole.USER, 
            request.reason
        )
        
        logger.info("Admin demoted to user",
                   user_id=user_id,
                   user_email=target_user.email,
                   demoted_by=current_user["email"],
                   reason=request.reason)
        
        return {
            "status": "success",
            "message": f"User {target_user.name} demoted to user successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to demote user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to demote user"
        )

@router.get("/users/{user_id}/audit", response_model=List[RoleChangeRecord])
async def get_user_role_history(
    user_id: str,
    current_user: Dict = Depends(require_admin_mode())
):
    """Get role change history for a user (admin only)"""
    try:
        db = get_database()
        history = await db.get_user_role_history(user_id)
        return history
        
    except Exception as e:
        logger.error("Failed to get user role history", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user role history"
        )

@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: Dict = Depends(require_admin_mode())
):
    """Deactivate a user account (admin only)"""
    try:
        db = get_database()
        
        # Prevent self-deactivation
        if user_id == current_user["sub"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate yourself"
            )
        
        target_user = await db.get_user(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        await db.update_user_status(user_id, False)
        
        logger.info("User deactivated",
                   user_id=user_id,
                   user_email=target_user.email,
                   deactivated_by=current_user["email"])
        
        return {
            "status": "success",
            "message": f"User {target_user.name} deactivated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to deactivate user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )

@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: Dict = Depends(require_admin_mode())
):
    """Activate a user account (admin only)"""
    try:
        db = get_database()
        
        target_user = await db.get_user(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        await db.update_user_status(user_id, True)
        
        logger.info("User activated",
                   user_id=user_id,
                   user_email=target_user.email,
                   activated_by=current_user["email"])
        
        return {
            "status": "success",
            "message": f"User {target_user.name} activated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to activate user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )

@router.get("/data/uploads/applications/{filename}")
async def serve_application_image(filename: str):
    """Serve application image files from GCS storage"""
    try:
        # Check if we're in production (GCS FUSE mount exists)
        if os.path.exists("/app/data"):
            # Production: GCS FUSE mount
            file_path = Path(f"/app/data/uploads/applications/{filename}")
        else:
            # Development: Local storage
            file_path = Path(f"./uploads/applications/{filename}")
        
        # Verify file exists
        if not file_path.exists():
            logger.warning("Application image not found", filename=filename, path=str(file_path))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )
        
        # Verify it's an image file
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
        if file_path.suffix.lower() not in allowed_extensions:
            logger.warning("Invalid file type requested", filename=filename, extension=file_path.suffix)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type"
            )
        
        logger.info("Serving application image", filename=filename, path=str(file_path), size=file_path.stat().st_size)
        
        # Determine media type
        media_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg', 
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml'
        }
        media_type = media_type_map.get(file_path.suffix.lower(), 'application/octet-stream')
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename,
            headers={"Cache-Control": "public, max-age=3600"}  # Cache for 1 hour
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to serve application image", filename=filename, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to serve image"
        )
