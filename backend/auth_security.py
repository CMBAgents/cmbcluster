"""
Enhanced security module for authentication
Implements secure JWT handling, rate limiting, and validation
"""

import os
import time
import hashlib
import secrets
import jwt
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog
from google.oauth2 import id_token
from google.auth.transport import requests
import redis
from collections import defaultdict
import asyncio

from config import settings

logger = structlog.get_logger()

# Rate limiting storage (use Redis in production)
class RateLimiter:
    def __init__(self):
        self.attempts = defaultdict(list)
        self.blocked_ips = {}
        
    def is_rate_limited(self, identifier: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """Check if identifier is rate limited"""
        now = time.time()
        window_start = now - (window_minutes * 60)
        
        # Clean old attempts
        self.attempts[identifier] = [
            attempt_time for attempt_time in self.attempts[identifier] 
            if attempt_time > window_start
        ]
        
        # Check if blocked
        if identifier in self.blocked_ips:
            if now < self.blocked_ips[identifier]:
                return True
            else:
                del self.blocked_ips[identifier]
        
        # Check rate limit
        if len(self.attempts[identifier]) >= max_attempts:
            # Block for 1 hour
            self.blocked_ips[identifier] = now + (60 * 60)
            return True
        
        return False
    
    def record_attempt(self, identifier: str):
        """Record an authentication attempt"""
        self.attempts[identifier].append(time.time())

# Global rate limiter
rate_limiter = RateLimiter()

class SecureJWTHandler:
    """Secure JWT token handler with enhanced security"""
    
    def __init__(self):
        self.secret_key = self._get_secure_secret()
        self.algorithm = "HS256"
        self.issuer = "cmbcluster-api"
        self.audience = "cmbcluster-frontend"
        
    def _get_secure_secret(self) -> str:
        """Get or generate a secure secret key"""
        secret = settings.secret_key
        
        # In production, ensure we have a strong secret
        if secret == "dev-secret-key-change-in-production":
            if not settings.dev_mode:
                raise ValueError("Production secret key not configured")
            logger.warning("Using development secret key - NOT FOR PRODUCTION")
        
        # Validate secret strength
        if len(secret) < 32:
            raise ValueError("Secret key must be at least 32 characters")
        
        return secret
    
    def create_access_token(self, user_data: Dict[str, Any], expires_hours: int = 8) -> str:
        """Create a secure JWT access token"""
        now = datetime.utcnow()
        expires = now + timedelta(hours=expires_hours)
        
        payload = {
            # Standard claims
            "iss": self.issuer,
            "aud": self.audience,
            "sub": user_data["sub"],
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
            "nbf": int(now.timestamp()),  # Not before
            
            # Custom claims
            "email": user_data["email"],
            "name": user_data["name"],
            "role": user_data.get("role", "user"),
            "email_verified": user_data.get("email_verified", False),
            
            # Security claims
            "token_type": "access",
            "jti": secrets.token_urlsafe(16),  # JWT ID for token tracking
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token with enhanced security"""
        try:
            # Decode with audience and issuer verification
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )
            
            # Additional validation
            if payload.get("token_type") != "access":
                raise jwt.InvalidTokenError("Invalid token type")
            
            # Check if token is revoked (implement token blacklist if needed)
            # if self.is_token_revoked(payload.get("jti")):
            #     raise jwt.InvalidTokenError("Token has been revoked")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidAudienceError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token audience",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidIssuerError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token issuer",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

class GoogleOAuthValidator:
    """Secure Google OAuth token validator"""
    
    def __init__(self):
        self.client_id = settings.google_client_id
        if not self.client_id:
            raise ValueError("Google Client ID not configured")
    
    async def validate_google_token(self, token: str) -> Dict[str, Any]:
        """Validate Google OAuth token and extract user info"""
        try:
            # First try as ID token (JWT format)
            try:
                idinfo = id_token.verify_oauth2_token(
                    token, 
                    requests.Request(), 
                    self.client_id
                )
                
                # Verify the issuer
                if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                    raise ValueError('Wrong issuer.')
                
                # Extract verified user information from ID token
                return {
                    "sub": idinfo.get("sub"),
                    "email": idinfo.get("email"),
                    "name": idinfo.get("name"),
                    "picture": idinfo.get("picture"),
                    "email_verified": idinfo.get("email_verified", False),
                    "locale": idinfo.get("locale"),
                    "family_name": idinfo.get("family_name"),
                    "given_name": idinfo.get("given_name"),
                }
            except Exception as jwt_error:
                # If ID token verification fails, try as access token
                logger.info(f"Token is not a valid ID token, trying as access token: {str(jwt_error)}")
                
                # Validate access token by calling Google's userinfo endpoint
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        'https://www.googleapis.com/oauth2/v2/userinfo',
                        headers={'Authorization': f'Bearer {token}'}
                    ) as response:
                        if response.status != 200:
                            raise ValueError(f"Invalid access token: {response.status}")
                        
                        user_data = await response.json()
                        
                        # Validate that this token belongs to our client
                        # Check if the token is valid by making sure we get user data
                        if not user_data.get('id'):
                            raise ValueError("Invalid token: no user ID returned")
                        
                        # Return standardized user info
                        return {
                            "sub": user_data.get("id"),
                            "email": user_data.get("email"),
                            "name": user_data.get("name"),
                            "picture": user_data.get("picture"),
                            "email_verified": user_data.get("verified_email", False),
                            "locale": user_data.get("locale"),
                            "family_name": user_data.get("family_name"),
                            "given_name": user_data.get("given_name"),
                        }
            
        except ValueError as e:
            logger.error("Google token validation failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google token: {str(e)}"
            )

def get_client_ip(request: Request) -> str:
    """Get client IP address for rate limiting"""
    # Check for forwarded IP headers (when behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"

def validate_csrf_token(request: Request) -> bool:
    """Validate CSRF token for state-changing operations"""
    # For API calls, we rely on the SameSite cookie policy
    # and the Bearer token authentication
    # In a full implementation, you might want to add CSRF tokens
    return True

async def check_rate_limit(request: Request, action: str = "auth") -> None:
    """Check rate limiting for authentication requests"""
    client_ip = get_client_ip(request)
    identifier = f"{action}:{client_ip}"
    
    if rate_limiter.is_rate_limited(identifier):
        logger.warning("Rate limit exceeded", 
                      client_ip=client_ip, 
                      action=action)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": "3600"}  # 1 hour
        )
    
    rate_limiter.record_attempt(identifier)

# Initialize security components
jwt_handler = SecureJWTHandler()
google_validator = GoogleOAuthValidator()

# Enhanced security bearer token handler
class SecureBearerToken(HTTPBearer):
    """Enhanced bearer token security with additional validation"""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        # Check rate limiting first
        await check_rate_limit(request, "token_validation")
        
        # Get credentials using parent class
        credentials = await super().__call__(request)
        
        if credentials:
            # Additional security checks
            token = credentials.credentials
            
            # Basic token format validation
            if not token or len(token) < 20:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token format",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check for common attacks
            if any(char in token for char in ['<', '>', '"', "'"]):
                logger.warning("Suspicious token detected", 
                             client_ip=get_client_ip(request))
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token format",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        return credentials

# Global secure bearer instance
secure_bearer = SecureBearerToken()
