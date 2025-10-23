"""
Amazon Web Services Storage Provider Implementation

This module implements the CloudStorageProvider interface for Amazon S3.
"""

import random
import time
import re
import hashlib
from typing import Dict, List, Optional
from datetime import datetime
import structlog

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
    ClientError = Exception
    BotoCoreError = Exception

from .base import CloudStorageProvider

logger = structlog.get_logger()


class AWSStorageProvider(CloudStorageProvider):
    """Amazon S3 implementation of the CloudStorageProvider interface."""

    # Cosmology-themed naming components (same as GCP for consistency)
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

    def __init__(self, region: str, account_id: Optional[str] = None):
        """
        Initialize AWS S3 Storage Provider.

        Args:
            region: AWS region for bucket creation
            account_id: AWS account ID (optional, used for bucket naming)
        """
        if not BOTO3_AVAILABLE:
            raise ImportError(
                "boto3 is required for AWS storage provider. "
                "Install it with: pip install boto3"
            )

        self.region = region
        self.account_id = account_id
        self.s3_client = boto3.client('s3', region_name=region)
        self.s3_resource = boto3.resource('s3', region_name=region)

        logger.info("Initialized AWS S3 storage provider",
                   region=region,
                   account_id=account_id)

    def _sanitize_for_storage(self, name: str) -> str:
        """Sanitize string for S3 bucket naming."""
        name = name.lower()
        # S3 buckets: lowercase letters, numbers, hyphens, dots
        # Must start with letter or number
        name = re.sub(r'[^a-z0-9.-]', '-', name)
        name = name.strip('-.')

        # Ensure starts with alphanumeric
        if name and not name[0].isalnum():
            name = 'b' + name

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

        # Ensure it meets S3 naming requirements
        bucket_name = self._sanitize_for_storage(bucket_name)

        # S3 bucket names must be globally unique and 3-63 characters
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
        """Create a new S3 bucket for user."""
        try:
            if not bucket_name:
                bucket_name = self.generate_cosmic_bucket_name(user_id)

            # Create bucket configuration
            create_bucket_config = {}

            # LocationConstraint is not needed for us-east-1
            if self.region != 'us-east-1':
                create_bucket_config['LocationConstraint'] = self.region

            # Create the bucket
            if create_bucket_config:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration=create_bucket_config
                )
            else:
                # us-east-1 doesn't need LocationConstraint
                self.s3_client.create_bucket(Bucket=bucket_name)

            # Enable versioning for data protection
            self.s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )

            # Set lifecycle rules to manage costs (delete old versions)
            lifecycle_config = {
                'Rules': [
                    {
                        'ID': 'DeleteOldVersions',
                        'Status': 'Enabled',
                        'NoncurrentVersionExpiration': {
                            'NoncurrentDays': 30,
                            'NewerNoncurrentVersions': 30
                        }
                    }
                ]
            }
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=lifecycle_config
            )

            # Add tags for organization
            self.s3_client.put_bucket_tagging(
                Bucket=bucket_name,
                Tagging={
                    'TagSet': [
                        {'Key': 'User', 'Value': user_id},
                        {'Key': 'ManagedBy', 'Value': 'CMBCluster'},
                        {'Key': 'CreatedAt', 'Value': datetime.utcnow().isoformat()}
                    ]
                }
            )

            logger.info("Created S3 bucket",
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

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')

            if error_code == 'BucketAlreadyExists' or error_code == 'BucketAlreadyOwnedByYou':
                logger.warning("Bucket name conflict, generating new name",
                              bucket_name=bucket_name,
                              user_id=user_id,
                              error_code=error_code)
                # Try with a new name
                new_bucket_name = self.generate_cosmic_bucket_name(user_id)
                return await self.create_bucket(user_id, new_bucket_name, storage_class)
            else:
                logger.error("Failed to create S3 bucket",
                            bucket_name=bucket_name,
                            user_id=user_id,
                            error=str(e),
                            error_code=error_code)
                raise

        except Exception as e:
            logger.error("Unexpected error creating S3 bucket",
                        bucket_name=bucket_name,
                        user_id=user_id,
                        error=str(e))
            raise

    async def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """Delete an S3 bucket."""
        try:
            bucket = self.s3_resource.Bucket(bucket_name)

            # Check if bucket exists
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code == '404':
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

            logger.info("Successfully deleted S3 bucket", bucket_name=bucket_name, force=force)
            return True

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')

            if error_code == 'NoSuchBucket' or error_code == '404':
                logger.warning("Bucket not found for deletion", bucket_name=bucket_name)
                return True  # Consider it successful if already deleted

            elif error_code == 'BucketNotEmpty':
                if force:
                    logger.error("Bucket still not empty after force deletion",
                               bucket_name=bucket_name)
                else:
                    logger.error("Bucket not empty and force=False",
                               bucket_name=bucket_name)
                return False

            else:
                logger.error("Error deleting S3 bucket",
                           bucket_name=bucket_name,
                           error=str(e),
                           error_code=error_code)
                return False

        except Exception as e:
            logger.error("Unexpected error deleting S3 bucket",
                        bucket_name=bucket_name,
                        error=str(e),
                        error_type=type(e).__name__)
            return False

    def _force_delete_bucket_contents(self, bucket):
        """Force delete all contents from a bucket including all versions."""
        try:
            logger.info("Starting force delete of bucket contents", bucket_name=bucket.name)

            # Delete all object versions and delete markers
            deleted_count = 0
            batch_size = 1000  # S3 allows up to 1000 objects per delete request

            # Use paginator to handle large numbers of objects
            paginator = self.s3_client.get_paginator('list_object_versions')
            pages = paginator.paginate(Bucket=bucket.name)

            for page in pages:
                # Collect objects to delete
                objects_to_delete = []

                # Add versions
                if 'Versions' in page:
                    for version in page['Versions']:
                        objects_to_delete.append({
                            'Key': version['Key'],
                            'VersionId': version['VersionId']
                        })

                # Add delete markers
                if 'DeleteMarkers' in page:
                    for marker in page['DeleteMarkers']:
                        objects_to_delete.append({
                            'Key': marker['Key'],
                            'VersionId': marker['VersionId']
                        })

                # Delete in batches
                if objects_to_delete:
                    for i in range(0, len(objects_to_delete), batch_size):
                        batch = objects_to_delete[i:i + batch_size]

                        response = self.s3_client.delete_objects(
                            Bucket=bucket.name,
                            Delete={'Objects': batch}
                        )

                        deleted = response.get('Deleted', [])
                        deleted_count += len(deleted)

                        errors = response.get('Errors', [])
                        if errors:
                            logger.warning("Some objects failed to delete",
                                         bucket_name=bucket.name,
                                         error_count=len(errors),
                                         errors=errors[:5])  # Log first 5 errors

                        logger.debug("Deleted batch of objects",
                                   bucket_name=bucket.name,
                                   batch_size=len(batch),
                                   deleted=len(deleted))

            logger.info("Bucket contents force deletion completed",
                       bucket_name=bucket.name,
                       total_deleted=deleted_count)

        except Exception as e:
            logger.error("Error during force delete of bucket contents",
                        bucket_name=bucket.name,
                        error=str(e),
                        error_type=type(e).__name__)
            raise

    async def get_bucket_metadata(self, bucket_name: str) -> Optional[Dict]:
        """Get metadata for an S3 bucket."""
        try:
            # Get bucket location
            location_response = self.s3_client.get_bucket_location(Bucket=bucket_name)
            location = location_response.get('LocationConstraint') or 'us-east-1'

            # Get bucket creation date
            bucket = self.s3_resource.Bucket(bucket_name)

            # Calculate bucket size and object count
            total_size = 0
            object_count = 0
            for obj in bucket.objects.all():
                total_size += obj.size
                object_count += 1

            # Check versioning status
            try:
                versioning = self.s3_client.get_bucket_versioning(Bucket=bucket_name)
                versioning_enabled = versioning.get('Status') == 'Enabled'
            except:
                versioning_enabled = False

            # Get lifecycle rules count
            try:
                lifecycle = self.s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                lifecycle_rules = len(lifecycle.get('Rules', []))
            except:
                lifecycle_rules = 0

            return {
                "bucket_name": bucket_name,
                "location": location,
                "storage_class": "STANDARD",  # S3 doesn't have bucket-level storage class
                "created_at": bucket.creation_date,
                "updated_at": None,  # S3 doesn't track bucket update time
                "size_bytes": total_size,
                "object_count": object_count,
                "versioning_enabled": versioning_enabled,
                "lifecycle_rules": lifecycle_rules
            }

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchBucket' or error_code == '404':
                logger.warning("Bucket not found", bucket_name=bucket_name)
                return None
            logger.error("Failed to get bucket metadata",
                        bucket_name=bucket_name,
                        error=str(e),
                        error_code=error_code)
            return None

        except Exception as e:
            logger.error("Unexpected error getting bucket metadata",
                        bucket_name=bucket_name,
                        error=str(e))
            return None

    async def list_buckets(self, user_prefix: str) -> List[Dict]:
        """List all S3 buckets for a user based on naming pattern."""
        try:
            buckets = []

            # List all buckets
            response = self.s3_client.list_buckets()

            for bucket_info in response.get('Buckets', []):
                bucket_name = bucket_info['Name']

                # Check if bucket name contains user identifier
                if user_prefix in bucket_name:
                    metadata = await self.get_bucket_metadata(bucket_name)
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
        """Generate S3 Mountpoint FUSE volume specification for Kubernetes."""
        return {
            "name": "user-workspace-fuse",
            "csi": {
                "driver": "s3.csi.aws.com",
                "volumeAttributes": {
                    "bucketName": bucket_name,
                    "region": self.region,
                    "mountOptions": "allow-delete,uid=1000,gid=1000"
                }
            }
        }

    def get_fuse_volume_mount(self, mount_path: str = "/workspace") -> Dict:
        """Generate volume mount specification for S3 Mountpoint FUSE."""
        return {
            "name": "user-workspace-fuse",
            "mountPath": mount_path
        }

    async def ensure_bucket_permissions(
        self,
        bucket_name: str,
        identity: str
    ) -> bool:
        """
        Ensure IAM role has proper bucket permissions.

        For AWS, the identity should be an IAM role ARN.
        Permissions are typically managed through IAM policies rather than bucket policies.
        """
        try:
            # Get existing bucket policy or create new one
            try:
                policy_response = self.s3_client.get_bucket_policy(Bucket=bucket_name)
                import json
                policy = json.loads(policy_response['Policy'])
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                    # Create new policy
                    policy = {
                        "Version": "2012-10-17",
                        "Statement": []
                    }
                else:
                    raise

            # Check if permission already exists
            role_arn = identity if identity.startswith('arn:') else f"arn:aws:iam::{self.account_id}:role/{identity}"

            for statement in policy.get('Statement', []):
                if statement.get('Principal', {}).get('AWS') == role_arn:
                    logger.info("Bucket permissions already configured",
                               bucket_name=bucket_name,
                               role_arn=role_arn)
                    return True

            # Add new permission statement
            policy['Statement'].append({
                "Sid": "AllowRoleAccess",
                "Effect": "Allow",
                "Principal": {
                    "AWS": role_arn
                },
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ]
            })

            # Set the bucket policy
            import json
            self.s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(policy)
            )

            logger.info("Added bucket permissions",
                       bucket_name=bucket_name,
                       role_arn=role_arn)

            return True

        except Exception as e:
            logger.error("Failed to set bucket permissions",
                        bucket_name=bucket_name,
                        identity=identity,
                        error=str(e))
            return False

    async def upload_object(
        self,
        bucket_name: str,
        object_name: str,
        content: bytes,
        content_type: Optional[str] = None
    ) -> bool:
        """Upload an object to S3 bucket."""
        try:
            # Determine content type
            if not content_type or content_type == 'application/octet-stream':
                import mimetypes
                guessed_type, _ = mimetypes.guess_type(object_name)
                content_type = guessed_type or 'application/octet-stream'

            logger.info("Uploading object to S3",
                       bucket_name=bucket_name,
                       object_name=object_name,
                       content_type=content_type,
                       size=len(content))

            # Upload the object
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=object_name,
                Body=content,
                ContentType=content_type
            )

            logger.info("Uploaded object to S3 bucket",
                       bucket_name=bucket_name,
                       object_name=object_name,
                       size=len(content),
                       content_type=content_type)

            return True

        except Exception as e:
            logger.error("Failed to upload object to S3",
                        bucket_name=bucket_name,
                        object_name=object_name,
                        error=str(e))
            return False

    async def download_object(
        self,
        bucket_name: str,
        object_name: str
    ) -> Optional[bytes]:
        """Download an object from S3 bucket."""
        try:
            logger.info("Downloading object from S3",
                       bucket_name=bucket_name,
                       object_name=object_name)

            response = self.s3_client.get_object(Bucket=bucket_name, Key=object_name)
            file_content = response['Body'].read()

            logger.info("Downloaded object from S3 bucket",
                       bucket_name=bucket_name,
                       object_name=object_name,
                       size=len(file_content))

            return file_content

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchKey':
                logger.warning("Object not found for download",
                              bucket_name=bucket_name,
                              object_name=object_name)
                return None
            logger.error("Failed to download object from S3",
                        bucket_name=bucket_name,
                        object_name=object_name,
                        error=str(e),
                        error_code=error_code)
            return None

        except Exception as e:
            logger.error("Unexpected error downloading object from S3",
                        bucket_name=bucket_name,
                        object_name=object_name,
                        error=str(e))
            return None

    async def list_objects(
        self,
        bucket_name: str,
        prefix: str = ""
    ) -> List[Dict]:
        """List objects in S3 bucket."""
        try:
            objects = []

            # Use paginator for large buckets
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

            for page in pages:
                for obj in page.get('Contents', []):
                    objects.append({
                        "name": obj['Key'],
                        "size": obj['Size'],
                        "content_type": None,  # Not available in list operation
                        "created": obj['LastModified'].isoformat(),
                        "updated": obj['LastModified'].isoformat(),
                        "etag": obj['ETag'].strip('"'),
                        "md5_hash": obj['ETag'].strip('"'),
                        "generation": None,  # S3 doesn't have generation concept
                        "url": f"s3://{bucket_name}/{obj['Key']}"
                    })

            logger.info("Listed objects in S3 bucket",
                       bucket_name=bucket_name,
                       prefix=prefix,
                       object_count=len(objects))

            return objects

        except Exception as e:
            logger.error("Failed to list objects in S3",
                        bucket_name=bucket_name,
                        prefix=prefix,
                        error=str(e))
            return []

    async def delete_object(
        self,
        bucket_name: str,
        object_name: str
    ) -> bool:
        """Delete an object from S3 bucket."""
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_name)

            logger.info("Deleted object from S3 bucket",
                       bucket_name=bucket_name,
                       object_name=object_name)

            return True

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            logger.error("Failed to delete object from S3",
                        bucket_name=bucket_name,
                        object_name=object_name,
                        error=str(e),
                        error_code=error_code)
            return False

        except Exception as e:
            logger.error("Unexpected error deleting object from S3",
                        bucket_name=bucket_name,
                        object_name=object_name,
                        error=str(e))
            return False

    async def get_object_info(
        self,
        bucket_name: str,
        object_name: str
    ) -> Optional[Dict]:
        """Get information about a specific object in S3."""
        try:
            response = self.s3_client.head_object(Bucket=bucket_name, Key=object_name)

            return {
                "name": object_name,
                "size": response['ContentLength'],
                "content_type": response.get('ContentType'),
                "created": response['LastModified'].isoformat(),
                "updated": response['LastModified'].isoformat(),
                "etag": response['ETag'].strip('"'),
                "md5_hash": response['ETag'].strip('"'),
                "generation": None,  # S3 doesn't have generation concept
                "url": f"s3://{bucket_name}/{object_name}",
                "metadata": response.get('Metadata', {})
            }

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404' or error_code == 'NoSuchKey':
                return None
            logger.error("Failed to get object info from S3",
                        bucket_name=bucket_name,
                        object_name=object_name,
                        error=str(e),
                        error_code=error_code)
            return None

        except Exception as e:
            logger.error("Unexpected error getting object info from S3",
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
