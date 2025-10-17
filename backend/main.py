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
from fastapi.staticfiles import StaticFiles
from fastapi import Body, Path
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from auth import get_current_user, oauth_router, get_user_info
from starlette.middleware.sessions import SessionMiddleware
from config import settings
from models import (
    Environment, EnvironmentRequest, ActivityLog, 
    HealthCheck, User, PodStatus
)
from storage_models import EnvironmentRequestWithStorage
from pod_manager import PodManager
from database import DatabaseManager
import storage_api
import file_api

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
    from database import get_database
    app_state["db_manager"] = get_database()
    logger.info("Database initialized", db_path=settings.database_path)
    
    # Check file encryption health

    
    # Initialize pod manager (it will use the global database instance)
    app_state["pod_manager"] = PodManager()
    
    # Background tasks
    cleanup_task = asyncio.create_task(periodic_cleanup())
    shutdown_task = asyncio.create_task(auto_shutdown_task())
    
    yield
    
    # Shutdown
    logger.info("Shutting down CMBCluster API")
    cleanup_task.cancel()
    shutdown_task.cancel()
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

# CORS middleware with enhanced security
allowed_origins = settings.get_allowed_origins()

# Emergency fallback for production CORS issues
# If we have frontend_url and api_url from environment but they're not in allowed_origins, add them
import os
frontend_url = os.getenv('FRONTEND_URL')
api_url = os.getenv('API_URL')

if frontend_url and frontend_url not in allowed_origins:
    allowed_origins.append(frontend_url)
    logger.warning(f"Added missing FRONTEND_URL to CORS origins: {frontend_url}")

if api_url and api_url not in allowed_origins:
    allowed_origins.append(api_url)
    logger.warning(f"Added missing API_URL to CORS origins: {api_url}")

logger.info(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type", 
        "X-Requested-With",
        "X-CSRF-Token",
        "X-Client-Version",
        "X-Client-Type"
    ],
    expose_headers=["X-Total-Count"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Add SessionMiddleware LAST - Required for OAuth
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.secret_key,
    max_age=settings.token_expire_hours * 3600  # Convert hours to seconds
)
# Security
security = HTTPBearer()

# Include routers - using working paths from Streamlit frontend
app.include_router(oauth_router, prefix="/auth")

# Storage endpoints: /storage/* (not /api/user/storage/*)  
 # storage_api.router already has prefix="/storage"

# Files endpoints: /user-files/* (not /api/user/files/*)
import file_api
app.include_router(oauth_router, prefix="/auth")
app.include_router(storage_api.router)
app.include_router(file_api.router)

# Admin and application endpoints
import admin_api
import applications_api
app.include_router(admin_api.router)
app.include_router(applications_api.router)

# NOTE: Static file serving is handled by the dedicated endpoint below
# at /data/uploads/applications/{filename} instead of using app.mount()
# to avoid conflicts and allow proper error handling and logging


# Remove non-working router includes - main.py direct endpoints are used instead
# import environment_api  
# import env_vars_api   
# import user_api
# app.include_router(environment_api.router, prefix="/api/user")
# app.include_router(env_vars_api.router, prefix="/api/user") 
# app.include_router(user_api.router, prefix="/api/user")

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    if settings.enable_security_headers:
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS for HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        if settings.csp_enabled:
            csp_parts = [
                f"default-src 'self'",
                f"script-src {' '.join(settings.csp_script_src)}",
                f"style-src {' '.join(settings.csp_style_src)}",
                f"font-src {' '.join(settings.csp_font_src)}",
                f"img-src {' '.join(settings.csp_img_src)}",
                f"connect-src {' '.join(settings.csp_connect_src)}",
                f"frame-ancestors 'none'",
                f"base-uri 'self'",
                f"form-action 'self'"
            ]
            response.headers["Content-Security-Policy"] = "; ".join(csp_parts)
    
    return response

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    if settings.enable_security_headers:
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS for HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        if settings.csp_enabled:
            csp_parts = [
                f"default-src 'self'",
                f"script-src {' '.join(settings.csp_script_src)}",
                f"style-src {' '.join(settings.csp_style_src)}",
                f"font-src {' '.join(settings.csp_font_src)}",
                f"img-src {' '.join(settings.csp_img_src)}",
                f"connect-src {' '.join(settings.csp_connect_src)}",
                f"frame-ancestors 'none'",
                f"base-uri 'self'",
                f"form-action 'self'"
            ]
            response.headers["Content-Security-Policy"] = "; ".join(csp_parts)
    
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with security context"""
    start_time = time.time()
    
    # Get client info for security logging
    client_ip = request.headers.get("X-Forwarded-For", 
                                   request.headers.get("X-Real-IP", 
                                   request.client.host if request.client else "unknown"))
    user_agent = request.headers.get("User-Agent", "unknown")
    
    # Special logging for OPTIONS requests to debug CORS issues
    if request.method == "OPTIONS":
        headers_dict = dict(request.headers)
        logger.warning("OPTIONS preflight request received", 
                      method=request.method,
                      url=str(request.url),
                      headers=headers_dict,
                      client_ip=client_ip)
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # Enhanced logging for security events
    log_data = {
        "method": request.method,
        "url": str(request.url),
        "status_code": response.status_code,
        "process_time": round(process_time, 4),
        "client_ip": client_ip,
        "user_agent": user_agent[:200],  # Truncate long user agents
    }
    
    # Log auth-related requests with higher priority
    if "/auth/" in str(request.url):
        log_data["auth_endpoint"] = True
        if settings.log_auth_events:
            logger.info("Auth request processed", **log_data)
    elif response.status_code >= 400:
        # Log errors for security monitoring  
        log_data["error"] = True
        if settings.log_security_events:
            logger.warning("HTTP error response", **log_data)
    else:
        logger.debug("HTTP request processed", **log_data)
    
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

@app.get("/data/uploads/applications/{filename}")
async def serve_application_image_direct(filename: str):
    """Direct endpoint to serve application images from GCS storage (without /admin prefix)"""
    from fastapi.responses import FileResponse
    import os
    from pathlib import Path
    
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

@app.post("/environments", tags=["environments"])
async def create_environment(
    request: EnvironmentRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Create a new user environment"""
    user_id = current_user["sub"]
    user_email = current_user["email"]
    
    logger.info("Creating environment", user_id=user_id, user_email=user_email, request=request.dict())
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
        
        # Start monitoring - only uptime-based auto-shutdown now
        # (No longer using inactivity-based monitoring since environments are standalone)
        # background_tasks.add_task(monitor_environment, user_id)
        
        await log_activity(user_id, "environment_created", f"Created environment {environment.pod_name}")
        
        return {
            "status": "created",
            "environment": environment,
            "message": "Environment created successfully"
        }
        
    except Exception as e:
        import traceback
        logger.error("Failed to create environment", 
                   user_id=user_id, 
                   error=str(e), 
                   traceback=traceback.format_exc())
        await log_activity(user_id, "environment_creation_failed", str(e))
        
        # Provide more detailed error message
        error_detail = f"Failed to create environment: {str(e)}"
        if "already exists" in str(e).lower():
            error_detail = "Environment with this configuration already exists"
        elif "resource" in str(e).lower():
            error_detail = "Insufficient resources available"
        elif "storage" in str(e).lower():
            error_detail = f"Storage configuration error: {str(e)}"
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )

@app.get("/environments/{env_id}/info", tags=["environments"])
async def get_environment_info(
    env_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get detailed environment information including uptime and shutdown warnings"""
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
        
        # Get user data for subscription info
        user = await db_manager.get_user(user_id)
        
        # Calculate uptime
        uptime_minutes = 0
        if environment.created_at:
            uptime_delta = datetime.utcnow() - environment.created_at
            uptime_minutes = int(uptime_delta.total_seconds() / 60)
        
        # Get auto-shutdown info
        from auto_shutdown_manager import get_auto_shutdown_manager
        shutdown_manager = get_auto_shutdown_manager()
        
        max_uptime = 60  # Default for free users
        auto_shutdown_enabled = True
        if user:
            max_uptime = user.max_uptime_minutes or 60
            auto_shutdown_enabled = user.auto_shutdown_enabled and user.subscription_tier == "free"
        
        # Check if warning was sent
        warning_sent = env_id in shutdown_manager.shutdown_warnings
        warning_time = shutdown_manager.shutdown_warnings.get(env_id)
        
        # Calculate time until shutdown
        time_until_shutdown = None
        if auto_shutdown_enabled and uptime_minutes < max_uptime:
            time_until_shutdown = max_uptime - uptime_minutes
        
        return {
            "environment": environment,
            "uptime_minutes": uptime_minutes,
            "max_uptime_minutes": max_uptime,
            "auto_shutdown_enabled": auto_shutdown_enabled,
            "time_until_shutdown_minutes": time_until_shutdown,
            "shutdown_warning_sent": warning_sent,
            "shutdown_warning_time": warning_time.isoformat() if warning_time else None,
            "subscription_tier": user.subscription_tier if user else "free"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get environment info", 
                    user_id=user_id, 
                    env_id=env_id, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get environment information"
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

@app.post("/environments/heartbeat", tags=["environments"])
async def send_heartbeat(current_user: Dict = Depends(get_current_user)):
    """Send heartbeat to keep environment alive"""
    user_id = current_user["sub"]
    
    try:
        # For now, just return success - in the future this could update last activity time
        # Currently environments are managed based on uptime, not activity
        await log_activity(user_id, "heartbeat", "Heartbeat sent")
        
        return {
            "status": "success",
            "message": "Heartbeat received"
        }
    except Exception as e:
        logger.error("Failed to process heartbeat", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process heartbeat"
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

class EnvVarRequest(BaseModel):
    key: str
    value: str

@app.post("/user-env-vars", tags=["user-env-vars"])
async def set_user_env_var(
    request: EnvVarRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Add or update an environment variable for the current user"""
    db_manager = app_state.get("db_manager")
    user_id = current_user["sub"]
    if not db_manager:
        raise HTTPException(status_code=500, detail="Database unavailable")
    try:
        await db_manager.set_user_env_var(user_id, request.key, request.value)
        return {"status": "success", "key": request.key, "value": request.value}
    except Exception as e:
        logger.error("Failed to set user env var", user_id=user_id, key=request.key, error=str(e))
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
# Note: Removed monitor_environment function since standalone environments 
# can't reliably report activity back to the main application

async def periodic_cleanup():
    """Periodic cleanup of failed/stuck resources only"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            logger.info("Running periodic cleanup for failed/stuck resources")
            
            # Only clean up truly failed or stuck pods, not based on inactivity
            # since we can't reliably detect activity in standalone environments
            pod_manager = app_state["pod_manager"]
            await pod_manager.cleanup_failed_pods()
            
        except Exception as e:
            logger.error("Error in periodic cleanup", error=str(e))

async def auto_shutdown_task():
    """Background task for auto-shutdown based on uptime"""
    while True:
        try:
            # Wait for the configured interval (default 5 minutes)
            await asyncio.sleep(settings.auto_shutdown_check_interval_minutes * 60)
            
            logger.debug("Running auto-shutdown check")
            
            # Import here to avoid circular imports
            from auto_shutdown_manager import get_auto_shutdown_manager
            
            shutdown_manager = get_auto_shutdown_manager()
            stats = await shutdown_manager.check_environments_for_shutdown()
            
            # Clean up old warning tracking data
            shutdown_manager.cleanup_warning_tracking()
            
            if stats["shutdown"] > 0 or stats["warned"] > 0:
                logger.info("Auto-shutdown task completed", stats=stats)
            else:
                logger.debug("Auto-shutdown task completed", stats=stats)
                
        except Exception as e:
            logger.error("Error in auto-shutdown task", error=str(e))

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.dev_mode,
        log_level="debug" if settings.debug else "info"
    )
