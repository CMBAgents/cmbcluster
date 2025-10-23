"""
Unit tests for cloud storage provider base class.

Tests the abstract base class and utility methods that are shared
across all cloud provider implementations.
"""

import pytest
import hashlib
from unittest.mock import Mock, patch
from backend.cloud_providers.base import CloudStorageProvider


class ConcreteStorageProvider(CloudStorageProvider):
    """Concrete implementation for testing abstract base class."""

    async def create_bucket(self, user_id, bucket_name=None, storage_class="STANDARD", **kwargs):
        return {"bucket_name": bucket_name or "test-bucket"}

    async def delete_bucket(self, bucket_name, force=False):
        return True

    async def get_bucket_metadata(self, bucket_name):
        return {"bucket_name": bucket_name}

    async def list_buckets(self, user_prefix):
        return []

    def get_fuse_volume_spec(self, bucket_name, mount_path="/workspace"):
        return {"volumeName": "test"}

    def get_fuse_volume_mount(self, mount_path="/workspace"):
        return {"mountPath": mount_path}

    async def ensure_bucket_permissions(self, bucket_name, identity):
        return True

    async def upload_object(self, bucket_name, object_name, content, content_type=None):
        return True

    async def download_object(self, bucket_name, object_name):
        return b"content"

    async def list_objects(self, bucket_name, prefix=""):
        return []

    async def delete_object(self, bucket_name, object_name):
        return True

    async def get_object_info(self, bucket_name, object_name):
        return {"object_name": object_name}


class TestCloudStorageProviderBase:
    """Test CloudStorageProvider base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract base class cannot be instantiated."""
        with pytest.raises(TypeError):
            CloudStorageProvider()

    def test_concrete_implementation_instantiation(self):
        """Test that concrete implementation can be instantiated."""
        provider = ConcreteStorageProvider()
        assert provider is not None

    def test_generate_bucket_name_format(self):
        """Test bucket name generation follows expected format."""
        provider = ConcreteStorageProvider()
        user_id = "user@example.com"

        bucket_name = provider.generate_bucket_name(user_id)

        # Should contain user hash and timestamp
        assert "user-" in bucket_name
        assert len(bucket_name) > 10

    def test_generate_bucket_name_uniqueness(self):
        """Test that bucket names are unique for same user."""
        provider = ConcreteStorageProvider()
        user_id = "user@example.com"

        name1 = provider.generate_bucket_name(user_id)
        name2 = provider.generate_bucket_name(user_id)

        # Should be different (timestamp and random suffix differ)
        assert name1 != name2

    def test_generate_bucket_name_consistency(self):
        """Test that bucket name generation is consistent for same hash."""
        provider = ConcreteStorageProvider()
        user_id = "user@example.com"

        bucket_name = provider.generate_bucket_name(user_id)

        # Should contain MD5 hash of user_id
        expected_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]
        assert expected_hash in bucket_name

    def test_format_bucket_size_bytes(self):
        """Test formatting bucket size in bytes."""
        provider = ConcreteStorageProvider()

        result = provider.format_bucket_size(512)
        assert "B" in result
        assert "512" in result

    def test_format_bucket_size_kilobytes(self):
        """Test formatting bucket size in kilobytes."""
        provider = ConcreteStorageProvider()

        result = provider.format_bucket_size(5120)  # 5 KB
        assert "KB" in result

    def test_format_bucket_size_megabytes(self):
        """Test formatting bucket size in megabytes."""
        provider = ConcreteStorageProvider()

        result = provider.format_bucket_size(5242880)  # 5 MB
        assert "MB" in result

    def test_format_bucket_size_gigabytes(self):
        """Test formatting bucket size in gigabytes."""
        provider = ConcreteStorageProvider()

        result = provider.format_bucket_size(5368709120)  # 5 GB
        assert "GB" in result

    def test_format_bucket_size_terabytes(self):
        """Test formatting bucket size in terabytes."""
        provider = ConcreteStorageProvider()

        result = provider.format_bucket_size(5497558138880)  # 5 TB
        assert "TB" in result

    def test_format_bucket_size_petabytes(self):
        """Test formatting bucket size in petabytes."""
        provider = ConcreteStorageProvider()

        result = provider.format_bucket_size(5644373770240)  # ~5 PB
        assert "PB" in result

    def test_format_bucket_size_zero(self):
        """Test formatting zero bytes."""
        provider = ConcreteStorageProvider()

        result = provider.format_bucket_size(0)
        assert "0.0 B" == result

    def test_format_bucket_size_decimal_places(self):
        """Test that bucket size has one decimal place."""
        provider = ConcreteStorageProvider()

        result = provider.format_bucket_size(1536)  # 1.5 KB
        assert "1.5 KB" == result
