// SecureVault Browser Extension - Background Script

class SecureVaultBackground {
    constructor() {
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Handle extension installation
        chrome.runtime.onInstalled.addListener((details) => {
            if (details.reason === 'install') {
                this.onInstall();
            } else if (details.reason === 'update') {
                this.onUpdate(details.previousVersion);
            }
        });
        
        // Handle messages from content scripts and popup
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            this.handleMessage(message, sender, sendResponse);
            return true; // Keep message channel open for async responses
        });
        
        // Handle tab updates to detect login forms
        chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
            if (changeInfo.status === 'complete' && tab.url) {
                this.onTabComplete(tabId, tab);
            }
        });
        
        // Handle browser action click
        chrome.action.onClicked.addListener((tab) => {
            this.openPopup();
        });
    }
    
    onInstall() {
        console.log('SecureVault extension installed');
        
        // Set default settings
        chrome.storage.local.set({
            settings: {
                autoFill: true,
                showIcons: true,
                secureMode: true
            }
        });
        
        // Open welcome page
        chrome.tabs.create({
            url: 'http://localhost:8000'
        });
    }
    
    onUpdate(previousVersion) {
        console.log(`SecureVault extension updated from ${previousVersion} to ${chrome.runtime.getManifest().version}`);
    }
    
    async handleMessage(message, sender, sendResponse) {
        try {
            switch (message.action) {
                case 'openPopup':
                    await this.openPopup();
                    sendResponse({ success: true });
                    break;
                    
                case 'getTabInfo':
                    const tab = await this.getCurrentTab();
                    sendResponse({ tab });
                    break;
                    
                case 'checkVaultConnection':
                    const isConnected = await this.checkVaultConnection();
                    sendResponse({ connected: isConnected });
                    break;
                    
                case 'logout':
                    await this.logout();
                    sendResponse({ success: true });
                    break;
                    
                default:
                    sendResponse({ error: 'Unknown action' });
            }
        } catch (error) {
            console.error('Background script error:', error);
            sendResponse({ error: error.message });
        }
    }
    
    async onTabComplete(tabId, tab) {
        try {
            // Skip non-http(s) URLs
            if (!tab.url.startsWith('http')) {
                return;
            }
            
            // Inject content script if needed
            await chrome.scripting.executeScript({
                target: { tabId: tabId },
                files: ['content.js']
            });
            
            // Send message to detect forms
            chrome.tabs.sendMessage(tabId, { action: 'detectForms' });
            
        } catch (error) {
            // Ignore errors for tabs we can't access
            console.debug('Could not inject content script:', error);
        }
    }
    
    async openPopup() {
        // The popup will open automatically when the user clicks the extension icon
        // This method is here for programmatic opening if needed
        console.log('Opening SecureVault popup');
    }
    
    async getCurrentTab() {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        return tabs[0];
    }
    
    async checkVaultConnection() {
        try {
            const response = await fetch('http://localhost:8000/api/auth/status');
            return response.ok;
        } catch (error) {
            return false;
        }
    }
    
    async logout() {
        // Clear stored session data
        await chrome.storage.local.remove(['sessionToken']);
        
        // Notify all tabs
        const tabs = await chrome.tabs.query({});
        tabs.forEach(tab => {
            chrome.tabs.sendMessage(tab.id, { action: 'logout' }).catch(() => {
                // Ignore errors for tabs without content script
            });
        });
    }
}

// Initialize background script
new SecureVaultBackground();
