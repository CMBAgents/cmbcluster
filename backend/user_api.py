from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
import structlog

from auth import get_current_user, get_user_info
from database import get_database

logger = structlog.get_logger()

router = APIRouter(prefix="/profile", tags=["user"])

@router.get("")
async def get_user_profile(current_user: Dict = Depends(get_current_user)):
    """Get user profile information"""
    user_id = current_user["sub"]
    
    try:
        # Get user info from token
        user_info = await get_user_info(current_user)
        
        # Get additional user data from database
        db_manager = get_database()
        db_user = await db_manager.get_user(user_id)
        
        profile = {
            "id": user_id,
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "created_at": db_user.created_at if db_user else None,
            "last_login": db_user.last_login if db_user else None,
        }
        
        return profile
        
    except Exception as e:
        logger.error("Failed to get user profile", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )