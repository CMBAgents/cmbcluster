"""
Google Cloud Platform Storage Provider Implementation

This module implements the CloudStorageProvider interface for Google Cloud Storage (GCS).
"""

import random
import time
import re
import hashlib
from typing import Dict, List, Optional
from datetime import datetime
import structlog
from google.cloud import storage
from google.api_core import exceptions as gcp_exceptions

from .base import CloudStorageProvider

logger = structlog.get_logger()


class GCPStorageProvider(CloudStorageProvider):
    """Google Cloud Storage implementation of the CloudStorageProvider interface."""

    # Cosmology-themed naming components
    CONSTELLATIONS = [
        "andromeda", "orion", "cassiopeia", "ursa", "draco", "cygnus", "lyra",
        "aquila", "pegasus", "perseus", "cepheus", "bootes", "corona", "hercules",
        "vega", "altair", "sirius", "polaris", "rigel", "betelgeuse", "capella",
        "arcturus", "spica", "aldebaran", "antares", "deneb", "regulus", "procyon"
    ]

    COSMIC_TERMS = [
        "nebula", "quasar", "pulsar", "galaxy", "comet", "meteor", "nova",
        "supernova", "blackhole", "wormhole", "plasma", "cosmic", "stellar",
        "interstellar", "galactic", "solar", "lunar", "celestial", "astral",
        "orbital", "binary", "cluster", "void", "fusion", "photon", "neutrino"
    ]

    def __init__(self, project_id: str, region: str):
        """
        Initialize GCP Storage Provider.

        Args:
            project_id: GCP project ID
            region: GCP region for bucket creation
        """
        self.project_id = project_id
        self.region = region
        self.client = storage.Client(project=project_id)
        logger.info("Initialized GCP storage provider",
                   project_id=project_id,
                   region=region)

    def _sanitize_for_storage(self, name: str) -> str:
        """Sanitize string for GCS bucket naming."""
        name = name.lower()
        name = re.sub(r'[^a-z0-9-]', '-', name)
        name = name.strip('-')
        return name[:63]

    def generate_cosmic_bucket_name(self, user_id: str) -> str:
        """Generate a cosmology-themed bucket name."""
        constellation = random.choice(self.CONSTELLATIONS)
        cosmic_term = random.choice(self.COSMIC_TERMS)

        # Create short user identifier (first 8 chars of user_id hash)
        user_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]

        # Add timestamp for uniqueness
        timestamp = int(time.time())

        # Format: {constellation}-{cosmic-term}-{user-hash}-{timestamp}
        bucket_name = f"{constellation}-{cosmic_term}-{user_hash}-{timestamp}"

        # Ensure it meets GCS naming requirements
        bucket_name = self._sanitize_for_storage(bucket_name)

        # GCS bucket names must be globally unique and 3-63 characters
        if len(bucket_name) > 63:
            # Truncate while preserving uniqueness
            bucket_name = f"{constellation[:10]}-{cosmic_term[:10]}-{user_hash}-{timestamp}"

        return bucket_name

    def generate_bucket_name(self, user_id: str) -> str:
        """Generate a unique bucket name for a user (uses cosmic naming)."""
        return self.generate_cosmic_bucket_name(user_id)

    async def create_bucket(
        self,
        user_id: str,
        bucket_name: Optional[str] = None,
        storage_class: str = "STANDARD",
        **kwargs
    ) -> Dict:
        """Create a new GCS bucket for user."""
        try:
            if not bucket_name:
                bucket_name = self.generate_cosmic_bucket_name(user_id)

            # Create bucket with proper configuration
            bucket = self.client.bucket(bucket_name)

            # Configure bucket
            bucket.storage_class = storage_class
            bucket.location = self.region

            # Enable versioning for data protection
            bucket.versioning_enabled = True

            # Set lifecycle rules to manage costs
            lifecycle_rule = {
                "action": {"type": "Delete"},
                "condition": {"numNewerVersions": 30}
            }
            bucket.lifecycle_rules = [lifecycle_rule]

            # Create the bucket
            bucket.create()

            logger.info("Created GCS bucket",
                       bucket_name=bucket_name,
                       user_id=user_id,
                       location=self.region,
                       storage_class=storage_class)

            return {
                "bucket_name": bucket_name,
                "location": self.region,
                "storage_class": storage_class,
                "created_at": datetime.utcnow(),
                "size_bytes": 0,
                "versioning_enabled": True
            }

        except gcp_exceptions.Conflict:
            logger.warning("Bucket name conflict, generating new name",
                          bucket_name=bucket_name,
                          user_id=user_id)
            # Try with a new name
            new_bucket_name = self.generate_cosmic_bucket_name(user_id)
            return await self.create_bucket(user_id, new_bucket_name, storage_class)

        except Exception as e:
            logger.error("Failed to create GCS bucket",
                        bucket_name=bucket_name,
                        user_id=user_id,
                        error=str(e))
            raise

    async def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """Delete a GCS bucket."""
        try:
            bucket = self.client.bucket(bucket_name)

            # First check if bucket exists
            if not bucket.exists():
                logger.warning("Bucket does not exist, considering deletion successful",
                             bucket_name=bucket_name)
                return True

            if force:
                logger.info("Force deleting bucket contents", bucket_name=bucket_name)
                # Delete all objects and their versions
                self._force_delete_bucket_contents(bucket)

            # Delete the bucket
            logger.info("Deleting bucket", bucket_name=bucket_name)
            bucket.delete()

            logger.info("Successfully deleted GCS bucket", bucket_name=bucket_name, force=force)
            return True

        except gcp_exceptions.NotFound:
            logger.warning("Bucket not found for deletion", bucket_name=bucket_name)
            return True  # Consider it successful if already deleted

        except gcp_exceptions.Conflict as e:
            error_msg = str(e)
            if "not empty" in error_msg.lower():
                if force:
                    logger.error("Bucket still not empty after force deletion",
                               bucket_name=bucket_name, error=error_msg)
                else:
                    logger.error("Bucket not empty and force=False",
                               bucket_name=bucket_name, error=error_msg)
            else:
                logger.error("Conflict error deleting bucket",
                           bucket_name=bucket_name, error=error_msg)
            return False

        except gcp_exceptions.Forbidden as e:
            logger.error("Permission denied deleting bucket",
                        bucket_name=bucket_name, error=str(e))
            return False

        except Exception as e:
            logger.error("Unexpected error deleting GCS bucket",
                        bucket_name=bucket_name,
                        error=str(e),
                        error_type=type(e).__name__)
            return False

    def _force_delete_bucket_contents(self, bucket):
        """Force delete all contents from a bucket including all versions."""
        try:
            logger.info("Starting force delete of bucket contents", bucket_name=bucket.name)

            # Get all objects including versions
            all_blobs = list(bucket.list_blobs(versions=True))
            logger.info("Found objects to delete",
                       bucket_name=bucket.name,
                       total_objects=len(all_blobs))

            if not all_blobs:
                logger.info("No objects found in bucket", bucket_name=bucket.name)
                return

            # Delete in batches to avoid timeouts
            batch_size = 100
            deleted_count = 0

            for i in range(0, len(all_blobs), batch_size):
                batch = all_blobs[i:i + batch_size]

                for blob in batch:
                    try:
                        blob.delete()
                        deleted_count += 1
                        logger.debug("Deleted blob version",
                                   blob_name=blob.name,
                                   generation=blob.generation,
                                   bucket_name=bucket.name)
                    except gcp_exceptions.NotFound:
                        deleted_count += 1
                        logger.debug("Blob already deleted",
                                   blob_name=blob.name,
                                   bucket_name=bucket.name)
                    except Exception as blob_error:
                        logger.warning("Failed to delete blob, continuing",
                                     blob_name=blob.name,
                                     error=str(blob_error),
                                     bucket_name=bucket.name)

                logger.info("Completed batch deletion",
                           batch_number=i // batch_size + 1,
                           batch_size=len(batch),
                           deleted_in_batch=len(batch),
                           total_deleted=deleted_count,
                           bucket_name=bucket.name)

            # Additional cleanup
            remaining_objects = list(bucket.list_blobs())
            if remaining_objects:
                logger.info("Cleaning up remaining objects",
                           bucket_name=bucket.name,
                           remaining_count=len(remaining_objects))

                for blob in remaining_objects:
                    try:
                        blob.delete()
                        deleted_count += 1
                    except:
                        pass  # Best effort cleanup

            logger.info("Bucket contents force deletion completed",
                       bucket_name=bucket.name,
                       total_deleted=deleted_count,
                       original_count=len(all_blobs))

        except Exception as e:
            logger.error("Error during force delete of bucket contents",
                        bucket_name=bucket.name,
                        error=str(e),
                        error_type=type(e).__name__)
            raise

    async def get_bucket_metadata(self, bucket_name: str) -> Optional[Dict]:
        """Get metadata for a GCS bucket."""
        try:
            bucket = self.client.bucket(bucket_name)
            bucket.reload()  # Fetch latest metadata

            # Calculate bucket size
            total_size = 0
            blob_count = 0
            for blob in bucket.list_blobs():
                total_size += blob.size or 0
                blob_count += 1

            return {
                "bucket_name": bucket_name,
                "location": bucket.location,
                "storage_class": bucket.storage_class,
                "created_at": getattr(bucket, 'time_created', None),
                "updated_at": getattr(bucket, 'updated', None),
                "size_bytes": total_size,
                "object_count": blob_count,
                "versioning_enabled": getattr(bucket, 'versioning_enabled', False),
                "lifecycle_rules": len(list(bucket.lifecycle_rules)) if hasattr(bucket, 'lifecycle_rules') else 0
            }

        except gcp_exceptions.NotFound:
            logger.warning("Bucket not found", bucket_name=bucket_name)
            return None

        except Exception as e:
            logger.error("Failed to get bucket metadata",
                        bucket_name=bucket_name,
                        error=str(e))
            return None

    async def list_buckets(self, user_prefix: str) -> List[Dict]:
        """List all GCS buckets for a user based on naming pattern."""
        try:
            buckets = []

            # List all buckets and filter by user pattern
            for bucket in self.client.list_buckets():
                # Check if bucket name contains user identifier
                if user_prefix in bucket.name:
                    metadata = await self.get_bucket_metadata(bucket.name)
                    if metadata:
                        buckets.append(metadata)

            # Sort by creation date (newest first)
            buckets.sort(key=lambda x: x['created_at'], reverse=True)

            return buckets

        except Exception as e:
            logger.error("Failed to list user buckets",
                        user_prefix=user_prefix,
                        error=str(e))
            return []

    def get_fuse_volume_spec(self, bucket_name: str, mount_path: str = "/workspace") -> Dict:
        """Generate GCS FUSE volume specification for Kubernetes."""
        return {
            "name": "user-workspace-fuse",
            "csi": {
                "driver": "gcsfuse.csi.storage.gke.io",
                "volumeAttributes": {
                    "bucketName": bucket_name,
                    "mountOptions": "implicit-dirs,uid=1000,gid=1000"
                }
            }
        }

    def get_fuse_volume_mount(self, mount_path: str = "/workspace") -> Dict:
        """Generate volume mount specification for GCS FUSE."""
        return {
            "name": "user-workspace-fuse",
            "mountPath": mount_path
        }

    async def ensure_bucket_permissions(
        self,
        bucket_name: str,
        identity: str
    ) -> bool:
        """Ensure service account has proper bucket permissions."""
        try:
            bucket = self.client.bucket(bucket_name)
            policy = bucket.get_iam_policy(requested_policy_version=3)

            # Add objectAdmin role for the service account
            object_admin_role = "roles/storage.objectAdmin"
            member = f"serviceAccount:{identity}"

            # Check if permission already exists
            for binding in policy.bindings:
                if binding.get("role") == object_admin_role:
                    if member in binding.get("members", []):
                        logger.info("Bucket permissions already configured",
                                   bucket_name=bucket_name,
                                   service_account=identity)
                        return True

            # Add the permission
            policy.bindings.append({
                "role": object_admin_role,
                "members": [member]
            })

            bucket.set_iam_policy(policy)

            logger.info("Added bucket permissions",
                       bucket_name=bucket_name,
                       service_account=identity,
                       role=object_admin_role)

            return True

        except Exception as e:
            logger.error("Failed to set bucket permissions",
                        bucket_name=bucket_name,
                        service_account=identity,
                        error=str(e))
            return False

    async def upload_object(
        self,
        bucket_name: str,
        object_name: str,
        content: bytes,
        content_type: Optional[str] = None
    ) -> bool:
        """Upload an object to GCS bucket."""
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_name)

            # Set content type
            if content_type and content_type != 'application/octet-stream':
                blob.content_type = content_type
            else:
                # Try to guess content type from filename
                import mimetypes
                guessed_type, _ = mimetypes.guess_type(object_name)
                if guessed_type:
                    blob.content_type = guessed_type
                else:
                    blob.content_type = 'application/octet-stream'

            logger.info("Uploading object to GCS",
                       bucket_name=bucket_name,
                       object_name=object_name,
                       content_type=blob.content_type,
                       size=len(content))

            # Upload the file content
            blob.upload_from_string(content, content_type=blob.content_type)

            logger.info("Uploaded object to GCS bucket",
                       bucket_name=bucket_name,
                       object_name=object_name,
                       size=len(content),
                       content_type=blob.content_type)

            return True

        except Exception as e:
            logger.error("Failed to upload object to GCS",
                        bucket_name=bucket_name,
                        object_name=object_name,
                        error=str(e))
            return False

    async def download_object(
        self,
        bucket_name: str,
        object_name: str
    ) -> Optional[bytes]:
        """Download an object from GCS bucket."""
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_name)

            # Check if object exists
            if not blob.exists():
                logger.warning("Object not found for download",
                              bucket_name=bucket_name,
                              object_name=object_name)
                return None

            # Download the object
            file_content = blob.download_as_bytes()

            logger.info("Downloaded object from GCS bucket",
                       bucket_name=bucket_name,
                       object_name=object_name,
                       size=len(file_content))

            return file_content

        except gcp_exceptions.NotFound:
            logger.warning("Object not found for download",
                          bucket_name=bucket_name,
                          object_name=object_name)
            return None
        except Exception as e:
            logger.error("Failed to download object from GCS",
                        bucket_name=bucket_name,
                        object_name=object_name,
                        error=str(e))
            return None

    async def list_objects(
        self,
        bucket_name: str,
        prefix: str = ""
    ) -> List[Dict]:
        """List objects in GCS bucket."""
        try:
            bucket = self.client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)

            objects = []
            for blob in blobs:
                objects.append({
                    "name": blob.name,
                    "size": blob.size,
                    "content_type": blob.content_type,
                    "created": blob.time_created.isoformat() if blob.time_created else None,
                    "updated": blob.updated.isoformat() if blob.updated else None,
                    "etag": blob.etag,
                    "md5_hash": blob.md5_hash,
                    "generation": blob.generation,
                    "url": f"gs://{bucket_name}/{blob.name}"
                })

            logger.info("Listed objects in GCS bucket",
                       bucket_name=bucket_name,
                       prefix=prefix,
                       object_count=len(objects))

            return objects

        except Exception as e:
            logger.error("Failed to list objects in GCS",
                        bucket_name=bucket_name,
                        prefix=prefix,
                        error=str(e))
            return []

    async def delete_object(
        self,
        bucket_name: str,
        object_name: str
    ) -> bool:
        """Delete an object from GCS bucket."""
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_name)

            # Check if object exists
            if not blob.exists():
                logger.warning("Object not found for deletion",
                              bucket_name=bucket_name,
                              object_name=object_name)
                return False

            # Delete the object
            blob.delete()

            logger.info("Deleted object from GCS bucket",
                       bucket_name=bucket_name,
                       object_name=object_name)

            return True

        except gcp_exceptions.NotFound:
            logger.warning("Object not found for deletion",
                          bucket_name=bucket_name,
                          object_name=object_name)
            return False
        except Exception as e:
            logger.error("Failed to delete object from GCS",
                        bucket_name=bucket_name,
                        object_name=object_name,
                        error=str(e))
            return False

    async def get_object_info(
        self,
        bucket_name: str,
        object_name: str
    ) -> Optional[Dict]:
        """Get information about a specific object in GCS."""
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_name)

            if not blob.exists():
                return None

            # Reload to get fresh metadata
            blob.reload()

            return {
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "etag": blob.etag,
                "md5_hash": blob.md5_hash,
                "generation": blob.generation,
                "url": f"gs://{bucket_name}/{blob.name}",
                "metadata": blob.metadata or {}
            }

        except Exception as e:
            logger.error("Failed to get object info from GCS",
                        bucket_name=bucket_name,
                        object_name=object_name,
                        error=str(e))
            return None

    def extract_cosmic_name_components(self, bucket_name: str) -> tuple[str, str]:
        """Extract the cosmic theme components from bucket name for display."""
        try:
            parts = bucket_name.split('-')
            if len(parts) >= 2:
                constellation = parts[0].title()
                cosmic_term = parts[1].title()
                return constellation, cosmic_term
            return "Unknown", "Cosmic"
        except:
            return "Unknown", "Cosmic"

    def get_friendly_display_name(self, bucket_name: str) -> str:
        """Generate a user-friendly display name from bucket name."""
        constellation, cosmic_term = self.extract_cosmic_name_components(bucket_name)
        return f"{constellation} {cosmic_term}"
