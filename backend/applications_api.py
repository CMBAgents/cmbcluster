from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import structlog

from auth import get_current_user
from models import ApplicationImage
from database import get_database

logger = structlog.get_logger()

router = APIRouter(prefix="/applications", tags=["applications"])

@router.get("", response_model=List[ApplicationImage])
async def list_public_applications(
    current_user: dict = Depends(get_current_user)
):
    """List available applications for all users"""
    try:
        logger.info("Listing public applications", user_id=current_user.get('sub'))
        db = get_database()
        applications = await db.list_applications()
        logger.info("Found applications for public listing", count=len(applications))
        return applications
        
    except Exception as e:
        logger.error("Failed to list applications", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list applications"
        )

@router.get("/{application_id}", response_model=ApplicationImage)
async def get_application_details(
    application_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get application details by ID"""
    try:
        db = get_database()
        application = await db.get_application(application_id)
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        return application
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get application details", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get application details"
        )
