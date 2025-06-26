"""
Data models for credential management
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import time


class Credential(BaseModel):
    id: str = Field(..., description="Unique identifier for the credential")
    service_name: str = Field(..., description="Name of the service/application")
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password or API key")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    tags: List[str] = Field(default_factory=list, description="Tags for organization")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CredentialCreate(BaseModel):
    service_name: str
    username: str
    password: str
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class CredentialUpdate(BaseModel):
    service_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class LoginRequest(BaseModel):
    master_password: str


class CreateVaultRequest(BaseModel):
    master_password: str


class ShareRequest(BaseModel):
    credential_id: str
    expires_in: int = Field(default=3600, description="Expiration time in seconds")
    password_protected: bool = Field(default=False)
    share_password: Optional[str] = None


class ShareResponse(BaseModel):
    token: str
    expires_at: float
    qr_code: Optional[str] = None


class SearchRequest(BaseModel):
    query: Optional[str] = None
    tags: Optional[List[str]] = None


class AuditLog(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    action: str
    credential_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class VaultStats(BaseModel):
    total_credentials: int
    created_at: float
    last_accessed: float
    vault_size: int
