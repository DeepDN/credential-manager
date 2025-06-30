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
from fastapi.responses import HTMLResponse, JSONResponse
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
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Secure Credential Manager</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, textarea, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .credential-item { border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 4px; }
            .hidden { display: none; }
            .error { color: red; margin-top: 10px; }
            .success { color: green; margin-top: 10px; }
            .logout-btn { float: right; background: #dc3545; }
            .logout-btn:hover { background: #c82333; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Secure Credential Manager</h1>
                <button id="logoutBtn" class="logout-btn hidden" onclick="logout()">Logout</button>
            </div>
            
            <!-- Login/Setup Screen -->
            <div id="authScreen">
                <div id="loginForm">
                    <h2>Login</h2>
                    <div class="form-group">
                        <label>Master Password:</label>
                        <input type="password" id="loginPassword" placeholder="Enter your master password">
                    </div>
                    <button onclick="login()">Login</button>
                    <div id="loginError" class="error hidden"></div>
                </div>
                
                <div id="setupForm" class="hidden">
                    <h2>Create New Vault</h2>
                    <div class="form-group">
                        <label>Master Password:</label>
                        <input type="password" id="setupPassword" placeholder="Choose a strong master password">
                    </div>
                    <div class="form-group">
                        <label>Confirm Password:</label>
                        <input type="password" id="confirmPassword" placeholder="Confirm your master password">
                    </div>
                    <button onclick="createVault()">Create Vault</button>
                    <div id="setupError" class="error hidden"></div>
                </div>
                
                <p style="text-align: center; margin-top: 20px;">
                    <a href="#" onclick="toggleSetup()">Need to create a new vault?</a>
                </p>
            </div>
            
            <!-- Main Application -->
            <div id="mainApp" class="hidden">
                <div style="margin-bottom: 20px;">
                    <h2>Add New Credential</h2>
                    <div class="form-group">
                        <label>Service/Application Name:</label>
                        <input type="text" id="serviceName" placeholder="e.g., Gmail, GitHub, AWS">
                    </div>
                    <div class="form-group">
                        <label>Username/Email:</label>
                        <input type="text" id="username" placeholder="username or email">
                    </div>
                    <div class="form-group">
                        <label>Password/API Key:</label>
                        <input type="password" id="password" placeholder="password or API key">
                    </div>
                    <div class="form-group">
                        <label>Notes (optional):</label>
                        <textarea id="notes" placeholder="Additional notes or remarks"></textarea>
                    </div>
                    <div class="form-group">
                        <label>Tags (comma-separated):</label>
                        <input type="text" id="tags" placeholder="work, personal, api">
                    </div>
                    <button onclick="addCredential()">Add Credential</button>
                    <div id="addError" class="error hidden"></div>
                    <div id="addSuccess" class="success hidden"></div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h2>Search Credentials</h2>
                    <div class="form-group">
                        <input type="text" id="searchQuery" placeholder="Search by service name, username, or notes">
                        <button onclick="searchCredentials()" style="margin-top: 10px;">Search</button>
                        <button onclick="loadAllCredentials()" style="margin-left: 10px;">Show All</button>
                    </div>
                </div>
                
                <div id="credentialsList">
                    <h2>Your Credentials</h2>
                    <div id="credentials"></div>
                </div>
            </div>
        </div>
        
        <script>
            let isAuthenticated = false;
            
            // Check if vault exists on page load
            window.onload = async function() {
                try {
                    const response = await fetch('/api/vault/exists');
                    const data = await response.json();
                    if (!data.exists) {
                        toggleSetup();
                    }
                } catch (error) {
                    console.error('Error checking vault:', error);
                }
            };
            
            function toggleSetup() {
                const loginForm = document.getElementById('loginForm');
                const setupForm = document.getElementById('setupForm');
                
                if (loginForm.classList.contains('hidden')) {
                    loginForm.classList.remove('hidden');
                    setupForm.classList.add('hidden');
                } else {
                    loginForm.classList.add('hidden');
                    setupForm.classList.remove('hidden');
                }
            }
            
            async function createVault() {
                const password = document.getElementById('setupPassword').value;
                const confirmPassword = document.getElementById('confirmPassword').value;
                const errorDiv = document.getElementById('setupError');
                
                if (password !== confirmPassword) {
                    errorDiv.textContent = 'Passwords do not match';
                    errorDiv.classList.remove('hidden');
                    return;
                }
                
                if (password.length < 8) {
                    errorDiv.textContent = 'Password must be at least 8 characters long';
                    errorDiv.classList.remove('hidden');
                    return;
                }
                
                try {
                    const response = await fetch('/api/vault/create', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ master_password: password })
                    });
                    
                    if (response.ok) {
                        alert('Vault created successfully! You can now login.');
                        toggleSetup();
                    } else {
                        const error = await response.json();
                        errorDiv.textContent = error.detail || 'Failed to create vault';
                        errorDiv.classList.remove('hidden');
                    }
                } catch (error) {
                    errorDiv.textContent = 'Network error occurred';
                    errorDiv.classList.remove('hidden');
                }
            }
            
            async function login() {
                const password = document.getElementById('loginPassword').value;
                const errorDiv = document.getElementById('loginError');
                
                try {
                    const response = await fetch('/api/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ master_password: password })
                    });
                    
                    if (response.ok) {
                        isAuthenticated = true;
                        document.getElementById('authScreen').classList.add('hidden');
                        document.getElementById('mainApp').classList.remove('hidden');
                        document.getElementById('logoutBtn').classList.remove('hidden');
                        loadAllCredentials();
                    } else {
                        const error = await response.json();
                        errorDiv.textContent = error.detail || 'Login failed';
                        errorDiv.classList.remove('hidden');
                    }
                } catch (error) {
                    errorDiv.textContent = 'Network error occurred';
                    errorDiv.classList.remove('hidden');
                }
            }
            
            function logout() {
                fetch('/api/auth/logout', { method: 'POST' });
                isAuthenticated = false;
                document.getElementById('authScreen').classList.remove('hidden');
                document.getElementById('mainApp').classList.add('hidden');
                document.getElementById('logoutBtn').classList.add('hidden');
                document.getElementById('credentials').innerHTML = '';
            }
            
            async function addCredential() {
                const serviceName = document.getElementById('serviceName').value;
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const notes = document.getElementById('notes').value;
                const tags = document.getElementById('tags').value.split(',').map(t => t.trim()).filter(t => t);
                
                const errorDiv = document.getElementById('addError');
                const successDiv = document.getElementById('addSuccess');
                
                if (!serviceName || !username || !password) {
                    errorDiv.textContent = 'Service name, username, and password are required';
                    errorDiv.classList.remove('hidden');
                    successDiv.classList.add('hidden');
                    return;
                }
                
                try {
                    const response = await fetch('/api/credentials', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            service_name: serviceName,
                            username: username,
                            password: password,
                            notes: notes,
                            tags: tags
                        })
                    });
                    
                    if (response.ok) {
                        successDiv.textContent = 'Credential added successfully!';
                        successDiv.classList.remove('hidden');
                        errorDiv.classList.add('hidden');
                        
                        // Clear form
                        document.getElementById('serviceName').value = '';
                        document.getElementById('username').value = '';
                        document.getElementById('password').value = '';
                        document.getElementById('notes').value = '';
                        document.getElementById('tags').value = '';
                        
                        loadAllCredentials();
                    } else {
                        const error = await response.json();
                        errorDiv.textContent = error.detail || 'Failed to add credential';
                        errorDiv.classList.remove('hidden');
                        successDiv.classList.add('hidden');
                    }
                } catch (error) {
                    errorDiv.textContent = 'Network error occurred';
                    errorDiv.classList.remove('hidden');
                    successDiv.classList.add('hidden');
                }
            }
            
            async function loadAllCredentials() {
                try {
                    const response = await fetch('/api/credentials');
                    if (response.ok) {
                        const credentials = await response.json();
                        displayCredentials(credentials);
                    }
                } catch (error) {
                    console.error('Error loading credentials:', error);
                }
            }
            
            async function searchCredentials() {
                const query = document.getElementById('searchQuery').value;
                
                try {
                    const response = await fetch('/api/credentials/search', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: query })
                    });
                    
                    if (response.ok) {
                        const credentials = await response.json();
                        displayCredentials(credentials);
                    }
                } catch (error) {
                    console.error('Error searching credentials:', error);
                }
            }
            
            function displayCredentials(credentials) {
                const container = document.getElementById('credentials');
                
                if (credentials.length === 0) {
                    container.innerHTML = '<p>No credentials found.</p>';
                    return;
                }
                
                container.innerHTML = credentials.map(cred => `
                    <div class="credential-item">
                        <h3>${cred.service_name}</h3>
                        <p><strong>Username:</strong> ${cred.username}</p>
                        <p><strong>Password:</strong> <span id="pwd-${cred.id}">••••••••</span> 
                           <button onclick="togglePassword('${cred.id}', '${cred.password}')">Show</button>
                           <button onclick="copyToClipboard('${cred.password}')">Copy</button>
                        </p>
                        ${cred.notes ? `<p><strong>Notes:</strong> ${cred.notes}</p>` : ''}
                        ${cred.tags.length > 0 ? `<p><strong>Tags:</strong> ${cred.tags.join(', ')}</p>` : ''}
                        <p><small>Created: ${new Date(cred.created_at * 1000).toLocaleString()}</small></p>
                        <button onclick="deleteCredential('${cred.id}')" style="background: #dc3545;">Delete</button>
                        <button onclick="shareCredential('${cred.id}')" style="background: #28a745;">Share</button>
                    </div>
                `).join('');
            }
            
            function togglePassword(credId, password) {
                const span = document.getElementById(`pwd-${credId}`);
                const button = span.nextElementSibling;
                
                if (span.textContent === '••••••••') {
                    span.textContent = password;
                    button.textContent = 'Hide';
                    
                    // Auto-hide after 10 seconds
                    setTimeout(() => {
                        span.textContent = '••••••••';
                        button.textContent = 'Show';
                    }, 10000);
                } else {
                    span.textContent = '••••••••';
                    button.textContent = 'Show';
                }
            }
            
            function copyToClipboard(text) {
                navigator.clipboard.writeText(text).then(() => {
                    alert('Copied to clipboard!');
                    
                    // Clear clipboard after 30 seconds
                    setTimeout(() => {
                        navigator.clipboard.writeText('');
                    }, 30000);
                });
            }
            
            async function deleteCredential(credId) {
                if (!confirm('Are you sure you want to delete this credential?')) {
                    return;
                }
                
                try {
                    const response = await fetch(`/api/credentials/${credId}`, {
                        method: 'DELETE'
                    });
                    
                    if (response.ok) {
                        loadAllCredentials();
                    } else {
                        alert('Failed to delete credential');
                    }
                } catch (error) {
                    alert('Error deleting credential');
                }
            }
            
            async function shareCredential(credId) {
                const expiresIn = prompt('Enter expiration time in minutes (default: 60):', '60');
                if (!expiresIn) return;
                
                try {
                    const response = await fetch('/api/credentials/share', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            credential_id: credId,
                            expires_in: parseInt(expiresIn) * 60
                        })
                    });
                    
                    if (response.ok) {
                        const shareData = await response.json();
                        const shareUrl = `${window.location.origin}/share/${shareData.token}`;
                        
                        prompt('Share this URL (expires in ' + expiresIn + ' minutes):', shareUrl);
                    } else {
                        alert('Failed to generate share link');
                    }
                } catch (error) {
                    alert('Error generating share link');
                }
            }
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
