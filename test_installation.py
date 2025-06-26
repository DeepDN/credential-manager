#!/usr/bin/env python3
"""
Test script to verify Credential Manager installation
"""
import sys
import importlib
import tempfile
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    required_modules = [
        'cryptography',
        'bcrypt',
        'fastapi',
        'uvicorn',
        'pydantic',
        'qrcode',
        'pyotp'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed_imports.append(module)
    
    return len(failed_imports) == 0

def test_app_imports():
    """Test if app modules can be imported"""
    print("\n🧪 Testing app modules...")
    
    try:
        from app.security import SecurityManager
        from app.vault import CredentialVault
        from app.models import Credential, CredentialCreate
        from app.main import app
        print("  ✅ All app modules imported successfully")
        return True
    except ImportError as e:
        print(f"  ❌ Failed to import app modules: {e}")
        return False

def test_security_functions():
    """Test basic security functions"""
    print("\n🧪 Testing security functions...")
    
    try:
        from app.security import SecurityManager
        
        # Test with temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            security = SecurityManager(tmp_path)
            
            # Test key derivation
            password = "test_password_123"
            salt = security.generate_salt()
            key = security.derive_key(password, salt)
            
            if len(key) == 44:  # Base64 encoded 32-byte key
                print("  ✅ Key derivation working")
            else:
                print("  ❌ Key derivation failed")
                return False
            
            # Test password hashing
            hashed = security.hash_master_password(password)
            if security.verify_master_password(password, hashed):
                print("  ✅ Password hashing working")
            else:
                print("  ❌ Password hashing failed")
                return False
            
            # Test vault creation
            if security.create_vault(password):
                print("  ✅ Vault creation working")
            else:
                print("  ❌ Vault creation failed")
                return False
            
            return True
            
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        print(f"  ❌ Security test failed: {e}")
        return False

def test_vault_operations():
    """Test basic vault operations"""
    print("\n🧪 Testing vault operations...")
    
    try:
        from app.vault import CredentialVault
        from app.models import CredentialCreate
        
        # Test with temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            vault = CredentialVault(tmp_path)
            
            # Create vault
            if not vault.create_vault("test_password_123"):
                print("  ❌ Failed to create test vault")
                return False
            
            # Authenticate
            if not vault.authenticate("test_password_123"):
                print("  ❌ Failed to authenticate")
                return False
            
            # Add credential
            cred_data = CredentialCreate(
                service_name="Test Service",
                username="test_user",
                password="test_pass",
                notes="Test notes"
            )
            
            cred_id = vault.add_credential(cred_data)
            if not cred_id:
                print("  ❌ Failed to add credential")
                return False
            
            # Retrieve credential
            credential = vault.get_credential(cred_id)
            if not credential or credential.service_name != "Test Service":
                print("  ❌ Failed to retrieve credential")
                return False
            
            print("  ✅ Vault operations working")
            return True
            
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        print(f"  ❌ Vault test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔐 Credential Manager Installation Test")
    print("=" * 45)
    
    tests = [
        ("Module Imports", test_imports),
        ("App Imports", test_app_imports),
        ("Security Functions", test_security_functions),
        ("Vault Operations", test_vault_operations)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 45)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Installation is working correctly.")
        print("\n🚀 You can now run:")
        print("  Web Interface: python run_web.py")
        print("  CLI Interface: python cli.py")
    else:
        print("❌ Some tests failed. Please check the installation.")
        print("💡 Try running: python setup.py")
    
    print("=" * 45)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
