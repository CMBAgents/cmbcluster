"""
Base Abstract Classes for Cloud Provider Implementations

This module defines the interfaces that all cloud provider implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime


class CloudStorageProvider(ABC):
    """
    Abstract base class for cloud storage providers.

    All cloud-specific storage implementations (GCP, AWS, etc.) must implement this interface
    to ensure consistent behavior across different cloud platforms.
    """

    @abstractmethod
    async def create_bucket(
        self,
        user_id: str,
        bucket_name: Optional[str] = None,
        storage_class: str = "STANDARD",
        **kwargs
    ) -> Dict:
        """
        Create a new storage bucket for a user.

        Args:
            user_id: Unique identifier for the user
            bucket_name: Optional specific bucket name (auto-generated if None)
            storage_class: Storage class/tier (e.g., STANDARD, NEARLINE, COLDLINE)
            **kwargs: Provider-specific additional parameters

        Returns:
            Dict containing bucket metadata:
                - bucket_name: str
                - location: str
                - storage_class: str
                - created_at: datetime
                - size_bytes: int
                - versioning_enabled: bool

        Raises:
            Exception: If bucket creation fails
        """
        pass

    @abstractmethod
    async def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """
        Delete a storage bucket.

        Args:
            bucket_name: Name of the bucket to delete
            force: If True, delete all objects in bucket before deleting bucket

        Returns:
            bool: True if deletion successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_bucket_metadata(self, bucket_name: str) -> Optional[Dict]:
        """
        Get metadata for a storage bucket.

        Args:
            bucket_name: Name of the bucket

        Returns:
            Dict with bucket metadata or None if bucket doesn't exist:
                - bucket_name: str
                - location: str
                - storage_class: str
                - created_at: datetime
                - updated_at: datetime
                - size_bytes: int
                - object_count: int
                - versioning_enabled: bool
        """
        pass

    @abstractmethod
    async def list_buckets(self, user_prefix: str) -> List[Dict]:
        """
        List all buckets for a user based on naming pattern.

        Args:
            user_prefix: Prefix to filter buckets by user

        Returns:
            List of bucket metadata dicts
        """
        pass

    @abstractmethod
    def get_fuse_volume_spec(self, bucket_name: str, mount_path: str = "/workspace") -> Dict:
        """
        Generate Kubernetes volume specification for FUSE mounting.

        This method returns the CSI volume specification needed to mount the cloud storage
        bucket as a filesystem in a Kubernetes pod.

        Args:
            bucket_name: Name of the bucket to mount
            mount_path: Path where the bucket should be mounted (default: /workspace)

        Returns:
            Dict containing Kubernetes volume spec with CSI driver configuration
        """
        pass

    @abstractmethod
    def get_fuse_volume_mount(self, mount_path: str = "/workspace") -> Dict:
        """
        Generate Kubernetes volume mount specification.

        Args:
            mount_path: Path where the volume should be mounted

        Returns:
            Dict containing Kubernetes volumeMount spec
        """
        pass

    @abstractmethod
    async def ensure_bucket_permissions(
        self,
        bucket_name: str,
        identity: str
    ) -> bool:
        """
        Ensure proper permissions are set on the bucket.

        Args:
            bucket_name: Name of the bucket
            identity: Cloud-specific identity (service account email, IAM role ARN, etc.)

        Returns:
            bool: True if permissions configured successfully
        """
        pass

    @abstractmethod
    async def upload_object(
        self,
        bucket_name: str,
        object_name: str,
        content: bytes,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Upload an object to the storage bucket.

        Args:
            bucket_name: Name of the bucket
            object_name: Name/path of the object
            content: Binary content to upload
            content_type: MIME type of the content

        Returns:
            bool: True if upload successful
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    # Utility methods that can have default implementations
    def generate_bucket_name(self, user_id: str) -> str:
        """
        Generate a unique bucket name for a user.

        This default implementation can be overridden by subclasses for provider-specific
        naming requirements.

        Args:
            user_id: Unique identifier for the user

        Returns:
            str: Generated bucket name
        """
        import hashlib
        import time
        import random

        # Create short user identifier
        user_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]
        timestamp = int(time.time())
        random_suffix = random.randint(1000, 9999)

        return f"user-{user_hash}-{timestamp}-{random_suffix}"

    def format_bucket_size(self, size_bytes: int) -> str:
        """
        Format bucket size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            str: Formatted size string (e.g., "1.5 GB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
