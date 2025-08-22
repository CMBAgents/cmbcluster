from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import json

class FileType(str, Enum):
    GCP_SERVICE_ACCOUNT = "gcp_service_account"
    CUSTOM_JSON = "custom_json"

class UserFile(BaseModel):
    id: str
    user_id: str
    file_name: str
    file_type: FileType
    encrypted_content: bytes
    environment_variable_name: Optional[str] = None
    container_path: str
    file_size: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class UserFileRequest(BaseModel):
    file_name: str
    file_type: FileType
    content: str  # JSON content as string
    environment_variable_name: str  # Now required
    container_path: Optional[str] = None

    @validator('environment_variable_name', always=True)
    def set_env_var_name(cls, v, values):
        """Auto-set environment variable name for GCP service accounts, validate for custom JSON"""
        file_type = values.get('file_type')
        
        if file_type == FileType.GCP_SERVICE_ACCOUNT:
            # Always set for GCP service accounts
            return "GOOGLE_APPLICATION_CREDENTIALS"
        else:
            # For custom JSON files, environment variable is required
            if not v or not v.strip():
                raise ValueError('Environment variable name is required for custom JSON files')
            return v.strip()

    @validator('container_path')
    def set_container_path(cls, v, values):
        """Auto-set container path based on file type"""
        if not v:
            file_type = values.get('file_type')
            file_name = values.get('file_name', 'file.json')
            
            if file_type == FileType.GCP_SERVICE_ACCOUNT:
                return "/app/secrets/gcp_service_account.json"
            else:
                # For custom JSON files, use /mnt/user-files/ prefix with original filename
                return f"/mnt/user-files/{file_name}"
        return v

    @validator('content')
    def validate_json_content(cls, v):
        """Validate that content is valid JSON"""
        try:
            json.loads(v)
        except json.JSONDecodeError:
            raise ValueError('Content must be valid JSON')
        return v

    @validator('content')
    def validate_gcp_service_account(cls, v, values):
        """Validate GCP service account key structure"""
        if values.get('file_type') == FileType.GCP_SERVICE_ACCOUNT:
            try:
                data = json.loads(v)
                required_fields = [
                    'type', 'project_id', 'private_key_id', 'private_key',
                    'client_email', 'client_id', 'auth_uri', 'token_uri'
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    raise ValueError(f'Missing required GCP service account fields: {missing_fields}')
                
                if data.get('type') != 'service_account':
                    raise ValueError('GCP service account type must be "service_account"')
                    
            except json.JSONDecodeError:
                raise ValueError('Invalid JSON content for GCP service account')
        return v

class UserFileResponse(BaseModel):
    id: str
    file_name: str
    file_type: FileType
    environment_variable_name: Optional[str] = None
    container_path: str
    file_size: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class UserFileUpdate(BaseModel):
    file_name: Optional[str] = None
    environment_variable_name: Optional[str] = None
    container_path: Optional[str] = None
    content: Optional[str] = None  # New content if updating

    @validator('environment_variable_name')
    def validate_env_var_name(cls, v):
        """Validate environment variable name if provided"""
        if v is not None and not v.strip():
            raise ValueError('Environment variable name cannot be empty')
        return v.strip() if v else None

    @validator('content')
    def validate_json_if_provided(cls, v):
        """Validate JSON if content is provided"""
        if v is not None:
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('Content must be valid JSON')
        return v
