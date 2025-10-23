"""
Abstract base class for authentication providers.

Defines the interface that all authentication providers must implement
to ensure consistent authentication behavior across different cloud platforms.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()


class AuthProvider(ABC):
    """
    Abstract base class for authentication providers.

    All authentication providers (Google OAuth, AWS Cognito, etc.) must
    implement this interface to ensure consistent authentication across
    different cloud platforms.
    """

    def __init__(self, **kwargs):
        """
        Initialize the authentication provider.

        Args:
            **kwargs: Provider-specific configuration parameters
        """
        self.provider_name = self.__class__.__name__
        logger.info(f"Initializing auth provider: {self.provider_name}")

    @abstractmethod
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate an OAuth/OIDC token from the provider.

        Args:
            token: The OAuth access token or ID token to validate

        Returns:
            Dict containing validated user information:
            {
                "sub": "unique-user-id",
                "email": "user@example.com",
                "email_verified": True/False,
                "name": "User Name",
                "picture": "https://...",
                "provider": "google"/"cognito"/etc
            }

        Raises:
            ValueError: If token is invalid or expired
            HTTPException: If validation fails
        """
        pass

    @abstractmethod
    def get_oauth_config(self) -> Dict[str, Any]:
        """
        Get OAuth configuration for the provider.

        Returns:
            Dict containing OAuth configuration:
            {
                "client_id": "...",
                "authorization_endpoint": "https://...",
                "token_endpoint": "https://...",
                "userinfo_endpoint": "https://...",
                "issuer": "https://...",
                "scopes": ["openid", "email", "profile"]
            }
        """
        pass

    @abstractmethod
    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Get detailed user information from the provider.

        Args:
            token: The OAuth access token

        Returns:
            Dict containing user information

        Raises:
            ValueError: If token is invalid
        """
        pass

    @abstractmethod
    async def validate_logout(self, token: str) -> bool:
        """
        Validate and handle logout for the provider.

        Some providers (like Cognito) support global sign-out,
        others (like Google) handle logout client-side.

        Args:
            token: The OAuth access token to invalidate

        Returns:
            True if logout was successful
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the provider name for identification.

        Returns:
            Provider name (e.g., "google", "cognito")
        """
        pass

    def supports_refresh(self) -> bool:
        """
        Check if provider supports token refresh.

        Returns:
            True if provider supports refresh tokens
        """
        return False

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh an access token using a refresh token (optional).

        Args:
            refresh_token: The refresh token

        Returns:
            Dict containing new access token and expiry, or None if not supported:
            {
                "access_token": "...",
                "expires_in": 3600,
                "refresh_token": "..."  # Optional new refresh token
            }
        """
        return None

    def normalize_user_info(self, raw_user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize user information from provider-specific format to standard format.

        Args:
            raw_user_info: Provider-specific user information

        Returns:
            Normalized user information with standard fields:
            {
                "sub": "unique-user-id",
                "email": "user@example.com",
                "email_verified": True/False,
                "name": "User Name",
                "picture": "https://...",
                "provider": "google"/"cognito"/etc
            }
        """
        # Default implementation - override in subclass if needed
        return {
            "sub": raw_user_info.get("sub"),
            "email": raw_user_info.get("email"),
            "email_verified": raw_user_info.get("email_verified", False),
            "name": raw_user_info.get("name", raw_user_info.get("email")),
            "picture": raw_user_info.get("picture"),
            "provider": self.get_provider_name()
        }

    async def validate_email_domain(self, email: str, allowed_domains: Optional[list] = None) -> bool:
        """
        Validate email domain against allowed domains.

        Args:
            email: Email address to validate
            allowed_domains: List of allowed domains (e.g., ["example.com"])

        Returns:
            True if email domain is allowed or no restrictions
        """
        if not allowed_domains:
            return True

        domain = email.split("@")[-1].lower()
        return domain in [d.lower() for d in allowed_domains]

    def __str__(self) -> str:
        return f"{self.provider_name} Authentication Provider"

    def __repr__(self) -> str:
        return f"<{self.provider_name}>"
