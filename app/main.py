"""
FastAPI main application for credential manager
"""
import os
import qrcode
import io
import base64
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .models import (
    Credential, CredentialCreate, CredentialUpdate, 
    LoginRequest, CreateVaultRequest, ShareRequest, ShareResponse,
    SearchRequest, AuditLog
)
from .vault import CredentialVault
from .mobile_api import mobile_router
from .browser_extension import browser_router
from .sync_service import sync_router
from .themes import themes_router
from .hsm import initialize_hsm, get_hsm_manager

app = FastAPI(
    title="SecureVault - Enterprise Password Manager",
    description="A military-grade, self-hosted password manager with advanced features",
    version="2.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# CORS middleware for local development and mobile/browser extensions
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "chrome-extension://*",
        "moz-extension://*",
        "safari-web-extension://*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include new feature routers
app.include_router(mobile_router)
app.include_router(browser_router)
app.include_router(sync_router)
app.include_router(themes_router)

# Initialize HSM on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Initialize HSM
    hsm_config = {
        'provider': 'softhsm',
        'key_store_path': './hsm_keys'
    }
    initialize_hsm(hsm_config)
    
    # Generate master key if not exists
    hsm_manager = get_hsm_manager()
    if hsm_manager.is_available():
        hsm_manager.generate_master_key()

# Global vault instance
vault = CredentialVault()

# Dependency to check authentication
def get_authenticated_vault():
    if not vault.is_authenticated():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return vault

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application page"""
    try:
        with open("app/templates/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback to basic HTML if template not found
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>SecureVault - Loading...</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    display: flex; 
                    justify-content: center; 
                    align-items: center; 
                    height: 100vh; 
                    margin: 0; 
                    background: #0f172a; 
                    color: white; 
                }
                .loading { text-align: center; }
                .spinner { 
                    border: 4px solid #334155; 
                    border-top: 4px solid #6366f1; 
                    border-radius: 50%; 
                    width: 40px; 
                    height: 40px; 
                    animation: spin 1s linear infinite; 
                    margin: 0 auto 20px; 
                }
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            </style>
        </head>
        <body>
            <div class="loading">
                <div class="spinner"></div>
                <h2>🔐 SecureVault</h2>
                <p>Loading your secure vault...</p>
            </div>
            <script>
                setTimeout(() => {
                    location.reload();
                }, 2000);
            </script>
        </body>
        </html>
        """

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "service": "SecureVault", "version": "2.0.0"}

@app.get("/api/vault/exists")
async def vault_exists():
    """Check if vault exists"""
    return {"exists": vault.vault_exists()}

@app.post("/api/vault/create")
async def create_vault(request: CreateVaultRequest):
    """Create new vault"""
    if vault.vault_exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vault already exists"
        )
    
    if len(request.master_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Master password must be at least 8 characters long"
        )
    
    if vault.create_vault(request.master_password):
        return {"message": "Vault created successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create vault"
        )

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Authenticate user"""
    if vault.is_locked_out():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to too many failed attempts"
        )
    
    if vault.authenticate(request.master_password):
        return {"message": "Login successful"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid master password"
        )

@app.post("/api/auth/logout")
async def logout():
    """Logout user"""
    vault.logout()
    return {"message": "Logged out successfully"}

@app.get("/api/auth/status")
async def auth_status():
    """Check authentication status"""
    return {
        "authenticated": vault.is_authenticated(),
        "locked_out": vault.is_locked_out()
    }

@app.post("/api/credentials", response_model=dict)
async def add_credential(
    credential: CredentialCreate,
    vault: CredentialVault = Depends(get_authenticated_vault)
):
    """Add new credential"""
    credential_id = vault.add_credential(credential)
    if credential_id:
        return {"id": credential_id, "message": "Credential added successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add credential"
        )

@app.get("/api/credentials", response_model=List[Credential])
async def get_credentials(vault: CredentialVault = Depends(get_authenticated_vault)):
    """Get all credentials"""
    return vault.get_all_credentials()

@app.get("/api/credentials/{credential_id}", response_model=Credential)
async def get_credential(
    credential_id: str,
    vault: CredentialVault = Depends(get_authenticated_vault)
):
    """Get specific credential"""
    credential = vault.get_credential(credential_id)
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    return credential

@app.put("/api/credentials/{credential_id}")
async def update_credential(
    credential_id: str,
    update_data: CredentialUpdate,
    vault: CredentialVault = Depends(get_authenticated_vault)
):
    """Update credential"""
    if vault.update_credential(credential_id, update_data):
        return {"message": "Credential updated successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )

@app.delete("/api/credentials/{credential_id}")
async def delete_credential(
    credential_id: str,
    vault: CredentialVault = Depends(get_authenticated_vault)
):
    """Delete credential"""
    if vault.delete_credential(credential_id):
        return {"message": "Credential deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )

@app.post("/api/credentials/search", response_model=List[Credential])
async def search_credentials(
    search_request: SearchRequest,
    vault: CredentialVault = Depends(get_authenticated_vault)
):
    """Search credentials"""
    return vault.search_credentials(
        query=search_request.query,
        tags=search_request.tags
    )

@app.post("/api/credentials/share", response_model=ShareResponse)
async def share_credential(
    share_request: ShareRequest,
    vault: CredentialVault = Depends(get_authenticated_vault)
):
    """Generate sharing token for credential"""
    token = vault.generate_sharing_token(
        share_request.credential_id,
        share_request.expires_in
    )
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found"
        )
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    share_url = f"http://localhost:8000/share/{token}"
    qr.add_data(share_url)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    qr_img.save(img_buffer, format='PNG')
    qr_code_b64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    return ShareResponse(
        token=token,
        expires_at=time.time() + share_request.expires_in,
        qr_code=f"data:image/png;base64,{qr_code_b64}"
    )

@app.get("/share/{token}", response_class=HTMLResponse)
async def view_shared_credential(token: str):
    """View shared credential"""
    credential_data = vault.decrypt_sharing_token(token)
    
    if not credential_data:
        return """
        <html><body>
            <h1>Invalid or Expired Link</h1>
            <p>This sharing link is invalid or has expired.</p>
        </body></html>
        """
    
    return f"""
    <html>
    <head>
        <title>Shared Credential</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .credential {{ border: 1px solid #ddd; padding: 20px; border-radius: 4px; }}
            button {{ background: #007bff; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin-left: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Shared Credential</h1>
            <div class="credential">
                <h3>{credential_data['service_name']}</h3>
                <p><strong>Username:</strong> {credential_data['username']} 
                   <button onclick="copyToClipboard('{credential_data['username']}')">Copy</button></p>
                <p><strong>Password:</strong> <span id="password">••••••••</span> 
                   <button onclick="togglePassword()">Show</button>
                   <button onclick="copyToClipboard('{credential_data['password']}')">Copy</button></p>
                {f"<p><strong>Notes:</strong> {credential_data['notes']}</p>" if credential_data.get('notes') else ''}
            </div>
            <p><small>⚠️ This link will expire and should not be shared further.</small></p>
        </div>
        
        <script>
            let passwordVisible = false;
            const actualPassword = '{credential_data['password']}';
            
            function togglePassword() {{
                const span = document.getElementById('password');
                const button = span.nextElementSibling;
                
                if (!passwordVisible) {{
                    span.textContent = actualPassword;
                    button.textContent = 'Hide';
                    passwordVisible = true;
                    
                    // Auto-hide after 10 seconds
                    setTimeout(() => {{
                        span.textContent = '••••••••';
                        button.textContent = 'Show';
                        passwordVisible = false;
                    }}, 10000);
                }} else {{
                    span.textContent = '••••••••';
                    button.textContent = 'Show';
                    passwordVisible = false;
                }}
            }}
            
            function copyToClipboard(text) {{
                navigator.clipboard.writeText(text).then(() => {{
                    alert('Copied to clipboard!');
                    
                    // Clear clipboard after 30 seconds
                    setTimeout(() => {{
                        navigator.clipboard.writeText('');
                    }}, 30000);
                }});
            }}
        </script>
    </body>
    </html>
    """

@app.get("/api/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(
    limit: int = 100,
    vault: CredentialVault = Depends(get_authenticated_vault)
):
    """Get audit logs"""
    return vault.get_audit_logs(limit)

@app.get("/api/vault/stats")
async def get_vault_stats(vault: CredentialVault = Depends(get_authenticated_vault)):
    """Get vault statistics"""
    stats = vault.get_vault_stats()
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get vault statistics"
        )
    return stats

@app.post("/api/vault/export")
async def export_vault(
    export_password: str,
    vault: CredentialVault = Depends(get_authenticated_vault)
):
    """Export vault data"""
    export_data = vault.export_vault(export_password)
    if not export_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export vault"
        )
    
    return {
        "export_data": export_data,
        "message": "Vault exported successfully"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
