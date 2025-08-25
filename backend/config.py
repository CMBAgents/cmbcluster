from pydantic_settings import BaseSettings
from typing import Optional, List
import os
import secrets

class Settings(BaseSettings):
    # Project settings
    project_id: str = "cmbcluster-dev"
    cluster_name: str = "cmbcluster"
    region: str = "us-central1"
    zone: str = "us-central1-a"
    
    # Domain settings
    base_domain: str = "cmbcluster.local"
    api_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"  # Updated for Next.js default port
    
    # OAuth settings (required in production)
    google_client_id: str = ""
    google_client_secret: str = ""
    
    # Security settings - CRITICAL FOR PRODUCTION
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    token_expire_hours: int = 8  # Reduced from 24 to 8 hours for better security
    
    # Trusted domains for CORS (production security)
    trusted_domains: List[str] = [
        "localhost:3000",
        "localhost:8501", 
        "127.0.0.1:3000",
        "127.0.0.1:8501"
    ]
    
    # Rate limiting settings
    rate_limit_enabled: bool = True
    max_auth_attempts_per_hour: int = 10
    max_api_requests_per_minute: int = 60
    
    # Application settings
    namespace: str = "cmbcluster"
    registry_url: str = "gcr.io/cmbcluster-dev"
    max_user_pods: int = 1
    storage_class_name: str = "standard-rwo"
    user_pod_sa_name: str = "cmbcluster-user-sa"
    
    # Auto-shutdown settings for free tier (uptime-based, not inactivity-based)
    free_tier_max_uptime_minutes: int = 60  # 1 hour for free users
    auto_shutdown_check_interval_minutes: int = 5  # Check every 5 minutes
    shutdown_warning_minutes: int = 10  # Warn 10 minutes before shutdown
    grace_period_minutes: int = 5  # Grace period after warning
    
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
    
    # Security headers and policies
    enable_security_headers: bool = True
    enable_csrf_protection: bool = True
    session_secure_cookies: bool = True
    
    # Session settings
    session_timeout_minutes: int = 480  # 8 hours
    session_refresh_threshold_minutes: int = 60  # Refresh if < 1 hour remaining
    
    # Content Security Policy
    csp_enabled: bool = True
    csp_script_src: List[str] = ["'self'", "'unsafe-inline'", "https://accounts.google.com"]
    csp_style_src: List[str] = ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"]
    csp_font_src: List[str] = ["'self'", "https://fonts.gstatic.com"]
    csp_img_src: List[str] = ["'self'", "data:", "https:"]
    csp_connect_src: List[str] = ["'self'", "https://accounts.google.com"]
    
    # Monitoring and logging
    log_auth_events: bool = True
    log_security_events: bool = True
    security_event_webhook: Optional[str] = None
    
    # Redis settings (for production rate limiting and session storage)
    redis_url: Optional[str] = None
    redis_enabled: bool = False
    
    def get_allowed_origins(self) -> List[str]:
        """Get allowed CORS origins based on environment"""
        if self.dev_mode:
            return [
                "http://localhost:3000",
                "http://localhost:8501",
                "http://127.0.0.1:3000", 
                "http://127.0.0.1:8501",
                "https://localhost:3000",
                "https://localhost:8501",
                self.frontend_url,
            ]
        else:
            # Production - strict CORS policy
            origins = []
            for domain in self.trusted_domains:
                origins.extend([
                    f"https://{domain}",
                    f"https://www.{domain}",
                ])
            return origins
    
    def validate_production_config(self) -> bool:
        """Validate that production configuration is secure"""
        if not self.dev_mode:
            issues = []
            
            # Check critical security settings
            if self.secret_key == "dev-secret-key-change-in-production":
                issues.append("Production secret key not set")
            
            if len(self.secret_key) < 32:
                issues.append("Secret key too short (minimum 32 characters)")
            
            if not self.google_client_id or not self.google_client_secret:
                issues.append("Google OAuth credentials not configured")
            
            if not self.tls_enabled:
                issues.append("TLS not enabled in production")
            
            if not self.session_secure_cookies:
                issues.append("Secure cookies not enabled")
            
            if self.debug:
                issues.append("Debug mode enabled in production")
            
            if issues:
                raise ValueError(f"Production security issues: {', '.join(issues)}")
        
        return True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# Validate production configuration on import
if not settings.dev_mode:
    settings.validate_production_config()
