from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Project settings
    project_id: str = "cmbcluster-dev"
    cluster_name: str = "cmbcluster"
    region: str = "us-central1"
    zone: str = "us-central1-a"
    
    # Domain settings
    base_domain: str = "cmbcluster.local"
    api_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:8501"
    
    # OAuth settings
    google_client_id: str = ""
    google_client_secret: str = ""
    
    # Security settings
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    token_expire_hours: int = 8
    
    # Application settings
    namespace: str = "cmbcluster"
    registry_url: str = "gcr.io/cmbcluster-dev"
    max_inactive_hours: int = 4
    max_user_pods: int = 1
    storage_class_name: str = "standard-rwo"
    user_pod_sa_name: str = "cmbcluster-user-sa"
    
    # Ingress and TLS settings
    ingress_class_name: str = "nginx"
    tls_enabled: bool = True
    cluster_issuer: str = "letsencrypt-prod"
    
    # Database settings
    database_path: str = "/app/data/cmbcluster.db"
    database_bucket: str = ""
    
    # Environment settings
    dev_mode: bool = False
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
