import os
import time
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import APIRouter, Body
from authlib.integrations.starlette_client import OAuth
from starlette.responses import RedirectResponse
import structlog
from pydantic import BaseModel

from config import settings
from models import User, UserRole
from database import get_database
from auth_security import (
    jwt_handler, 
    google_validator, 
    secure_bearer, 
    check_rate_limit,
    get_client_ip,
    validate_csrf_token
)

logger = structlog.get_logger()
oauth_router = APIRouter()

# OAuth setup (for legacy support if needed)
oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Pydantic models for requests
class TokenExchangeRequest(BaseModel):
    google_token: str
    user_info: Dict[str, Any]

class TokenVerifyResponse(BaseModel):
    valid: bool
    user_data: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None

@oauth_router.post("/token-exchange")
async def exchange_google_token(
    request: Request,
    token_request: TokenExchangeRequest
):
    """
    Exchange Google OAuth token for backend JWT token
    This is the secure token exchange endpoint called by NextAuth
    """
    try:
        # Rate limiting
        await check_rate_limit(request, "token_exchange")
        
        client_ip = get_client_ip(request)
        logger.info("Token exchange request", client_ip=client_ip)
        
        # Validate Google token
        user_info = await google_validator.validate_google_token(token_request.google_token)
        
        # Additional security checks
        if not user_info.get("email_verified", False):
            logger.warning("Unverified email attempted login", 
                         email=user_info.get("email"),
                         client_ip=client_ip)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email address not verified"
            )
        
        # Create or update user in database
        user = await create_or_update_user(user_info)
        
        # Create secure JWT token
        token_data = {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "email_verified": True
        }
        
        access_token = jwt_handler.create_access_token(token_data)
        
        logger.info("Token exchange successful", 
                   user_id=user.id,
                   user_email=user.email,
                   client_ip=client_ip)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 8 * 60 * 60,  # 8 hours
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role.value
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token exchange failed", 
                    error=str(e),
                    client_ip=get_client_ip(request))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@oauth_router.get("/verify-token")
async def verify_token_endpoint(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(secure_bearer)
):
    """
    Verify JWT token endpoint
    Called by NextAuth to validate backend tokens
    """
    try:
        # Rate limiting
        await check_rate_limit(request, "token_verify")
        
        token = credentials.credentials
        
        # Verify token using secure handler
        payload = jwt_handler.verify_token(token)
        
        logger.debug("Token verification successful", 
                    user_id=payload.get("sub"),
                    client_ip=get_client_ip(request))
        
        return TokenVerifyResponse(
            valid=True,
            user_data={
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "name": payload.get("name"),
                "role": payload.get("role")
            },
            expires_at=datetime.fromtimestamp(payload.get("exp", 0))
        )
        
    except HTTPException:
        # Token verification failed - return specific error
        raise
    except Exception as e:
        logger.error("Token verification error", 
                    error=str(e),
                    client_ip=get_client_ip(request))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )

@oauth_router.post("/refresh-token")
async def refresh_token_endpoint(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(secure_bearer)
):
    """
    Refresh JWT token endpoint
    Provides token rotation for enhanced security
    """
    try:
        # Rate limiting
        await check_rate_limit(request, "token_refresh")
        
        token = credentials.credentials
        
        # Verify current token
        payload = jwt_handler.verify_token(token)
        
        # Get fresh user data from database
        db = get_database()
        user = await db.get_user(payload.get("sub"))
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account inactive"
            )
        
        # Create new token with fresh data
        token_data = {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "email_verified": True
        }
        
        new_token = jwt_handler.create_access_token(token_data)
        
        logger.info("Token refresh successful", 
                   user_id=user.id,
                   client_ip=get_client_ip(request))
        
        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_in": 8 * 60 * 60,  # 8 hours
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", 
                    error=str(e),
                    client_ip=get_client_ip(request))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

# Legacy OAuth endpoints (kept for backward compatibility)
@oauth_router.get("/login")
async def oauth_login(request: Request):
    """Initiate Google OAuth login (legacy endpoint)"""
    await check_rate_limit(request, "oauth_login")
    
    redirect_uri = f"{settings.api_url}/auth/callback"
    logger.info("OAuth login initiated", redirect_uri=redirect_uri)
    
    return await oauth.google.authorize_redirect(request, redirect_uri)

@oauth_router.get("/callback")
async def oauth_callback(request: Request):
    """Handle OAuth callback from Google (legacy endpoint)"""
    try:
        await check_rate_limit(request, "oauth_callback")
        
        # Get access token from Google
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from OAuth provider"
            )
        
        # Create or update user
        user = await create_or_update_user(user_info)
        
        # Create JWT access token
        token_data = {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "email_verified": True
        }
        
        access_token = jwt_handler.create_access_token(token_data)
        
        # Redirect to frontend with token
        frontend_url = f"{settings.frontend_url}?token={access_token}"
        
        logger.info("OAuth login successful", 
                   user_id=user.id, 
                   user_email=user.email)
        
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        logger.error("OAuth callback failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )

@oauth_router.post("/exchange")
async def exchange_nextauth_jwt(request: Request):
    """Exchange NextAuth JWT token for backend JWT token"""
    try:
        # Get the request body
        body = await request.json()
        nextauth_token = body.get('nextauth_token')
        
        if not nextauth_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing nextauth_token"
            )
        
        # Validate and decode NextAuth JWT token
        import json
        import base64
        
        # Basic JWT structure validation
        parts = nextauth_token.split('.')
        if len(parts) != 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JWT token format"
            )
        
        # Decode the payload to extract user info
        try:
            # Decode the payload (we'll validate signature using NextAuth secret)
            payload_part = parts[1]
            # Add padding if needed
            payload_part += '=' * (4 - len(payload_part) % 4)
            payload_bytes = base64.urlsafe_b64decode(payload_part)
            token_payload = json.loads(payload_bytes)
            
            # Validate token hasn't expired
            if token_payload.get('exp') and token_payload['exp'] < time.time():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="NextAuth token has expired"
                )
            
            # Extract user info from JWT payload
            user_info = {
                'sub': token_payload.get('sub'),
                'email': token_payload.get('email'),
                'name': token_payload.get('name'),
            }
            
            # Validate required fields
            for field in ['sub', 'email', 'name']:
                if not user_info.get(field):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Missing required field in JWT: {field}"
                    )
                
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JWT token payload"
            )
        
        # Validate JWT signature with NextAuth secret
        nextauth_secret = os.getenv('NEXTAUTH_SECRET')
        if not nextauth_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="NextAuth secret not configured"
            )
        
        try:
            # Verify the JWT signature using NextAuth secret
            verified_payload = jwt.decode(
                nextauth_token,
                nextauth_secret,
                algorithms=['HS256']  # NextAuth uses HS256 by default
            )
            
            # Update user_info with verified payload data
            user_info = {
                'sub': verified_payload.get('sub'),
                'email': verified_payload.get('email'),
                'name': verified_payload.get('name'),
            }
            
        except JWTError as e:
            logger.error("NextAuth JWT verification failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid NextAuth JWT signature"
            )
        
        # Create or update user in our database using JWT payload data
        user = await create_or_update_user(user_info)
        
        # Create our backend JWT token
        backend_token = create_access_token(user)
        
        logger.info("JWT token exchange successful", 
                   user_id=user.id, 
                   user_email=user.email)
        
        return {
            "status": "success",
            "access_token": backend_token,
            "token_type": "bearer",
            "expires_in": settings.token_expire_hours * 3600,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role.value
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("JWT exchange failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token exchange failed: {str(e)}"
        )

async def create_or_update_user(user_info: Dict) -> User:
    """Create or update user from OAuth info using database"""
    user_id = user_info.get('sub')
    email = user_info.get('email')
    name = user_info.get('name', email)
    
    if not user_id or not email:
        raise ValueError("Missing required user information")
    
    db = get_database()
    
    # Try to get existing user
    existing_user = await db.get_user(user_id)
    
    if existing_user:
        # Update existing user's last login and info
        await db.update_user_login(user_id)
        existing_user.last_login = datetime.utcnow()
        existing_user.name = name
        existing_user.email = email
        return existing_user
    else:
        # Create new user
        user = User(
            id=user_id,
            email=email,
            name=name,
            role=UserRole.USER,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow(),
            is_active=True
        )
        await db.create_user(user)
        
        logger.info("New user created", 
                   user_id=user_id, 
                   email=email)
        
        return user

def create_access_token(user: User) -> str:
    """Create JWT access token for user (legacy compatibility)"""
    token_data = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "email_verified": True
    }
    return jwt_handler.create_access_token(token_data)

def verify_token(token: str) -> Dict:
    """Verify and decode JWT token (legacy compatibility)"""
    return jwt_handler.verify_token(token)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(secure_bearer)) -> Dict:
    """Get current authenticated user with enhanced security"""
    token = credentials.credentials
    
    # Development mode bypass (with security warnings)
    if settings.dev_mode and token == "dev-token":
        logger.warning("Development mode authentication bypass used - NOT FOR PRODUCTION")
        exp = datetime.utcnow() + timedelta(hours=settings.token_expire_hours)
        return {
            "sub": "dev-user-123",
            "email": "dev@cmbcluster.local",
            "name": "Dev User",
            "role": "user",
            "exp": exp.timestamp(),
            "iat": datetime.utcnow().timestamp()
        }
    
    # Use secure token verification
    return jwt_handler.verify_token(token)

async def get_user_info(user_data: Dict) -> User:
    """Get user info from token data using database"""
    user_id = user_data["sub"]
    
    db = get_database()
    user = await db.get_user(user_id)
    
    if user:
        return user
    
    # Create user if not exists (shouldn't happen in normal flow)
    user = User(
        id=user_id,
        email=user_data.get("email", "unknown@example.com"),
        name=user_data.get("name", "Unknown User"),
        role=UserRole(user_data.get("role", "user")),
        created_at=datetime.utcnow(),
        is_active=True
    )
    await db.create_user(user)
    return user

def require_role(required_role: UserRole):
    """Decorator to require specific user role"""
    def role_checker(current_user: Dict = Depends(get_current_user)):
        user_role = UserRole(current_user.get("role", "user"))
        if user_role != required_role and user_role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Additional security endpoints
@oauth_router.post("/logout")
async def logout_endpoint(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(secure_bearer)
):
    """
    Logout endpoint - invalidate token
    In a full implementation, you would add the token to a blacklist
    """
    try:
        token = credentials.credentials
        payload = jwt_handler.verify_token(token)
        
        logger.info("User logout", 
                   user_id=payload.get("sub"),
                   client_ip=get_client_ip(request))
        
        # In a production system, add token to blacklist here
        # blacklist_token(payload.get("jti"))
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error("Logout error", error=str(e))
        return {"message": "Logout completed"}
