import os
import time
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import APIRouter
from authlib.integrations.starlette_client import OAuth
from starlette.responses import RedirectResponse
import structlog

from config import settings
from models import User, UserRole
from database import get_database

logger = structlog.get_logger()
security = HTTPBearer()
oauth_router = APIRouter()

# OAuth setup
oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@oauth_router.get("/login")
async def oauth_login(request: Request):
    """Initiate Google OAuth login"""
    redirect_uri = f"{settings.api_url}/auth/callback"
    
    logger.info("OAuth login initiated", redirect_uri=redirect_uri)
    
    return await oauth.google.authorize_redirect(request, redirect_uri)

@oauth_router.get("/callback")
async def oauth_callback(request: Request):
    """Handle OAuth callback from Google"""
    try:
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
        access_token = create_access_token(user)
        
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
    
    db = get_database()
    
    # Try to get existing user
    existing_user = await db.get_user(user_id)
    
    if existing_user:
        # Update existing user's last login
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
        return user
    
    return user

def create_access_token(user: User) -> str:
    """Create JWT access token for user"""
    payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "exp": datetime.utcnow() + timedelta(hours=settings.token_expire_hours),
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

def verify_token(token: str) -> Dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Get current authenticated user"""
    token = credentials.credentials
    
    if settings.dev_mode and token == "dev-token":
        # Development mode bypass
        exp = datetime.utcnow() + timedelta(hours=settings.token_expire_hours)
        return {
            "sub": "dev-user-123",
            "email": "dev@cmbcluster.local",
            "name": "Dev User",
            "role": "user",
            "exp": exp.timestamp(),
            "iat": datetime.utcnow().timestamp()
        }
    
    return verify_token(token)

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
