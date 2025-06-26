"""
Vault management for secure credential storage
"""
import json
import os
import time
import uuid
from typing import List, Optional, Dict, Any
from .models import Credential, CredentialCreate, CredentialUpdate, AuditLog
from .security import SecurityManager


class CredentialVault:
    def __init__(self, vault_path: str = "vault.enc"):
        self.vault_path = vault_path
        self.security = SecurityManager(vault_path)
        self.audit_logs: List[AuditLog] = []
        
    def vault_exists(self) -> bool:
        """Check if vault file exists"""
        return os.path.exists(self.vault_path)
    
    def create_vault(self, master_password: str) -> bool:
        """Create new vault with master password"""
        return self.security.create_vault(master_password)
    
    def authenticate(self, master_password: str) -> bool:
        """Authenticate with master password"""
        success = self.security.authenticate(master_password)
        if success:
            self._log_action("LOGIN", details={"success": True})
        else:
            self._log_action("LOGIN", details={"success": False})
        return success
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.security.is_session_valid()
    
    def is_locked_out(self) -> bool:
        """Check if account is locked"""
        return self.security.is_locked_out()
    
    def logout(self):
        """Logout and clear session"""
        self._log_action("LOGOUT")
        self.security.logout()
    
    def _load_credentials(self) -> Dict[str, Credential]:
        """Load and decrypt credentials from vault"""
        if not self.is_authenticated():
            return {}
        
        try:
            with open(self.vault_path, 'r') as f:
                vault_data = json.load(f)
            
            encrypted_credentials = vault_data['credentials']
            decrypted_data = self.security.decrypt_data(encrypted_credentials)
            
            if not decrypted_data:
                return {}
            
            credentials_dict = json.loads(decrypted_data)
            credentials = {}
            
            for cred_id, cred_data in credentials_dict.items():
                credentials[cred_id] = Credential(**cred_data)
            
            self.security.update_activity()
            return credentials
            
        except Exception as e:
            print(f"Error loading credentials: {e}")
            return {}
    
    def _save_credentials(self, credentials: Dict[str, Credential]) -> bool:
        """Encrypt and save credentials to vault"""
        if not self.is_authenticated():
            return False
        
        try:
            # Convert credentials to dict format
            credentials_dict = {}
            for cred_id, credential in credentials.items():
                credentials_dict[cred_id] = credential.dict()
            
            # Encrypt credentials
            credentials_json = json.dumps(credentials_dict)
            encrypted_credentials = self.security.encrypt_data(credentials_json)
            
            if not encrypted_credentials:
                return False
            
            # Load existing vault data
            with open(self.vault_path, 'r') as f:
                vault_data = json.load(f)
            
            # Update credentials
            vault_data['credentials'] = encrypted_credentials
            
            # Save back to file
            with open(self.vault_path, 'w') as f:
                json.dump(vault_data, f)
            
            self.security.update_activity()
            return True
            
        except Exception as e:
            print(f"Error saving credentials: {e}")
            return False
    
    def add_credential(self, credential_data: CredentialCreate) -> Optional[str]:
        """Add new credential to vault"""
        if not self.is_authenticated():
            return None
        
        credentials = self._load_credentials()
        
        # Create new credential
        credential_id = str(uuid.uuid4())
        credential = Credential(
            id=credential_id,
            **credential_data.dict()
        )
        
        credentials[credential_id] = credential
        
        if self._save_credentials(credentials):
            self._log_action("ADD_CREDENTIAL", credential_id, {
                "service_name": credential_data.service_name
            })
            return credential_id
        
        return None
    
    def get_credential(self, credential_id: str) -> Optional[Credential]:
        """Get specific credential by ID"""
        if not self.is_authenticated():
            return None
        
        credentials = self._load_credentials()
        credential = credentials.get(credential_id)
        
        if credential:
            self._log_action("VIEW_CREDENTIAL", credential_id, {
                "service_name": credential.service_name
            })
        
        return credential
    
    def get_all_credentials(self) -> List[Credential]:
        """Get all credentials"""
        if not self.is_authenticated():
            return []
        
        credentials = self._load_credentials()
        self._log_action("LIST_CREDENTIALS", details={
            "count": len(credentials)
        })
        
        return list(credentials.values())
    
    def update_credential(self, credential_id: str, update_data: CredentialUpdate) -> bool:
        """Update existing credential"""
        if not self.is_authenticated():
            return False
        
        credentials = self._load_credentials()
        
        if credential_id not in credentials:
            return False
        
        credential = credentials[credential_id]
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(credential, field, value)
        
        credential.updated_at = time.time()
        credentials[credential_id] = credential
        
        if self._save_credentials(credentials):
            self._log_action("UPDATE_CREDENTIAL", credential_id, {
                "service_name": credential.service_name,
                "updated_fields": list(update_dict.keys())
            })
            return True
        
        return False
    
    def delete_credential(self, credential_id: str) -> bool:
        """Delete credential from vault"""
        if not self.is_authenticated():
            return False
        
        credentials = self._load_credentials()
        
        if credential_id not in credentials:
            return False
        
        credential = credentials[credential_id]
        del credentials[credential_id]
        
        if self._save_credentials(credentials):
            self._log_action("DELETE_CREDENTIAL", credential_id, {
                "service_name": credential.service_name
            })
            return True
        
        return False
    
    def search_credentials(self, query: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Credential]:
        """Search credentials by query or tags"""
        if not self.is_authenticated():
            return []
        
        credentials = self._load_credentials()
        results = []
        
        for credential in credentials.values():
            match = True
            
            # Text search
            if query:
                query_lower = query.lower()
                if not (query_lower in credential.service_name.lower() or 
                       query_lower in credential.username.lower() or
                       (credential.notes and query_lower in credential.notes.lower())):
                    match = False
            
            # Tag search
            if tags and match:
                if not any(tag in credential.tags for tag in tags):
                    match = False
            
            if match:
                results.append(credential)
        
        self._log_action("SEARCH_CREDENTIALS", details={
            "query": query,
            "tags": tags,
            "results_count": len(results)
        })
        
        return results
    
    def generate_sharing_token(self, credential_id: str, expires_in: int = 3600) -> Optional[str]:
        """Generate sharing token for credential"""
        if not self.is_authenticated():
            return None
        
        credential = self.get_credential(credential_id)
        if not credential:
            return None
        
        # Create shareable credential data (without sensitive internal info)
        share_data = {
            "service_name": credential.service_name,
            "username": credential.username,
            "password": credential.password,
            "notes": credential.notes
        }
        
        token = self.security.generate_sharing_token(share_data, expires_in)
        
        self._log_action("GENERATE_SHARE_TOKEN", credential_id, {
            "service_name": credential.service_name,
            "expires_in": expires_in
        })
        
        return token
    
    def decrypt_sharing_token(self, token: str) -> Optional[Dict]:
        """Decrypt sharing token"""
        return self.security.decrypt_sharing_token(token)
    
    def export_vault(self, export_password: str) -> Optional[str]:
        """Export encrypted vault data"""
        if not self.is_authenticated():
            return None
        
        credentials = self._load_credentials()
        
        # Create export data
        export_data = {
            "credentials": [cred.dict() for cred in credentials.values()],
            "exported_at": time.time(),
            "version": "1.0"
        }
        
        # Encrypt with export password
        from .security import SecurityManager
        export_security = SecurityManager()
        salt = export_security.generate_salt()
        key = export_security.derive_key(export_password, salt)
        
        from cryptography.fernet import Fernet
        import base64
        
        fernet = Fernet(key)
        encrypted_export = fernet.encrypt(json.dumps(export_data).encode())
        
        export_package = {
            "salt": base64.b64encode(salt).decode(),
            "data": base64.b64encode(encrypted_export).decode()
        }
        
        self._log_action("EXPORT_VAULT", details={
            "credentials_count": len(credentials)
        })
        
        return base64.b64encode(json.dumps(export_package).encode()).decode()
    
    def _log_action(self, action: str, credential_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Log user action for audit trail"""
        log_entry = AuditLog(
            action=action,
            credential_id=credential_id,
            details=details
        )
        self.audit_logs.append(log_entry)
        
        # Keep only last 1000 log entries
        if len(self.audit_logs) > 1000:
            self.audit_logs = self.audit_logs[-1000:]
    
    def get_audit_logs(self, limit: int = 100) -> List[AuditLog]:
        """Get recent audit logs"""
        if not self.is_authenticated():
            return []
        
        return self.audit_logs[-limit:]
    
    def get_vault_stats(self) -> Optional[Dict]:
        """Get vault statistics"""
        if not self.is_authenticated():
            return None
        
        credentials = self._load_credentials()
        metadata = self.security.load_vault_metadata()
        
        if not metadata:
            return None
        
        return {
            "total_credentials": len(credentials),
            "created_at": metadata.get("created_at", 0),
            "last_accessed": self.security.last_activity,
            "vault_size": os.path.getsize(self.vault_path) if os.path.exists(self.vault_path) else 0
        }
