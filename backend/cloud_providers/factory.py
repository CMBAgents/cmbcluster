"""
Cloud Provider Factory

This module provides a factory for creating the appropriate cloud storage provider
based on configuration.
"""

import structlog
from typing import Literal

from .base import CloudStorageProvider
from .gcp_provider import GCPStorageProvider
from .aws_provider import AWSStorageProvider

logger = structlog.get_logger()


class StorageProviderFactory:
    """Factory class for creating cloud storage provider instances."""

    @staticmethod
    def create(
        provider_type: Literal["gcp", "aws"],
        **kwargs
    ) -> CloudStorageProvider:
        """
        Create a cloud storage provider instance based on the specified type.

        Args:
            provider_type: Type of cloud provider ("gcp" or "aws")
            **kwargs: Provider-specific configuration parameters

        Returns:
            CloudStorageProvider: Instance of the appropriate provider

        Raises:
            ValueError: If provider_type is not supported
            ImportError: If required dependencies for the provider are not installed

        Examples:
            # Create GCP provider
            provider = StorageProviderFactory.create(
                "gcp",
                project_id="my-project",
                region="us-central1"
            )

            # Create AWS provider
            provider = StorageProviderFactory.create(
                "aws",
                region="us-east-1",
                account_id="123456789012"
            )
        """
        provider_type = provider_type.lower()

        if provider_type == "gcp":
            return StorageProviderFactory._create_gcp_provider(**kwargs)
        elif provider_type == "aws":
            return StorageProviderFactory._create_aws_provider(**kwargs)
        else:
            raise ValueError(
                f"Unsupported cloud provider: {provider_type}. "
                f"Supported providers: gcp, aws"
            )

    @staticmethod
    def _create_gcp_provider(**kwargs) -> GCPStorageProvider:
        """
        Create a GCP storage provider instance.

        Required kwargs:
            - project_id: GCP project ID
            - region: GCP region

        Returns:
            GCPStorageProvider instance
        """
        project_id = kwargs.get('project_id')
        region = kwargs.get('region')

        if not project_id:
            raise ValueError("project_id is required for GCP provider")
        if not region:
            raise ValueError("region is required for GCP provider")

        logger.info("Creating GCP storage provider",
                   project_id=project_id,
                   region=region)

        try:
            return GCPStorageProvider(
                project_id=project_id,
                region=region
            )
        except ImportError as e:
            logger.error("Failed to create GCP provider - missing dependencies",
                        error=str(e))
            raise ImportError(
                "google-cloud-storage is required for GCP provider. "
                "Install it with: pip install google-cloud-storage"
            ) from e

    @staticmethod
    def _create_aws_provider(**kwargs) -> AWSStorageProvider:
        """
        Create an AWS storage provider instance.

        Required kwargs:
            - region: AWS region

        Optional kwargs:
            - account_id: AWS account ID

        Returns:
            AWSStorageProvider instance
        """
        region = kwargs.get('region')
        account_id = kwargs.get('account_id')

        if not region:
            raise ValueError("region is required for AWS provider")

        logger.info("Creating AWS storage provider",
                   region=region,
                   account_id=account_id)

        try:
            return AWSStorageProvider(
                region=region,
                account_id=account_id
            )
        except ImportError as e:
            logger.error("Failed to create AWS provider - missing dependencies",
                        error=str(e))
            raise ImportError(
                "boto3 is required for AWS provider. "
                "Install it with: pip install boto3"
            ) from e

    @staticmethod
    def create_from_config(config) -> CloudStorageProvider:
        """
        Create a cloud storage provider from a configuration object.

        This is a convenience method that extracts provider configuration
        from a settings/config object.

        Args:
            config: Configuration object with cloud provider settings

        Returns:
            CloudStorageProvider: Instance of the appropriate provider

        Example:
            from config import settings
            provider = StorageProviderFactory.create_from_config(settings)
        """
        provider_type = getattr(config, 'cloud_provider', 'gcp').lower()

        logger.info("Creating storage provider from config",
                   provider_type=provider_type)

        if provider_type == "gcp":
            return StorageProviderFactory._create_gcp_provider(
                project_id=config.project_id,
                region=config.region
            )
        elif provider_type == "aws":
            return StorageProviderFactory._create_aws_provider(
                region=getattr(config, 'aws_region', config.region),
                account_id=getattr(config, 'aws_account_id', None)
            )
        else:
            raise ValueError(
                f"Unsupported cloud provider in config: {provider_type}"
            )
