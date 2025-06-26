"""
Security module for credential encryption and authentication
"""
import os
import json
import time
import hashlib
import secrets
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import bcrypt
import base64


class SecurityManager:
    def __init__(self, vault_path: str = "vault.enc"):
        self.vault_path = vault_path
        self.session_key: Optional[bytes] = None
        self.last_activity = time.time()
        self.session_timeout = 300  # 5 minutes
        self.failed_attempts = 0
        self.lockout_until = 0
        self.max_attempts = 5
        self.lockout_duration = 300  # 5 minutes
        
    def derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def generate_salt(self) -> bytes:
        """Generate a random salt"""
        return os.urandom(16)
    
    def hash_master_password(self, password: str) -> str:
        """Hash master password for storage"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_master_password(self, password: str, hashed: str) -> bool:
        """Verify master password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def is_locked_out(self) -> bool:
        """Check if account is locked due to failed attempts"""
        return time.time() < self.lockout_until
    
    def record_failed_attempt(self):
        """Record a failed login attempt"""
        self.failed_attempts += 1
        if self.failed_attempts >= self.max_attempts:
            self.lockout_until = time.time() + self.lockout_duration
    
    def reset_failed_attempts(self):
        """Reset failed attempts counter"""
        self.failed_attempts = 0
        self.lockout_until = 0
    
    def is_session_valid(self) -> bool:
        """Check if current session is still valid"""
        if not self.session_key:
            return False
        
        if time.time() - self.last_activity > self.session_timeout:
            self.session_key = None
            return False
        
        return True
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()
    
    def authenticate(self, master_password: str) -> bool:
        """Authenticate user with master password"""
        if self.is_locked_out():
            return False
        
        # Load vault metadata
        vault_data = self.load_vault_metadata()
        if not vault_data:
            return False
        
        if self.verify_master_password(master_password, vault_data['master_hash']):
            self.session_key = self.derive_key(master_password, vault_data['salt'])
            self.reset_failed_attempts()
            self.update_activity()
            return True
        else:
            self.record_failed_attempt()
            return False
    
    def create_vault(self, master_password: str) -> bool:
        """Create new encrypted vault"""
        salt = self.generate_salt()
        master_hash = self.hash_master_password(master_password)
        
        vault_metadata = {
            'salt': base64.b64encode(salt).decode(),
            'master_hash': master_hash,
            'created_at': time.time(),
            'version': '1.0'
        }
        
        # Create empty encrypted credentials
        key = self.derive_key(master_password, salt)
        fernet = Fernet(key)
        empty_credentials = fernet.encrypt(json.dumps({}).encode())
        
        vault_data = {
            'metadata': vault_metadata,
            'credentials': base64.b64encode(empty_credentials).decode()
        }
        
        try:
            with open(self.vault_path, 'w') as f:
                json.dump(vault_data, f)
            return True
        except Exception as e:
            print(f"Error creating vault: {e}")
            return False
    
    def load_vault_metadata(self) -> Optional[Dict]:
        """Load vault metadata"""
        try:
            if not os.path.exists(self.vault_path):
                return None
            
            with open(self.vault_path, 'r') as f:
                vault_data = json.load(f)
                metadata = vault_data['metadata']
                metadata['salt'] = base64.b64decode(metadata['salt'])
                return metadata
        except Exception as e:
            print(f"Error loading vault metadata: {e}")
            return None
    
    def encrypt_data(self, data: str) -> Optional[str]:
        """Encrypt data using session key"""
        if not self.is_session_valid():
            return None
        
        try:
            fernet = Fernet(self.session_key)
            encrypted = fernet.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            print(f"Error encrypting data: {e}")
            return None
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt data using session key"""
        if not self.is_session_valid():
            return None
        
        try:
            fernet = Fernet(self.session_key)
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            print(f"Error decrypting data: {e}")
            return None
    
    def generate_sharing_token(self, credential_data: Dict, expires_in: int = 3600) -> str:
        """Generate temporary sharing token for credential"""
        token_data = {
            'credential': credential_data,
            'expires_at': time.time() + expires_in,
            'token_id': secrets.token_urlsafe(16)
        }
        
        # Use a temporary key for sharing tokens
        temp_key = Fernet.generate_key()
        fernet = Fernet(temp_key)
        encrypted_token = fernet.encrypt(json.dumps(token_data).encode())
        
        # Combine key and token for sharing
        sharing_data = {
            'key': base64.b64encode(temp_key).decode(),
            'token': base64.b64encode(encrypted_token).decode()
        }
        
        return base64.b64encode(json.dumps(sharing_data).encode()).decode()
    
    def decrypt_sharing_token(self, token: str) -> Optional[Dict]:
        """Decrypt and validate sharing token"""
        try:
            sharing_data = json.loads(base64.b64decode(token).decode())
            temp_key = base64.b64decode(sharing_data['key'])
            encrypted_token = base64.b64decode(sharing_data['token'])
            
            fernet = Fernet(temp_key)
            token_data = json.loads(fernet.decrypt(encrypted_token).decode())
            
            # Check if token is expired
            if time.time() > token_data['expires_at']:
                return None
            
            return token_data['credential']
        except Exception as e:
            print(f"Error decrypting sharing token: {e}")
            return None
    
    def logout(self):
        """Clear session"""
        self.session_key = None
        self.last_activity = 0
