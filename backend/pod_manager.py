import asyncio
import time
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import structlog
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from .config import settings
from .models import Environment, EnvironmentRequest, PodStatus
from .storage_models import StorageType, StorageStatus, UserStorage
from .storage_manager import StorageManager
from .database import get_database

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

            # Merge env_vars from config (request) with DB (DB values overwritten by request)
            merged_env_vars = dict(user_env_vars)
            if getattr(config, "env_vars", None):
                merged_env_vars.update(config.env_vars)

            # Handle storage selection/creation
            storage = await self._handle_storage_selection(user_id, config)

            # Create secret for env vars
            secret_name = await self._create_env_secret(safe_user_id, env_id, merged_env_vars)

            # Create pod with cloud storage, referencing secret
            pod_spec = self._build_pod_spec_with_storage(
                user_id, safe_user_id, env_id, user_email, pod_name, config, storage, secret_name
            )
            self.k8s_client.create_namespaced_pod(
                namespace=namespace, 
                body=pod_spec
            )

            # Create service
            await self._create_user_service(safe_user_id, env_id)

            # Create ingress
            await self._create_user_ingress(safe_user_id, env_id)

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
        secret_name: str = None
    ) -> Dict:
        """Build Kubernetes pod specification with cloud storage and env secret"""
        image = config.image or f"{settings.registry_url}/cmbagent:latest"

        # Default env vars (non-sensitive, always injected)
        env_list = [
            {"name": "USER_ID", "value": user_id},
            {"name": "USER_EMAIL", "value": user_email},
            {"name": "ENV_ID", "value": env_id},
            {"name": "HUB_URL", "value": settings.api_url},
            {"name": "WORKSPACE_DIR", "value": "/cmbagent"},
            {"name": "STORAGE_BUCKET", "value": storage.bucket_name},
            {"name": "STORAGE_TYPE", "value": storage.storage_type.value},
            # CMBAgent specific environment variables
            {"name": "HOME", "value": "/cmbagent"},
            {"name": "CMBAGENT_ROOT", "value": "/cmbagent"},
            {"name": "CMBAGENT_OUTPUT_DIR", "value": "/cmbagent/cmbagent_output"},
            {"name": "MPLCONFIGDIR", "value": "/cmbagent/.matplotlib"}
        ]

        env_from = []
        if secret_name:
            env_from.append({"secretRef": {"name": secret_name}})

        return {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": pod_name,
                "namespace": settings.namespace,
                "labels": {
                    "app": "cmbagent",
                    "user-id": safe_user_id,
                    "env-id": env_id,
                    "component": "user-pod"
                },
                "annotations": {
                    "user.email": user_email,
                    "env.id": env_id,
                    "storage.id": storage.id,
                    "storage.bucket": storage.bucket_name,
                    "created.at": datetime.utcnow().isoformat(),
                    "managed.by": "cmbcluster",
                    "gke-gcsfuse/volumes": "true",  # Enable GCS FUSE
                    "iam.gke.io/gcp-service-account": f"{settings.cluster_name}-workload-sa@{settings.project_id}.iam.gserviceaccount.com"
                }
            },
            "spec": {
                "containers": [{
                    "name": "cmbagent",
                    "image": image,
                    "ports": [{"containerPort": 8501, "name": "streamlit"}],
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
                    "volumeMounts": [{
                        "name": "user-workspace",
                        "mountPath": "/cmbagent"
                    }],
                    "lifecycle": {
                        "postStart": {
                            "exec": {
                                "command": [
                                    "/bin/sh", "-c",
                                    "sleep 10 && mkdir -p /cmbagent/cmbagent_output /cmbagent/.matplotlib && chmod 755 /cmbagent/cmbagent_output /cmbagent/.matplotlib && touch /cmbagent/mount_test.txt && echo 'Mount and directories initialized' || echo 'Mount initialization failed'"
                                ]
                            }
                        }
                    },
                    "securityContext": {
                        "runAsUser": 1000,
                        "runAsGroup": 1000,
                        "allowPrivilegeEscalation": False
                    },
                    "livenessProbe": {
                        "httpGet": {
                            "path": "/_stcore/health",
                            "port": 8501
                        },
                        "initialDelaySeconds": 30,
                        "periodSeconds": 10
                    },
                    "readinessProbe": {
                        "httpGet": {
                            "path": "/_stcore/health",
                            "port": 8501
                        },
                        "initialDelaySeconds": 5,
                        "periodSeconds": 5
                    }
                }],
                "volumes": [{
                    "name": "user-workspace",
                    "csi": {
                        "driver": "gcsfuse.csi.storage.gke.io",
                        "volumeAttributes": {
                            "bucketName": storage.bucket_name,
                            "mountOptions": "implicit-dirs,uid=1000,gid=1000,file-mode=644,dir-mode=755"
                        }
                    }
                }],
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
    
    async def _create_user_service(self, safe_user_id: str, env_id: str):
        """Create Kubernetes service for user pod"""
        service_name = f"service-{safe_user_id}-{env_id}"
        namespace = settings.namespace
        
        service_spec = {
            "apiVersion": "v1",
            "kind": "Service", 
            "metadata": {
                "name": service_name,
                "namespace": namespace,
                "labels": {
                    "app": "cmbagent",
                    "user-id": safe_user_id,
                    "env-id": env_id
                }
            },
            "spec": {
                "selector": {"user-id": safe_user_id, "env-id": env_id},
                "ports": [{
                    "port": 80,
                    "targetPort": 8501,
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

    async def _create_user_ingress(self, safe_user_id: str, env_id: str):
        """Create Kubernetes ingress for user pod"""
        ingress_name = f"ingress-{safe_user_id}-{env_id}"
        service_name = f"service-{safe_user_id}-{env_id}"
        namespace = settings.namespace
        host = f"{safe_user_id}-{env_id}.{settings.base_domain}"
        
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
                    "app": "cmbcluster-user-env",
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
                                        "number": 80
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
        user_envs = [env for key, env in self.user_environments.items() if env.user_id == user_id]
        
        for environment in user_envs:
            environment.last_activity = datetime.utcnow()
    
    async def cleanup_stale_pods(self):
        """Clean up stale or inactive pods"""
        logger.info("Running stale pod cleanup")
        
        current_time = datetime.utcnow()
        stale_keys = []
        
        for env_key, environment in self.user_environments.items():
            if environment.last_activity:
                inactive_time = current_time - environment.last_activity
                
                if inactive_time > timedelta(hours=settings.max_inactive_hours):
                    stale_keys.append(env_key)
        
        # Clean up stale environments
        for env_key in stale_keys:
            try:
                environment = self.user_environments[env_key]
                await self.delete_user_environment(environment.user_id, env_id=environment.env_id)
                logger.info("Cleaned up stale environment", user_id=environment.user_id, env_id=environment.env_id)
            except Exception as e:
                logger.error("Failed to cleanup stale environment", 
                           env_key=env_key, 
                           error=str(e))
    
    async def cleanup_all(self):
        """Clean up all managed resources"""
        logger.info("Cleaning up all user environments")
        
        for env_key in list(self.user_environments.keys()):
            try:
                environment = self.user_environments[env_key]
                await self.delete_user_environment(environment.user_id, env_id=environment.env_id)
            except Exception as e:
                logger.error("Failed to cleanup environment during shutdown", 
                           env_key=env_key, 
                           error=str(e))
    
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
