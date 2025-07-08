import asyncio
import time
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import structlog
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from config import settings
from models import Environment, EnvironmentRequest, PodStatus

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
    """Manages Kubernetes pods for user environments"""
    
    def __init__(self):
        self.user_environments: Dict[str, Environment] = {}
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
        """Create a new user environment pod (multi-env per user)"""
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
            # Create PVC for user workspace
            await self._create_user_pvc(safe_user_id, env_id)
            
            # Create pod
            pod_spec = self._build_pod_spec(user_id, safe_user_id, env_id, user_email, pod_name, config)
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
                    "storage_size": config.storage_size
                }
            )
            
            # Store environment with composite key to support multiple environments per user
            env_key = f"{user_id}:{env_id}"
            self.user_environments[env_key] = environment
            
            logger.info("User environment created successfully", 
                        user_id=user_id, 
                        user_email=user_email,
                        safe_user_id=safe_user_id,
                        env_id=env_id,
                        url=environment.url,
                        pod_name=pod_name)
            
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
    
    def _generate_pod_name(self, safe_user_id: str, env_id: str) -> str:
        """Generate unique pod name for user"""
        timestamp = int(time.time())
        # Kubernetes names must be lowercase and contain only letters, numbers, and hyphens
        return f"user-{safe_user_id[:20]}-{env_id}-{timestamp}"
    
    def _build_pod_spec(
        self, 
        user_id: str, 
        safe_user_id: str,
        env_id: str,
        user_email: str, 
        pod_name: str, 
        config: EnvironmentRequest
    ) -> Dict:
        """Build Kubernetes pod specification"""
        image = config.image or f"{settings.registry_url}/cmbagent:latest"
        
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
                    "created.at": datetime.utcnow().isoformat(),
                    "managed.by": "cmbcluster"
                }
            },
            "spec": {
                "containers": [{
                    "name": "cmbagent",
                    "image": image,
                    "ports": [{"containerPort": 8501, "name": "streamlit"}],
                    "env": [
                        {"name": "USER_ID", "value": user_id},
                        {"name": "USER_EMAIL", "value": user_email},
                        {"name": "ENV_ID", "value": env_id},
                        {"name": "HUB_URL", "value": settings.api_url},
                        {"name": "WORKSPACE_DIR", "value": "/workspace"}
                    ],
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
                        "mountPath": "/workspace"
                    }],
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
                    "persistentVolumeClaim": {
                        "claimName": f"workspace-{safe_user_id}-{env_id}"
                    }
                }],
                "restartPolicy": "Never",
                "serviceAccountName": settings.user_pod_sa_name
            }
        }
    
    async def _create_user_pvc(self, safe_user_id: str, env_id: str):
        """Create persistent volume claim for user"""
        pvc_name = f"workspace-{safe_user_id}-{env_id}"
        namespace = settings.namespace
        
        pvc_spec = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": pvc_name,
                "namespace": namespace,
                "labels": {
                    "app": "cmbagent",
                    "user-id": safe_user_id,
                    "env-id": env_id
                }
            },
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {
                    "requests": {"storage": "10Gi"}
                },
                "storageClassName": "standard-rwo"
            }
        }
        
        try:
            self.k8s_client.create_namespaced_persistent_volume_claim(
                namespace=namespace, 
                body=pvc_spec
            )
            logger.info("Created PVC for user", user_id=safe_user_id, env_id=env_id, pvc_name=pvc_name)
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.info("PVC already exists", user_id=safe_user_id, env_id=env_id, pvc_name=pvc_name)
            else:
                raise
    
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
        user_envs = [env for key, env in self.user_environments.items() if env.user_id == user_id]
        if not user_envs:
            return False
        
        # Check if any environment is active
        for environment in user_envs:
            try:
                pod = self.k8s_client.read_namespaced_pod(
                    name=environment.pod_name,
                    namespace=settings.namespace
                )
                
                # Update environment status
                environment.status = PodStatus(pod.status.phase.lower())
                
                if pod.status.phase in ["Running", "Pending"]:
                    return True
                    
            except ApiException as e:
                if e.status == 404:
                    # Pod doesn't exist, remove from tracking
                    env_key = f"{environment.user_id}:{environment.env_id}"
                    if env_key in self.user_environments:
                        del self.user_environments[env_key]
                else:
                    raise
        
        return False
    
    async def get_user_environment(self, user_id: str) -> Optional[Environment]:
        """Get user environment info - returns the first active environment for the user"""
        # Find the most recent environment for this user
        user_envs = [env for key, env in self.user_environments.items() if env.user_id == user_id]
        
        if not user_envs:
            return None
        
        # Sort by creation time and get the most recent
        environment = sorted(user_envs, key=lambda x: x.created_at, reverse=True)[0]
        
        # Update pod status
        try:
            pod = self.k8s_client.read_namespaced_pod(
                name=environment.pod_name,
                namespace=settings.namespace
            )
            environment.status = PodStatus(pod.status.phase.lower())
        except ApiException as e:
            if e.status == 404:
                environment.status = PodStatus.FAILED
            else:
                environment.status = PodStatus.UNKNOWN
        
        return environment
    
    async def get_user_environments(self, user_id: str) -> List[Environment]:
        """Get all environments for a user"""
        user_envs = [env for key, env in self.user_environments.items() if env.user_id == user_id]
        
        # Update pod statuses
        for environment in user_envs:
            try:
                pod = self.k8s_client.read_namespaced_pod(
                    name=environment.pod_name,
                    namespace=settings.namespace
                )
                environment.status = PodStatus(pod.status.phase.lower())
            except ApiException as e:
                if e.status == 404:
                    environment.status = PodStatus.FAILED
                else:
                    environment.status = PodStatus.UNKNOWN
        
        # Sort by creation time (newest first)
        return sorted(user_envs, key=lambda x: x.created_at, reverse=True)
    
    async def delete_user_environment(self, user_id: str, user_email: str = None, env_id: str = None):
        """Delete user environment and associated resources. If env_id is provided, delete that environment, else delete the most recent."""
        # Find the environment to delete
        user_envs = [env for key, env in self.user_environments.items() if env.user_id == user_id]
        if not user_envs:
            logger.warning("No environments found for user", user_id=user_id)
            return
        
        if env_id:
            # Handle both cases: short env_id (f5a0cb53) or combined id (user_id-env_id)
            actual_env_id = env_id
            if '-' in env_id and env_id.startswith(user_id):
                # Extract the short env_id from combined id (user_id-env_id)
                actual_env_id = env_id.split('-', 1)[1]
                logger.info("Parsed combined env_id", original=env_id, parsed=actual_env_id)
            
            environment = next((env for env in user_envs if env.env_id == actual_env_id), None)
            if not environment:
                # Also try matching by full id
                environment = next((env for env in user_envs if env.id == env_id), None)
                if not environment:
                    logger.warning("Environment to delete not found", 
                                 user_id=user_id, 
                                 env_id=env_id,
                                 actual_env_id=actual_env_id,
                                 available_envs=[{"id": env.id, "env_id": env.env_id} for env in user_envs])
                    return
        else:
            environment = sorted(user_envs, key=lambda x: x.created_at, reverse=True)[0]
        
        # Use the correct key format that matches how environments are stored
        env_key = f"{environment.user_id}:{environment.env_id}"
        
        # Always use the stored user_email for DNS/subdomain naming
        if user_email is None:
            user_email = environment.user_email
        safe_user_id = _sanitize_for_dns(user_email)
        env_id = environment.env_id
        namespace = settings.namespace
        
        logger.info("Deleting user environment", user_id=user_id, env_id=env_id, pod_name=environment.pod_name, env_key=env_key)
        
        try:
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
            
            # Remove from tracking
            if env_key in self.user_environments:
                del self.user_environments[env_key]
                logger.info("Environment removed from tracking", env_key=env_key)
            else:
                logger.warning("Environment key not found in tracking", env_key=env_key, available_keys=list(self.user_environments.keys()))
                
            logger.info("User environment deleted successfully", user_id=user_id, env_id=env_id)
            
        except Exception as e:
            logger.error("Failed to delete user environment", user_id=user_id, env_id=env_id, error=str(e))
            raise
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
