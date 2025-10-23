"""
Google OAuth authentication provider implementation.

Handles authentication using Google OAuth 2.0 / OpenID Connect.
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException, status
import structlog
from google.oauth2 import id_token
from google.auth.transport import requests
import httpx

from .base import AuthProvider

logger = structlog.get_logger()


class GoogleAuthProvider(AuthProvider):
    """
    Google OAuth 2.0 authentication provider.

    Uses Google's OpenID Connect implementation to validate tokens
    and retrieve user information.
    """

    def __init__(self, client_id: str, client_secret: str, **kwargs):
        """
        Initialize Google OAuth provider.

        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.client_id = client_id
        self.client_secret = client_secret
        self.issuer = "https://accounts.google.com"
        self.userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"

        # Validate configuration
        if not self.client_id or self.client_id == "build-time-placeholder":
            logger.warning("Google OAuth client ID not configured properly")
        if not self.client_secret or self.client_secret == "build-time-placeholder":
            logger.warning("Google OAuth client secret not configured properly")

        logger.info("Google OAuth provider initialized", client_id=self.client_id[:20] + "...")

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a Google ID token or access token.

        For ID tokens, uses Google's token verification library.
        For access tokens, calls the userinfo endpoint.

        Args:
            token: Google ID token or access token

        Returns:
            Dict containing validated user information

        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Try to validate as ID token first (preferred)
            try:
                id_info = id_token.verify_oauth2_token(
                    token,
                    requests.Request(),
                    self.client_id
                )

                # Verify issuer
                if id_info.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
                    raise ValueError("Invalid issuer")

                # Verify audience
                if id_info.get("aud") != self.client_id:
                    raise ValueError("Invalid audience")

                logger.info("Google ID token validated successfully",
                           user_id=id_info.get("sub"),
                           email=id_info.get("email"))

                return self.normalize_user_info(id_info)

            except Exception as id_token_error:
                # If ID token validation fails, try as access token
                logger.debug("Not a valid ID token, trying as access token",
                           error=str(id_token_error))

                user_info = await self.get_user_info(token)
                return self.normalize_user_info(user_info)

        except Exception as e:
            logger.error("Google token validation failed",
                        error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google token: {str(e)}"
            )

    def get_oauth_config(self) -> Dict[str, Any]:
        """
        Get Google OAuth configuration.

        Returns:
            OAuth configuration for Google
        """
        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_endpoint": "https://oauth2.googleapis.com/token",
            "userinfo_endpoint": self.userinfo_endpoint,
            "issuer": self.issuer,
            "scopes": ["openid", "email", "profile"],
            "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration"
        }

    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Get user information from Google using an access token.

        Args:
            token: Google OAuth access token

        Returns:
            Dict containing user information from Google

        Raises:
            HTTPException: If request fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.userinfo_endpoint,
                    headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code != 200:
                    logger.error("Google userinfo request failed",
                               status_code=response.status_code,
                               response=response.text)
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Failed to get user info from Google"
                    )

                user_info = response.json()
                logger.info("Google user info retrieved successfully",
                           user_id=user_info.get("sub"),
                           email=user_info.get("email"))

                return user_info

        except httpx.HTTPError as e:
            logger.error("HTTP error getting Google user info", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to communicate with Google"
            )

    async def validate_logout(self, token: str) -> bool:
        """
        Validate logout for Google OAuth.

        Note: Google OAuth doesn't support server-side logout.
        Logout is handled client-side by NextAuth.

        Args:
            token: The OAuth access token (not used for Google)

        Returns:
            True (always succeeds for Google)
        """
        logger.info("Google logout handled client-side")
        return True

    def get_provider_name(self) -> str:
        """
        Get provider name.

        Returns:
            "google"
        """
        return "google"

    def supports_refresh(self) -> bool:
        """
        Check if Google supports token refresh.

        Returns:
            True (Google supports refresh tokens)
        """
        return True

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh a Google OAuth access token.

        Args:
            refresh_token: Google refresh token

        Returns:
            Dict with new access token and expiry
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token"
                    }
                )

                if response.status_code != 200:
                    logger.error("Google token refresh failed",
                               status_code=response.status_code)
                    return None

                token_data = response.json()
                logger.info("Google token refreshed successfully")

                return {
                    "access_token": token_data.get("access_token"),
                    "expires_in": token_data.get("expires_in", 3600),
                    "token_type": token_data.get("token_type", "Bearer")
                }

        except Exception as e:
            logger.error("Error refreshing Google token", error=str(e))
            return None

    def normalize_user_info(self, raw_user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Google user info to standard format.

        Args:
            raw_user_info: Raw user info from Google

        Returns:
            Normalized user information
        """
        return {
            "sub": raw_user_info.get("sub"),
            "email": raw_user_info.get("email"),
            "email_verified": raw_user_info.get("email_verified", False),
            "name": raw_user_info.get("name", raw_user_info.get("email")),
            "picture": raw_user_info.get("picture"),
            "given_name": raw_user_info.get("given_name"),
            "family_name": raw_user_info.get("family_name"),
            "provider": "google"
        }
