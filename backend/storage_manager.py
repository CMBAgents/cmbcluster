import asyncio
import re
import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import structlog
from google.cloud import storage
from google.api_core import exceptions as gcp_exceptions

from .config import settings

logger = structlog.get_logger()

class StorageManager:
    """Manages cloud storage buckets for user environments"""
    
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
    
    def __init__(self):
        self.project_id = settings.project_id
        self.region = settings.region
        self.client = storage.Client(project=self.project_id)
    
    def _sanitize_for_storage(self, name: str) -> str:
        """Sanitize string for storage bucket naming"""
        name = name.lower()
        name = re.sub(r'[^a-z0-9-]', '-', name)
        name = name.strip('-')
        return name[:63]
    
    def generate_cosmic_bucket_name(self, user_id: str) -> str:
        """Generate a cosmology-themed bucket name"""
        constellation = random.choice(self.CONSTELLATIONS)
        cosmic_term = random.choice(self.COSMIC_TERMS)
        
        # Create short user identifier (first 8 chars of user_id hash)
        import hashlib
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
    
    async def create_user_bucket(
        self, 
        user_id: str, 
        bucket_name: Optional[str] = None,
        storage_class: str = "STANDARD"
    ) -> Dict:
        """Create a new storage bucket for user"""
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
            
            logger.info("Created storage bucket", 
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
            return await self.create_user_bucket(user_id, new_bucket_name, storage_class)
            
        except Exception as e:
            logger.error("Failed to create storage bucket", 
                        bucket_name=bucket_name, 
                        user_id=user_id, 
                        error=str(e))
            raise
    
    async def delete_user_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """Delete a user storage bucket"""
        try:
            bucket = self.client.bucket(bucket_name)
            
            if force:
                # Delete all objects first
                blobs = list(bucket.list_blobs())
                for blob in blobs:
                    blob.delete()
                    logger.debug("Deleted blob", blob_name=blob.name, bucket_name=bucket_name)
            
            # Delete the bucket
            bucket.delete()
            
            logger.info("Deleted storage bucket", bucket_name=bucket_name, force=force)
            return True
            
        except gcp_exceptions.NotFound:
            logger.warning("Bucket not found for deletion", bucket_name=bucket_name)
            return True  # Consider it successful if already deleted
            
        except Exception as e:
            logger.error("Failed to delete storage bucket", 
                        bucket_name=bucket_name, 
                        error=str(e))
            return False
    
    async def get_bucket_metadata(self, bucket_name: str) -> Optional[Dict]:
        """Get metadata for a storage bucket"""
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
    
    async def list_user_buckets(self, user_prefix: str) -> List[Dict]:
        """List all buckets for a user based on naming pattern"""
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
        """Generate volume specification for cloud fuse CSI"""
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
        """Generate volume mount specification for cloud fuse"""
        return {
            "name": "user-workspace-fuse",
            "mountPath": mount_path
        }
    
    async def ensure_bucket_permissions(
        self, 
        bucket_name: str, 
        service_account_email: str
    ) -> bool:
        """Ensure service account has proper bucket permissions"""
        try:
            bucket = self.client.bucket(bucket_name)
            policy = bucket.get_iam_policy(requested_policy_version=3)
            
            # Add objectAdmin role for the service account
            object_admin_role = "roles/storage.objectAdmin"
            member = f"serviceAccount:{service_account_email}"
            
            # Check if permission already exists
            for binding in policy.bindings:
                if binding.get("role") == object_admin_role:
                    if member in binding.get("members", []):
                        logger.info("Bucket permissions already configured", 
                                   bucket_name=bucket_name, 
                                   service_account=service_account_email)
                        return True
            
            # Add the permission
            policy.bindings.append({
                "role": object_admin_role,
                "members": [member]
            })
            
            bucket.set_iam_policy(policy)
            
            logger.info("Added bucket permissions", 
                       bucket_name=bucket_name, 
                       service_account=service_account_email,
                       role=object_admin_role)
            
            return True
            
        except Exception as e:
            logger.error("Failed to set bucket permissions", 
                        bucket_name=bucket_name, 
                        service_account=service_account_email,
                        error=str(e))
            return False
    
    def format_bucket_size(self, size_bytes: int) -> str:
        """Format bucket size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def extract_cosmic_name_components(self, bucket_name: str) -> Tuple[str, str]:
        """Extract the cosmic theme components from bucket name for display"""
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
        """Generate a user-friendly display name from bucket name"""
        constellation, cosmic_term = self.extract_cosmic_name_components(bucket_name)
        return f"{constellation} {cosmic_term}"

    async def upload_object(self, bucket_name: str, object_name: str, file_content: bytes, content_type: str = None) -> bool:
        """Upload an object to the storage bucket"""
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_name)
            
            # Set content type if provided, with fallback
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
            
            logger.info("About to upload object", 
                       bucket_name=bucket_name,
                       object_name=object_name,
                       content_type=blob.content_type,
                       size=len(file_content))
            
            # Upload the file content
            blob.upload_from_string(file_content, content_type=blob.content_type)
            
            logger.info("Uploaded object to bucket", 
                       bucket_name=bucket_name,
                       object_name=object_name,
                       size=len(file_content),
                       content_type=blob.content_type)
            
            return True
            
        except Exception as e:
            logger.error("Failed to upload object", 
                        bucket_name=bucket_name,
                        object_name=object_name,
                        error=str(e))
            return False

    async def download_object(self, bucket_name: str, object_name: str) -> Optional[bytes]:
        """Download an object from the storage bucket"""
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
            
            logger.info("Downloaded object from bucket", 
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
            logger.error("Failed to download object", 
                        bucket_name=bucket_name,
                        object_name=object_name,
                        error=str(e))
            return None

    async def list_objects(self, bucket_name: str, prefix: str = "") -> List[Dict]:
        """List objects in the storage bucket"""
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
            
            logger.info("Listed objects in bucket", 
                       bucket_name=bucket_name,
                       prefix=prefix,
                       object_count=len(objects))
            
            return objects
            
        except Exception as e:
            logger.error("Failed to list objects", 
                        bucket_name=bucket_name,
                        prefix=prefix,
                        error=str(e))
            return []

    async def delete_object(self, bucket_name: str, object_name: str) -> bool:
        """Delete an object from the storage bucket"""
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
            
            logger.info("Deleted object from bucket", 
                       bucket_name=bucket_name,
                       object_name=object_name)
            
            return True
            
        except gcp_exceptions.NotFound:
            logger.warning("Object not found for deletion", 
                          bucket_name=bucket_name,
                          object_name=object_name)
            return False
        except Exception as e:
            logger.error("Failed to delete object", 
                        bucket_name=bucket_name,
                        object_name=object_name,
                        error=str(e))
            return False

    async def get_object_info(self, bucket_name: str, object_name: str) -> Optional[Dict]:
        """Get information about a specific object"""
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
            logger.error("Failed to get object info", 
                        bucket_name=bucket_name,
                        object_name=object_name,
                        error=str(e))
            return None
