"""
Mobile API endpoints for SecureVault
Provides optimized API endpoints for mobile applications
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
import time
import uuid
from .models import Credential, CredentialCreate, CredentialUpdate
from .vault import CredentialVault

# Mobile API Router
mobile_router = APIRouter(prefix="/api/mobile", tags=["mobile"])

# Security scheme
security = HTTPBearer()

class MobileAuthRequest(BaseModel):
    master_password: str
    device_id: str
    device_name: str
    platform: str  # "ios" or "android"

class MobileAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    vault_stats: Dict[str, Any]

class MobileCredential(BaseModel):
    id: str
    service: str
    username: str
    password: str
    url: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []
    created_at: str
    updated_at: str
    favorite: bool = False

class MobileCredentialCreate(BaseModel):
    service: str
    username: str
    password: str
    url: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []
    favorite: bool = False

class MobileCredentialUpdate(BaseModel):
    service: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    favorite: Optional[bool] = None

class MobileSearchRequest(BaseModel):
    query: str
    tags: Optional[List[str]] = None
    favorites_only: bool = False
    limit: int = 50
    offset: int = 0

class MobileSyncRequest(BaseModel):
    last_sync: Optional[str] = None
    device_id: str

class MobileSyncResponse(BaseModel):
    credentials: List[MobileCredential]
    deleted_ids: List[str]
    sync_timestamp: str
    has_more: bool

class DeviceManager:
    """Manage mobile device registrations and tokens"""
    
    def __init__(self):
        self.registered_devices = {}
        self.active_sessions = {}
        self.jwt_secret = "your-jwt-secret-key"  # In production, use environment variable
        
    def register_device(self, device_id: str, device_name: str, platform: str) -> bool:
        """Register a new mobile device"""
        self.registered_devices[device_id] = {
            'device_name': device_name,
            'platform': platform,
            'registered_at': time.time(),
            'last_seen': time.time()
        }
        return True
        
    def generate_tokens(self, device_id: str, vault_authenticated: bool = False) -> Dict[str, Any]:
        """Generate access and refresh tokens for mobile device"""
        now = time.time()
        
        # Access token (30 minutes)
        access_payload = {
            'device_id': device_id,
            'type': 'access',
            'iat': now,
            'exp': now + 1800,  # 30 minutes
            'vault_auth': vault_authenticated
        }
        
        # Refresh token (7 days)
        refresh_payload = {
            'device_id': device_id,
            'type': 'refresh',
            'iat': now,
            'exp': now + 604800  # 7 days
        }
        
        access_token = jwt.encode(access_payload, self.jwt_secret, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, self.jwt_secret, algorithm='HS256')
        
        # Store active session
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = {
            'device_id': device_id,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'created_at': now,
            'vault_authenticated': vault_authenticated
        }
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 1800,
            'session_id': session_id
        }
        
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

# Global device manager
device_manager = DeviceManager()

def get_mobile_vault(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get authenticated vault for mobile"""
    token_payload = device_manager.verify_token(credentials.credentials)
    
    if not token_payload.get('vault_auth', False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vault not authenticated"
        )
    
    # Return vault instance (in production, you'd get device-specific vault)
    from .main import vault
    if not vault.is_authenticated():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vault session expired"
        )
    
    return vault

@mobile_router.post("/auth/register", response_model=Dict[str, str])
async def register_mobile_device(auth_request: MobileAuthRequest):
    """Register a new mobile device"""
    try:
        # Register device
        device_manager.register_device(
            auth_request.device_id,
            auth_request.device_name,
            auth_request.platform
        )
        
        return {"status": "registered", "device_id": auth_request.device_id}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@mobile_router.post("/auth/login", response_model=MobileAuthResponse)
async def mobile_login(auth_request: MobileAuthRequest):
    """Authenticate mobile device and unlock vault"""
    try:
        # Import vault from main app
        from .main import vault
        
        # Authenticate with vault
        if not vault.authenticate(auth_request.master_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid master password"
            )
        
        # Generate tokens
        tokens = device_manager.generate_tokens(auth_request.device_id, vault_authenticated=True)
        
        # Get vault statistics
        stats = vault.get_vault_stats()
        
        return MobileAuthResponse(
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            expires_in=tokens['expires_in'],
            vault_stats=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@mobile_router.get("/credentials", response_model=List[MobileCredential])
async def get_mobile_credentials(
    limit: int = 50,
    offset: int = 0,
    vault: CredentialVault = Depends(get_mobile_vault)
):
    """Get credentials optimized for mobile display"""
    try:
        credentials = vault.get_all_credentials()
        
        # Convert to mobile format
        mobile_credentials = []
        for cred in credentials[offset:offset + limit]:
            mobile_cred = MobileCredential(
                id=cred.id,
                service=cred.service,
                username=cred.username,
                password=cred.password,
                url=cred.url,
                notes=cred.notes,
                tags=cred.tags,
                created_at=cred.created_at.isoformat(),
                updated_at=cred.updated_at.isoformat(),
                favorite=getattr(cred, 'favorite', False)
            )
            mobile_credentials.append(mobile_cred)
            
        return mobile_credentials
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get credentials: {str(e)}"
        )

@mobile_router.post("/credentials", response_model=MobileCredential)
async def create_mobile_credential(
    credential: MobileCredentialCreate,
    vault: CredentialVault = Depends(get_mobile_vault)
):
    """Create new credential via mobile"""
    try:
        # Convert to standard credential format
        cred_create = CredentialCreate(
            service=credential.service,
            username=credential.username,
            password=credential.password,
            url=credential.url,
            notes=credential.notes,
            tags=credential.tags
        )
        
        created_cred = vault.add_credential(cred_create)
        
        # Convert to mobile format
        return MobileCredential(
            id=created_cred.id,
            service=created_cred.service,
            username=created_cred.username,
            password=created_cred.password,
            url=created_cred.url,
            notes=created_cred.notes,
            tags=created_cred.tags,
            created_at=created_cred.created_at.isoformat(),
            updated_at=created_cred.updated_at.isoformat(),
            favorite=credential.favorite
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create credential: {str(e)}"
        )

@mobile_router.post("/search", response_model=List[MobileCredential])
async def search_mobile_credentials(
    search_request: MobileSearchRequest,
    vault: CredentialVault = Depends(get_mobile_vault)
):
    """Search credentials optimized for mobile"""
    try:
        results = vault.search_credentials(search_request.query)
        
        # Filter by tags if specified
        if search_request.tags:
            results = [r for r in results if any(tag in r.tags for tag in search_request.tags)]
        
        # Convert to mobile format
        mobile_results = []
        for cred in results[search_request.offset:search_request.offset + search_request.limit]:
            mobile_cred = MobileCredential(
                id=cred.id,
                service=cred.service,
                username=cred.username,
                password=cred.password,
                url=cred.url,
                notes=cred.notes,
                tags=cred.tags,
                created_at=cred.created_at.isoformat(),
                updated_at=cred.updated_at.isoformat(),
                favorite=getattr(cred, 'favorite', False)
            )
            mobile_results.append(mobile_cred)
            
        return mobile_results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@mobile_router.post("/sync", response_model=MobileSyncResponse)
async def sync_mobile_data(
    sync_request: MobileSyncRequest,
    vault: CredentialVault = Depends(get_mobile_vault)
):
    """Sync data for mobile app"""
    try:
        # Get all credentials (in production, implement incremental sync)
        credentials = vault.get_all_credentials()
        
        mobile_credentials = []
        for cred in credentials:
            mobile_cred = MobileCredential(
                id=cred.id,
                service=cred.service,
                username=cred.username,
                password=cred.password,
                url=cred.url,
                notes=cred.notes,
                tags=cred.tags,
                created_at=cred.created_at.isoformat(),
                updated_at=cred.updated_at.isoformat(),
                favorite=getattr(cred, 'favorite', False)
            )
            mobile_credentials.append(mobile_cred)
        
        return MobileSyncResponse(
            credentials=mobile_credentials,
            deleted_ids=[],  # Implement deleted items tracking
            sync_timestamp=str(int(time.time())),
            has_more=False
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )

@mobile_router.get("/vault/stats")
async def get_mobile_vault_stats(vault: CredentialVault = Depends(get_mobile_vault)):
    """Get vault statistics for mobile dashboard"""
    try:
        return vault.get_vault_stats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )
