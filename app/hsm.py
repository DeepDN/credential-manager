"""
Hardware Security Module (HSM) Support for SecureVault
Provides integration with hardware security modules for enhanced key protection
"""
import os
import logging
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)

class HSMProvider:
    """Base class for HSM providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_available = False
        
    def initialize(self) -> bool:
        """Initialize HSM connection"""
        raise NotImplementedError
        
    def generate_key(self, key_id: str) -> bool:
        """Generate a new key in HSM"""
        raise NotImplementedError
        
    def encrypt(self, key_id: str, data: bytes) -> bytes:
        """Encrypt data using HSM key"""
        raise NotImplementedError
        
    def decrypt(self, key_id: str, encrypted_data: bytes) -> bytes:
        """Decrypt data using HSM key"""
        raise NotImplementedError

class SoftHSM(HSMProvider):
    """Software HSM implementation for development and testing"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.keys = {}
        self.key_store_path = config.get('key_store_path', './hsm_keys')
        
    def initialize(self) -> bool:
        """Initialize software HSM"""
        try:
            os.makedirs(self.key_store_path, exist_ok=True)
            self.is_available = True
            logger.info("Software HSM initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Software HSM: {e}")
            return False
            
    def generate_key(self, key_id: str) -> bool:
        """Generate RSA key pair"""
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Store private key
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            key_file = os.path.join(self.key_store_path, f"{key_id}.pem")
            with open(key_file, 'wb') as f:
                f.write(private_pem)
                
            self.keys[key_id] = private_key
            logger.info(f"Generated key: {key_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate key {key_id}: {e}")
            return False
            
    def _load_key(self, key_id: str):
        """Load key from storage"""
        if key_id in self.keys:
            return self.keys[key_id]
            
        key_file = os.path.join(self.key_store_path, f"{key_id}.pem")
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
                self.keys[key_id] = private_key
                return private_key
        return None
        
    def encrypt(self, key_id: str, data: bytes) -> bytes:
        """Encrypt data using RSA public key"""
        try:
            private_key = self._load_key(key_id)
            if not private_key:
                raise ValueError(f"Key {key_id} not found")
                
            public_key = private_key.public_key()
            encrypted = public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return encrypted
            
        except Exception as e:
            logger.error(f"Encryption failed for key {key_id}: {e}")
            raise
            
    def decrypt(self, key_id: str, encrypted_data: bytes) -> bytes:
        """Decrypt data using RSA private key"""
        try:
            private_key = self._load_key(key_id)
            if not private_key:
                raise ValueError(f"Key {key_id} not found")
                
            decrypted = private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted
            
        except Exception as e:
            logger.error(f"Decryption failed for key {key_id}: {e}")
            raise

class HSMManager:
    """HSM Manager to handle different HSM providers"""
    
    def __init__(self):
        self.providers = {}
        self.active_provider = None
        
    def register_provider(self, name: str, provider: HSMProvider):
        """Register an HSM provider"""
        self.providers[name] = provider
        
    def initialize_provider(self, provider_name: str, config: Dict[str, Any]) -> bool:
        """Initialize a specific HSM provider"""
        try:
            if provider_name == "softhsm":
                provider = SoftHSM(config)
            else:
                raise ValueError(f"Unknown HSM provider: {provider_name}")
                
            if provider.initialize():
                self.providers[provider_name] = provider
                self.active_provider = provider
                logger.info(f"HSM provider {provider_name} initialized")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to initialize HSM provider {provider_name}: {e}")
            return False
            
    def is_available(self) -> bool:
        """Check if HSM is available"""
        return self.active_provider is not None and self.active_provider.is_available
        
    def generate_master_key(self, key_id: str = "vault_master_key") -> bool:
        """Generate master key for vault encryption"""
        if not self.is_available():
            return False
        return self.active_provider.generate_key(key_id)
        
    def encrypt_vault_key(self, vault_key: bytes, key_id: str = "vault_master_key") -> Optional[str]:
        """Encrypt vault key using HSM"""
        if not self.is_available():
            return None
            
        try:
            encrypted = self.active_provider.encrypt(key_id, vault_key)
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encrypt vault key: {e}")
            return None
            
    def decrypt_vault_key(self, encrypted_key: str, key_id: str = "vault_master_key") -> Optional[bytes]:
        """Decrypt vault key using HSM"""
        if not self.is_available():
            return None
            
        try:
            encrypted_data = base64.b64decode(encrypted_key.encode('utf-8'))
            return self.active_provider.decrypt(key_id, encrypted_data)
        except Exception as e:
            logger.error(f"Failed to decrypt vault key: {e}")
            return None

# Global HSM manager instance
hsm_manager = HSMManager()

def initialize_hsm(config: Optional[Dict[str, Any]] = None) -> bool:
    """Initialize HSM with configuration"""
    if config is None:
        config = {
            'provider': 'softhsm',
            'key_store_path': './hsm_keys'
        }
    
    provider_name = config.get('provider', 'softhsm')
    return hsm_manager.initialize_provider(provider_name, config)

def get_hsm_manager() -> HSMManager:
    """Get the global HSM manager instance"""
    return hsm_manager
