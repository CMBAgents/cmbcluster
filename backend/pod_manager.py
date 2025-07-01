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
            
            self.user_environments[f"{user_id}:{env_id}"] = environment
            
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
        image = config.image or f"{settings.registry_url}/cmbcluster-user-env:latest"
        
        return {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": pod_name,
                "namespace": settings.namespace,
                "labels": {
                    "app": "cmbcluster-user-env",
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
                    "name": "user-environment",
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
                    "app": "cmbcluster-user-env",
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
                    "app": "cmbcluster-user-env",
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
    
    async def user_has_active_pod(self, user_id: str) -> bool:
        """Check if user has an active pod"""
        if user_id not in self.user_environments:
            return False
        
        environment = self.user_environments[user_id]
        
        try:
            pod = self.k8s_client.read_namespaced_pod(
                name=environment.pod_name,
                namespace=settings.namespace
            )
            
            # Update environment status
            environment.status = PodStatus(pod.status.phase.lower())
            
            return pod.status.phase in ["Running", "Pending"]
            
        except ApiException as e:
            if e.status == 404:
                # Pod doesn't exist, remove from tracking
                del self.user_environments[user_id]
                return False
            raise
    
    async def get_user_environment(self, user_id: str) -> Optional[Environment]:
        """Get user environment info"""
        if user_id not in self.user_environments:
            return None
        
        environment = self.user_environments[user_id]
        
        # Update pod status
        try:
            pod = self.k8s_client.read_namespaced_pod(
                name=environment.pod_name,
                namespace=settings.namespace
            )
            environment.status = PodStatus(pod.status.phase.lower())
        except ApiException:
            environment.status = PodStatus.UNKNOWN
        
        return environment
    
    async def delete_user_environment(self, user_id: str, user_email: str = None):
        """Delete user environment and associated resources"""
        if user_id not in self.user_environments:
            return
        environment = self.user_environments[user_id]
        # Always use the stored user_email for DNS/subdomain naming
        if user_email is None:
            user_email = environment.user_email
        safe_user_id = _sanitize_for_dns(user_email)
        env_id = environment.env_id
        namespace = settings.namespace
        
        logger.info("Deleting user environment", 
                   user_id=user_id, 
                   pod_name=environment.pod_name)
        
        try:
            # Delete pod
            try:
                self.k8s_client.delete_namespaced_pod(
                    name=environment.pod_name,
                    namespace=namespace
                )
            except ApiException as e:
                if e.status != 404:
                    raise
            
            # Delete service
            try:
                service_name = f"service-{safe_user_id}-{env_id}"
                self.k8s_client.delete_namespaced_service(
                    name=service_name,
                    namespace=namespace
                )
            except ApiException as e:
                if e.status != 404:
                    raise
            
            # Note: Keep PVC for data persistence
            
            # Remove from tracking
            del self.user_environments[user_id]
            
            logger.info("User environment deleted successfully", user_id=user_id)
            
        except Exception as e:
            logger.error("Failed to delete user environment", 
                        user_id=user_id, 
                        error=str(e))
            raise
    
    async def update_user_activity(self, user_id: str):
        """Update user activity timestamp"""
        if user_id in self.user_environments:
            self.user_environments[user_id].last_activity = datetime.utcnow()
    
    async def cleanup_stale_pods(self):
        """Clean up stale or inactive pods"""
        logger.info("Running stale pod cleanup")
        
        current_time = datetime.utcnow()
        stale_users = []
        
        for user_id, environment in self.user_environments.items():
            if environment.last_activity:
                inactive_time = current_time - environment.last_activity
                
                if inactive_time > timedelta(hours=settings.max_inactive_hours):
                    stale_users.append(user_id)
        
        # Clean up stale environments
        for user_id in stale_users:
            try:
                await self.delete_user_environment(user_id)
                logger.info("Cleaned up stale environment", user_id=user_id)
            except Exception as e:
                logger.error("Failed to cleanup stale environment", 
                           user_id=user_id, 
                           error=str(e))
    
    async def cleanup_all(self):
        """Clean up all managed resources"""
        logger.info("Cleaning up all user environments")
        
        for user_id in list(self.user_environments.keys()):
            try:
                await self.delete_user_environment(user_id)
            except Exception as e:
                logger.error("Failed to cleanup environment during shutdown", 
                           user_id=user_id, 
                           error=str(e))
