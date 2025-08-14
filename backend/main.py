import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import structlog
from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Body, Path
from fastapi.security import HTTPBearer

from .auth import get_current_user, oauth_router, get_user_info
from starlette.middleware.sessions import SessionMiddleware
from .config import settings
from .models import (
    Environment, EnvironmentRequest, ActivityLog, 
    HealthCheck, User, PodStatus
)
from .storage_models import EnvironmentRequestWithStorage
from .pod_manager import PodManager
from .database import DatabaseManager
from .storage_manager import StorageManager
from . import storage_api

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global state
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting CMBCluster API", version="1.0.0")
    app_state["start_time"] = time.time()
    
    # Initialize database
    from .database import get_database
    app_state["db_manager"] = get_database()
    logger.info("Database initialized", db_path=settings.database_path)
    
    # Initialize pod manager (it will use the global database instance)
    app_state["pod_manager"] = PodManager()
    
    # Initialize storage manager
    app.state.storage_manager = StorageManager()
    logger.info("Storage manager initialized")

    # Background tasks
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # Shutdown
    logger.info("Shutting down CMBCluster API")
    cleanup_task.cancel()
    if app_state.get("pod_manager"):
        await app_state["pod_manager"].cleanup_all()

app = FastAPI(
    title="CMBCluster API",
    description="Multi-tenant Streamlit Platform for Cosmology Research",
    version="1.0.0",
    docs_url="/docs" if settings.dev_mode else None,
    redoc_url="/redoc" if settings.dev_mode else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "https://localhost:8501",
        settings.frontend_url,
        f"https://*.{settings.base_domain}",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add SessionMiddleware LAST - Required for OAuth
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.secret_key,
    max_age=settings.token_expire_hours * 3600  # Convert hours to seconds
)
# Security
security = HTTPBearer()

# Include auth router
app.include_router(oauth_router, prefix="/auth", tags=["authentication"])

# Include storage router
app.include_router(storage_api.router)

# Include python_service router
from .python_service.main import router as science_router
app.include_router(science_router)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        "HTTP request processed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=round(process_time, 4)
    )
    
    return response

@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "service": "CMBCluster API",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs" if settings.dev_mode else "disabled"
    }

@app.get("/health", response_model=HealthCheck, tags=["health"])
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - app_state.get("start_time", time.time())
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        uptime=uptime
    )

@app.post("/environments", tags=["environments"])
async def create_environment(
    request: EnvironmentRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Create a new user environment"""
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
        
        # Start monitoring
        background_tasks.add_task(monitor_environment, user_id)
        
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

@app.get("/environments", tags=["environments"])
async def get_environment_status(current_user: Dict = Depends(get_current_user)):
    """Get current user's environment status"""
    user_id = current_user["sub"]
    pod_manager = app_state["pod_manager"]
    
    try:
        if await pod_manager.user_has_active_pod(user_id):
            environment = await pod_manager.get_user_environment(user_id)
            return {
                "active": True,
                "environment": environment
            }
        else:
            return {
                "active": False,
                "environment": None
            }
    except Exception as e:
        logger.error("Failed to get environment status", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get environment status"
        )


# Delete a specific environment by env_id (multi-env support)
from fastapi import Query

@app.delete("/environments", tags=["environments"])
async def delete_environment(
    env_id: str = Query(None, description="Environment ID to delete (optional, deletes latest if not provided)"),
    current_user: Dict = Depends(get_current_user)
):
    """Delete user's environment (optionally by env_id)"""
    user_id = current_user["sub"]
    user_email = current_user["email"]
    pod_manager = app_state["pod_manager"]

    # Debug logging
    logger.info("Delete environment request", user_id=user_id, env_id=env_id, user_email=user_email)

    try:
        if env_id:
            logger.info("Deleting specific environment", env_id=env_id)
            await pod_manager.delete_user_environment(user_id, user_email, env_id=env_id)
        else:
            logger.info("Deleting latest environment")
            await pod_manager.delete_user_environment(user_id, user_email)
        await log_activity(user_id, "environment_deleted", f"Environment deleted (env_id={env_id})")

        logger.info("Environment deletion successful", user_id=user_id, env_id=env_id)
        return {
            "status": "deleted",
            "message": "Environment deleted successfully"
        }
    except ValueError as e:
        # Handle case where environment is not found
        logger.warning("Environment not found for deletion", user_id=user_id, env_id=env_id, error=str(e))
        await log_activity(user_id, "environment_deletion_failed", f"Environment not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment not found: {str(e)}"
        )
    except Exception as e:
        logger.error("Failed to delete environment", user_id=user_id, env_id=env_id, error=str(e), exc_info=True)
        await log_activity(user_id, "environment_deletion_failed", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete environment: {str(e)}"
        )


@app.post("/environments/heartbeat", tags=["environments"])
async def environment_heartbeat(current_user: Dict = Depends(get_current_user)):
    """Update environment activity timestamp"""
    user_id = current_user["sub"]
    pod_manager = app_state["pod_manager"]
    
    try:
        await pod_manager.update_user_activity(user_id)
        return {
            "status": "updated",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error("Failed to update heartbeat", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update activity"
        )

@app.get("/activity", tags=["activity"])
async def get_user_activity(
    limit: int = 50,
    current_user: Dict = Depends(get_current_user)
):
    """Get user activity log"""
    user_id = current_user["sub"]
    
    try:
        activities = await get_user_activity_log(user_id, limit)
        return {"activities": activities}
    except Exception as e:
        logger.error("Failed to get activity log", user_id=user_id, error=str(e))
        return {"activities": []}

@app.get("/users/me", response_model=User, tags=["users"])
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current user information"""
    return get_user_info(current_user)

@app.get("/environments/list", tags=["environments"])
async def list_user_environments(current_user: Dict = Depends(get_current_user)):
    """List all environments for the current user (multi-environment support)"""
    user_id = current_user["sub"]
    pod_manager = app_state["pod_manager"]
    
    logger.info("List environments request", user_id=user_id)
    
    try:
        # Use the new method to get all environments with updated status
        envs = await pod_manager.get_user_environments(user_id)
        
        # Convert Environment objects to dicts for JSON serialization
        env_dicts = []
        for env in envs:
            env_dict = env.dict() if hasattr(env, 'dict') else env.__dict__
            # Ensure both 'id' and 'env_id' are available for frontend compatibility
            if 'env_id' in env_dict and 'id' not in env_dict:
                env_dict['id'] = env_dict['env_id']
            logger.info("Environment serialized", env_dict=env_dict)
            env_dicts.append(env_dict)
        
        logger.info("Returning environments", count=len(env_dicts), user_id=user_id)
        return {"environments": env_dicts}
    except Exception as e:
        logger.error("Failed to list environments", user_id=user_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list environments: {str(e)}"
        )

# --- User Environment Variables API ---
@app.get("/user-env-vars", tags=["user-env-vars"])
async def get_user_env_vars(current_user: Dict = Depends(get_current_user)):
    """Get all environment variables for the current user"""
    db_manager = app_state.get("db_manager")
    user_id = current_user["sub"]
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database unavailable")
    try:
        env_vars = await db_manager.get_user_env_vars(user_id)
        return {"env_vars": env_vars}
    except Exception as e:
        logger.error("Failed to get user env vars", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get environment variables")

@app.post("/user-env-vars", tags=["user-env-vars"])
async def set_user_env_var(
    key: str = Body(..., embed=True),
    value: str = Body(..., embed=True),
    current_user: Dict = Depends(get_current_user)
):
    """Add or update an environment variable for the current user"""
    db_manager = app_state.get("db_manager")
    user_id = current_user["sub"]
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database unavailable")
    try:
        await db_manager.set_user_env_var(user_id, key, value)
        return {"status": "success", "key": key, "value": value}
    except Exception as e:
        logger.error("Failed to set user env var", user_id=user_id, key=key, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to set environment variable")

@app.delete("/user-env-vars/{key}", tags=["user-env-vars"])
async def delete_user_env_var(
    key: str = Path(...),
    current_user: Dict = Depends(get_current_user)
):
    """Delete an environment variable for the current user"""
    db_manager = app_state.get("db_manager")
    user_id = current_user["sub"]
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database unavailable")
    try:
        await db_manager.delete_user_env_var(user_id, key)
        return {"status": "success", "key": key}
    except Exception as e:
        logger.error("Failed to delete user env var", user_id=user_id, key=key, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete environment variable")

# Background tasks
async def monitor_environment(user_id: str):
    """Monitor environment activity and cleanup if inactive"""
    pod_manager = app_state["pod_manager"]
    
    while await pod_manager.user_has_active_pod(user_id):
        await asyncio.sleep(300)  # Check every 5 minutes
        
        try:
            environment = await pod_manager.get_user_environment(user_id)
            if environment and environment.last_activity:
                inactive_time = datetime.utcnow() - environment.last_activity
                
                if inactive_time > timedelta(hours=settings.max_inactive_hours):
                    logger.info("Cleaning up inactive environment", user_id=user_id)
                    await pod_manager.delete_user_environment(user_id)
                    await log_activity(user_id, "environment_auto_cleanup", "Environment cleaned up due to inactivity")
                    break
        except Exception as e:
            logger.error("Error monitoring environment", user_id=user_id, error=str(e))
            break

async def periodic_cleanup():
    """Periodic cleanup of stale resources"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            logger.info("Running periodic cleanup")
            
            pod_manager = app_state["pod_manager"]
            await pod_manager.cleanup_stale_pods()
            
        except Exception as e:
            logger.error("Error in periodic cleanup", error=str(e))

async def log_activity(user_id: str, action: str, details: str):
    """Log user activity to database"""
    try:
        db_manager = app_state.get("db_manager")
        if not db_manager:
            logger.error("Database manager not available for activity logging")
            return
            
        activity = ActivityLog(
            id=f"{user_id}_{int(time.time())}",
            user_id=user_id,
            action=action,
            details=details,
            timestamp=datetime.utcnow(),
            status="success" if "failed" not in action.lower() else "error"
        )
        
        await db_manager.log_activity(activity)
        
        logger.info(
            "User activity logged",
            user_id=user_id,
            action=action,
            details=details
        )
        
    except Exception as e:
        logger.error("Failed to log activity", user_id=user_id, error=str(e))

async def get_user_activity_log(user_id: str, limit: int = 50) -> List[Dict]:
    """Get user activity log from database"""
    try:
        db_manager = app_state.get("db_manager")
        if not db_manager:
            logger.error("Database manager not available for activity retrieval")
            return []
            
        activities = await db_manager.get_user_activity(user_id, limit)
        
        # The database already returns the activities in the right format
        return activities
        
    except Exception as e:
        logger.error("Failed to get activity log", user_id=user_id, error=str(e))
        return []


from fastapi.responses import StreamingResponse

async def fake_llm_streamer():
    """A fake LLM streamer that yields text chunks."""
    text = "This is a simulated stream of tokens from a large language model. " \
           "Each word is sent as a separate chunk to demonstrate live updates " \
           "on the client-side."
    words = text.split(" ")
    for word in words:
        yield f"data: {word} \n\n"
        await asyncio.sleep(0.1)

@app.get("/stream", tags=["streaming"])
async def stream(current_user: Dict = Depends(get_current_user)):
    """A streaming endpoint to simulate LLM token generation."""
    return StreamingResponse(fake_llm_streamer(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.dev_mode,
        log_level="debug" if settings.debug else "info"
    )
