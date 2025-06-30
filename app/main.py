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
        <html lang="en">
        <head>
            <title>SecureVault - Loading...</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <style>
                body { 
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex; 
                    flex-direction: column;
                    justify-content: center; 
                    align-items: center; 
                    height: 100vh; 
                    margin: 0; 
                    background: #0f172a; 
                    color: white;
                    background-image: 
                        radial-gradient(circle at 25% 25%, rgba(99, 102, 241, 0.1) 0%, transparent 50%),
                        radial-gradient(circle at 75% 75%, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
                }
                .loading { 
                    text-align: center; 
                    background: #1e293b;
                    padding: 3rem;
                    border-radius: 16px;
                    border: 1px solid #475569;
                    box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1);
                }
                .spinner { 
                    border: 4px solid #334155; 
                    border-top: 4px solid #6366f1; 
                    border-radius: 50%; 
                    width: 40px; 
                    height: 40px; 
                    animation: spin 1s linear infinite; 
                    margin: 0 auto 20px; 
                }
                .title {
                    font-size: 2rem;
                    font-weight: 700;
                    margin-bottom: 0.5rem;
                    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }
                .subtitle {
                    color: #cbd5e1;
                    margin-bottom: 2rem;
                }
                .creator-credit {
                    margin-top: 2rem;
                    padding-top: 2rem;
                    border-top: 1px solid #475569;
                    color: #94a3b8;
                    font-size: 0.875rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                }
                .creator-credit strong {
                    color: #6366f1;
                    font-weight: 600;
                }
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            </style>
        </head>
        <body>
            <div class="loading">
                <div class="spinner"></div>
                <h2 class="title">🔐 SecureVault</h2>
                <p class="subtitle">Loading your secure vault...</p>
                <div class="creator-credit">
                    Created by <strong>Deepak Nemade</strong>
                </div>
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
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Invalid Link - SecureVault</title>
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <style>
                :root {
                    --primary-color: #6366f1;
                    --dark-bg: #0f172a;
                    --card-bg: #1e293b;
                    --text-primary: #f8fafc;
                    --text-secondary: #cbd5e1;
                    --border-color: #475569;
                    --error-color: #ef4444;
                }
                
                * { margin: 0; padding: 0; box-sizing: border-box; }
                
                body {
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: var(--dark-bg);
                    color: var(--text-primary);
                    line-height: 1.6;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background-image: 
                        radial-gradient(circle at 25% 25%, rgba(99, 102, 241, 0.1) 0%, transparent 50%),
                        radial-gradient(circle at 75% 75%, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
                }
                
                .container {
                    max-width: 500px;
                    margin: 2rem;
                    background: var(--card-bg);
                    padding: 3rem 2rem;
                    border-radius: 16px;
                    box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
                    border: 1px solid var(--border-color);
                    text-align: center;
                }
                
                .error-icon {
                    font-size: 4rem;
                    color: var(--error-color);
                    margin-bottom: 1.5rem;
                }
                
                .title {
                    font-size: 1.75rem;
                    font-weight: 700;
                    margin-bottom: 1rem;
                    color: var(--text-primary);
                }
                
                .message {
                    color: var(--text-secondary);
                    margin-bottom: 2rem;
                    font-size: 1.1rem;
                }
                
                .footer {
                    margin-top: 2rem;
                    padding-top: 2rem;
                    border-top: 1px solid var(--border-color);
                    color: var(--text-secondary);
                    font-size: 0.875rem;
                }
                
                .creator-credit {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                    margin-top: 1rem;
                }
                
                .creator-credit strong {
                    color: var(--primary-color);
                    font-weight: 600;
                }
                
                .creator-credit i {
                    color: var(--primary-color);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h1 class="title">Invalid or Expired Link</h1>
                <p class="message">This sharing link is invalid or has expired for security reasons.</p>
                
                <div class="footer">
                    <p>Powered by SecureVault - Enterprise Password Manager</p>
                    <div class="creator-credit">
                        <i class="fas fa-code"></i>
                        Created by <strong>Deepak Nemade</strong>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    return f"""
    <html>
    <head>
        <title>Shared Credential - SecureVault</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --primary-color: #6366f1;
                --dark-bg: #0f172a;
                --card-bg: #1e293b;
                --surface-bg: #334155;
                --text-primary: #f8fafc;
                --text-secondary: #cbd5e1;
                --border-color: #475569;
                --success-color: #10b981;
                --warning-color: #f59e0b;
            }}
            
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{ 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--dark-bg);
                color: var(--text-primary);
                line-height: 1.6;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                background-image: 
                    radial-gradient(circle at 25% 25%, rgba(99, 102, 241, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 75% 75%, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
            }}
            
            .container {{ 
                max-width: 500px; 
                margin: 2rem auto; 
                background: var(--card-bg); 
                padding: 2rem; 
                border-radius: 16px; 
                box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
                border: 1px solid var(--border-color);
                backdrop-filter: blur(10px);
                flex: 1;
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 2rem;
            }}
            
            .title {{
                font-size: 1.75rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                background: linear-gradient(135deg, var(--primary-color) 0%, #8b5cf6 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}
            
            .subtitle {{
                color: var(--text-secondary);
                font-size: 0.875rem;
            }}
            
            .credential {{ 
                background: var(--surface-bg);
                border: 1px solid var(--border-color); 
                padding: 1.5rem; 
                border-radius: 12px; 
                margin-bottom: 1.5rem;
            }}
            
            .credential h3 {{
                color: var(--text-primary);
                margin-bottom: 1rem;
                font-size: 1.25rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .field {{
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 0.5rem;
            }}
            
            .field-label {{
                font-weight: 500;
                color: var(--text-secondary);
            }}
            
            .field-value {{
                color: var(--text-primary);
                font-family: monospace;
                background: rgba(99, 102, 241, 0.1);
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                flex: 1;
                min-width: 0;
            }}
            
            .btn {{ 
                background: var(--primary-color); 
                color: white; 
                padding: 0.5rem 1rem; 
                border: none; 
                border-radius: 6px; 
                cursor: pointer; 
                font-size: 0.875rem;
                font-weight: 500;
                transition: all 0.2s ease;
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .btn:hover {{ 
                background: #4f46e5;
                transform: translateY(-1px);
            }}
            
            .btn-secondary {{
                background: var(--surface-bg);
                border: 1px solid var(--border-color);
            }}
            
            .btn-secondary:hover {{
                background: var(--card-bg);
            }}
            
            .warning {{
                background: rgba(245, 158, 11, 0.1);
                border: 1px solid rgba(245, 158, 11, 0.2);
                color: #fbbf24;
                padding: 1rem;
                border-radius: 8px;
                font-size: 0.875rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 2rem;
                padding-top: 2rem;
                border-top: 1px solid var(--border-color);
                color: var(--text-secondary);
                font-size: 0.875rem;
            }}
            
            .creator-credit {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
                margin-top: 1rem;
            }}
            
            .creator-credit strong {{
                color: var(--primary-color);
                font-weight: 600;
            }}
            
            .creator-credit i {{
                color: var(--primary-color);
            }}
            
            @media (max-width: 768px) {{
                .container {{ margin: 1rem; padding: 1.5rem; }}
                .field {{ flex-direction: column; align-items: flex-start; }}
                .field-value {{ width: 100%; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="title">
                    <i class="fas fa-share-alt"></i>
                    Shared Credential
                </h1>
                <p class="subtitle">Securely shared via SecureVault</p>
            </div>
            
            <div class="credential">
                <h3>
                    <i class="fas fa-globe"></i>
                    {credential_data['service_name']}
                </h3>
                
                <div class="field">
                    <span class="field-label">Username:</span>
                    <span class="field-value">{credential_data['username']}</span>
                    <button class="btn btn-secondary" onclick="copyToClipboard('{credential_data['username']}')">
                        <i class="fas fa-copy"></i> Copy
                    </button>
                </div>
                
                <div class="field">
                    <span class="field-label">Password:</span>
                    <span class="field-value" id="password">••••••••</span>
                    <button class="btn btn-secondary" onclick="togglePassword()">
                        <i class="fas fa-eye" id="toggleIcon"></i> Show
                    </button>
                    <button class="btn" onclick="copyToClipboard('{credential_data['password']}')">
                        <i class="fas fa-copy"></i> Copy
                    </button>
                </div>
                
                {f'<div class="field"><span class="field-label">Notes:</span><span class="field-value">{credential_data["notes"]}</span></div>' if credential_data.get('notes') else ''}
            </div>
            
            <div class="warning">
                <i class="fas fa-exclamation-triangle"></i>
                This link will expire and should not be shared further for security reasons.
            </div>
            
            <div class="footer">
                <p>Powered by SecureVault - Enterprise Password Manager</p>
                <div class="creator-credit">
                    <i class="fas fa-code"></i>
                    Created by <strong>Deepak Nemade</strong>
                </div>
            </div>
        </div>
        
        <script>
            let passwordVisible = false;
            const actualPassword = '{credential_data['password']}';
            
            function togglePassword() {{
                const span = document.getElementById('password');
                const icon = document.getElementById('toggleIcon');
                const button = span.nextElementSibling;
                
                if (!passwordVisible) {{
                    span.textContent = actualPassword;
                    button.innerHTML = '<i class="fas fa-eye-slash" id="toggleIcon"></i> Hide';
                    passwordVisible = true;
                    
                    // Auto-hide after 10 seconds
                    setTimeout(() => {{
                        if (passwordVisible) {{
                            span.textContent = '••••••••';
                            button.innerHTML = '<i class="fas fa-eye" id="toggleIcon"></i> Show';
                            passwordVisible = false;
                        }}
                    }}, 10000);
                }} else {{
                    span.textContent = '••••••••';
                    button.innerHTML = '<i class="fas fa-eye" id="toggleIcon"></i> Show';
                    passwordVisible = false;
                }}
            }}
            
            function copyToClipboard(text) {{
                navigator.clipboard.writeText(text).then(() => {{
                    // Show success message
                    const originalText = event.target.innerHTML;
                    event.target.innerHTML = '<i class="fas fa-check"></i> Copied!';
                    event.target.style.background = 'var(--success-color)';
                    
                    setTimeout(() => {{
                        event.target.innerHTML = originalText;
                        event.target.style.background = '';
                    }}, 2000);
                    
                    // Clear clipboard after 30 seconds for security
                    setTimeout(() => {{
                        navigator.clipboard.writeText('');
                    }}, 30000);
                }}).catch(() => {{
                    // Fallback for older browsers
                    const textArea = document.createElement('textarea');
                    textArea.value = text;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    
                    const originalText = event.target.innerHTML;
                    event.target.innerHTML = '<i class="fas fa-check"></i> Copied!';
                    event.target.style.background = 'var(--success-color)';
                    
                    setTimeout(() => {{
                        event.target.innerHTML = originalText;
                        event.target.style.background = '';
                    }}, 2000);
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
