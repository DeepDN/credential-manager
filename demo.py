#!/usr/bin/env python3
"""
Demo script to showcase Credential Manager features
"""
import time
from app.vault import CredentialVault
from app.models import CredentialCreate

def demo_cli():
    """Demonstrate CLI functionality"""
    print("🔐 Credential Manager Demo")
    print("=" * 30)
    
    # Create vault instance
    vault = CredentialVault("demo_vault.enc")
    
    # Create demo vault
    print("\n1. Creating demo vault...")
    master_password = "demo_password_123"
    if vault.create_vault(master_password):
        print("✅ Demo vault created")
    else:
        print("❌ Failed to create vault")
        return
    
    # Authenticate
    print("\n2. Authenticating...")
    if vault.authenticate(master_password):
        print("✅ Authentication successful")
    else:
        print("❌ Authentication failed")
        return
    
    # Add sample credentials
    print("\n3. Adding sample credentials...")
    
    sample_credentials = [
        CredentialCreate(
            service_name="Gmail",
            username="john.doe@gmail.com",
            password="super_secure_password_123",
            notes="Personal email account",
            tags=["email", "personal"]
        ),
        CredentialCreate(
            service_name="GitHub",
            username="johndoe",
            password="github_token_xyz789",
            notes="Development account",
            tags=["development", "work"]
        ),
        CredentialCreate(
            service_name="AWS Console",
            username="john.doe@company.com",
            password="aws_complex_password_456",
            notes="Production AWS account - handle with care",
            tags=["cloud", "work", "production"]
        ),
        CredentialCreate(
            service_name="Database Server",
            username="db_admin",
            password="db_super_secret_789",
            notes="Main production database",
            tags=["database", "production"]
        )
    ]
    
    added_ids = []
    for cred in sample_credentials:
        cred_id = vault.add_credential(cred)
        if cred_id:
            added_ids.append(cred_id)
            print(f"  ✅ Added: {cred.service_name}")
        else:
            print(f"  ❌ Failed to add: {cred.service_name}")
    
    # List all credentials
    print(f"\n4. Listing all credentials ({len(added_ids)} total)...")
    credentials = vault.get_all_credentials()
    for i, cred in enumerate(credentials, 1):
        print(f"  {i}. {cred.service_name} ({cred.username})")
        if cred.tags:
            print(f"     Tags: {', '.join(cred.tags)}")
    
    # Search demonstration
    print("\n5. Searching credentials...")
    
    # Search by query
    work_creds = vault.search_credentials(query="work")
    print(f"  Work-related credentials: {len(work_creds)}")
    for cred in work_creds:
        print(f"    - {cred.service_name}")
    
    # Search by tags
    prod_creds = vault.search_credentials(tags=["production"])
    print(f"  Production credentials: {len(prod_creds)}")
    for cred in prod_creds:
        print(f"    - {cred.service_name}")
    
    # Generate sharing token
    print("\n6. Generating sharing token...")
    if added_ids:
        token = vault.generate_sharing_token(added_ids[0], expires_in=3600)
        if token:
            print(f"  ✅ Sharing token generated (expires in 1 hour)")
            print(f"  Token length: {len(token)} characters")
            
            # Test token decryption
            shared_data = vault.decrypt_sharing_token(token)
            if shared_data:
                print(f"  ✅ Token validation successful")
                print(f"  Shared service: {shared_data['service_name']}")
            else:
                print("  ❌ Token validation failed")
        else:
            print("  ❌ Failed to generate sharing token")
    
    # Export vault
    print("\n7. Exporting vault...")
    export_password = "export_password_456"
    export_data = vault.export_vault(export_password)
    if export_data:
        print(f"  ✅ Vault exported successfully")
        print(f"  Export data length: {len(export_data)} characters")
    else:
        print("  ❌ Failed to export vault")
    
    # Show vault statistics
    print("\n8. Vault statistics...")
    stats = vault.get_vault_stats()
    if stats:
        print(f"  Total credentials: {stats['total_credentials']}")
        print(f"  Vault size: {stats['vault_size']} bytes")
        print(f"  Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats['created_at']))}")
    
    # Show audit logs
    print("\n9. Recent audit logs...")
    logs = vault.get_audit_logs(limit=5)
    for log in reversed(logs[-5:]):  # Show last 5 in chronological order
        timestamp = time.strftime('%H:%M:%S', time.localtime(log.timestamp))
        print(f"  [{timestamp}] {log.action}")
        if log.details and 'service_name' in log.details:
            print(f"    Service: {log.details['service_name']}")
    
    print("\n" + "=" * 30)
    print("🎉 Demo completed successfully!")
    print("\n💡 Key Features Demonstrated:")
    print("  ✅ Secure vault creation with master password")
    print("  ✅ Strong encryption (AES-256 + PBKDF2)")
    print("  ✅ Credential CRUD operations")
    print("  ✅ Advanced search and filtering")
    print("  ✅ Secure credential sharing with tokens")
    print("  ✅ Encrypted vault export/backup")
    print("  ✅ Comprehensive audit logging")
    print("  ✅ Session management and security")
    
    print("\n🚀 Next Steps:")
    print("  • Run 'python3 run_web.py' for web interface")
    print("  • Run 'python3 cli.py' for interactive CLI")
    print("  • Visit http://127.0.0.1:8000 in your browser")
    
    # Cleanup demo vault
    import os
    if os.path.exists("demo_vault.enc"):
        os.remove("demo_vault.enc")
        print("\n🧹 Demo vault cleaned up")

if __name__ == "__main__":
    demo_cli()
