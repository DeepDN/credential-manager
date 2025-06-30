// Global state
let currentCredentials = [];
let editingCredentialId = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Close modals when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            closeModal(e.target.id);
        }
    });

    // Handle escape key to close modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal:not(.hidden)');
            if (openModal) {
                closeModal(openModal.id);
            }
        }
    });
}

// Check authentication status
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();
        
        if (data.authenticated) {
            showMainApp();
            loadCredentials();
        } else {
            checkVaultExists();
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
        showError('Failed to check authentication status');
    }
}

// Check if vault exists
async function checkVaultExists() {
    try {
        const response = await fetch('/api/vault/exists');
        const data = await response.json();
        
        if (data.exists) {
            showLoginForm();
        } else {
            showSetupForm();
        }
    } catch (error) {
        console.error('Error checking vault:', error);
        showError('Failed to check vault status');
    }
}

// Toggle between login and setup forms
function toggleSetup() {
    const loginForm = document.getElementById('loginForm');
    const setupForm = document.getElementById('setupForm');
    
    if (loginForm.classList.contains('hidden')) {
        showLoginForm();
    } else {
        showSetupForm();
    }
}

// Show login form
function showLoginForm() {
    document.getElementById('loginForm').classList.remove('hidden');
    document.getElementById('setupForm').classList.add('hidden');
    document.getElementById('loginPassword').focus();
}

// Show setup form
function showSetupForm() {
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('setupForm').classList.remove('hidden');
    document.getElementById('setupPassword').focus();
}

// Show main application
function showMainApp() {
    document.getElementById('authScreen').classList.add('hidden');
    document.getElementById('mainApp').classList.remove('hidden');
    document.getElementById('logoutBtn').classList.remove('hidden');
}

// Show authentication screen
function showAuthScreen() {
    document.getElementById('authScreen').classList.remove('hidden');
    document.getElementById('mainApp').classList.add('hidden');
    document.getElementById('logoutBtn').classList.add('hidden');
}

// Login function
async function login(event) {
    event.preventDefault();
    
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');
    
    if (!password) {
        showError('Please enter your master password', errorDiv);
        return;
    }

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ master_password: password })
        });

        const data = await response.json();

        if (response.ok) {
            hideError(errorDiv);
            showMainApp();
            loadCredentials();
            document.getElementById('loginPassword').value = '';
        } else {
            showError(data.detail || 'Login failed', errorDiv);
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('Network error. Please try again.', errorDiv);
    }
}

// Create vault function
async function createVault(event) {
    event.preventDefault();
    
    const password = document.getElementById('setupPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const errorDiv = document.getElementById('setupError');

    if (!password || !confirmPassword) {
        showError('Please fill in all fields', errorDiv);
        return;
    }

    if (password !== confirmPassword) {
        showError('Passwords do not match', errorDiv);
        return;
    }

    if (password.length < 8) {
        showError('Password must be at least 8 characters long', errorDiv);
        return;
    }

    try {
        const response = await fetch('/api/vault/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ master_password: password })
        });

        const data = await response.json();

        if (response.ok) {
            hideError(errorDiv);
            showMainApp();
            loadCredentials();
            document.getElementById('setupPassword').value = '';
            document.getElementById('confirmPassword').value = '';
        } else {
            showError(data.detail || 'Failed to create vault', errorDiv);
        }
    } catch (error) {
        console.error('Create vault error:', error);
        showError('Network error. Please try again.', errorDiv);
    }
}

// Logout function
async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        showAuthScreen();
        currentCredentials = [];
        checkVaultExists();
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Load credentials
async function loadCredentials() {
    try {
        const response = await fetch('/api/credentials');
        
        if (response.ok) {
            currentCredentials = await response.json();
            displayCredentials(currentCredentials);
            updateStats();
        } else {
            showError('Failed to load credentials');
        }
    } catch (error) {
        console.error('Error loading credentials:', error);
        showError('Network error while loading credentials');
    }
}

// Display credentials
function displayCredentials(credentials) {
    const container = document.getElementById('credentialsList');
    
    if (credentials.length === 0) {
        container.innerHTML = `
            <div class="credential-item text-center" style="padding: 3rem;">
                <i class="fas fa-key" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 1rem;"></i>
                <p style="color: var(--text-muted);">No credentials found. Add your first credential to get started.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = credentials.map(credential => `
        <div class="credential-item" data-id="${credential.id}">
            <div class="credential-header">
                <h3 class="credential-title">
                    <i class="fas fa-globe" style="margin-right: 0.5rem; color: var(--primary-color);"></i>
                    ${escapeHtml(credential.service_name)}
                </h3>
                <div class="credential-actions">
                    <button class="btn-icon" onclick="copyToClipboard('${credential.username}')" title="Copy Username">
                        <i class="fas fa-user"></i>
                    </button>
                    <button class="btn-icon" onclick="copyPassword('${credential.id}')" title="Copy Password">
                        <i class="fas fa-key"></i>
                    </button>
                    <button class="btn-icon" onclick="editCredential('${credential.id}')" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon" onclick="deleteCredential('${credential.id}')" title="Delete" style="color: var(--error-color);">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="credential-details">
                <div>
                    <strong>Username:</strong> ${escapeHtml(credential.username || 'N/A')}
                </div>
                <div>
                    <strong>Website:</strong> 
                    ${credential.url ? `<a href="${escapeHtml(credential.url)}" target="_blank" style="color: var(--primary-color);">${escapeHtml(credential.url)}</a>` : 'N/A'}
                </div>
                <div>
                    <strong>Last Modified:</strong> ${formatDate(credential.updated_at)}
                </div>
                ${credential.notes ? `<div><strong>Notes:</strong> ${escapeHtml(credential.notes)}</div>` : ''}
            </div>
        </div>
    `).join('');
}

// Update statistics
function updateStats() {
    document.getElementById('totalCredentials').textContent = currentCredentials.length;
    
    // Calculate strong passwords (simple heuristic)
    const strongPasswords = currentCredentials.filter(cred => 
        cred.password && cred.password.length >= 12
    ).length;
    document.getElementById('strongPasswords').textContent = strongPasswords;
    
    // Recent activity (credentials modified in last 7 days)
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    const recentActivity = currentCredentials.filter(cred => 
        new Date(cred.updated_at) > weekAgo
    ).length;
    document.getElementById('recentActivity').textContent = recentActivity;
    
    // Security score (percentage of strong passwords)
    const securityScore = currentCredentials.length > 0 
        ? Math.round((strongPasswords / currentCredentials.length) * 100)
        : 100;
    document.getElementById('securityScore').textContent = `${securityScore}%`;
}

// Search credentials
function searchCredentials() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    
    if (!query) {
        displayCredentials(currentCredentials);
        return;
    }

    const filtered = currentCredentials.filter(credential =>
        credential.service_name.toLowerCase().includes(query) ||
        (credential.username && credential.username.toLowerCase().includes(query)) ||
        (credential.url && credential.url.toLowerCase().includes(query)) ||
        (credential.notes && credential.notes.toLowerCase().includes(query))
    );

    displayCredentials(filtered);
}

// Show add credential modal
function showAddCredentialModal() {
    editingCredentialId = null;
    document.getElementById('modalTitle').textContent = 'Add New Credential';
    document.getElementById('credentialForm').reset();
    document.getElementById('credentialModal').classList.remove('hidden');
    document.getElementById('credentialName').focus();
}

// Edit credential
async function editCredential(id) {
    const credential = currentCredentials.find(c => c.id === id);
    if (!credential) return;

    editingCredentialId = id;
    document.getElementById('modalTitle').textContent = 'Edit Credential';
    document.getElementById('credentialName').value = credential.service_name;
    document.getElementById('credentialUsername').value = credential.username || '';
    document.getElementById('credentialUrl').value = credential.url || '';
    document.getElementById('credentialNotes').value = credential.notes || '';
    
    // Get the actual password
    try {
        const response = await fetch(`/api/credentials/${id}`);
        if (response.ok) {
            const fullCredential = await response.json();
            document.getElementById('credentialPassword').value = fullCredential.password;
        }
    } catch (error) {
        console.error('Error loading credential details:', error);
    }
    
    document.getElementById('credentialModal').classList.remove('hidden');
    document.getElementById('credentialName').focus();
}

// Save credential
async function saveCredential(event) {
    event.preventDefault();
    
    const formData = {
        service_name: document.getElementById('credentialName').value,
        username: document.getElementById('credentialUsername').value,
        password: document.getElementById('credentialPassword').value,
        url: document.getElementById('credentialUrl').value,
        notes: document.getElementById('credentialNotes').value,
        tags: []
    };

    try {
        let response;
        
        if (editingCredentialId) {
            // Update existing credential
            response = await fetch(`/api/credentials/${editingCredentialId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
        } else {
            // Create new credential
            response = await fetch('/api/credentials', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
        }

        if (response.ok) {
            closeModal('credentialModal');
            loadCredentials();
            showSuccess(editingCredentialId ? 'Credential updated successfully' : 'Credential added successfully');
        } else {
            const data = await response.json();
            showError(data.detail || 'Failed to save credential');
        }
    } catch (error) {
        console.error('Error saving credential:', error);
        showError('Network error while saving credential');
    }
}

// Delete credential
async function deleteCredential(id) {
    const credential = currentCredentials.find(c => c.id === id);
    if (!credential) return;

    if (!confirm(`Are you sure you want to delete "${credential.service_name}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/credentials/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            loadCredentials();
            showSuccess('Credential deleted successfully');
        } else {
            const data = await response.json();
            showError(data.detail || 'Failed to delete credential');
        }
    } catch (error) {
        console.error('Error deleting credential:', error);
        showError('Network error while deleting credential');
    }
}

// Copy to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showSuccess('Copied to clipboard');
    } catch (error) {
        console.error('Error copying to clipboard:', error);
        showError('Failed to copy to clipboard');
    }
}

// Copy password
async function copyPassword(id) {
    try {
        const response = await fetch(`/api/credentials/${id}`);
        if (response.ok) {
            const credential = await response.json();
            await copyToClipboard(credential.password);
        } else {
            showError('Failed to get password');
        }
    } catch (error) {
        console.error('Error copying password:', error);
        showError('Failed to copy password');
    }
}

// Refresh credentials
function refreshCredentials() {
    loadCredentials();
    showSuccess('Credentials refreshed');
}

// Toggle password visibility
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const button = input.nextElementSibling;
    const icon = button.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// Close modal
function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
    editingCredentialId = null;
}

// Show error message
function showError(message, container = null) {
    if (container) {
        container.querySelector('span').textContent = message;
        container.classList.remove('hidden');
    } else {
        // Show global error notification
        showNotification(message, 'error');
    }
}

// Hide error message
function hideError(container) {
    container.classList.add('hidden');
}

// Show success message
function showSuccess(message) {
    showNotification(message, 'success');
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 2000;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
    `;
    
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
