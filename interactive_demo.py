#!/usr/bin/env python3
"""
Interactive demo showing the credential manager in action
"""
import time
import os
from app.vault import CredentialVault
from app.models import CredentialCreate

def print_header(title):
    print(f"\n{'='*50}")
    print(f"🔐 {title}")
    print(f"{'='*50}")

def print_step(step, description):
    print(f"\n📋 Step {step}: {description}")
    print("-" * 30)

def simulate_typing(text, delay=0.03):
    """Simulate typing effect"""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def main():
    print_header("CREDENTIAL MANAGER LIVE DEMO")
    
    # Clean up any existing demo vault
    demo_vault_path = "live_demo_vault.enc"
    if os.path.exists(demo_vault_path):
        os.remove(demo_vault_path)
    
    vault = CredentialVault(demo_vault_path)
    
    print_step(1, "Creating a new secure vault")
    master_password = "MySecurePassword123!"
    
    print("🔑 Setting master password...")
    simulate_typing(f"Master Password: {'*' * len(master_password)}")
    
    if vault.create_vault(master_password):
        print("✅ Vault created successfully with AES-256 encryption!")
    else:
        print("❌ Failed to create vault")
        return
    
    print_step(2, "Authenticating with master password")
    print("🔐 Authenticating...")
    
    if vault.authenticate(master_password):
        print("✅ Authentication successful!")
        print("🔒 Session established with 5-minute timeout")
    else:
        print("❌ Authentication failed")
        return
    
    print_step(3, "Adding sample credentials")
    
    credentials_to_add = [
        {
            "service": "Gmail Account",
            "username": "john.doe@gmail.com", 
            "password": "SuperSecure123!",
            "notes": "Personal email account",
            "tags": ["email", "personal"]
        },
        {
            "service": "GitHub",
            "username": "johndoe",
            "password": "github_pat_xyz789",
            "notes": "Development account with 2FA enabled",
            "tags": ["development", "work", "git"]
        },
        {
            "service": "AWS Console",
            "username": "admin@company.com",
            "password": "AWS_Complex_Pass_456!",
            "notes": "Production AWS account - CRITICAL",
            "tags": ["cloud", "aws", "production"]
        }
    ]
    
    added_credentials = []
    
    for i, cred_data in enumerate(credentials_to_add, 1):
        print(f"\n📝 Adding credential {i}/3: {cred_data['service']}")
        
        credential = CredentialCreate(
            service_name=cred_data["service"],
            username=cred_data["username"],
            password=cred_data["password"],
            notes=cred_data["notes"],
            tags=cred_data["tags"]
        )
        
        cred_id = vault.add_credential(credential)
        if cred_id:
            added_credentials.append(cred_id)
            print(f"   ✅ {cred_data['service']} added successfully")
            print(f"   🏷️  Tags: {', '.join(cred_data['tags'])}")
        else:
            print(f"   ❌ Failed to add {cred_data['service']}")
    
    print_step(4, "Listing all stored credentials")
    
    all_credentials = vault.get_all_credentials()
    print(f"📊 Found {len(all_credentials)} credentials in vault:")
    
    for i, cred in enumerate(all_credentials, 1):
        print(f"\n{i}. 🔐 {cred.service_name}")
        print(f"   👤 Username: {cred.username}")
        print(f"   🔑 Password: {'*' * len(cred.password)} ({len(cred.password)} chars)")
        if cred.notes:
            print(f"   📝 Notes: {cred.notes}")
        if cred.tags:
            print(f"   🏷️  Tags: {', '.join(cred.tags)}")
        print(f"   📅 Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cred.created_at))}")
    
    print_step(5, "Demonstrating search functionality")
    
    # Search by text
    print("🔍 Searching for 'AWS' credentials...")
    aws_results = vault.search_credentials(query="AWS")
    print(f"   Found {len(aws_results)} result(s):")
    for cred in aws_results:
        print(f"   - {cred.service_name} ({cred.username})")
    
    # Search by tags
    print("\n🔍 Searching for 'production' tagged credentials...")
    prod_results = vault.search_credentials(tags=["production"])
    print(f"   Found {len(prod_results)} result(s):")
    for cred in prod_results:
        print(f"   - {cred.service_name} (Tags: {', '.join(cred.tags)})")
    
    print_step(6, "Generating secure sharing token")
    
    if added_credentials:
        print("🔗 Creating temporary sharing link for Gmail account...")
        token = vault.generate_sharing_token(added_credentials[0], expires_in=3600)  # 1 hour
        
        if token:
            print("✅ Sharing token generated successfully!")
            print(f"🔒 Token length: {len(token)} characters")
            print(f"⏰ Expires in: 1 hour")
            print(f"🌐 Share URL: http://localhost:8080/share/{token[:20]}...")
            
            # Verify token works
            shared_data = vault.decrypt_sharing_token(token)
            if shared_data:
                print("✅ Token validation successful!")
                print(f"📧 Shared service: {shared_data['service_name']}")
            else:
                print("❌ Token validation failed")
        else:
            print("❌ Failed to generate sharing token")
    
    print_step(7, "Creating encrypted backup")
    
    export_password = "BackupPassword456!"
    print("💾 Exporting vault with separate backup password...")
    
    export_data = vault.export_vault(export_password)
    if export_data:
        backup_filename = f"vault_backup_{int(time.time())}.enc"
        with open(backup_filename, 'w') as f:
            f.write(export_data)
        
        print(f"✅ Vault exported successfully!")
        print(f"📁 Backup file: {backup_filename}")
        print(f"📊 Backup size: {len(export_data)} characters")
        print(f"🔐 Encrypted with separate password")
    else:
        print("❌ Failed to export vault")
    
    print_step(8, "Viewing audit logs")
    
    print("📋 Recent activity log:")
    logs = vault.get_audit_logs(limit=8)
    
    for log in reversed(logs[-8:]):  # Show most recent first
        timestamp = time.strftime('%H:%M:%S', time.localtime(log.timestamp))
        action_emoji = {
            'LOGIN': '🔐',
            'ADD_CREDENTIAL': '➕',
            'VIEW_CREDENTIAL': '👁️',
            'SEARCH_CREDENTIALS': '🔍',
            'GENERATE_SHARE_TOKEN': '🔗',
            'EXPORT_VAULT': '💾',
            'LIST_CREDENTIALS': '📋'
        }.get(log.action, '📝')
        
        print(f"   [{timestamp}] {action_emoji} {log.action}")
        if log.details and 'service_name' in log.details:
            print(f"       📧 Service: {log.details['service_name']}")
    
    print_step(9, "Vault statistics")
    
    stats = vault.get_vault_stats()
    if stats:
        print("📊 Vault Statistics:")
        print(f"   🔐 Total Credentials: {stats['total_credentials']}")
        print(f"   📅 Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats['created_at']))}")
        print(f"   🕒 Last Accessed: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats['last_accessed']))}")
        print(f"   💾 Vault Size: {stats['vault_size']} bytes")
    
    print_step(10, "Security features demonstration")
    
    print("🛡️  Security Features Active:")
    print("   ✅ AES-256 encryption with authenticated encryption")
    print("   ✅ PBKDF2 key derivation (100,000 iterations)")
    print("   ✅ Bcrypt master password hashing")
    print("   ✅ Session timeout (5 minutes)")
    print("   ✅ Failed attempt protection (5 attempts)")
    print("   ✅ Secure credential sharing with expiration")
    print("   ✅ Comprehensive audit logging")
    print("   ✅ Encrypted vault export/backup")
    
    print_header("DEMO COMPLETED SUCCESSFULLY!")
    
    print("\n🎉 Key Features Demonstrated:")
    print("   • Secure vault creation and authentication")
    print("   • Encrypted credential storage and retrieval")
    print("   • Advanced search and filtering")
    print("   • Temporary credential sharing")
    print("   • Encrypted backup and export")
    print("   • Comprehensive audit logging")
    print("   • Real-time vault statistics")
    
    print("\n🚀 Ready to Use:")
    print("   • Web Interface: python3 run_web.py")
    print("   • CLI Interface: python3 cli.py")
    print("   • Start Script: ./start.sh")
    
    print("\n🔒 Your credentials are secure with enterprise-grade encryption!")
    
    # Cleanup
    print(f"\n🧹 Cleaning up demo files...")
    if os.path.exists(demo_vault_path):
        os.remove(demo_vault_path)
        print("   ✅ Demo vault removed")
    
    # Remove backup file if created
    for file in os.listdir('.'):
        if file.startswith('vault_backup_') and file.endswith('.enc'):
            os.remove(file)
            print(f"   ✅ Demo backup file removed")

if __name__ == "__main__":
    main()
