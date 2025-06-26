#!/usr/bin/env python3
"""
Test CLI functionality
"""
import os
import sys

def test_cli_import():
    """Test if CLI can be imported and basic functions work"""
    try:
        # Add the current directory to Python path
        sys.path.insert(0, os.getcwd())
        
        from app.vault import CredentialVault
        from app.models import CredentialCreate
        
        print("✅ CLI modules imported successfully")
        
        # Test vault creation (with temp file)
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            vault = CredentialVault(tmp_path)
            if vault.create_vault("test123"):
                print("✅ Vault creation works")
            else:
                print("❌ Vault creation failed")
                return False
                
            if vault.authenticate("test123"):
                print("✅ Authentication works")
            else:
                print("❌ Authentication failed")
                return False
                
            print("✅ CLI functionality verified")
            return True
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False

def main():
    print("🧪 Testing CLI Interface")
    print("=" * 25)
    
    if test_cli_import():
        print("\n🎉 CLI is ready to use!")
        print("\n🚀 To start CLI:")
        print("   cd /home/deepak/credential-manager")
        print("   source venv/bin/activate")
        print("   python3 cli.py")
    else:
        print("\n❌ CLI test failed")

if __name__ == "__main__":
    main()
