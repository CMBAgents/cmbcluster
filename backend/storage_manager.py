"""
Storage Manager - Cloud-Agnostic Storage Management

This module provides a unified interface for managing cloud storage across different providers.
It uses the cloud provider abstraction layer to support both GCP and AWS.
"""

from typing import Dict, List, Optional, Tuple
import structlog

from config import settings
from cloud_providers import CloudStorageProvider, StorageProviderFactory

logger = structlog.get_logger()


class StorageManager:
    """
    Manages cloud storage buckets for user environments.

    This class provides a cloud-agnostic interface for storage operations,
    delegating to the appropriate cloud provider based on configuration.
    """

    def __init__(self):
        """Initialize StorageManager with the configured cloud provider."""
        # Create the appropriate provider based on settings
        self.provider: CloudStorageProvider = StorageProviderFactory.create_from_config(settings)

        logger.info("Initialized StorageManager",
                   cloud_provider=settings.cloud_provider,
                   provider_type=type(self.provider).__name__)

    # ====================
    # Bucket Management
    # ====================

    async def create_user_bucket(
        self,
        user_id: str,
        bucket_name: Optional[str] = None,
        storage_class: str = "STANDARD"
    ) -> Dict:
        """
        Create a new storage bucket for user.

        Args:
            user_id: Unique identifier for the user
            bucket_name: Optional specific bucket name (auto-generated if None)
            storage_class: Storage class/tier

        Returns:
            Dict containing bucket metadata
        """
        return await self.provider.create_bucket(user_id, bucket_name, storage_class)

    async def delete_user_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """
        Delete a user storage bucket.

        Args:
            bucket_name: Name of the bucket to delete
            force: If True, delete all objects in bucket before deleting bucket

        Returns:
            bool: True if deletion successful
        """
        return await self.provider.delete_bucket(bucket_name, force)

    async def get_bucket_metadata(self, bucket_name: str) -> Optional[Dict]:
        """
        Get metadata for a storage bucket.

        Args:
            bucket_name: Name of the bucket

        Returns:
            Dict with bucket metadata or None if bucket doesn't exist
        """
        return await self.provider.get_bucket_metadata(bucket_name)

    async def list_user_buckets(self, user_prefix: str) -> List[Dict]:
        """
        List all buckets for a user based on naming pattern.

        Args:
            user_prefix: Prefix to filter buckets by user

        Returns:
            List of bucket metadata dicts
        """
        return await self.provider.list_buckets(user_prefix)

    # ====================
    # Kubernetes Volume Specs
    # ====================

    def get_fuse_volume_spec(self, bucket_name: str, mount_path: str = "/workspace") -> Dict:
        """
        Generate volume specification for cloud FUSE CSI.

        Args:
            bucket_name: Name of the bucket to mount
            mount_path: Path where the bucket should be mounted

        Returns:
            Dict containing Kubernetes volume spec
        """
        return self.provider.get_fuse_volume_spec(bucket_name, mount_path)

    def get_fuse_volume_mount(self, mount_path: str = "/workspace") -> Dict:
        """
        Generate volume mount specification for cloud FUSE.

        Args:
            mount_path: Path where the volume should be mounted

        Returns:
            Dict containing Kubernetes volumeMount spec
        """
        return self.provider.get_fuse_volume_mount(mount_path)

    # ====================
    # Permissions Management
    # ====================

    async def ensure_bucket_permissions(
        self,
        bucket_name: str,
        service_account_email: str
    ) -> bool:
        """
        Ensure service account has proper bucket permissions.

        Args:
            bucket_name: Name of the bucket
            service_account_email: Service account email or IAM identity

        Returns:
            bool: True if permissions configured successfully
        """
        return await self.provider.ensure_bucket_permissions(
            bucket_name,
            service_account_email
        )

    # ====================
    # Object Operations
    # ====================

    async def upload_object(
        self,
        bucket_name: str,
        object_name: str,
        file_content: bytes,
        content_type: str = None
    ) -> bool:
        """
        Upload an object to the storage bucket.

        Args:
            bucket_name: Name of the bucket
            object_name: Name/path of the object
            file_content: Binary content to upload
            content_type: MIME type of the content

        Returns:
            bool: True if upload successful
        """
        return await self.provider.upload_object(
            bucket_name,
            object_name,
            file_content,
            content_type
        )

    async def download_object(
        self,
        bucket_name: str,
        object_name: str
    ) -> Optional[bytes]:
        """
        Download an object from the storage bucket.

        Args:
            bucket_name: Name of the bucket
            object_name: Name/path of the object

        Returns:
            bytes: Object content or None if not found
        """
        return await self.provider.download_object(bucket_name, object_name)

    async def list_objects(
        self,
        bucket_name: str,
        prefix: str = ""
    ) -> List[Dict]:
        """
        List objects in the storage bucket.

        Args:
            bucket_name: Name of the bucket
            prefix: Optional prefix to filter objects

        Returns:
            List of object metadata dicts
        """
        return await self.provider.list_objects(bucket_name, prefix)

    async def delete_object(
        self,
        bucket_name: str,
        object_name: str
    ) -> bool:
        """
        Delete an object from the storage bucket.

        Args:
            bucket_name: Name of the bucket
            object_name: Name/path of the object

        Returns:
            bool: True if deletion successful
        """
        return await self.provider.delete_object(bucket_name, object_name)

    async def get_object_info(
        self,
        bucket_name: str,
        object_name: str
    ) -> Optional[Dict]:
        """
        Get information about a specific object.

        Args:
            bucket_name: Name of the bucket
            object_name: Name/path of the object

        Returns:
            Dict with object metadata or None if not found
        """
        return await self.provider.get_object_info(bucket_name, object_name)

    # ====================
    # Utility Methods
    # ====================

    def format_bucket_size(self, size_bytes: int) -> str:
        """
        Format bucket size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            str: Formatted size string
        """
        return self.provider.format_bucket_size(size_bytes)

    def extract_cosmic_name_components(self, bucket_name: str) -> Tuple[str, str]:
        """
        Extract the cosmic theme components from bucket name for display.

        Args:
            bucket_name: Bucket name to parse

        Returns:
            Tuple of (constellation, cosmic_term)
        """
        # Check if provider has this method (GCP and AWS providers do)
        if hasattr(self.provider, 'extract_cosmic_name_components'):
            return self.provider.extract_cosmic_name_components(bucket_name)

        # Fallback for providers without this method
        try:
            parts = bucket_name.split('-')
            if len(parts) >= 2:
                return parts[0].title(), parts[1].title()
            return "Unknown", "Cosmic"
        except:
            return "Unknown", "Cosmic"

    def get_friendly_display_name(self, bucket_name: str) -> str:
        """
        Generate a user-friendly display name from bucket name.

        Args:
            bucket_name: Bucket name to format

        Returns:
            str: Friendly display name
        """
        # Check if provider has this method
        if hasattr(self.provider, 'get_friendly_display_name'):
            return self.provider.get_friendly_display_name(bucket_name)

        # Fallback
        constellation, cosmic_term = self.extract_cosmic_name_components(bucket_name)
        return f"{constellation} {cosmic_term}"

    def generate_cosmic_bucket_name(self, user_id: str) -> str:
        """
        Generate a cosmology-themed bucket name.

        Args:
            user_id: User identifier

        Returns:
            str: Generated bucket name
        """
        # Check if provider has this method (GCP and AWS providers do)
        if hasattr(self.provider, 'generate_cosmic_bucket_name'):
            return self.provider.generate_cosmic_bucket_name(user_id)

        # Fallback to base method
        return self.provider.generate_bucket_name(user_id)
