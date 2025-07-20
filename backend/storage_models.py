from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class StorageType(str, Enum):
    """Storage backend types"""
    PVC = "pvc"
    CLOUD_STORAGE = "cloud_storage"
    FUSE = "fuse"

class StorageStatus(str, Enum):
    """Storage status states"""
    CREATING = "creating"
    ACTIVE = "active"
    DELETING = "deleting"
    FAILED = "failed"
    UNKNOWN = "unknown"

class UserStorage(BaseModel):
    """User storage bucket metadata"""
    id: str  # Unique storage ID
    user_id: str
    bucket_name: str
    display_name: str  # User-friendly cosmic name
    storage_type: StorageType = StorageType.CLOUD_STORAGE
    status: StorageStatus = StorageStatus.CREATING
    created_at: datetime
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    object_count: int = 0
    location: str
    storage_class: str = "STANDARD"
    versioning_enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class StorageRequest(BaseModel):
    """Request model for creating storage"""
    storage_type: StorageType = StorageType.CLOUD_STORAGE
    storage_class: str = "STANDARD"
    custom_name: Optional[str] = None  # Allow custom bucket name
    location: Optional[str] = None

class StorageSelectionRequest(BaseModel):
    """Request model for selecting storage during environment creation"""
    storage_id: Optional[str] = None  # Existing storage to attach
    create_new: bool = False  # Create new storage
    storage_request: Optional[StorageRequest] = None  # New storage configuration

class EnvironmentStorageConfig(BaseModel):
    """Storage configuration for environment creation"""
    storage_id: str
    bucket_name: str
    mount_path: str = "/workspace"
    storage_type: StorageType = StorageType.CLOUD_STORAGE

class StorageUsageStats(BaseModel):
    """Storage usage statistics"""
    total_buckets: int
    total_size_bytes: int
    active_buckets: int
    last_updated: datetime

class StorageMetadata(BaseModel):
    """Detailed storage metadata for management"""
    storage: UserStorage
    bucket_metadata: Optional[Dict[str, Any]] = None
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list)
    permissions_valid: bool = True
    
class BucketOperationRequest(BaseModel):
    """Request model for bucket operations"""
    operation: str  # "delete", "download", "backup"
    force: bool = False  # Force operation even with data
    backup_location: Optional[str] = None

class StorageListResponse(BaseModel):
    """Response model for storage listing"""
    storages: List[UserStorage]
    total_count: int
    usage_stats: StorageUsageStats

class StorageCreationResponse(BaseModel):
    """Response model for storage creation"""
    storage: UserStorage
    bucket_metadata: Dict[str, Any]
    permissions_configured: bool
    
# Enhanced environment request model with storage selection
class EnvironmentRequestWithStorage(BaseModel):
    """Environment creation request with storage options"""
    # Resource configuration (existing)
    cpu_limit: Optional[float] = 1.0
    memory_limit: Optional[str] = "2Gi"
    image: Optional[str] = None
    
    # Storage configuration (new)
    storage_selection: Optional[StorageSelectionRequest] = None
    
    # Backward compatibility for storage_size (now ignored)
    storage_size: Optional[str] = "10Gi"  # Kept for API compatibility
