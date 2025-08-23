from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    RESEARCHER = "researcher"

class SubscriptionTier(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class PodStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    SUCCEEDED = "succeeded"
    UNKNOWN = "unknown"

class User(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole = UserRole.USER
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    
    # Subscription fields
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    subscription_expires_at: Optional[datetime] = None
    max_uptime_minutes: Optional[int] = 60  # None = unlimited, 60 = 1 hour for free
    auto_shutdown_enabled: bool = True

class Environment(BaseModel):
    id: str
    user_id: str
    user_email: str  # Added field for correct DNS/subdomain naming
    env_id: str      # Unique environment/session ID for multi-env support
    pod_name: str
    status: PodStatus
    url: Optional[str] = None
    created_at: datetime
    last_activity: Optional[datetime] = None
    resource_config: Dict[str, Any] = Field(default_factory=dict)

class EnvironmentRequest(BaseModel):
    cpu_limit: Optional[float] = 1.0
    memory_limit: Optional[str] = "2Gi"
    storage_size: Optional[str] = "10Gi"  # Kept for backward compatibility
    image: Optional[str] = None

    # Storage selection (new)
    storage_id: Optional[str] = None  # Existing storage to attach
    create_new_storage: bool = False  # Create new storage
    storage_class: Optional[str] = "STANDARD"  # For new storage

    # User-supplied environment variables
    env_vars: Optional[Dict[str, str]] = None

class ActivityLog(BaseModel):
    id: str
    user_id: str
    action: str
    details: Optional[str] = None
    timestamp: datetime
    status: str = "success"
    ip_address: Optional[str] = None

class HealthCheck(BaseModel):
    status: str = "healthy"
    timestamp: datetime
    version: str = "1.0.0"
    uptime: float

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []

class UserInDB(User):
    hashed_password: Optional[str] = None
