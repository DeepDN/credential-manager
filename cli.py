#!/usr/bin/env python3
"""
Command Line Interface for Credential Manager
"""
import os
import sys
import getpass
import json
from typing import Optional
from app.vault import CredentialVault
from app.models import CredentialCreate, CredentialUpdate


class CredentialManagerCLI:
    def __init__(self):
        self.vault = CredentialVault()
        
    def run(self):
        """Main CLI loop"""
        print("🔐 Secure Credential Manager CLI")
        print("=" * 40)
        
        # Check if vault exists
        if not self.vault.vault_exists():
            print("No vault found. Creating new vault...")
            if not self.create_vault():
                print("Failed to create vault. Exiting.")
                return
        
        # Authenticate
        if not self.authenticate():
            print("Authentication failed. Exiting.")
            return
        
        print("\n✅ Successfully authenticated!")
        
        # Main menu loop
        while True:
            try:
                self.show_menu()
                choice = input("\nEnter your choice: ").strip()
                
                if choice == '1':
                    self.add_credential()
                elif choice == '2':
                    self.list_credentials()
                elif choice == '3':
                    self.search_credentials()
                elif choice == '4':
                    self.view_credential()
                elif choice == '5':
                    self.update_credential()
                elif choice == '6':
                    self.delete_credential()
                elif choice == '7':
                    self.share_credential()
                elif choice == '8':
                    self.export_vault()
                elif choice == '9':
                    self.show_audit_logs()
                elif choice == '10':
                    self.show_vault_stats()
                elif choice == '0':
                    print("Goodbye! 👋")
                    break
                else:
                    print("Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def show_menu(self):
        """Display main menu"""
        print("\n" + "=" * 40)
        print("MAIN MENU")
        print("=" * 40)
        print("1. Add Credential")
        print("2. List All Credentials")
        print("3. Search Credentials")
        print("4. View Credential Details")
        print("5. Update Credential")
        print("6. Delete Credential")
        print("7. Share Credential")
        print("8. Export Vault")
        print("9. View Audit Logs")
        print("10. Vault Statistics")
        print("0. Exit")
    
    def create_vault(self) -> bool:
        """Create new vault"""
        print("\n📁 Creating New Vault")
        print("-" * 20)
        
        while True:
            password = getpass.getpass("Enter master password (min 8 chars): ")
            if len(password) < 8:
                print("❌ Password must be at least 8 characters long.")
                continue
                
            confirm = getpass.getpass("Confirm master password: ")
            if password != confirm:
                print("❌ Passwords don't match.")
                continue
                
            break
        
        if self.vault.create_vault(password):
            print("✅ Vault created successfully!")
            return True
        else:
            print("❌ Failed to create vault.")
            return False
    
    def authenticate(self) -> bool:
        """Authenticate user"""
        print("\n🔑 Authentication Required")
        print("-" * 25)
        
        max_attempts = 3
        attempts = 0
        
        while attempts < max_attempts:
            if self.vault.is_locked_out():
                print("❌ Account is temporarily locked due to failed attempts.")
                return False
            
            password = getpass.getpass("Enter master password: ")
            
            if self.vault.authenticate(password):
                return True
            else:
                attempts += 1
                remaining = max_attempts - attempts
                if remaining > 0:
                    print(f"❌ Invalid password. {remaining} attempts remaining.")
                else:
                    print("❌ Too many failed attempts.")
        
        return False
    
    def add_credential(self):
        """Add new credential"""
        print("\n➕ Add New Credential")
        print("-" * 20)
        
        service_name = input("Service/Application name: ").strip()
        if not service_name:
            print("❌ Service name is required.")
            return
        
        username = input("Username/Email: ").strip()
        if not username:
            print("❌ Username is required.")
            return
        
        password = getpass.getpass("Password/API Key: ")
        if not password:
            print("❌ Password is required.")
            return
        
        notes = input("Notes (optional): ").strip() or None
        tags_input = input("Tags (comma-separated, optional): ").strip()
        tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else []
        
        credential_data = CredentialCreate(
            service_name=service_name,
            username=username,
            password=password,
            notes=notes,
            tags=tags
        )
        
        credential_id = self.vault.add_credential(credential_data)
        if credential_id:
            print(f"✅ Credential added successfully! ID: {credential_id}")
        else:
            print("❌ Failed to add credential.")
    
    def list_credentials(self):
        """List all credentials"""
        print("\n📋 All Credentials")
        print("-" * 20)
        
        credentials = self.vault.get_all_credentials()
        
        if not credentials:
            print("No credentials found.")
            return
        
        for i, cred in enumerate(credentials, 1):
            print(f"\n{i}. {cred.service_name}")
            print(f"   Username: {cred.username}")
            print(f"   ID: {cred.id}")
            if cred.tags:
                print(f"   Tags: {', '.join(cred.tags)}")
    
    def search_credentials(self):
        """Search credentials"""
        print("\n🔍 Search Credentials")
        print("-" * 20)
        
        query = input("Search query (service name, username, notes): ").strip()
        tags_input = input("Tags to filter by (comma-separated, optional): ").strip()
        tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else None
        
        results = self.vault.search_credentials(
            query=query if query else None,
            tags=tags
        )
        
        if not results:
            print("No matching credentials found.")
            return
        
        print(f"\n📋 Found {len(results)} credential(s):")
        for i, cred in enumerate(results, 1):
            print(f"\n{i}. {cred.service_name}")
            print(f"   Username: {cred.username}")
            print(f"   ID: {cred.id}")
            if cred.tags:
                print(f"   Tags: {', '.join(cred.tags)}")
    
    def view_credential(self):
        """View credential details"""
        print("\n👁️  View Credential Details")
        print("-" * 25)
        
        cred_id = input("Enter credential ID: ").strip()
        if not cred_id:
            print("❌ Credential ID is required.")
            return
        
        credential = self.vault.get_credential(cred_id)
        if not credential:
            print("❌ Credential not found.")
            return
        
        print(f"\n📄 Credential Details:")
        print(f"Service: {credential.service_name}")
        print(f"Username: {credential.username}")
        
        show_password = input("Show password? (y/N): ").strip().lower()
        if show_password == 'y':
            print(f"Password: {credential.password}")
        else:
            print("Password: ••••••••")
        
        if credential.notes:
            print(f"Notes: {credential.notes}")
        
        if credential.tags:
            print(f"Tags: {', '.join(credential.tags)}")
        
        print(f"Created: {credential.created_at}")
        print(f"Updated: {credential.updated_at}")
    
    def update_credential(self):
        """Update credential"""
        print("\n✏️  Update Credential")
        print("-" * 20)
        
        cred_id = input("Enter credential ID: ").strip()
        if not cred_id:
            print("❌ Credential ID is required.")
            return
        
        credential = self.vault.get_credential(cred_id)
        if not credential:
            print("❌ Credential not found.")
            return
        
        print(f"\nCurrent details for: {credential.service_name}")
        print("Leave blank to keep current value:")
        
        service_name = input(f"Service name [{credential.service_name}]: ").strip()
        username = input(f"Username [{credential.username}]: ").strip()
        
        change_password = input("Change password? (y/N): ").strip().lower()
        password = None
        if change_password == 'y':
            password = getpass.getpass("New password: ")
        
        notes = input(f"Notes [{credential.notes or 'None'}]: ").strip()
        tags_input = input(f"Tags [{', '.join(credential.tags) if credential.tags else 'None'}]: ").strip()
        
        update_data = CredentialUpdate()
        
        if service_name:
            update_data.service_name = service_name
        if username:
            update_data.username = username
        if password:
            update_data.password = password
        if notes:
            update_data.notes = notes
        if tags_input:
            update_data.tags = [tag.strip() for tag in tags_input.split(',')]
        
        if self.vault.update_credential(cred_id, update_data):
            print("✅ Credential updated successfully!")
        else:
            print("❌ Failed to update credential.")
    
    def delete_credential(self):
        """Delete credential"""
        print("\n🗑️  Delete Credential")
        print("-" * 20)
        
        cred_id = input("Enter credential ID: ").strip()
        if not cred_id:
            print("❌ Credential ID is required.")
            return
        
        credential = self.vault.get_credential(cred_id)
        if not credential:
            print("❌ Credential not found.")
            return
        
        print(f"\n⚠️  You are about to delete:")
        print(f"Service: {credential.service_name}")
        print(f"Username: {credential.username}")
        
        confirm = input("\nAre you sure? Type 'DELETE' to confirm: ").strip()
        if confirm != 'DELETE':
            print("❌ Deletion cancelled.")
            return
        
        if self.vault.delete_credential(cred_id):
            print("✅ Credential deleted successfully!")
        else:
            print("❌ Failed to delete credential.")
    
    def share_credential(self):
        """Share credential"""
        print("\n🔗 Share Credential")
        print("-" * 20)
        
        cred_id = input("Enter credential ID: ").strip()
        if not cred_id:
            print("❌ Credential ID is required.")
            return
        
        credential = self.vault.get_credential(cred_id)
        if not credential:
            print("❌ Credential not found.")
            return
        
        print(f"\nSharing: {credential.service_name}")
        
        try:
            expires_in = int(input("Expiration time in minutes (default 60): ").strip() or "60")
            expires_in *= 60  # Convert to seconds
        except ValueError:
            expires_in = 3600  # Default 1 hour
        
        token = self.vault.generate_sharing_token(cred_id, expires_in)
        if token:
            print(f"\n✅ Sharing token generated!")
            print(f"Token: {token}")
            print(f"Expires in: {expires_in // 60} minutes")
            print("\n⚠️  Keep this token secure and share only with trusted recipients.")
        else:
            print("❌ Failed to generate sharing token.")
    
    def export_vault(self):
        """Export vault"""
        print("\n📤 Export Vault")
        print("-" * 15)
        
        export_password = getpass.getpass("Enter export password: ")
        if not export_password:
            print("❌ Export password is required.")
            return
        
        export_data = self.vault.export_vault(export_password)
        if export_data:
            filename = f"vault_export_{int(time.time())}.enc"
            with open(filename, 'w') as f:
                f.write(export_data)
            
            print(f"✅ Vault exported to: {filename}")
            print("⚠️  Keep this file and export password secure!")
        else:
            print("❌ Failed to export vault.")
    
    def show_audit_logs(self):
        """Show audit logs"""
        print("\n📊 Audit Logs")
        print("-" * 15)
        
        try:
            limit = int(input("Number of recent logs to show (default 20): ").strip() or "20")
        except ValueError:
            limit = 20
        
        logs = self.vault.get_audit_logs(limit)
        
        if not logs:
            print("No audit logs found.")
            return
        
        for log in reversed(logs):  # Show most recent first
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(log.timestamp))
            print(f"\n[{timestamp}] {log.action}")
            if log.credential_id:
                print(f"  Credential ID: {log.credential_id}")
            if log.details:
                print(f"  Details: {json.dumps(log.details, indent=2)}")
    
    def show_vault_stats(self):
        """Show vault statistics"""
        print("\n📈 Vault Statistics")
        print("-" * 20)
        
        stats = self.vault.get_vault_stats()
        if not stats:
            print("❌ Failed to get vault statistics.")
            return
        
        print(f"Total Credentials: {stats['total_credentials']}")
        print(f"Vault Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats['created_at']))}")
        print(f"Last Accessed: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats['last_accessed']))}")
        print(f"Vault File Size: {stats['vault_size']} bytes")


if __name__ == "__main__":
    import time
    cli = CredentialManagerCLI()
    cli.run()
