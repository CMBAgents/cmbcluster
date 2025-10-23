"""
Unit tests for cloud provider factory.

Tests the factory pattern for creating cloud storage providers.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.cloud_providers.factory import StorageProviderFactory
from backend.cloud_providers.gcp_provider import GCPStorageProvider
from backend.cloud_providers.aws_provider import AWSStorageProvider


class TestStorageProviderFactory:
    """Test StorageProviderFactory class."""

    def test_create_gcp_provider(self):
        """Test creating a GCP storage provider."""
        with patch('backend.cloud_providers.factory.GCPStorageProvider') as mock_gcp:
            provider = StorageProviderFactory.create(
                "gcp",
                project_id="test-project",
                region="us-central1"
            )
            mock_gcp.assert_called_once_with(
                project_id="test-project",
                region="us-central1"
            )

    def test_create_aws_provider(self):
        """Test creating an AWS storage provider."""
        with patch('backend.cloud_providers.factory.AWSStorageProvider') as mock_aws:
            provider = StorageProviderFactory.create(
                "aws",
                region="us-east-1",
                account_id="123456789012"
            )
            mock_aws.assert_called_once_with(
                region="us-east-1",
                account_id="123456789012"
            )

    def test_create_gcp_provider_case_insensitive(self):
        """Test that provider type is case insensitive."""
        with patch('backend.cloud_providers.factory.GCPStorageProvider') as mock_gcp:
            StorageProviderFactory.create(
                "GCP",
                project_id="test-project",
                region="us-central1"
            )
            mock_gcp.assert_called_once()

    def test_create_aws_provider_case_insensitive(self):
        """Test that AWS provider type is case insensitive."""
        with patch('backend.cloud_providers.factory.AWSStorageProvider') as mock_aws:
            StorageProviderFactory.create(
                "AWS",
                region="us-east-1"
            )
            mock_aws.assert_called_once()

    def test_create_invalid_provider(self):
        """Test creating an unsupported provider raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            StorageProviderFactory.create("azure", region="us-east-1")
        assert "Unsupported cloud provider: azure" in str(exc_info.value)
        assert "gcp, aws" in str(exc_info.value)

    def test_create_gcp_missing_project_id(self):
        """Test GCP creation fails without project_id."""
        with pytest.raises(ValueError) as exc_info:
            StorageProviderFactory.create("gcp", region="us-central1")
        assert "project_id is required for GCP provider" in str(exc_info.value)

    def test_create_gcp_missing_region(self):
        """Test GCP creation fails without region."""
        with pytest.raises(ValueError) as exc_info:
            StorageProviderFactory.create("gcp", project_id="test-project")
        assert "region is required for GCP provider" in str(exc_info.value)

    def test_create_aws_missing_region(self):
        """Test AWS creation fails without region."""
        with pytest.raises(ValueError) as exc_info:
            StorageProviderFactory.create("aws")
        assert "region is required for AWS provider" in str(exc_info.value)

    def test_create_gcp_import_error(self):
        """Test GCP creation handles missing dependencies."""
        with patch('backend.cloud_providers.factory.GCPStorageProvider', side_effect=ImportError("google-cloud-storage not found")):
            with pytest.raises(ImportError) as exc_info:
                StorageProviderFactory.create(
                    "gcp",
                    project_id="test-project",
                    region="us-central1"
                )
            assert "google-cloud-storage is required" in str(exc_info.value)

    def test_create_aws_import_error(self):
        """Test AWS creation handles missing dependencies."""
        with patch('backend.cloud_providers.factory.AWSStorageProvider', side_effect=ImportError("boto3 not found")):
            with pytest.raises(ImportError) as exc_info:
                StorageProviderFactory.create("aws", region="us-east-1")
            assert "boto3 is required" in str(exc_info.value)

    def test_create_from_config_gcp(self):
        """Test creating provider from config object (GCP)."""
        mock_config = Mock()
        mock_config.cloud_provider = "gcp"
        mock_config.project_id = "test-project"
        mock_config.region = "us-central1"

        with patch('backend.cloud_providers.factory.GCPStorageProvider') as mock_gcp:
            StorageProviderFactory.create_from_config(mock_config)
            mock_gcp.assert_called_once_with(
                project_id="test-project",
                region="us-central1"
            )

    def test_create_from_config_aws(self):
        """Test creating provider from config object (AWS)."""
        mock_config = Mock()
        mock_config.cloud_provider = "aws"
        mock_config.aws_region = "us-east-1"
        mock_config.aws_account_id = "123456789012"

        with patch('backend.cloud_providers.factory.AWSStorageProvider') as mock_aws:
            StorageProviderFactory.create_from_config(mock_config)
            mock_aws.assert_called_once_with(
                region="us-east-1",
                account_id="123456789012"
            )

    def test_create_from_config_defaults_to_gcp(self):
        """Test that missing cloud_provider defaults to GCP."""
        mock_config = Mock(spec=[])  # No cloud_provider attribute
        mock_config.project_id = "test-project"
        mock_config.region = "us-central1"

        with patch('backend.cloud_providers.factory.GCPStorageProvider') as mock_gcp:
            StorageProviderFactory.create_from_config(mock_config)
            mock_gcp.assert_called_once()

    def test_create_from_config_invalid_provider(self):
        """Test creating from config with invalid provider."""
        mock_config = Mock()
        mock_config.cloud_provider = "invalid"

        with pytest.raises(ValueError) as exc_info:
            StorageProviderFactory.create_from_config(mock_config)
        assert "Unsupported cloud provider in config" in str(exc_info.value)
