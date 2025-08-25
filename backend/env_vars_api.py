from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
import structlog

from auth import get_current_user
from database import get_database

logger = structlog.get_logger()

router = APIRouter(prefix="/env-vars", tags=["env-vars"])

@router.get("", response_model=Dict[str, str])
async def get_user_env_vars(current_user: Dict = Depends(get_current_user)):
    """Get user environment variables"""
    user_id = current_user["sub"]
    
    try:
        db_manager = get_database()
        env_vars = await db_manager.get_user_env_vars(user_id)
        return env_vars or {}
    except Exception as e:
        logger.error("Failed to get user env vars", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get environment variables"
        )

@router.post("")
async def set_user_env_var(
    data: Dict[str, str],
    current_user: Dict = Depends(get_current_user)
):
    """Set user environment variable"""
    user_id = current_user["sub"]
    key = data.get("key")
    value = data.get("value")
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Key is required"
        )
    
    try:
        db_manager = get_database()
        await db_manager.set_user_env_var(user_id, key, value)
        
        from main import log_activity
        await log_activity(user_id, "env_var_set", f"Set environment variable: {key}")
        
        return {"message": "Environment variable set successfully"}
    except Exception as e:
        logger.error("Failed to set user env var", user_id=user_id, key=key, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set environment variable"
        )

@router.delete("/{key}")
async def delete_user_env_var(
    key: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete user environment variable"""
    user_id = current_user["sub"]
    
    try:
        db_manager = get_database()
        await db_manager.delete_user_env_var(user_id, key)
        
        from main import log_activity
        await log_activity(user_id, "env_var_deleted", f"Deleted environment variable: {key}")
        
        return {"message": "Environment variable deleted successfully"}
    except Exception as e:
        logger.error("Failed to delete user env var", user_id=user_id, key=key, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete environment variable"
        )