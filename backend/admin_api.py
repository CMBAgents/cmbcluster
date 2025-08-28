from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional
import structlog
from datetime import datetime
import uuid

from auth import get_current_user, require_role
from models import User, UserRole, ActivityLog
from database import get_database

logger = structlog.get_logger()

router = APIRouter(prefix="/admin", tags=["admin"])

# Application/Image Management Models
from pydantic import BaseModel

class ApplicationImage(BaseModel):
    id: str
    name: str
    summary: str
    image_path: str
    icon_url: Optional[str] = None
    category: str = "research"
    created_at: datetime
    created_by: str
    is_active: bool = True
    tags: List[str] = []

class ApplicationImageRequest(BaseModel):
    name: str
    summary: str
    image_path: str
    icon_url: Optional[str] = None
    category: str = "research"
    tags: List[str] = []

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

# Application/Image Management Endpoints
@router.post("/applications", response_model=ApplicationImageResponse)
async def create_application(
    request: ApplicationImageRequest,
    current_user: Dict = Depends(require_admin_mode)
):
    """Create a new application image (admin only)"""
    try:
        db = get_database()
        
        application = ApplicationImage(
            id=str(uuid.uuid4()),
            name=request.name,
            summary=request.summary,
            image_path=request.image_path,
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

@router.get("/applications", response_model=List[ApplicationImage])
async def list_applications(
    current_user: Dict = Depends(require_admin_mode)
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
    current_user: Dict = Depends(require_admin_mode)
):
    """Update an application (admin only)"""
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

@router.delete("/applications/{application_id}")
async def delete_application(
    application_id: str,
    current_user: Dict = Depends(require_admin_mode)
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
    current_user: Dict = Depends(require_admin_mode)
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

@router.post("/users/{user_id}/promote")
async def promote_user_to_admin(
    user_id: str,
    request: UserManagementRequest,
    current_user: Dict = Depends(require_admin_mode)
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
    current_user: Dict = Depends(require_admin_mode)
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
    current_user: Dict = Depends(require_admin_mode)
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
    current_user: Dict = Depends(require_admin_mode)
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
    current_user: Dict = Depends(require_admin_mode)
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
