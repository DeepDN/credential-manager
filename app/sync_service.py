"""
Self-hosted Sync Service for SecureVault
Provides secure synchronization between multiple devices
"""
import os
import json
import time
import hashlib
import asyncio
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel
from cryptography.fernet import Fernet
import sqlite3
from datetime import datetime, timedelta

# Sync API Router
sync_router = APIRouter(prefix="/api/sync", tags=["sync"])

class SyncDevice(BaseModel):
    device_id: str
    device_name: str
    device_type: str  # "desktop", "mobile", "browser"
    platform: str
    last_sync: Optional[str] = None
    sync_key: str

class SyncData(BaseModel):
    device_id: str
    vault_hash: str
    encrypted_data: str
    timestamp: str
    changes: List[Dict[str, Any]]

class SyncRequest(BaseModel):
    device_id: str
    last_sync_timestamp: Optional[str] = None
    vault_hash: str

class SyncResponse(BaseModel):
    has_updates: bool
    encrypted_data: Optional[str] = None
    vault_hash: Optional[str] = None
    timestamp: str
    conflicts: List[Dict[str, Any]] = []

class ConflictResolution(BaseModel):
    conflict_id: str
    resolution: str  # "local", "remote", "merge"
    merged_data: Optional[Dict[str, Any]] = None

class SyncDatabase:
    """SQLite database for sync operations"""
    
    def __init__(self, db_path: str = "./sync.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize sync database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Devices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                device_name TEXT NOT NULL,
                device_type TEXT NOT NULL,
                platform TEXT NOT NULL,
                sync_key TEXT NOT NULL,
                last_sync TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Sync data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                vault_hash TEXT NOT NULL,
                encrypted_data TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                changes TEXT,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        ''')
        
        # Conflicts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id_1 TEXT NOT NULL,
                device_id_2 TEXT NOT NULL,
                conflict_type TEXT NOT NULL,
                conflict_data TEXT NOT NULL,
                resolved BOOLEAN DEFAULT FALSE,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def register_device(self, device: SyncDevice) -> bool:
        """Register a new sync device"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            cursor.execute('''
                INSERT OR REPLACE INTO devices 
                (device_id, device_name, device_type, platform, sync_key, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (device.device_id, device.device_name, device.device_type, 
                  device.platform, device.sync_key, now, now))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Failed to register device: {e}")
            return False
            
    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM devices WHERE device_id = ?', (device_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return {
                    'device_id': row[0],
                    'device_name': row[1],
                    'device_type': row[2],
                    'platform': row[3],
                    'sync_key': row[4],
                    'last_sync': row[5],
                    'created_at': row[6],
                    'updated_at': row[7]
                }
            return None
            
        except Exception as e:
            print(f"Failed to get device: {e}")
            return None
            
    def store_sync_data(self, sync_data: SyncData) -> bool:
        """Store sync data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sync_data 
                (device_id, vault_hash, encrypted_data, timestamp, changes)
                VALUES (?, ?, ?, ?, ?)
            ''', (sync_data.device_id, sync_data.vault_hash, sync_data.encrypted_data,
                  sync_data.timestamp, json.dumps(sync_data.changes)))
            
            # Update device last sync
            cursor.execute('''
                UPDATE devices SET last_sync = ?, updated_at = ?
                WHERE device_id = ?
            ''', (sync_data.timestamp, datetime.now().isoformat(), sync_data.device_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Failed to store sync data: {e}")
            return False
            
    def get_latest_sync_data(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get latest sync data for device"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM sync_data 
                WHERE device_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (device_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'device_id': row[1],
                    'vault_hash': row[2],
                    'encrypted_data': row[3],
                    'timestamp': row[4],
                    'changes': json.loads(row[5]) if row[5] else []
                }
            return None
            
        except Exception as e:
            print(f"Failed to get sync data: {e}")
            return None

class SyncManager:
    """Manage sync operations"""
    
    def __init__(self):
        self.db = SyncDatabase()
        self.encryption_key = self._get_or_create_sync_key()
        self.fernet = Fernet(self.encryption_key)
        
    def _get_or_create_sync_key(self) -> bytes:
        """Get or create sync encryption key"""
        key_file = "./sync_key.key"
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
            
    def register_device(self, device: SyncDevice) -> bool:
        """Register device for sync"""
        return self.db.register_device(device)
        
    def encrypt_vault_data(self, vault_data: str) -> str:
        """Encrypt vault data for sync"""
        encrypted = self.fernet.encrypt(vault_data.encode())
        return encrypted.decode()
        
    def decrypt_vault_data(self, encrypted_data: str) -> str:
        """Decrypt vault data from sync"""
        decrypted = self.fernet.decrypt(encrypted_data.encode())
        return decrypted.decode()
        
    def calculate_vault_hash(self, vault_data: str) -> str:
        """Calculate hash of vault data"""
        return hashlib.sha256(vault_data.encode()).hexdigest()
        
    def detect_conflicts(self, device_id: str, vault_hash: str) -> List[Dict[str, Any]]:
        """Detect sync conflicts"""
        conflicts = []
        
        # Get latest sync data for this device
        latest_sync = self.db.get_latest_sync_data(device_id)
        if latest_sync and latest_sync['vault_hash'] != vault_hash:
            conflicts.append({
                'type': 'vault_mismatch',
                'device_id': device_id,
                'local_hash': vault_hash,
                'remote_hash': latest_sync['vault_hash'],
                'timestamp': latest_sync['timestamp']
            })
            
        return conflicts
        
    def sync_vault_data(self, device_id: str, vault_data: str, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync vault data"""
        try:
            # Calculate hash
            vault_hash = self.calculate_vault_hash(vault_data)
            
            # Encrypt data
            encrypted_data = self.encrypt_vault_data(vault_data)
            
            # Store sync data
            sync_data = SyncData(
                device_id=device_id,
                vault_hash=vault_hash,
                encrypted_data=encrypted_data,
                timestamp=datetime.now().isoformat(),
                changes=changes
            )
            
            success = self.db.store_sync_data(sync_data)
            
            return {
                'success': success,
                'vault_hash': vault_hash,
                'timestamp': sync_data.timestamp
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global sync manager
sync_manager = SyncManager()

def get_sync_device(device_id: str) -> Dict[str, Any]:
    """Get and verify sync device"""
    device = sync_manager.db.get_device(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not registered for sync"
        )
    return device

@sync_router.post("/register")
async def register_sync_device(device: SyncDevice):
    """Register device for sync"""
    try:
        success = sync_manager.register_device(device)
        if success:
            return {"status": "registered", "device_id": device.device_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register device"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@sync_router.post("/upload")
async def upload_sync_data(
    device_id: str,
    vault_data: str,
    changes: List[Dict[str, Any]] = []
):
    """Upload vault data for sync"""
    try:
        # Verify device
        device = get_sync_device(device_id)
        
        # Sync data
        result = sync_manager.sync_vault_data(device_id, vault_data, changes)
        
        if result['success']:
            return {
                "status": "uploaded",
                "vault_hash": result['vault_hash'],
                "timestamp": result['timestamp']
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Upload failed')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@sync_router.post("/download", response_model=SyncResponse)
async def download_sync_data(sync_request: SyncRequest):
    """Download latest vault data"""
    try:
        # Verify device
        device = get_sync_device(sync_request.device_id)
        
        # Get latest sync data
        latest_sync = sync_manager.db.get_latest_sync_data(sync_request.device_id)
        
        if not latest_sync:
            return SyncResponse(
                has_updates=False,
                timestamp=datetime.now().isoformat()
            )
        
        # Check if there are updates
        has_updates = (
            not sync_request.last_sync_timestamp or 
            latest_sync['timestamp'] > sync_request.last_sync_timestamp or
            latest_sync['vault_hash'] != sync_request.vault_hash
        )
        
        if has_updates:
            # Decrypt data
            decrypted_data = sync_manager.decrypt_vault_data(latest_sync['encrypted_data'])
            
            # Detect conflicts
            conflicts = sync_manager.detect_conflicts(sync_request.device_id, sync_request.vault_hash)
            
            return SyncResponse(
                has_updates=True,
                encrypted_data=latest_sync['encrypted_data'],
                vault_hash=latest_sync['vault_hash'],
                timestamp=latest_sync['timestamp'],
                conflicts=conflicts
            )
        else:
            return SyncResponse(
                has_updates=False,
                timestamp=latest_sync['timestamp']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )

@sync_router.get("/status/{device_id}")
async def get_sync_status(device_id: str):
    """Get sync status for device"""
    try:
        device = get_sync_device(device_id)
        latest_sync = sync_manager.db.get_latest_sync_data(device_id)
        
        return {
            "device_id": device_id,
            "device_name": device['device_name'],
            "last_sync": device['last_sync'],
            "has_data": latest_sync is not None,
            "vault_hash": latest_sync['vault_hash'] if latest_sync else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status check failed: {str(e)}"
        )

@sync_router.delete("/device/{device_id}")
async def unregister_sync_device(device_id: str):
    """Unregister device from sync"""
    try:
        # Verify device exists
        device = get_sync_device(device_id)
        
        # Remove device and its sync data
        conn = sqlite3.connect(sync_manager.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM sync_data WHERE device_id = ?', (device_id,))
        cursor.execute('DELETE FROM devices WHERE device_id = ?', (device_id,))
        
        conn.commit()
        conn.close()
        
        return {"status": "unregistered", "device_id": device_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unregistration failed: {str(e)}"
        )

@sync_router.get("/devices")
async def list_sync_devices():
    """List all registered sync devices"""
    try:
        conn = sqlite3.connect(sync_manager.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT device_id, device_name, device_type, platform, last_sync FROM devices')
        rows = cursor.fetchall()
        
        conn.close()
        
        devices = []
        for row in rows:
            devices.append({
                'device_id': row[0],
                'device_name': row[1],
                'device_type': row[2],
                'platform': row[3],
                'last_sync': row[4]
            })
            
        return {"devices": devices}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list devices: {str(e)}"
        )
