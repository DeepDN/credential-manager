"""
Browser Extension API for SecureVault
Provides secure communication with browser extensions
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import hashlib
import time
import secrets
from .models import Credential
from .vault import CredentialVault

# Browser Extension API Router
browser_router = APIRouter(prefix="/api/browser", tags=["browser"])

class ExtensionAuthRequest(BaseModel):
    master_password: str
    extension_id: str
    browser: str  # "chrome", "firefox", "safari"
    origin: str

class ExtensionAuthResponse(BaseModel):
    session_token: str
    expires_in: int
    permissions: List[str]

class AutofillRequest(BaseModel):
    url: str
    domain: str
    form_fields: List[Dict[str, str]]
    session_token: str

class AutofillResponse(BaseModel):
    credentials: List[Dict[str, Any]]
    suggestions: List[Dict[str, str]]

class PasswordGenerateRequest(BaseModel):
    length: int = 16
    include_symbols: bool = True
    include_numbers: bool = True
    include_uppercase: bool = True
    include_lowercase: bool = True
    exclude_ambiguous: bool = True

class PasswordGenerateResponse(BaseModel):
    password: str
    strength: str
    entropy: float

class ExtensionCredential(BaseModel):
    id: str
    service: str
    username: str
    url: Optional[str] = None
    domain: str
    match_score: float

class ExtensionManager:
    """Manage browser extension sessions and security"""
    
    def __init__(self):
        self.active_sessions = {}
        self.trusted_extensions = {
            # Chrome extension IDs
            'chrome': ['securevault-chrome-ext-id'],
            # Firefox extension IDs  
            'firefox': ['securevault-firefox-ext-id'],
            # Safari extension IDs
            'safari': ['securevault-safari-ext-id']
        }
        
    def is_trusted_extension(self, extension_id: str, browser: str) -> bool:
        """Check if extension is trusted"""
        return extension_id in self.trusted_extensions.get(browser, [])
        
    def create_session(self, extension_id: str, browser: str, origin: str) -> Dict[str, Any]:
        """Create secure session for browser extension"""
        session_token = secrets.token_urlsafe(32)
        session_data = {
            'extension_id': extension_id,
            'browser': browser,
            'origin': origin,
            'created_at': time.time(),
            'expires_at': time.time() + 3600,  # 1 hour
            'permissions': ['read_credentials', 'autofill', 'generate_password']
        }
        
        self.active_sessions[session_token] = session_data
        return {
            'session_token': session_token,
            'expires_in': 3600,
            'permissions': session_data['permissions']
        }
        
    def verify_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Verify browser extension session"""
        session = self.active_sessions.get(session_token)
        if not session:
            return None
            
        if time.time() > session['expires_at']:
            del self.active_sessions[session_token]
            return None
            
        return session
        
    def revoke_session(self, session_token: str) -> bool:
        """Revoke browser extension session"""
        if session_token in self.active_sessions:
            del self.active_sessions[session_token]
            return True
        return False

class PasswordGenerator:
    """Secure password generator for browser extension"""
    
    @staticmethod
    def generate_password(
        length: int = 16,
        include_symbols: bool = True,
        include_numbers: bool = True,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        exclude_ambiguous: bool = True
    ) -> str:
        """Generate secure password"""
        chars = ""
        
        if include_lowercase:
            chars += "abcdefghijklmnopqrstuvwxyz"
        if include_uppercase:
            chars += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if include_numbers:
            chars += "0123456789"
        if include_symbols:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
            
        if exclude_ambiguous:
            # Remove ambiguous characters
            ambiguous = "0O1lI|"
            chars = ''.join(c for c in chars if c not in ambiguous)
            
        if not chars:
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            
        password = ''.join(secrets.choice(chars) for _ in range(length))
        return password
        
    @staticmethod
    def calculate_strength(password: str) -> tuple[str, float]:
        """Calculate password strength"""
        length = len(password)
        charset_size = 0
        
        if any(c.islower() for c in password):
            charset_size += 26
        if any(c.isupper() for c in password):
            charset_size += 26
        if any(c.isdigit() for c in password):
            charset_size += 10
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            charset_size += 23
            
        # Calculate entropy
        import math
        entropy = length * math.log2(charset_size) if charset_size > 0 else 0
        
        # Determine strength
        if entropy < 30:
            strength = "weak"
        elif entropy < 60:
            strength = "medium"
        elif entropy < 90:
            strength = "strong"
        else:
            strength = "very_strong"
            
        return strength, entropy

class DomainMatcher:
    """Match credentials to domains for autofill"""
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return url.lower()
            
    @staticmethod
    def calculate_match_score(credential_url: str, target_url: str) -> float:
        """Calculate how well a credential matches a target URL"""
        if not credential_url:
            return 0.0
            
        cred_domain = DomainMatcher.extract_domain(credential_url)
        target_domain = DomainMatcher.extract_domain(target_url)
        
        # Exact domain match
        if cred_domain == target_domain:
            return 1.0
            
        # Subdomain match
        if cred_domain in target_domain or target_domain in cred_domain:
            return 0.8
            
        # Partial domain match
        cred_parts = cred_domain.split('.')
        target_parts = target_domain.split('.')
        
        if len(cred_parts) >= 2 and len(target_parts) >= 2:
            if cred_parts[-2:] == target_parts[-2:]:  # Same root domain
                return 0.6
                
        return 0.0

# Global extension manager
extension_manager = ExtensionManager()

def get_browser_vault(request: Request):
    """Dependency to get authenticated vault for browser extension"""
    session_token = request.headers.get('X-Session-Token')
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token required"
        )
    
    session = extension_manager.verify_session(session_token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    # Return vault instance
    from .main import vault
    if not vault.is_authenticated():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vault not authenticated"
        )
    
    return vault

@browser_router.post("/auth", response_model=ExtensionAuthResponse)
async def authenticate_extension(auth_request: ExtensionAuthRequest):
    """Authenticate browser extension"""
    try:
        # Verify trusted extension
        if not extension_manager.is_trusted_extension(auth_request.extension_id, auth_request.browser):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Untrusted extension"
            )
        
        # Authenticate with vault
        from .main import vault
        if not vault.authenticate(auth_request.master_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid master password"
            )
        
        # Create session
        session_data = extension_manager.create_session(
            auth_request.extension_id,
            auth_request.browser,
            auth_request.origin
        )
        
        return ExtensionAuthResponse(**session_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

@browser_router.post("/autofill", response_model=AutofillResponse)
async def get_autofill_suggestions(
    autofill_request: AutofillRequest,
    vault: CredentialVault = Depends(get_browser_vault)
):
    """Get autofill suggestions for browser"""
    try:
        # Get all credentials
        all_credentials = vault.get_all_credentials()
        
        # Find matching credentials
        matching_credentials = []
        for cred in all_credentials:
            match_score = DomainMatcher.calculate_match_score(cred.url or "", autofill_request.url)
            if match_score > 0.5:  # Only include good matches
                matching_credentials.append({
                    'id': cred.id,
                    'service': cred.service,
                    'username': cred.username,
                    'password': cred.password,
                    'url': cred.url,
                    'match_score': match_score
                })
        
        # Sort by match score
        matching_credentials.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Generate suggestions
        suggestions = []
        for cred in matching_credentials[:5]:  # Top 5 matches
            suggestions.append({
                'id': cred['id'],
                'service': cred['service'],
                'username': cred['username'],
                'match_score': cred['match_score']
            })
        
        return AutofillResponse(
            credentials=matching_credentials,
            suggestions=suggestions
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Autofill failed: {str(e)}"
        )

@browser_router.post("/generate-password", response_model=PasswordGenerateResponse)
async def generate_password_for_extension(
    generate_request: PasswordGenerateRequest,
    vault: CredentialVault = Depends(get_browser_vault)
):
    """Generate password for browser extension"""
    try:
        password = PasswordGenerator.generate_password(
            length=generate_request.length,
            include_symbols=generate_request.include_symbols,
            include_numbers=generate_request.include_numbers,
            include_uppercase=generate_request.include_uppercase,
            include_lowercase=generate_request.include_lowercase,
            exclude_ambiguous=generate_request.exclude_ambiguous
        )
        
        strength, entropy = PasswordGenerator.calculate_strength(password)
        
        return PasswordGenerateResponse(
            password=password,
            strength=strength,
            entropy=entropy
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password generation failed: {str(e)}"
        )

@browser_router.get("/credentials/search")
async def search_credentials_for_extension(
    domain: str,
    vault: CredentialVault = Depends(get_browser_vault)
):
    """Search credentials by domain for browser extension"""
    try:
        all_credentials = vault.get_all_credentials()
        
        matching_credentials = []
        for cred in all_credentials:
            if cred.url and domain.lower() in cred.url.lower():
                matching_credentials.append(ExtensionCredential(
                    id=cred.id,
                    service=cred.service,
                    username=cred.username,
                    url=cred.url,
                    domain=DomainMatcher.extract_domain(cred.url or ""),
                    match_score=DomainMatcher.calculate_match_score(cred.url or "", f"https://{domain}")
                ))
        
        # Sort by match score
        matching_credentials.sort(key=lambda x: x.match_score, reverse=True)
        
        return matching_credentials
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@browser_router.post("/logout")
async def logout_extension(request: Request):
    """Logout browser extension"""
    try:
        session_token = request.headers.get('X-Session-Token')
        if session_token:
            extension_manager.revoke_session(session_token)
        
        return {"status": "logged_out"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )
