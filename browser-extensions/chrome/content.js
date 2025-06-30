// SecureVault Browser Extension - Content Script

class SecureVaultContentScript {
    constructor() {
        this.setupMessageListener();
        this.detectForms();
    }
    
    setupMessageListener() {
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            switch (message.action) {
                case 'fillCredential':
                    this.fillCredential(message.credential);
                    break;
                case 'fillPassword':
                    this.fillPassword(message.password);
                    break;
                case 'detectForms':
                    this.detectForms();
                    break;
            }
            sendResponse({ success: true });
        });
    }
    
    detectForms() {
        // Find login forms on the page
        const forms = document.querySelectorAll('form');
        const loginForms = [];
        
        forms.forEach(form => {
            const passwordFields = form.querySelectorAll('input[type="password"]');
            const usernameFields = form.querySelectorAll('input[type="text"], input[type="email"], input[name*="user"], input[name*="email"], input[id*="user"], input[id*="email"]');
            
            if (passwordFields.length > 0 && usernameFields.length > 0) {
                loginForms.push({
                    form: form,
                    usernameField: usernameFields[0],
                    passwordField: passwordFields[0]
                });
            }
        });
        
        // Add SecureVault icon to detected forms
        loginForms.forEach(formData => {
            this.addSecureVaultIcon(formData);
        });
    }
    
    addSecureVaultIcon(formData) {
        // Check if icon already exists
        if (formData.usernameField.parentElement.querySelector('.securevault-icon')) {
            return;
        }
        
        // Create SecureVault icon
        const icon = document.createElement('div');
        icon.className = 'securevault-icon';
        icon.innerHTML = '🔐';
        icon.title = 'Fill with SecureVault';
        icon.style.cssText = `
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            cursor: pointer;
            font-size: 16px;
            z-index: 10000;
            background: white;
            padding: 2px;
            border-radius: 3px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        `;
        
        // Position the username field relatively
        const usernameFieldStyle = window.getComputedStyle(formData.usernameField);
        if (usernameFieldStyle.position === 'static') {
            formData.usernameField.style.position = 'relative';
        }
        
        // Add icon to username field container
        formData.usernameField.parentElement.style.position = 'relative';
        formData.usernameField.parentElement.appendChild(icon);
        
        // Add click listener
        icon.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.openSecureVaultPopup();
        });
    }
    
    fillCredential(credential) {
        // Find the best matching form fields
        const usernameField = this.findBestUsernameField();
        const passwordField = this.findBestPasswordField();
        
        if (usernameField && credential.username) {
            this.fillField(usernameField, credential.username);
        }
        
        if (passwordField && credential.password) {
            this.fillField(passwordField, credential.password);
        }
        
        // Focus on the next field or submit button
        if (passwordField) {
            passwordField.focus();
        }
    }
    
    fillPassword(password) {
        const passwordField = this.findBestPasswordField();
        if (passwordField) {
            this.fillField(passwordField, password);
            passwordField.focus();
        }
    }
    
    fillField(field, value) {
        // Set the value
        field.value = value;
        
        // Trigger events to ensure the form recognizes the change
        const events = ['input', 'change', 'keyup', 'keydown'];
        events.forEach(eventType => {
            const event = new Event(eventType, { bubbles: true });
            field.dispatchEvent(event);
        });
        
        // For React and other frameworks
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeInputValueSetter.call(field, value);
        
        const inputEvent = new Event('input', { bubbles: true });
        field.dispatchEvent(inputEvent);
    }
    
    findBestUsernameField() {
        // Look for username/email fields
        const selectors = [
            'input[type="email"]',
            'input[type="text"][name*="user"]',
            'input[type="text"][name*="email"]',
            'input[type="text"][id*="user"]',
            'input[type="text"][id*="email"]',
            'input[type="text"][placeholder*="user"]',
            'input[type="text"][placeholder*="email"]',
            'input[name="username"]',
            'input[name="email"]',
            'input[id="username"]',
            'input[id="email"]'
        ];
        
        for (const selector of selectors) {
            const field = document.querySelector(selector);
            if (field && this.isVisible(field)) {
                return field;
            }
        }
        
        // Fallback: find the first visible text input before a password field
        const passwordFields = document.querySelectorAll('input[type="password"]');
        for (const passwordField of passwordFields) {
            if (this.isVisible(passwordField)) {
                const form = passwordField.closest('form') || document;
                const textInputs = form.querySelectorAll('input[type="text"], input[type="email"]');
                
                for (const textInput of textInputs) {
                    if (this.isVisible(textInput) && this.isBeforeInDOM(textInput, passwordField)) {
                        return textInput;
                    }
                }
            }
        }
        
        return null;
    }
    
    findBestPasswordField() {
        const passwordFields = document.querySelectorAll('input[type="password"]');
        
        // Return the first visible password field
        for (const field of passwordFields) {
            if (this.isVisible(field)) {
                return field;
            }
        }
        
        return null;
    }
    
    isVisible(element) {
        const style = window.getComputedStyle(element);
        return style.display !== 'none' && 
               style.visibility !== 'hidden' && 
               style.opacity !== '0' &&
               element.offsetWidth > 0 && 
               element.offsetHeight > 0;
    }
    
    isBeforeInDOM(element1, element2) {
        return element1.compareDocumentPosition(element2) & Node.DOCUMENT_POSITION_FOLLOWING;
    }
    
    openSecureVaultPopup() {
        // This would typically open the extension popup
        // For now, we'll just send a message to the background script
        chrome.runtime.sendMessage({ action: 'openPopup' });
    }
}

// Initialize content script
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new SecureVaultContentScript();
    });
} else {
    new SecureVaultContentScript();
}
