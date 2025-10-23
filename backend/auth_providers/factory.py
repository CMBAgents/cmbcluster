"""
Authentication provider factory for creating provider instances.

Automatically selects and configures the appropriate authentication provider
based on configuration settings.
"""

from typing import Optional
import structlog

from .base import AuthProvider
from .google_provider import GoogleAuthProvider
from .aws_provider import AWSCognitoAuthProvider

logger = structlog.get_logger()


class AuthProviderFactory:
    """
    Factory for creating authentication provider instances.

    Supports automatic provider selection based on configuration
    or explicit provider creation.
    """

    @staticmethod
    def create(
        provider_type: str,
        **kwargs
    ) -> AuthProvider:
        """
        Create an authentication provider by type.

        Args:
            provider_type: Provider type ("google" or "cognito")
            **kwargs: Provider-specific configuration parameters

        Returns:
            Configured authentication provider instance

        Raises:
            ValueError: If provider type is unsupported or configuration is invalid
        """
        provider_type = provider_type.lower()

        logger.info(f"Creating auth provider: {provider_type}")

        if provider_type == "google":
            return AuthProviderFactory._create_google_provider(**kwargs)

        elif provider_type == "cognito" or provider_type == "aws":
            return AuthProviderFactory._create_cognito_provider(**kwargs)

        else:
            raise ValueError(
                f"Unsupported authentication provider: {provider_type}. "
                f"Supported providers: google, cognito"
            )

    @staticmethod
    def create_from_config(settings) -> AuthProvider:
        """
        Create authentication provider from settings object.

        Provider selection priority (deployment-agnostic):
        1. AUTH_PROVIDER setting (explicit selection: "google" or "cognito")
        2. Available credentials (auto-detect)
        3. CLOUD_PROVIDER setting (fallback: gcp → google, aws → cognito)

        This allows flexible authentication configuration:
        - Use Google OAuth on AWS deployments
        - Use AWS Cognito on GCP deployments
        - Explicitly choose provider regardless of cloud platform

        Args:
            settings: Settings object with authentication configuration

        Returns:
            Configured authentication provider

        Raises:
            ValueError: If no valid authentication provider is configured
        """
        # Priority 1: Check explicit AUTH_PROVIDER setting
        if hasattr(settings, 'auth_provider') and settings.auth_provider and \
           settings.auth_provider.lower() != "auto":
            auth_provider = settings.auth_provider.lower()
            logger.info(f"AUTH_PROVIDER explicitly set to: {auth_provider}")

            if auth_provider == "google":
                logger.info("Creating Google OAuth provider (explicitly configured)")
                return AuthProviderFactory._create_google_provider(
                    client_id=settings.google_client_id,
                    client_secret=settings.google_client_secret
                )

            elif auth_provider == "cognito":
                logger.info("Creating AWS Cognito provider (explicitly configured)")
                return AuthProviderFactory._create_cognito_provider(
                    user_pool_id=settings.cognito_user_pool_id,
                    client_id=settings.cognito_client_id,
                    client_secret=settings.cognito_client_secret,
                    region=getattr(settings, 'aws_region', 'us-east-1'),
                    issuer=getattr(settings, 'cognito_issuer', None)
                )

            else:
                raise ValueError(
                    f"Invalid AUTH_PROVIDER: {auth_provider}. "
                    f"Valid options: 'google', 'cognito', or 'auto'"
                )

        # Priority 2: Auto-detect based on available credentials
        logger.info("AUTH_PROVIDER is 'auto', detecting based on available credentials")

        # Check for Google OAuth configuration
        if hasattr(settings, 'google_client_id') and settings.google_client_id and \
           settings.google_client_id != "build-time-placeholder":
            logger.info("Detected Google OAuth configuration, using Google provider")
            return AuthProviderFactory._create_google_provider(
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret
            )

        # Check for AWS Cognito configuration
        if hasattr(settings, 'cognito_user_pool_id') and settings.cognito_user_pool_id:
            logger.info("Detected AWS Cognito configuration, using Cognito provider")
            return AuthProviderFactory._create_cognito_provider(
                user_pool_id=settings.cognito_user_pool_id,
                client_id=settings.cognito_client_id,
                client_secret=settings.cognito_client_secret,
                region=getattr(settings, 'aws_region', 'us-east-1'),
                issuer=getattr(settings, 'cognito_issuer', None)
            )

        # Priority 3: Fallback to CLOUD_PROVIDER setting
        if hasattr(settings, 'cloud_provider'):
            cloud_provider = settings.cloud_provider.lower()
            logger.info(f"Falling back to CLOUD_PROVIDER setting: {cloud_provider}")

            if cloud_provider == "gcp":
                if hasattr(settings, 'google_client_id'):
                    logger.info("Cloud provider is GCP, using Google OAuth")
                    return AuthProviderFactory._create_google_provider(
                        client_id=settings.google_client_id,
                        client_secret=settings.google_client_secret
                    )

            elif cloud_provider == "aws":
                if hasattr(settings, 'cognito_user_pool_id'):
                    logger.info("Cloud provider is AWS, using Cognito")
                    return AuthProviderFactory._create_cognito_provider(
                        user_pool_id=settings.cognito_user_pool_id,
                        client_id=settings.cognito_client_id,
                        client_secret=settings.cognito_client_secret,
                        region=getattr(settings, 'aws_region', 'us-east-1'),
                        issuer=getattr(settings, 'cognito_issuer', None)
                    )

        # No valid configuration found
        raise ValueError(
            "No authentication provider configured. "
            "Please configure either:\n"
            "  - Google OAuth: Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET\n"
            "  - AWS Cognito: Set COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID, and COGNITO_CLIENT_SECRET\n"
            "  - Or explicitly set AUTH_PROVIDER to 'google' or 'cognito'"
        )

    @staticmethod
    def _create_google_provider(**kwargs) -> GoogleAuthProvider:
        """
        Create Google OAuth provider with validation.

        Args:
            **kwargs: Configuration parameters for Google provider

        Returns:
            Configured GoogleAuthProvider

        Raises:
            ValueError: If required configuration is missing
        """
        client_id = kwargs.get('client_id')
        client_secret = kwargs.get('client_secret')

        if not client_id or client_id == "build-time-placeholder":
            raise ValueError(
                "Google OAuth client_id is required. "
                "Please set GOOGLE_CLIENT_ID environment variable."
            )

        if not client_secret or client_secret == "build-time-placeholder":
            raise ValueError(
                "Google OAuth client_secret is required. "
                "Please set GOOGLE_CLIENT_SECRET environment variable."
            )

        return GoogleAuthProvider(
            client_id=client_id,
            client_secret=client_secret
        )

    @staticmethod
    def _create_cognito_provider(**kwargs) -> AWSCognitoAuthProvider:
        """
        Create AWS Cognito provider with validation.

        Args:
            **kwargs: Configuration parameters for Cognito provider

        Returns:
            Configured AWSCognitoAuthProvider

        Raises:
            ValueError: If required configuration is missing
        """
        user_pool_id = kwargs.get('user_pool_id')
        client_id = kwargs.get('client_id')
        client_secret = kwargs.get('client_secret')
        region = kwargs.get('region', 'us-east-1')
        issuer = kwargs.get('issuer')

        if not user_pool_id:
            raise ValueError(
                "AWS Cognito user_pool_id is required. "
                "Please set COGNITO_USER_POOL_ID environment variable."
            )

        if not client_id:
            raise ValueError(
                "AWS Cognito client_id is required. "
                "Please set COGNITO_CLIENT_ID environment variable."
            )

        if not client_secret:
            raise ValueError(
                "AWS Cognito client_secret is required. "
                "Please set COGNITO_CLIENT_SECRET environment variable."
            )

        return AWSCognitoAuthProvider(
            user_pool_id=user_pool_id,
            client_id=client_id,
            client_secret=client_secret,
            region=region,
            issuer=issuer
        )

    @staticmethod
    def get_supported_providers() -> list:
        """
        Get list of supported authentication providers.

        Returns:
            List of supported provider names
        """
        return ["google", "cognito"]

    @staticmethod
    def detect_configured_provider(settings) -> Optional[str]:
        """
        Detect which authentication provider is configured.

        Args:
            settings: Settings object

        Returns:
            Provider name ("google" or "cognito") or None if none configured
        """
        # Check Google
        if hasattr(settings, 'google_client_id') and settings.google_client_id and \
           settings.google_client_id != "build-time-placeholder":
            return "google"

        # Check Cognito
        if hasattr(settings, 'cognito_user_pool_id') and settings.cognito_user_pool_id:
            return "cognito"

        return None
