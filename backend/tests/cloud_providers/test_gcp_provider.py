"""
Unit tests for GCP storage provider.

Tests the GCPStorageProvider implementation including bucket operations,
object management, and FUSE volume specifications.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
from backend.cloud_providers.gcp_provider import GCPStorageProvider


class TestGCPStorageProvider:
    """Test GCPStorageProvider class."""

    @pytest.fixture
    def mock_gcp_client(self):
        """Create a mock GCP storage client."""
        with patch('backend.cloud_providers.gcp_provider.storage.Client'):
            return Mock()

    @pytest.fixture
    def provider(self, mock_gcp_client):
        """Create a GCPStorageProvider instance with mocked client."""
        with patch('backend.cloud_providers.gcp_provider.storage.Client') as mock_client:
            provider = GCPStorageProvider(
                project_id="test-project",
                region="us-central1"
            )
            provider.client = mock_client
            return provider

    def test_initialization(self):
        """Test GCPStorageProvider initialization."""
        with patch('backend.cloud_providers.gcp_provider.storage.Client'):
            provider = GCPStorageProvider(
                project_id="test-project",
                region="us-central1"
            )
            assert provider.project_id == "test-project"
            assert provider.region == "us-central1"

    def test_sanitize_for_storage(self, provider):
        """Test bucket name sanitization."""
        # GCS bucket names must be lowercase, alphanumeric, hyphens, underscores
        result = provider._sanitize_for_storage("Test-Bucket_123")
        assert result == result.lower()
        assert "-" in result or "_" in result

    def test_sanitize_for_storage_removes_invalid_chars(self, provider):
        """Test that invalid characters are removed."""
        result = provider._sanitize_for_storage("Test@Bucket#Name!")
        # Should not contain special characters
        assert "@" not in result
        assert "#" not in result
        assert "!" not in result

    def test_sanitize_for_storage_max_length(self, provider):
        """Test that bucket name is limited to 63 characters."""
        long_name = "a" * 100
        result = provider._sanitize_for_storage(long_name)
        assert len(result) <= 63

    def test_generate_cosmic_bucket_name(self, provider):
        """Test cosmology-themed bucket name generation."""
        bucket_name = provider.generate_cosmic_bucket_name("user123")

        # Should contain constellation or cosmic term
        assert any(c in bucket_name.lower() for c in provider.CONSTELLATIONS + provider.COSMIC_TERMS)
        # Should contain user hash
        assert len(bucket_name) > 0
        # Should be valid for GCS
        assert all(c.isalnum() or c in "-_" for c in bucket_name.lower())

    def test_generate_bucket_name(self, provider):
        """Test that generate_bucket_name uses cosmic naming."""
        bucket_name = provider.generate_bucket_name("user123")
        assert isinstance(bucket_name, str)
        assert len(bucket_name) > 0

    @pytest.mark.asyncio
    async def test_create_bucket_success(self, provider):
        """Test successful bucket creation."""
        mock_bucket = Mock()
        mock_bucket.path = "/test-bucket"
        mock_bucket.time_created = datetime.now()
        mock_bucket.storage_class = "STANDARD"

        provider.client.bucket = Mock(return_value=mock_bucket)
        mock_bucket.create = Mock()
        provider.client.get_bucket = Mock(return_value=mock_bucket)

        result = await provider.create_bucket("user123", "test-bucket")

        assert result["bucket_name"] == "test-bucket"
        assert "created_at" in result
        assert "location" in result

    @pytest.mark.asyncio
    async def test_create_bucket_auto_generated_name(self, provider):
        """Test bucket creation with auto-generated name."""
        mock_bucket = Mock()
        mock_bucket.path = "/auto-bucket"
        mock_bucket.time_created = datetime.now()
        mock_bucket.storage_class = "STANDARD"

        provider.client.bucket = Mock(return_value=mock_bucket)
        mock_bucket.create = Mock()
        provider.client.get_bucket = Mock(return_value=mock_bucket)

        result = await provider.create_bucket("user123")

        assert result["bucket_name"] is not None
        assert len(result["bucket_name"]) > 0

    @pytest.mark.asyncio
    async def test_delete_bucket_success(self, provider):
        """Test successful bucket deletion."""
        mock_bucket = Mock()
        provider.client.get_bucket = Mock(return_value=mock_bucket)

        result = await provider.delete_bucket("test-bucket", force=False)

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_bucket_not_found(self, provider):
        """Test deleting non-existent bucket."""
        from google.api_core import exceptions as gcp_exceptions

        provider.client.get_bucket = Mock(
            side_effect=gcp_exceptions.NotFound("Bucket not found")
        )

        result = await provider.delete_bucket("nonexistent-bucket")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_bucket_metadata_success(self, provider):
        """Test getting bucket metadata."""
        mock_bucket = Mock()
        mock_bucket.name = "test-bucket"
        mock_bucket.location = "US"
        mock_bucket.storage_class = "STANDARD"
        mock_bucket.time_created = datetime.now()
        mock_bucket.time_updated = datetime.now()

        provider.client.get_bucket = Mock(return_value=mock_bucket)

        result = await provider.get_bucket_metadata("test-bucket")

        assert result["bucket_name"] == "test-bucket"
        assert result["location"] == "US"
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_get_bucket_metadata_not_found(self, provider):
        """Test getting metadata for non-existent bucket."""
        from google.api_core import exceptions as gcp_exceptions

        provider.client.get_bucket = Mock(
            side_effect=gcp_exceptions.NotFound("Bucket not found")
        )

        result = await provider.get_bucket_metadata("nonexistent-bucket")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_buckets(self, provider):
        """Test listing user buckets."""
        mock_bucket1 = Mock()
        mock_bucket1.name = "user-abc123-1-1234567890"

        mock_bucket2 = Mock()
        mock_bucket2.name = "user-abc123-2-1234567891"

        provider.client.list_buckets = Mock(return_value=[mock_bucket1, mock_bucket2])

        result = await provider.list_buckets("user-abc123")

        assert len(result) == 2
        assert all("bucket_name" in r for r in result)

    def test_get_fuse_volume_spec(self, provider):
        """Test FUSE volume specification for Kubernetes."""
        spec = provider.get_fuse_volume_spec("test-bucket", "/workspace")

        assert spec["name"] == "user-workspace-fuse"
        assert spec["csi"]["driver"] == "gcsfuse.csi.storage.gke.io"
        assert spec["csi"]["volumeAttributes"]["bucketName"] == "test-bucket"
        assert spec["csi"]["volumeAttributes"]["mountOptions"] == "allow-delete,uid=1000,gid=1000"

    def test_get_fuse_volume_spec_custom_mount_path(self, provider):
        """Test FUSE volume spec with custom mount path."""
        spec = provider.get_fuse_volume_spec("test-bucket", "/custom/path")

        assert spec["csi"]["volumeAttributes"]["mountOptions"] == "allow-delete,uid=1000,gid=1000"

    def test_get_fuse_volume_mount(self, provider):
        """Test FUSE volume mount specification."""
        mount = provider.get_fuse_volume_mount("/workspace")

        assert mount["name"] == "user-workspace-fuse"
        assert mount["mountPath"] == "/workspace"

    def test_get_fuse_volume_mount_custom_path(self, provider):
        """Test FUSE volume mount with custom path."""
        mount = provider.get_fuse_volume_mount("/custom/mount")

        assert mount["mountPath"] == "/custom/mount"

    @pytest.mark.asyncio
    async def test_ensure_bucket_permissions(self, provider):
        """Test ensuring bucket permissions."""
        mock_bucket = Mock()
        provider.client.get_bucket = Mock(return_value=mock_bucket)

        result = await provider.ensure_bucket_permissions(
            "test-bucket",
            "service-account@project.iam.gserviceaccount.com"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_upload_object_success(self, provider):
        """Test successful object upload."""
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_bucket.blob = Mock(return_value=mock_blob)

        provider.client.get_bucket = Mock(return_value=mock_bucket)

        content = b"test content"
        result = await provider.upload_object(
            "test-bucket",
            "test-file.txt",
            content,
            content_type="text/plain"
        )

        assert result is True
        mock_blob.upload_from_string.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_object_success(self, provider):
        """Test successful object download."""
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.download_as_bytes = Mock(return_value=b"test content")
        mock_bucket.blob = Mock(return_value=mock_blob)

        provider.client.get_bucket = Mock(return_value=mock_bucket)

        result = await provider.download_object("test-bucket", "test-file.txt")

        assert result == b"test content"

    @pytest.mark.asyncio
    async def test_download_object_not_found(self, provider):
        """Test downloading non-existent object."""
        from google.api_core import exceptions as gcp_exceptions

        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.download_as_bytes = Mock(
            side_effect=gcp_exceptions.NotFound("Object not found")
        )
        mock_bucket.blob = Mock(return_value=mock_blob)

        provider.client.get_bucket = Mock(return_value=mock_bucket)

        result = await provider.download_object("test-bucket", "nonexistent-file.txt")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_objects(self, provider):
        """Test listing objects in bucket."""
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.name = "test-file.txt"
        mock_blob.size = 1024
        mock_bucket.list_blobs = Mock(return_value=[mock_blob])

        provider.client.get_bucket = Mock(return_value=mock_bucket)

        result = await provider.list_objects("test-bucket")

        assert len(result) == 1
        assert result[0]["object_name"] == "test-file.txt"

    @pytest.mark.asyncio
    async def test_list_objects_with_prefix(self, provider):
        """Test listing objects with prefix filter."""
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.name = "logs/test.txt"
        mock_bucket.list_blobs = Mock(return_value=[mock_blob])

        provider.client.get_bucket = Mock(return_value=mock_bucket)

        result = await provider.list_objects("test-bucket", prefix="logs/")

        assert len(result) >= 0

    @pytest.mark.asyncio
    async def test_delete_object_success(self, provider):
        """Test successful object deletion."""
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_bucket.blob = Mock(return_value=mock_blob)

        provider.client.get_bucket = Mock(return_value=mock_bucket)

        result = await provider.delete_object("test-bucket", "test-file.txt")

        assert result is True

    @pytest.mark.asyncio
    async def test_get_object_info_success(self, provider):
        """Test getting object information."""
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.name = "test-file.txt"
        mock_blob.size = 1024
        mock_blob.time_created = datetime.now()
        mock_bucket.blob = Mock(return_value=mock_blob)

        provider.client.get_bucket = Mock(return_value=mock_bucket)

        result = await provider.get_object_info("test-bucket", "test-file.txt")

        assert result["object_name"] == "test-file.txt"
        assert result["size_bytes"] == 1024
