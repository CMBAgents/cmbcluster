import asyncio
import time
import re
import uuid
import tempfile
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import structlog
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import subprocess
import re as regex

from config import settings
from models import Environment, EnvironmentRequest, PodStatus
from storage_models import StorageType, StorageStatus, UserStorage
from storage_manager import StorageManager
from database import get_database
from file_encryption import get_file_encryption

logger = structlog.get_logger()

def _sanitize_for_dns(name: str) -> str:
    """Sanitizes a string to be a valid DNS-1123 subdomain.
    Must be lowercase, max 63 chars, start/end with alphanum, and contain only a-z, 0-9, and -.
    """
    name = name.lower()
    name = re.sub(r'[^a-z0-9-]', '-', name)
    name = name.strip('-')
    return name[:63]


class PodManager:
    def _get_pod_annotations(self, user_email: str, env_id: str, storage, app_name: str) -> dict:
        """
        Get cloud-specific pod annotations for FUSE mount and IAM bindings.

        Args:
            user_email: User's email address
            env_id: Environment ID
            storage: UserStorage object with bucket information
            app_name: Application name

        Returns:
            Dictionary of pod annotations specific to the cloud provider
        """
        # Base annotations (cloud-agnostic)
        annotations = {
            "user.email": user_email,
            "env.id": env_id,
            "storage.id": storage.id,
            "storage.bucket": storage.bucket_name,
            "created.at": datetime.utcnow().isoformat(),
            "managed.by": "cmbcluster",
            "app.name": app_name
        }

        # Add cloud-specific annotations
        if settings.cloud_provider == "gcp":
            # GCP: Enable GCS FUSE and bind to Workload Identity
            annotations.update({
                "gke-gcsfuse/volumes": "true",
                "iam.gke.io/gcp-service-account": f"{settings.cluster_name}-workload-sa@{settings.project_id}.iam.gserviceaccount.com"
            })
        elif settings.cloud_provider == "aws":
            # AWS: Bind to IRSA role for S3 access
            # The role ARN should be configured via Kubernetes ServiceAccount annotation
            # No additional pod annotations needed for AWS S3 CSI driver
            pass

        return annotations

    async def _create_env_secret(self, safe_user_id: str, env_id: str, env_vars: dict):
        """Create a Kubernetes Secret for user environment variables"""
        from kubernetes.client import V1Secret
        namespace = settings.namespace
        secret_name = f"user-env-{safe_user_id}-{env_id}"
        # Kubernetes Secret data must be string:string (not None)
        secret_data = {k: str(v) for k, v in env_vars.items() if v is not None}
        secret = V1Secret(
            metadata={"name": secret_name, "namespace": namespace},
            string_data=secret_data,
            type="Opaque"
        )
        try:
            self.k8s_client.create_namespaced_secret(namespace=namespace, body=secret)
            logger.info("Created env secret for pod", secret_name=secret_name)
        except ApiException as e:
            if e.status == 409:
                logger.info("Env secret already exists", secret_name=secret_name)
            else:
                logger.error("Failed to create env secret", secret_name=secret_name, error=str(e))
                raise
        return secret_name
    
    async def _resolve_image_config(self, config: EnvironmentRequest) -> tuple[str, int, str, str]:
        """Resolve the container image path, port, working directory, and app name from application ID or use defaults"""
        # If application_id is provided, look up the image path, port, working_dir, and name
        if hasattr(config, 'application_id') and config.application_id:
            try:
                logger.info("Looking up application", application_id=config.application_id)
                application = await self.db.get_application(config.application_id)
                if application and application.is_active:
                    port = getattr(application, 'port', 8888) or 8888
                    working_dir = getattr(application, 'working_dir', '/cmbagent') or '/cmbagent'
                    # Sanitize application name for use in Kubernetes labels and container names
                    app_name = _sanitize_for_dns(application.name)
                    logger.info("Using application image",
                              application_id=config.application_id,
                              application_name=application.name,
                              sanitized_app_name=app_name,
                              image_path=application.image_path,
                              port=port,
                              working_dir=working_dir)

                    # Validate image path
                    if not application.image_path or not application.image_path.strip():
                        logger.warning("Application has empty image path, using default",
                                     application_id=config.application_id)
                        # Fall through to defaults
                    else:
                        return application.image_path, port, working_dir, app_name
                else:
                    logger.warning("Application not found or inactive, using default image",
                                 application_id=config.application_id,
                                 application_exists=application is not None,
                                 application_active=application.is_active if application else None)
            except Exception as e:
                logger.error("Failed to resolve application image, using default",
                           application_id=config.application_id,
                           error=str(e))
                import traceback
                logger.error("Application lookup traceback", traceback=traceback.format_exc())

        # Fall back to explicit image or configured default
        image = config.image or settings.default_image
        port = getattr(config, 'port', 8888)  # Default port if not specified
        working_dir = '/cmbagent'  # Default working directory
        app_name = 'cmbagent'  # Default application name
        return image, port, working_dir, app_name

    async def _resolve_image_path(self, config: EnvironmentRequest) -> str:
        """Legacy method for backward compatibility"""
        image, _, _, _ = await self._resolve_image_config(config)
        return image

    def _sanitize_k8s_key(self, key: str) -> str:
        """Sanitize a string to be a valid Kubernetes Secret/ConfigMap key"""
        import re
        # Kubernetes keys must consist of alphanumeric characters, '-', '_' or '.'
        # Replace invalid characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', key)
        
        # Ensure it doesn't start or end with special characters
        sanitized = sanitized.strip('._-')
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = "file"
        
        return sanitized

    async def _create_file_secret(self, safe_user_id: str, env_id: str, user_files: dict):
        """Create a Kubernetes Secret for user files"""
        from kubernetes.client import V1Secret
        
        if not user_files:
            return None
        
        namespace = settings.namespace
        secret_name = f"user-files-{safe_user_id}-{env_id}"
        
        # Decrypt and prepare file data for secret
        encryption = get_file_encryption()
        secret_data = {}
        key_mapping = {}  # Track original filename to sanitized key mapping
        
        for file_id, user_file in user_files.items():
            try:
                # Decrypt file content
                decrypted_content = encryption.decrypt_content(user_file.encrypted_content)
                
                # Use a filename based on the container path, but sanitize for Kubernetes
                original_filename = os.path.basename(user_file.container_path)
                sanitized_key = self._sanitize_k8s_key(original_filename)
                
                # Handle potential key collisions by adding a suffix
                counter = 1
                unique_key = sanitized_key
                while unique_key in secret_data:
                    unique_key = f"{sanitized_key}_{counter}"
                    counter += 1
                
                secret_data[unique_key] = decrypted_content
                key_mapping[unique_key] = original_filename
                
                logger.debug("Added file to secret", 
                           original_filename=original_filename,
                           sanitized_key=unique_key,
                           env_var=user_file.environment_variable_name,
                           container_path=user_file.container_path)
                
            except Exception as e:
                logger.error("Failed to decrypt file for secret", 
                           file_id=file_id, 
                           filename=user_file.file_name,
                           error=str(e),
                           error_type=type(e).__name__)
                # Don't raise - continue with other files, but log the issue
                logger.warning("Skipping file due to decryption error - may need to re-upload", 
                             file_id=file_id,
                             filename=user_file.file_name)
        
        if not secret_data:
            logger.info("No file data to create secret with", user_files_count=len(user_files))
            return None
        
        logger.info("Creating file secret with sanitized keys",
                   secret_name=secret_name,
                   file_count=len(secret_data),
                   key_mapping=key_mapping)
        
        secret = V1Secret(
            metadata={"name": secret_name, "namespace": namespace},
            string_data=secret_data,
            type="Opaque"
        )
        
        try:
            self.k8s_client.create_namespaced_secret(namespace=namespace, body=secret)
            logger.info("Created file secret for pod", 
                       secret_name=secret_name, 
                       file_count=len(secret_data))
        except ApiException as e:
            if e.status == 409:
                logger.info("File secret already exists", secret_name=secret_name)
            else:
                logger.error("Failed to create file secret", 
                           secret_name=secret_name, 
                           error=str(e))
                raise
        
        return secret_name

    async def _delete_env_secret(self, safe_user_id: str, env_id: str):
        """Delete the Kubernetes Secret for user environment variables"""
        namespace = settings.namespace
        secret_name = f"user-env-{safe_user_id}-{env_id}"
        try:
            self.k8s_client.delete_namespaced_secret(name=secret_name, namespace=namespace)
            logger.info("Deleted env secret for pod", secret_name=secret_name)
        except ApiException as e:
            if e.status == 404:
                logger.info("Env secret already deleted", secret_name=secret_name)
            else:
                logger.error("Failed to delete env secret", secret_name=secret_name, error=str(e))
                raise

    async def _delete_file_secret(self, safe_user_id: str, env_id: str):
        """Delete the Kubernetes Secret for user files"""
        namespace = settings.namespace
        secret_name = f"user-files-{safe_user_id}-{env_id}"
        try:
            self.k8s_client.delete_namespaced_secret(name=secret_name, namespace=namespace)
            logger.info("Deleted file secret for pod", secret_name=secret_name)
        except ApiException as e:
            if e.status == 404:
                logger.info("File secret already deleted", secret_name=secret_name)
            else:
                logger.error("Failed to delete file secret", secret_name=secret_name, error=str(e))
                raise
    """Manages Kubernetes pods for user environments"""
    
    def __init__(self):
        self.db = get_database()
        self.storage_manager = StorageManager()
        self._setup_kubernetes()
    
    def _setup_kubernetes(self):
        """Setup Kubernetes client"""
        try:
            # Try in-cluster config first
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes config")
        except:
            try:
                # Fall back to local kubeconfig
                config.load_kube_config()
                logger.info("Loaded local Kubernetes config")
            except Exception as e:
                logger.error("Failed to load Kubernetes config", error=str(e))
                raise
        
        self.k8s_client = client.CoreV1Api()
        self.apps_client = client.AppsV1Api()
        self.networking_client = client.NetworkingV1Api()
        
        # Validate permissions on startup
        self._validate_permissions()
    
    def _validate_permissions(self):
        """Validate that the service account has required permissions"""
        try:
            # Test basic permissions by listing pods in the namespace
            self.k8s_client.list_namespaced_pod(namespace=settings.namespace, limit=1)
            logger.info("Successfully validated pod permissions")
            
            # Test service permissions
            self.k8s_client.list_namespaced_service(namespace=settings.namespace, limit=1)
            logger.info("Successfully validated service permissions")
            
            # Test PVC permissions
            self.k8s_client.list_namespaced_persistent_volume_claim(namespace=settings.namespace, limit=1)
            logger.info("Successfully validated PVC permissions")
            
            # Test ingress permissions
            self.networking_client.list_namespaced_ingress(namespace=settings.namespace, limit=1)
            logger.info("Successfully validated ingress permissions")
            
        except ApiException as e:
            if e.status == 403:
                logger.error("Permission denied - check RBAC configuration", 
                           status=e.status, 
                           reason=e.reason,
                           namespace=settings.namespace)
                logger.error("Required permissions: pods, services, persistentvolumeclaims, ingresses (create, delete, get, list, patch, update, watch)")
            else:
                logger.warning("Permission validation failed", 
                             status=e.status, 
                             reason=e.reason)
        except Exception as e:
            logger.warning("Permission validation failed", error=str(e))
    
    async def create_user_environment(
        self, 
        user_id: str, 
        user_email: str, 
        config: EnvironmentRequest
    ) -> Environment:
        """Create a new user environment pod with cloud storage"""
        safe_user_id = _sanitize_for_dns(user_email)
        env_id = str(uuid.uuid4())[:8]  # Short unique ID for this environment
        pod_name = self._generate_pod_name(safe_user_id, env_id)
        namespace = settings.namespace
        
        logger.info("Creating user environment", 
                    user_id=user_id, 
                    user_email=user_email,
                    safe_user_id=safe_user_id,
                    env_id=env_id,
                    pod_name=pod_name)
        
        try:
            # Ensure default OPENAI_API_KEY env var exists for user
            user_env_vars = await self.db.get_user_env_vars(user_id)
            if "OPENAI_API_KEY" not in user_env_vars:
                await self.db.set_user_env_var(user_id, "OPENAI_API_KEY", "")
                user_env_vars["OPENAI_API_KEY"] = ""

            # Get user files for environment variables and mounting
            user_files = await self.db.get_user_files_for_environment(user_id)
            
            # Add file-based environment variables to merged env vars
            for env_var_name, user_file in user_files.items():
                user_env_vars[env_var_name] = user_file.container_path

            # Merge env_vars from config (request) with DB (DB values overwritten by request)
            merged_env_vars = dict(user_env_vars)
            if getattr(config, "env_vars", None):
                merged_env_vars.update(config.env_vars)

            # Handle storage selection/creation
            storage = await self._handle_storage_selection(user_id, config)

            # Resolve image path, port, working directory, and app name from application ID if provided
            image_path, container_port, working_dir, app_name = await self._resolve_image_config(config)

            # Create secret for env vars
            secret_name = await self._create_env_secret(safe_user_id, env_id, merged_env_vars)

            # Create secret for user files
            file_secret_name = await self._create_file_secret(safe_user_id, env_id, user_files)

            # Create pod with cloud storage, referencing secrets
            logger.info("Building pod specification",
                       pod_name=pod_name,
                       image_path=image_path,
                       container_port=container_port,
                       working_dir=working_dir,
                       app_name=app_name)

            pod_spec = self._build_pod_spec_with_storage(
                user_id, safe_user_id, env_id, user_email, pod_name, config, storage, secret_name, file_secret_name, image_path, container_port, working_dir, app_name
            )
            
            logger.info("Creating pod in Kubernetes", pod_name=pod_name, namespace=namespace)
            try:
                self.k8s_client.create_namespaced_pod(
                    namespace=namespace, 
                    body=pod_spec
                )
                logger.info("Pod created successfully", pod_name=pod_name)
            except Exception as k8s_error:
                logger.error("Kubernetes pod creation failed", 
                           pod_name=pod_name,
                           error=str(k8s_error),
                           error_type=type(k8s_error).__name__)
                if hasattr(k8s_error, 'status') and hasattr(k8s_error, 'reason'):
                    logger.error("Kubernetes API error details",
                               status=k8s_error.status,
                               reason=k8s_error.reason,
                               body=getattr(k8s_error, 'body', None))
                raise

            # Create service
            await self._create_user_service(safe_user_id, env_id, container_port, app_name)

            # Create ingress
            await self._create_user_ingress(safe_user_id, env_id, container_port, app_name)

            # Create environment record
            environment = Environment(
                id=f"{user_id}-{env_id}",
                user_id=user_id,
                user_email=user_email,
                env_id=env_id,
                pod_name=pod_name,
                status=PodStatus.PENDING,
                url=f"https://{safe_user_id}-{env_id}.{settings.base_domain}",
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                resource_config={
                    "cpu_limit": config.cpu_limit,
                    "memory_limit": config.memory_limit,
                    "storage_id": storage.id,
                    "storage_bucket": storage.bucket_name,
                    "storage_type": storage.storage_type.value
                }
            )

            # Store environment in database
            await self.db.create_environment(environment)

            # Link environment to storage
            await self.db.link_environment_storage(environment.id, storage.id)

            logger.info("User environment created successfully", 
                        user_id=user_id, 
                        user_email=user_email,
                        safe_user_id=safe_user_id,
                        env_id=env_id,
                        url=environment.url,
                        pod_name=pod_name,
                        storage_bucket=storage.bucket_name)

            return environment

        except Exception as e:
            logger.error("Failed to create user environment", 
                        user_id=user_id, 
                        user_email=user_email,
                        env_id=env_id,
                        error=str(e))
            
            # Enhanced error logging for debugging
            if isinstance(e, ApiException):
                logger.error("Kubernetes API error details",
                           status=e.status,
                           reason=e.reason,
                           body=e.body if hasattr(e, 'body') else 'N/A')
                
                if e.status == 403:
                    logger.error("Permission denied - check RBAC configuration for service account")
            
            # Cleanup any partially created resources
            try:
                await self._cleanup_failed_environment(safe_user_id, env_id)
            except Exception as cleanup_error:
                logger.error("Failed to cleanup after failed environment creation",
                           cleanup_error=str(cleanup_error))
            
            raise
    
    async def _handle_storage_selection(self, user_id: str, config: EnvironmentRequest) -> UserStorage:
        """Handle storage selection or creation for environment"""
        
        # If storage_id is provided, use existing storage
        if config.storage_id:
            storage = await self.db.get_storage_by_id(config.storage_id)
            if not storage or storage.user_id != user_id:
                raise ValueError(f"Storage {config.storage_id} not found or not accessible")
            
            # Ensure storage is active
            if storage.status != StorageStatus.ACTIVE:
                raise ValueError(f"Storage {config.storage_id} is not active")
            
            # Update last accessed time
            await self.db.update_storage_metadata(storage.id, storage.size_bytes, storage.object_count)
            logger.info("Using existing storage", storage_id=storage.id, bucket_name=storage.bucket_name)
            return storage
        
        # If create_new_storage is True, create new storage
        if config.create_new_storage:
            import uuid
            storage_id = str(uuid.uuid4())
            
            logger.info("Creating new storage bucket", user_id=user_id, storage_id=storage_id)
            
            # Create bucket
            bucket_metadata = await self.storage_manager.create_user_bucket(
                user_id=user_id,
                storage_class=config.storage_class or "STANDARD"
            )
            
            # Generate display name
            display_name = self.storage_manager.get_friendly_display_name(bucket_metadata['bucket_name'])
            
            # Create storage record
            storage = UserStorage(
                id=storage_id,
                user_id=user_id,
                bucket_name=bucket_metadata['bucket_name'],
                display_name=display_name,
                storage_type=StorageType.CLOUD_STORAGE,
                status=StorageStatus.ACTIVE,
                created_at=bucket_metadata['created_at'],
                size_bytes=0,
                object_count=0,
                location=bucket_metadata['location'],
                storage_class=bucket_metadata['storage_class'],
                versioning_enabled=bucket_metadata['versioning_enabled']
            )
            
            await self.db.create_storage(storage)
            
            # Configure permissions for user environment service account
            user_sa_email = f"{settings.cluster_name}-workload-sa@{settings.project_id}.iam.gserviceaccount.com"
            await self.storage_manager.ensure_bucket_permissions(storage.bucket_name, user_sa_email)
            
            logger.info("Created new storage successfully", 
                       storage_id=storage.id, 
                       bucket_name=storage.bucket_name,
                       display_name=display_name)
            return storage
        
        # Default: Check for existing storage or create first one
        # This should only happen if neither storage_id nor create_new_storage is specified
        user_storages = await self.db.get_user_storages(user_id)
        
        if user_storages:
            # Use most recent active storage
            for storage in user_storages:
                if storage.status == StorageStatus.ACTIVE:
                    await self.db.update_storage_metadata(storage.id, storage.size_bytes, storage.object_count)
                    logger.info("Using default existing storage", 
                               storage_id=storage.id, 
                               bucket_name=storage.bucket_name)
                    return storage
        
        # No existing storage, create first one automatically
        import uuid
        storage_id = str(uuid.uuid4())
        
        logger.info("No existing storage found, creating first storage automatically", user_id=user_id)
        
        bucket_metadata = await self.storage_manager.create_user_bucket(
            user_id=user_id,
            storage_class="STANDARD"
        )
        
        display_name = self.storage_manager.get_friendly_display_name(bucket_metadata['bucket_name'])
        
        storage = UserStorage(
            id=storage_id,
            user_id=user_id,
            bucket_name=bucket_metadata['bucket_name'],
            display_name=display_name,
            storage_type=StorageType.CLOUD_STORAGE,
            status=StorageStatus.ACTIVE,
            created_at=bucket_metadata['created_at'],
            size_bytes=0,
            object_count=0,
            location=bucket_metadata['location'],
            storage_class=bucket_metadata['storage_class'],
            versioning_enabled=bucket_metadata['versioning_enabled']
        )
        
        await self.db.create_storage(storage)
        
        # Configure permissions
        sa_email = f"{settings.cluster_name}-workload-sa@{settings.project_id}.iam.gserviceaccount.com"
        await self.storage_manager.ensure_bucket_permissions(storage.bucket_name, sa_email)
        
        logger.info("Created first storage successfully", 
                   storage_id=storage.id, 
                   bucket_name=storage.bucket_name)
        return storage
    
    async def delete_user_storage(self, user_id: str, storage_id: str) -> bool:
        """Delete user storage and associated bucket"""
        try:
            # Get storage record
            storage = await self.db.get_storage_by_id(storage_id)
            if not storage or storage.user_id != user_id:
                raise ValueError(f"Storage {storage_id} not found or not accessible")
            
            logger.info("Deleting user storage", 
                       user_id=user_id, 
                       storage_id=storage_id,
                       bucket_name=storage.bucket_name)
            
            # Check if storage is being used by any active environments
            user_envs = await self.db.get_user_environments(user_id)
            active_envs_using_storage = []
            
            for env in user_envs:
                if (env.resource_config.get('storage_id') == storage_id and 
                    env.status in [PodStatus.PENDING, PodStatus.RUNNING]):
                    active_envs_using_storage.append(env.env_id)
            
            if active_envs_using_storage:
                raise ValueError(f"Cannot delete storage: in use by active environments {active_envs_using_storage}")
            
            # Delete the bucket from GCS
            await self.storage_manager.delete_user_bucket(storage.bucket_name)
            
            # Mark storage as deleted in database
            await self.db.delete_storage(storage_id)
            
            logger.info("Storage deleted successfully", 
                       user_id=user_id, 
                       storage_id=storage_id,
                       bucket_name=storage.bucket_name)
            
            return True
            
        except Exception as e:
            logger.error("Failed to delete storage", 
                        user_id=user_id, 
                        storage_id=storage_id,
                        error=str(e))
            raise
    
    async def get_user_storages(self, user_id: str) -> List[UserStorage]:
        """Get all storage for a user with current status"""
        try:
            storages = await self.db.get_user_storages(user_id)
            
            # Update storage metadata from GCS
            for storage in storages:
                if storage.status == StorageStatus.ACTIVE:
                    try:
                        # Get current bucket info
                        bucket_info = await self.storage_manager.get_bucket_info(storage.bucket_name)
                        if bucket_info:
                            await self.db.update_storage_metadata(
                                storage.id, 
                                bucket_info.get('size_bytes', 0),
                                bucket_info.get('object_count', 0)
                            )
                            storage.size_bytes = bucket_info.get('size_bytes', 0)
                            storage.object_count = bucket_info.get('object_count', 0)
                    except Exception as e:
                        logger.warning("Failed to update storage metadata", 
                                     storage_id=storage.id,
                                     bucket_name=storage.bucket_name,
                                     error=str(e))
            
            return storages
            
        except Exception as e:
            logger.error("Failed to get user storages", user_id=user_id, error=str(e))
            raise
    
    def _generate_pod_name(self, safe_user_id: str, env_id: str) -> str:
        """Generate unique pod name for user"""
        timestamp = int(time.time())
        # Kubernetes names must be lowercase and contain only letters, numbers, and hyphens
        return f"user-{safe_user_id[:20]}-{env_id}-{timestamp}"
    
    def _build_pod_spec_with_storage(
        self,
        user_id: str,
        safe_user_id: str,
        env_id: str,
        user_email: str,
        pod_name: str,
        config: EnvironmentRequest,
        storage: UserStorage,
        secret_name: str = None,
        file_secret_name: str = None,
        image_path: str = None,
        container_port: int = 8888,
        working_dir: str = '/cmbagent',
        app_name: str = 'cmbagent'
    ) -> Dict:
        """Build Kubernetes pod specification with cloud storage and env secret"""
        image = image_path or config.image or settings.default_image

        # Default env vars (non-sensitive, always injected)
        env_list = [
            {"name": "USER_ID", "value": user_id},
            {"name": "USER_EMAIL", "value": user_email},
            {"name": "ENV_ID", "value": env_id},
            {"name": "HUB_URL", "value": settings.api_url},
            {"name": "WORKSPACE_DIR", "value": working_dir},
            {"name": "STORAGE_BUCKET", "value": storage.bucket_name},
            {"name": "STORAGE_TYPE", "value": storage.storage_type.value},
            # Application specific environment variables (using dynamic working_dir)
            {"name": "HOME", "value": working_dir},
            {"name": "CMBAGENT_ROOT", "value": working_dir},
            {"name": "CMBAGENT_OUTPUT_DIR", "value": f"{working_dir}/cmbagent_output"},
            {"name": "MPLCONFIGDIR", "value": f"{working_dir}/.matplotlib"},
            # Denario-specific environment variable to override PROJECT_DIR with absolute path
            {"name": "PROJECT_DIR", "value": working_dir},
            # GCSFUSE optimization settings for better I/O performance
            {"name": "GCSFUSE_WRITE_BUFFER_SIZE", "value": "67108864"},  # 64MB
            {"name": "GCSFUSE_MAX_RETRY_SLEEP", "value": "30"},
            {"name": "GCSFUSE_MAX_CONNS_PER_HOST", "value": "100"}
        ]

        env_from = []
        if secret_name:
            env_from.append({"secretRef": {"name": secret_name}})

        # Build volume mounts - start with workspace mount using dynamic working_dir
        volume_mounts = [{
            "name": "user-workspace",
            "mountPath": working_dir
        }]

        # Build volumes - start with workspace volume using dynamic working_dir
        # Cloud-agnostic storage configuration
        volume_spec = self.storage_manager.provider.get_fuse_volume_spec(
            bucket_name=storage.bucket_name,
            mount_path=working_dir
        )

        volumes = [{
            "name": "user-workspace",
            **volume_spec
        }]

        # Add file secret volume and mounts if files exist
        if file_secret_name:
            # Add file secret volume
            volumes.append({
                "name": "user-files",
                "secret": {
                    "secretName": file_secret_name,
                    "defaultMode": 384  # 0600 in octal
                }
            })
            
            # Mount the entire secret to /app/secrets
            volume_mounts.append({
                "name": "user-files",
                "mountPath": "/app/secrets",
                "readOnly": True
            })

        return {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": pod_name,
                "namespace": settings.namespace,
                "labels": {
                    "app": app_name,
                    "user-id": safe_user_id,
                    "env-id": env_id,
                    "component": "user-pod"
                },
                "annotations": self._get_pod_annotations(
                    user_email=user_email,
                    env_id=env_id,
                    storage=storage,
                    app_name=app_name
                )
            },
            "spec": {
                "initContainers": [{
                    "name": "wait-for-mount",
                    "image": "busybox:latest",
                    "command": ["/bin/sh"],
                    "args": [
                        "-c",
                        f"echo 'Waiting for GCS FUSE mount to be ready...'; for i in $(seq 1 60); do if [ -d {working_dir} ] && touch {working_dir}/.mount_test 2>/dev/null; then rm -f {working_dir}/.mount_test; echo 'Mount is ready and writable'; mkdir -p {working_dir}/cmbagent_output {working_dir}/.matplotlib 2>/dev/null || true; exit 0; fi; echo \"Attempt $i: Mount not ready yet...\"; sleep 2; done; echo 'ERROR: Mount did not become ready in time'; exit 1"
                    ],
                    "volumeMounts": [{
                        "name": "user-workspace",
                        "mountPath": working_dir
                    }],
                    "securityContext": {
                        "runAsUser": 1000,
                        "runAsGroup": 1000,
                        "allowPrivilegeEscalation": False
                    }
                }],
                "containers": [{
                    "name": app_name,
                    "image": image,
                    "ports": [{"containerPort": container_port, "name": "ui"}],
                    "env": env_list,
                    "envFrom": env_from,
                    "resources": {
                        "requests": {
                            "cpu": str(config.cpu_limit / 2),
                            "memory": str(int(config.memory_limit.rstrip('Gi')) // 2) + "Gi"
                        },
                        "limits": {
                            "cpu": str(config.cpu_limit),
                            "memory": config.memory_limit
                        }
                    },
                    "volumeMounts": volume_mounts,
                    "workingDir": working_dir,
                    "securityContext": {
                        "runAsUser": 1000,
                        "runAsGroup": 1000,
                        "allowPrivilegeEscalation": False
                    },
                    "startupProbe": {
                        "exec": {
                            "command": ["/bin/sh", "-c", f"test -d {working_dir} && test -w {working_dir}"]
                        },
                        "initialDelaySeconds": 10,
                        "periodSeconds": 5,
                        "failureThreshold": 30,
                        "timeoutSeconds": 3
                    },
                    "readinessProbe": {
                        "exec": {
                            "command": ["/bin/sh", "-c", f"test -d {working_dir} && test -w {working_dir}"]
                        },
                        "initialDelaySeconds": 5,
                        "periodSeconds": 10,
                        "failureThreshold": 3,
                        "timeoutSeconds": 3
                    }
                }],
                "volumes": volumes,
                "restartPolicy": "Never",
                "serviceAccountName": settings.user_pod_sa_name,
                "securityContext": {
                    "fsGroup": 1000
                }
            }
        }
    
    async def _create_user_pvc(self, safe_user_id: str, env_id: str):
        """Legacy PVC creation method - now deprecated in favor of cloud storage"""
        # This method is kept for backward compatibility but not used
        # in new cloud storage implementation
        logger.warning("PVC creation called but deprecated", 
                      safe_user_id=safe_user_id, 
                      env_id=env_id)
        pass
    
    async def _create_user_service(self, safe_user_id: str, env_id: str, container_port: int = 8888, app_name: str = 'cmbagent'):
        """Create Kubernetes service for user pod"""
        service_name = f"service-{safe_user_id}-{env_id}"
        namespace = settings.namespace

        logger.info("Creating service with dynamic port",
                   service_name=service_name,
                   container_port=container_port,
                   app_name=app_name)

        service_spec = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": service_name,
                "namespace": namespace,
                "labels": {
                    "app": app_name,
                    "user-id": safe_user_id,
                    "env-id": env_id
                }
            },
            "spec": {
                "selector": {"user-id": safe_user_id, "env-id": env_id},
                "ports": [{
                    "port": 80,  # External port (ingress -> service)
                    "targetPort": container_port,  # Dynamic port to container
                    "protocol": "TCP"
                }],
                "type": "ClusterIP"
            }
        }
        
        try:
            self.k8s_client.create_namespaced_service(
                namespace=namespace,
                body=service_spec
            )
            logger.info("Created service for user", user_id=safe_user_id, env_id=env_id, service_name=service_name)
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.info("Service already exists", user_id=safe_user_id, env_id=env_id, service_name=service_name)
            else:
                raise

    async def _create_user_ingress(self, safe_user_id: str, env_id: str, container_port: int = 8888, app_name: str = 'cmbagent'):
        """Create Kubernetes ingress for user pod"""
        ingress_name = f"ingress-{safe_user_id}-{env_id}"
        service_name = f"service-{safe_user_id}-{env_id}"
        namespace = settings.namespace
        host = f"{safe_user_id}-{env_id}.{settings.base_domain}"

        logger.info("Creating ingress with dynamic port",
                   ingress_name=ingress_name,
                   host=host,
                   container_port=container_port,
                   app_name=app_name)
        
        # Base annotations
        annotations = {
            "kubernetes.io/ingress.class": "nginx",
            "nginx.ingress.kubernetes.io/rewrite-target": "/",
            "nginx.ingress.kubernetes.io/proxy-connect-timeout": "600",
            "nginx.ingress.kubernetes.io/proxy-send-timeout": "600",
            "nginx.ingress.kubernetes.io/proxy-read-timeout": "600",
            # WebSocket support for Streamlit
            "nginx.ingress.kubernetes.io/proxy-read-timeout": "3600",
            "nginx.ingress.kubernetes.io/proxy-send-timeout": "3600"
        }
        
        # Add TLS/SSL annotations if enabled
        tls_enabled = getattr(settings, 'tls_enabled', False)
        if tls_enabled:
            annotations.update({
                "cert-manager.io/cluster-issuer": getattr(settings, 'cluster_issuer', 'letsencrypt-prod'),
                "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                "nginx.ingress.kubernetes.io/force-ssl-redirect": "true"
            })
        else:
            annotations["nginx.ingress.kubernetes.io/ssl-redirect"] = "false"
        
        ingress_spec = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": ingress_name,
                "namespace": namespace,
                "labels": {
                    "app": app_name,
                    "user-id": safe_user_id,
                    "env-id": env_id
                },
                "annotations": annotations
            },
            "spec": {
                "ingressClassName": getattr(settings, 'ingress_class_name', 'nginx'),
                "rules": [{
                    "host": host,
                    "http": {
                        "paths": [{
                            "path": "/",
                            "pathType": "Prefix",
                            "backend": {
                                "service": {
                                    "name": service_name,
                                    "port": {
                                        "number": 80  # Service port (ingress -> service), service handles dynamic targetPort to container
                                    }
                                }
                            }
                        }]
                    }
                }]
            }
        }
        
        # Add TLS configuration if enabled
        if tls_enabled:
            ingress_spec["spec"]["tls"] = [{
                "hosts": [host],
                "secretName": f"tls-{safe_user_id}-{env_id}"
            }]
        
        try:
            self.networking_client.create_namespaced_ingress(
                namespace=namespace,
                body=ingress_spec
            )
            logger.info("Created ingress for user", 
                       user_id=safe_user_id, 
                       env_id=env_id, 
                       ingress_name=ingress_name,
                       host=host,
                       tls_enabled=tls_enabled)
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.info("Ingress already exists", 
                           user_id=safe_user_id, 
                           env_id=env_id, 
                           ingress_name=ingress_name)
            else:
                raise
    
    async def user_has_active_pod(self, user_id: str) -> bool:
        """Check if user has an active pod"""
        user_envs = await self.db.get_user_environments(user_id)
        if not user_envs:
            return False
        
        # Check if any environment is active
        for environment in user_envs:
            try:
                pod = self.k8s_client.read_namespaced_pod(
                    name=environment.pod_name,
                    namespace=settings.namespace
                )
                
                # Update environment status in database
                pod_status = PodStatus(pod.status.phase.lower())
                await self.db.update_environment_status(environment.env_id, pod_status)
                
                if pod.status.phase in ["Running", "Pending"]:
                    return True
                    
            except ApiException as e:
                if e.status == 404:
                    # Pod doesn't exist, update status to failed in database
                    await self.db.update_environment_status(environment.env_id, PodStatus.FAILED)
                else:
                    raise
        
        return False
    
    async def get_user_environment(self, user_id: str) -> Optional[Environment]:
        """Get user environment info - returns the first active environment for the user"""
        # Find the most recent environment for this user
        user_envs = await self.db.get_user_environments(user_id)
        
        if not user_envs:
            return None
        
        # Get the most recent environment (already sorted by created_at DESC in database query)
        environment = user_envs[0]
        
        # Update pod status
        try:
            pod = self.k8s_client.read_namespaced_pod(
                name=environment.pod_name,
                namespace=settings.namespace
            )
            pod_status = PodStatus(pod.status.phase.lower())
            await self.db.update_environment_status(environment.env_id, pod_status)
            environment.status = pod_status
        except ApiException as e:
            if e.status == 404:
                await self.db.update_environment_status(environment.env_id, PodStatus.FAILED)
                environment.status = PodStatus.FAILED
            else:
                environment.status = PodStatus.UNKNOWN
        
        return environment
    
    async def get_user_environments(self, user_id: str) -> List[Environment]:
        """Get all environments for a user"""
        user_envs = await self.db.get_user_environments(user_id)
        
        # Update pod statuses
        for environment in user_envs:
            try:
                pod = self.k8s_client.read_namespaced_pod(
                    name=environment.pod_name,
                    namespace=settings.namespace
                )
                pod_status = PodStatus(pod.status.phase.lower())
                await self.db.update_environment_status(environment.env_id, pod_status)
                environment.status = pod_status
            except ApiException as e:
                if e.status == 404:
                    await self.db.update_environment_status(environment.env_id, PodStatus.FAILED)
                    environment.status = PodStatus.FAILED
                else:
                    environment.status = PodStatus.UNKNOWN
        
        return user_envs
    
    async def delete_user_environment(self, user_id: str, user_email: str = None, env_id: str = None):
        """Delete user environment and associated resources. If env_id is provided, delete that environment, else delete the most recent."""
        # Find the environment to delete
        if env_id:
            environment = await self.db.get_environment(user_id, env_id)
            if not environment:
                logger.warning("Environment to delete not found", 
                             user_id=user_id, 
                             env_id=env_id)
                raise ValueError(f"Environment {env_id} not found for user {user_id}")
        else:
            user_envs = await self.db.get_user_environments(user_id)
            if not user_envs:
                logger.warning("No environments found for user", user_id=user_id)
                raise ValueError(f"No environments found for user {user_id}")
            environment = user_envs[0]  # Most recent (already sorted)
        
        # Use the correct user_email for DNS/subdomain naming
        if user_email is None:
            user_email = environment.user_email
        safe_user_id = _sanitize_for_dns(user_email)
        env_id = environment.env_id
        namespace = settings.namespace
        
        logger.info("Deleting user environment", user_id=user_id, env_id=env_id, pod_name=environment.pod_name)
        
        try:
            # Delete the env secret
            await self._delete_env_secret(safe_user_id, env_id)
            
            # Delete the file secret
            await self._delete_file_secret(safe_user_id, env_id)

            # Delete TLS secret for this environment
            tls_secret_name = f"tls-{safe_user_id}-{env_id}"
            try:
                self.k8s_client.delete_namespaced_secret(name=tls_secret_name, namespace=namespace)
                logger.info("TLS secret deleted successfully", secret_name=tls_secret_name)
            except ApiException as e:
                if e.status != 404:
                    raise
                logger.info("TLS secret not found (already deleted)", secret_name=tls_secret_name)

            # Delete pod
            try:
                self.k8s_client.delete_namespaced_pod(
                    name=environment.pod_name,
                    namespace=namespace
                )
                logger.info("Pod deleted successfully", pod_name=environment.pod_name)
            except ApiException as e:
                if e.status != 404:
                    raise
                logger.info("Pod not found (already deleted)", pod_name=environment.pod_name)

            # Delete service
            try:
                service_name = f"service-{safe_user_id}-{env_id}"
                self.k8s_client.delete_namespaced_service(
                    name=service_name,
                    namespace=namespace
                )
                logger.info("Service deleted successfully", service_name=service_name)
            except ApiException as e:
                if e.status != 404:
                    raise
                logger.info("Service not found (already deleted)", service_name=service_name)

            # Delete ingress
            try:
                ingress_name = f"ingress-{safe_user_id}-{env_id}"
                self.networking_client.delete_namespaced_ingress(
                    name=ingress_name,
                    namespace=namespace
                )
                logger.info("Ingress deleted successfully", ingress_name=ingress_name)
            except ApiException as e:
                if e.status != 404:
                    raise
                logger.info("Ingress not found (already deleted)", ingress_name=ingress_name)

            # Note: Keep PVC for data persistence

            # Remove from database
            deleted = await self.db.delete_environment(user_id, env_id)
            if deleted:
                logger.info("Environment removed from database", user_id=user_id, env_id=env_id)
            else:
                logger.warning("Environment not found in database", user_id=user_id, env_id=env_id)

            logger.info("User environment deleted successfully", user_id=user_id, env_id=env_id)

        except Exception as e:
            logger.error("Failed to delete user environment", user_id=user_id, env_id=env_id, error=str(e))
            raise
    
    async def update_user_activity(self, user_id: str):
        """Update user activity timestamp for all user environments"""
        try:
            # Update activity in database for all user environments
            await self.db.update_environment_activity(user_id)
            logger.debug("Updated user activity", user_id=user_id)
        except Exception as e:
            logger.error("Failed to update user activity", user_id=user_id, error=str(e))
            raise
    
    async def cleanup_failed_pods(self):
        """Clean up only truly failed or stuck pods, not based on inactivity"""
        logger.info("Running cleanup for failed/stuck pods only")
        
        try:
            # Get all environments and check their actual pod status
            all_environments = await self.db.get_all_running_environments()
            
            logger.info("Checking pod status for cleanup", count=len(all_environments))
            
            for environment in all_environments:
                try:
                    # Check actual pod status in Kubernetes
                    try:
                        pod = self.k8s_client.read_namespaced_pod(
                            name=environment.pod_name,
                            namespace=settings.namespace
                        )
                        
                        # Only clean up if pod is actually failed or in error state
                        if pod.status.phase in ["Failed", "Succeeded"]:
                            logger.info("Cleaning up failed/completed pod", 
                                       user_id=environment.user_id, 
                                       env_id=environment.env_id,
                                       pod_phase=pod.status.phase)
                            
                            await self.delete_user_environment(environment.user_id, environment.user_email, environment.env_id)
                            
                            # Log the cleanup activity
                            from main import log_activity
                            await log_activity(environment.user_id, "environment_cleanup_failed", 
                                              f"Environment {environment.env_id} cleaned up - pod status: {pod.status.phase}")
                        
                        # Update database status to match actual pod status
                        from models import PodStatus
                        db_status = PodStatus(pod.status.phase.lower())
                        if db_status != environment.status:
                            await self.db.update_environment_status(environment.env_id, db_status)
                            
                    except ApiException as e:
                        if e.status == 404:
                            # Pod doesn't exist but database thinks it's running
                            logger.info("Cleaning up orphaned database record - pod not found", 
                                       user_id=environment.user_id, 
                                       env_id=environment.env_id)
                            
                            await self.db.delete_environment(environment.user_id, environment.env_id)
                            
                            from main import log_activity
                            await log_activity(environment.user_id, "environment_cleanup_orphaned", 
                                              f"Environment {environment.env_id} removed - pod no longer exists")
                        else:
                            logger.warning("Error checking pod status", 
                                         pod_name=environment.pod_name, 
                                         error=str(e))
                            
                except Exception as e:
                    logger.error("Error processing environment for cleanup", 
                               user_id=environment.user_id,
                               env_id=environment.env_id, 
                               error=str(e))
                               
        except Exception as e:
            logger.error("Error during failed pod cleanup", error=str(e))
    
    async def cleanup_all(self):
        """Clean up all managed resources"""
        logger.info("Cleaning up all user environments")
        
        try:
            # Get all environments from database
            # Since we don't have a method to get ALL environments, we'll need to implement cleanup differently
            # For now, this is called during shutdown, so we can be more aggressive
            logger.info("Application shutdown - cleaning up all environments")
            
            # Note: This is primarily for graceful shutdown
            # In a production system, you might want to iterate through all users
            # or add a get_all_environments method to the database
            
        except Exception as e:
            logger.error("Error during cleanup all", error=str(e))
    
    async def _cleanup_failed_environment(self, safe_user_id: str, env_id: str):
        """Clean up partially created resources after a failed environment creation"""
        namespace = settings.namespace
        
        logger.info("Cleaning up failed environment", 
                   safe_user_id=safe_user_id, 
                   env_id=env_id)
        
        # Try to delete TLS secret
        tls_secret_name = f"tls-{safe_user_id}-{env_id}"
        try:
            self.k8s_client.delete_namespaced_secret(name=tls_secret_name, namespace=namespace)
            logger.info("TLS secret deleted successfully", secret_name=tls_secret_name)
        except ApiException as e:
            if e.status != 404:  # Ignore if not found
                logger.warning("Failed to cleanup TLS secret", error=str(e))

        # Try to delete pod
        try:
            pod_name = self._generate_pod_name(safe_user_id, env_id)
            self.k8s_client.delete_namespaced_pod(
                name=pod_name,
                namespace=namespace
            )
        except ApiException as e:
            if e.status != 404:  # Ignore if not found
                logger.warning("Failed to cleanup pod", error=str(e))

        # Try to delete service
        try:
            service_name = f"service-{safe_user_id}-{env_id}"
            self.k8s_client.delete_namespaced_service(
                name=service_name,
                namespace=namespace
            )
        except ApiException as e:
            if e.status != 404:  # Ignore if not found
                logger.warning("Failed to cleanup service", error=str(e))

        # Try to delete ingress
        try:
            ingress_name = f"ingress-{safe_user_id}-{env_id}"
            self.networking_client.delete_namespaced_ingress(
                name=ingress_name,
                namespace=namespace
            )
        except ApiException as e:
            if e.status != 404:  # Ignore if not found
                logger.warning("Failed to cleanup ingress", error=str(e))

        # Note: Keep PVC for potential retry/data recovery
