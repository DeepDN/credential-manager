// SecureVault Browser Extension - Popup Script

class SecureVaultExtension {
    constructor() {
        this.apiBase = 'http://localhost:8000/api/browser';
        this.sessionToken = null;
        this.currentTab = null;
        this.init();
    }
    
    async init() {
        // Get current tab
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        this.currentTab = tabs[0];
        
        // Check if already authenticated
        const stored = await chrome.storage.local.get(['sessionToken']);
        if (stored.sessionToken) {
            this.sessionToken = stored.sessionToken;
            await this.showMainApp();
        }
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Login button
        document.getElementById('loginBtn').addEventListener('click', () => this.authenticate());
        
        // Enter key on password field
        document.getElementById('masterPassword').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.authenticate();
            }
        });
        
        // Search input
        document.getElementById('searchInput').addEventListener('input', (e) => {
            this.searchCredentials(e.target.value);
        });
        
        // Generate password button
        document.getElementById('generateBtn').addEventListener('click', () => this.generatePassword());
    }
    
    async authenticate() {
        const password = document.getElementById('masterPassword').value;
        const loginBtn = document.getElementById('loginBtn');
        const errorDiv = document.getElementById('authError');
        
        if (!password) {
            this.showError('Please enter your master password', 'authError');
            return;
        }
        
        loginBtn.disabled = true;
        loginBtn.textContent = 'Authenticating...';
        errorDiv.classList.add('hidden');
        
        try {
            const response = await fetch(`${this.apiBase}/auth`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    master_password: password,
                    extension_id: chrome.runtime.id,
                    browser: 'chrome',
                    origin: this.currentTab.url
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.sessionToken = data.session_token;
                
                // Store session token
                await chrome.storage.local.set({ sessionToken: this.sessionToken });
                
                await this.showMainApp();
            } else {
                const error = await response.json();
                this.showError(error.detail || 'Authentication failed', 'authError');
            }
        } catch (error) {
            this.showError('Connection failed. Make sure SecureVault is running.', 'authError');
        } finally {
            loginBtn.disabled = false;
            loginBtn.textContent = 'Unlock Vault';
        }
    }
    
    async showMainApp() {
        document.getElementById('authScreen').classList.add('hidden');
        document.getElementById('mainApp').classList.remove('hidden');
        
        await this.loadCredentials();
    }
    
    async loadCredentials() {
        const credentialsList = document.getElementById('credentialsList');
        const emptyState = document.getElementById('emptyState');
        
        try {
            const domain = new URL(this.currentTab.url).hostname;
            
            const response = await fetch(`${this.apiBase}/credentials/search?domain=${encodeURIComponent(domain)}`, {
                headers: {
                    'X-Session-Token': this.sessionToken
                }
            });
            
            if (response.ok) {
                const credentials = await response.json();
                this.displayCredentials(credentials);
            } else if (response.status === 401) {
                // Session expired
                await this.logout();
            } else {
                throw new Error('Failed to load credentials');
            }
        } catch (error) {
            credentialsList.innerHTML = '<div class="error">Failed to load credentials</div>';
        }
    }
    
    displayCredentials(credentials) {
        const credentialsList = document.getElementById('credentialsList');
        const emptyState = document.getElementById('emptyState');
        
        if (credentials.length === 0) {
            credentialsList.classList.add('hidden');
            emptyState.classList.remove('hidden');
            return;
        }
        
        credentialsList.classList.remove('hidden');
        emptyState.classList.add('hidden');
        
        credentialsList.innerHTML = credentials.map(cred => `
            <div class="credential-item" data-id="${cred.id}">
                <div class="credential-service">${this.escapeHtml(cred.service)}</div>
                <div class="credential-username">${this.escapeHtml(cred.username)}</div>
            </div>
        `).join('');
        
        // Add click listeners
        credentialsList.querySelectorAll('.credential-item').forEach(item => {
            item.addEventListener('click', () => {
                const credId = item.dataset.id;
                const credential = credentials.find(c => c.id === credId);
                this.fillCredential(credential);
            });
        });
    }
    
    async fillCredential(credential) {
        try {
            // Send message to content script to fill the form
            await chrome.tabs.sendMessage(this.currentTab.id, {
                action: 'fillCredential',
                credential: {
                    username: credential.username,
                    password: credential.password
                }
            });
            
            // Close popup
            window.close();
        } catch (error) {
            console.error('Failed to fill credential:', error);
        }
    }
    
    async generatePassword() {
        const generateBtn = document.getElementById('generateBtn');
        
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';
        
        try {
            const response = await fetch(`${this.apiBase}/generate-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Session-Token': this.sessionToken
                },
                body: JSON.stringify({
                    length: 16,
                    include_symbols: true,
                    include_numbers: true,
                    include_uppercase: true,
                    include_lowercase: true,
                    exclude_ambiguous: true
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Copy to clipboard
                await navigator.clipboard.writeText(data.password);
                
                // Send to content script to fill password field
                await chrome.tabs.sendMessage(this.currentTab.id, {
                    action: 'fillPassword',
                    password: data.password
                });
                
                // Show success message
                generateBtn.textContent = 'Copied!';
                setTimeout(() => {
                    generateBtn.textContent = 'Generate Password';
                }, 2000);
                
            } else {
                throw new Error('Failed to generate password');
            }
        } catch (error) {
            console.error('Password generation failed:', error);
            generateBtn.textContent = 'Failed';
            setTimeout(() => {
                generateBtn.textContent = 'Generate Password';
            }, 2000);
        } finally {
            generateBtn.disabled = false;
        }
    }
    
    async searchCredentials(query) {
        if (!query.trim()) {
            await this.loadCredentials();
            return;
        }
        
        try {
            const response = await fetch(`${this.apiBase}/credentials/search?domain=${encodeURIComponent(query)}`, {
                headers: {
                    'X-Session-Token': this.sessionToken
                }
            });
            
            if (response.ok) {
                const credentials = await response.json();
                this.displayCredentials(credentials);
            }
        } catch (error) {
            console.error('Search failed:', error);
        }
    }
    
    async logout() {
        await chrome.storage.local.remove(['sessionToken']);
        this.sessionToken = null;
        
        document.getElementById('mainApp').classList.add('hidden');
        document.getElementById('authScreen').classList.remove('hidden');
        document.getElementById('masterPassword').value = '';
    }
    
    showError(message, elementId) {
        const errorDiv = document.getElementById(elementId);
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize extension when popup loads
document.addEventListener('DOMContentLoaded', () => {
    new SecureVaultExtension();
});
