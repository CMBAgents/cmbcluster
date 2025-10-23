from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator
from typing import Optional, List, Literal
import os
import secrets
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # === Cloud Provider Selection ===
    cloud_provider: Literal["gcp", "aws"] = "gcp"  # "gcp" or "aws"

    # === GCP Settings ===
    project_id: str = "cmbcluster"
    cluster_name: str = "cmbcluster"
    region: str = "us-central1"
    zone: str = "us-central1-a"

    # === AWS Settings ===
    aws_account_id: Optional[str] = None
    aws_region: Optional[str] = None
    eks_cluster_name: Optional[str] = None
    ecr_registry_url: Optional[str] = None
    s3_database_bucket: Optional[str] = None
    s3_user_bucket_prefix: Optional[str] = None

    # Domain settings
    base_domain: str = "cmbcluster.local"
    api_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"  # Updated for Next.js default port

    # === Authentication Provider Selection ===
    # Explicit auth provider selection (deployment-agnostic)
    # Options: "google", "cognito", or "auto"
    # "auto" = automatically detect based on available credentials
    # This allows you to use Google OAuth on AWS or Cognito on GCP if desired
    auth_provider: str = "auto"

    # === OAuth settings ===
    # Google OAuth (can be used on any cloud platform)
    google_client_id: str = ""
    google_client_secret: str = ""

    # AWS Cognito (can be used on any cloud platform)
    cognito_user_pool_id: Optional[str] = None
    cognito_client_id: Optional[str] = None
    cognito_client_secret: Optional[str] = None
    cognito_issuer: Optional[str] = None
    
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
    default_image: str = "borisbolliet/cmbagent-ui"  # Default container image
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
    
    # Admin user configuration
    admin_emails: List[str] = [
        "g22yash.tiwari@gmail.com",
        "22yash.tiwari@gmail.com"  # Both variations of the email
    ]
    first_user_is_admin: bool = True  # First user automatically becomes admin

    # === Pydantic Validators ===

    @field_validator('cloud_provider')
    @classmethod
    def validate_cloud_provider(cls, v: str) -> str:
        """Validate cloud provider selection"""
        if v not in ['gcp', 'aws']:
            raise ValueError(f"cloud_provider must be 'gcp' or 'aws', got '{v}'")
        return v

    @field_validator('auth_provider')
    @classmethod
    def validate_auth_provider(cls, v: str) -> str:
        """Validate authentication provider selection"""
        if v not in ['auto', 'google', 'cognito']:
            raise ValueError(f"auth_provider must be 'auto', 'google', or 'cognito', got '{v}'")
        return v

    @model_validator(mode='after')
    def validate_cloud_config(self) -> 'Settings':
        """Validate cloud-specific configuration based on cloud_provider"""
        if self.cloud_provider == 'gcp':
            # GCP-specific validation
            if not self.project_id or self.project_id == "cmbcluster":
                logger.warning("GCP PROJECT_ID not configured or using default value")

            if not self.region or self.region == "us-central1":
                logger.info("Using default GCP region: us-central1")

        elif self.cloud_provider == 'aws':
            # AWS-specific validation
            if not self.aws_account_id:
                raise ValueError("AWS_ACCOUNT_ID required when CLOUD_PROVIDER=aws")

            if not self.aws_region:
                raise ValueError("AWS_REGION required when CLOUD_PROVIDER=aws")

            if not self.eks_cluster_name:
                raise ValueError("EKS_CLUSTER_NAME required when CLOUD_PROVIDER=aws")

            # Validate AWS account ID format (12 digits)
            if not (self.aws_account_id.isdigit() and len(self.aws_account_id) == 12):
                raise ValueError(f"Invalid AWS_ACCOUNT_ID format: {self.aws_account_id} (must be 12 digits)")

        return self

    @model_validator(mode='after')
    def validate_auth_config(self) -> 'Settings':
        """Validate authentication provider configuration"""
        has_google = bool(self.google_client_id and self.google_client_secret)
        has_cognito = bool(
            self.cognito_user_pool_id and
            self.cognito_client_id and
            self.cognito_client_secret and
            self.cognito_issuer
        )

        # If explicit auth provider is set, validate required credentials
        if self.auth_provider == 'google':
            if not has_google:
                raise ValueError(
                    "AUTH_PROVIDER=google requires GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
                )

        elif self.auth_provider == 'cognito':
            if not has_cognito:
                raise ValueError(
                    "AUTH_PROVIDER=cognito requires COGNITO_USER_POOL_ID, "
                    "COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET, and COGNITO_ISSUER"
                )

        elif self.auth_provider == 'auto':
            # Auto mode: at least one provider must be configured
            if not has_google and not has_cognito:
                # Fall back to cloud provider default
                if self.cloud_provider == 'gcp':
                    logger.warning(
                        "No authentication provider configured. "
                        "Please configure Google OAuth credentials for GCP deployment."
                    )
                elif self.cloud_provider == 'aws':
                    logger.warning(
                        "No authentication provider configured. "
                        "Please configure AWS Cognito credentials for AWS deployment."
                    )

        return self

    @model_validator(mode='after')
    def validate_production_security(self) -> 'Settings':
        """Validate production security settings"""
        if not self.dev_mode:
            issues = []

            # Check critical security settings
            if self.secret_key == "dev-secret-key-change-in-production":
                issues.append("Production SECRET_KEY not set (generate with: openssl rand -hex 32)")

            if len(self.secret_key) < 32:
                issues.append(f"SECRET_KEY too short ({len(self.secret_key)} chars, minimum 32)")

            # Check authentication is configured
            has_google = bool(self.google_client_id and self.google_client_secret)
            has_cognito = bool(
                self.cognito_user_pool_id and
                self.cognito_client_id and
                self.cognito_client_secret
            )

            if not has_google and not has_cognito:
                issues.append("No authentication provider configured (Google OAuth or AWS Cognito)")

            if not self.tls_enabled:
                issues.append("TLS_ENABLED=false in production (must be true)")

            if not self.session_secure_cookies:
                issues.append("SESSION_SECURE_COOKIES=false in production (must be true)")

            if self.debug:
                issues.append("DEBUG=true in production (must be false)")

            if issues:
                error_msg = "Production security configuration issues:\n" + "\n".join(f"  - {issue}" for issue in issues)
                logger.error(error_msg)
                raise ValueError(error_msg)

        return self

    def get_admin_emails(self) -> List[str]:
        """Get admin emails from config and environment variables"""
        emails = list(self.admin_emails)  # Start with configured emails
        
        # Add emails from environment variable (comma-separated)
        env_emails = os.getenv("ADMIN_EMAILS", "").strip()
        if env_emails:
            env_email_list = [email.strip() for email in env_emails.split(",") if email.strip()]
            emails.extend(env_email_list)
        
        # Remove duplicates (case-insensitive)
        unique_emails = []
        seen = set()
        for email in emails:
            email_lower = email.lower()
            if email_lower not in seen:
                unique_emails.append(email)
                seen.add(email_lower)
        
        return unique_emails
    
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
            # Production - include actual deployed URLs
            origins = []
            
            # Always add the configured frontend URL
            if self.frontend_url:
                origins.append(self.frontend_url)
            
            # Add default trusted domains with https
            for domain in self.trusted_domains:
                origins.extend([
                    f"https://{domain}",
                    f"https://www.{domain}",
                ])
            
            # Extract domain from frontend_url and add common variations
            if self.frontend_url:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(self.frontend_url)
                    if parsed.hostname:
                        # Add the exact domain from frontend_url
                        origins.extend([
                            f"https://{parsed.hostname}",
                            f"http://{parsed.hostname}",  # For development/testing
                        ])
                        
                        # For nip.io domains, add the base IP pattern
                        if 'nip.io' in parsed.hostname:
                            # Extract IP and add common nip.io patterns
                            ip_part = parsed.hostname.replace('.nip.io', '')
                            origins.extend([
                                f"https://{ip_part}.nip.io",
                                f"https://api.{ip_part}.nip.io",
                                f"http://{ip_part}.nip.io",
                                f"http://api.{ip_part}.nip.io",
                            ])
                except Exception as e:
                    logger.warning(f"Failed to parse frontend_url for CORS: {e}")
            
            # Special handling for nip.io domains - extract from API_URL if available
            if self.api_url and 'nip.io' in self.api_url:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(self.api_url)
                    if parsed.hostname and 'nip.io' in parsed.hostname:
                        # Extract IP from api.IP.nip.io format
                        hostname_parts = parsed.hostname.split('.')
                        if len(hostname_parts) >= 3 and hostname_parts[0] == 'api':
                            ip_part = '.'.join(hostname_parts[1:-2])  # Get IP part
                            origins.extend([
                                f"https://{ip_part}.nip.io",
                                f"http://{ip_part}.nip.io",
                                f"https://api.{ip_part}.nip.io",
                                f"http://api.{ip_part}.nip.io",
                            ])
                except Exception as e:
                    logger.warning(f"Failed to parse api_url for CORS: {e}")
            
            # Remove duplicates and return
            unique_origins = list(set(origins))
            logger.info(f"Production CORS origins: {unique_origins}")
            return unique_origins

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env file

settings = Settings()

# Configuration is automatically validated on instantiation via Pydantic validators
