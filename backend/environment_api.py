from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from typing import Dict, List
import structlog
from datetime import datetime
import time

from auth import get_current_user
from models import Environment, EnvironmentRequest, HealthCheck, User, PodStatus
from storage_models import EnvironmentRequestWithStorage

logger = structlog.get_logger()

router = APIRouter(prefix="/environments", tags=["environments"])

@router.get("", response_model=List[Environment])
async def list_environments(current_user: Dict = Depends(get_current_user)):
    """List user environments"""
    # This will be implemented by moving the logic from main.py
    from main import app_state
    
    user_id = current_user["sub"]
    pod_manager = app_state["pod_manager"]
    
    try:
        # Get user environment
        environment = await pod_manager.get_user_environment(user_id)
        if environment:
            return [environment]
        return []
    except Exception as e:
        logger.error("Failed to list environments", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list environments"
        )

@router.post("", response_model=dict)
async def create_environment(
    request: EnvironmentRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Create a new user environment"""
    from main import app_state, log_activity
    
    user_id = current_user["sub"]
    user_email = current_user["email"]
    
    pod_manager = app_state["pod_manager"]
    
    try:
        # Check if user already has active environment
        if await pod_manager.user_has_active_pod(user_id):
            existing_env = await pod_manager.get_user_environment(user_id)
            await log_activity(user_id, "environment_access", "Accessed existing environment")
            return {
                "status": "existing",
                "environment": existing_env,
                "message": "Environment already exists"
            }
        
        # Create new environment
        environment = await pod_manager.create_user_environment(
            user_id=user_id,
            user_email=user_email,
            config=request
        )
        
        await log_activity(user_id, "environment_created", f"Created environment {environment.pod_name}")
        
        return {
            "status": "created",
            "environment": environment,
            "message": "Environment created successfully"
        }
        
    except Exception as e:
        logger.error("Failed to create environment", user_id=user_id, error=str(e))
        await log_activity(user_id, "environment_creation_failed", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create environment"
        )

@router.get("/{env_id}", response_model=dict)
async def get_environment_by_id(
    env_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get environment by ID"""
    from main import app_state
    
    user_id = current_user["sub"]
    
    try:
        # Get environment
        db_manager = app_state.get("db_manager")
        environment = await db_manager.get_environment(user_id, env_id)
        
        if not environment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Environment not found"
            )
            
        return {"environment": environment}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get environment", user_id=user_id, env_id=env_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get environment"
        )

@router.post("/{env_id}/restart")
async def restart_environment(
    env_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Restart environment"""
    from main import app_state, log_activity
    
    user_id = current_user["sub"]
    pod_manager = app_state["pod_manager"]
    
    try:
        # Restart environment
        await pod_manager.restart_user_environment(user_id)
        await log_activity(user_id, "environment_restarted", f"Restarted environment {env_id}")
        
        return {"message": "Environment restarted successfully"}
        
    except Exception as e:
        logger.error("Failed to restart environment", user_id=user_id, env_id=env_id, error=str(e))
        await log_activity(user_id, "environment_restart_failed", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restart environment"
        )

@router.post("/{env_id}/stop")
async def stop_environment(
    env_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Stop environment"""
    from main import app_state, log_activity
    
    user_id = current_user["sub"]
    pod_manager = app_state["pod_manager"]
    
    try:
        # Stop environment
        await pod_manager.stop_user_environment(user_id)
        await log_activity(user_id, "environment_stopped", f"Stopped environment {env_id}")
        
        return {"status": "success", "message": "Environment stopped successfully"}
        
    except Exception as e:
        logger.error("Failed to stop environment", user_id=user_id, env_id=env_id, error=str(e))
        await log_activity(user_id, "environment_stop_failed", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop environment"
        )

@router.delete("/{env_id}")
async def delete_environment(
    env_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete environment"""
    from main import app_state, log_activity
    
    user_id = current_user["sub"]
    pod_manager = app_state["pod_manager"]
    
    try:
        # Delete environment
        await pod_manager.delete_user_environment(user_id)
        await log_activity(user_id, "environment_deleted", f"Deleted environment {env_id}")
        
        return {"status": "deleted", "message": "Environment deleted successfully"}
        
    except Exception as e:
        logger.error("Failed to delete environment", user_id=user_id, env_id=env_id, error=str(e))
        await log_activity(user_id, "environment_deletion_failed", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete environment"
        )