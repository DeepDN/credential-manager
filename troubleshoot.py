#!/usr/bin/env python3
"""
Troubleshooting script for Credential Manager
"""
import os
import sys
import subprocess
import socket

def print_step(step, description):
    print(f"\n{'='*50}")
    print(f"🔧 Step {step}: {description}")
    print(f"{'='*50}")

def check_python():
    print("🐍 Python Information:")
    print(f"   Version: {sys.version}")
    print(f"   Executable: {sys.executable}")
    return True

def check_virtual_env():
    print("📦 Virtual Environment:")
    if 'VIRTUAL_ENV' in os.environ:
        print(f"   ✅ Active: {os.environ['VIRTUAL_ENV']}")
        return True
    else:
        print("   ❌ Not activated")
        print("   💡 Run: source venv/bin/activate")
        return False

def check_dependencies():
    print("📚 Dependencies:")
    required_modules = [
        'cryptography', 'bcrypt', 'fastapi', 'uvicorn', 
        'pydantic', 'qrcode', 'pyotp'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module}")
            missing.append(module)
    
    return len(missing) == 0

def find_free_port(start_port=8000):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

def test_app_import():
    print("🔧 Testing Application Import:")
    try:
        from app.main import app
        print("   ✅ FastAPI app imported successfully")
        return True
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False

def create_simple_launcher():
    """Create a simple launcher script"""
    port = find_free_port()
    if not port:
        print("   ❌ No free ports found")
        return False
    
    launcher_content = f'''#!/usr/bin/env python3
import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🔐 Starting Credential Manager")
    print("=" * 40)
    print(f"🌐 Web Interface: http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop")
    print("=" * 40)
    
    try:
        uvicorn.run(app, host="127.0.0.1", port={port}, log_level="info")
    except Exception as e:
        print(f"❌ Error: {{e}}")
        print("💡 Try running: python3 troubleshoot.py")
'''
    
    with open('simple_run.py', 'w') as f:
        f.write(launcher_content)
    
    os.chmod('simple_run.py', 0o755)
    print(f"   ✅ Created simple_run.py (port {port})")
    return port

def main():
    print("🔐 Credential Manager Troubleshooting")
    print("=" * 40)
    
    # Step 1: Check Python
    print_step(1, "Checking Python Installation")
    check_python()
    
    # Step 2: Check Virtual Environment
    print_step(2, "Checking Virtual Environment")
    venv_ok = check_virtual_env()
    
    if not venv_ok:
        print("\n💡 To activate virtual environment:")
        print("   cd /home/deepak/credential-manager")
        print("   source venv/bin/activate")
        print("   python3 troubleshoot.py")
        return
    
    # Step 3: Check Dependencies
    print_step(3, "Checking Dependencies")
    deps_ok = check_dependencies()
    
    if not deps_ok:
        print("\n💡 To install missing dependencies:")
        print("   pip install -r requirements.txt")
        return
    
    # Step 4: Test App Import
    print_step(4, "Testing Application")
    app_ok = test_app_import()
    
    if not app_ok:
        print("\n❌ Application import failed")
        return
    
    # Step 5: Create Simple Launcher
    print_step(5, "Creating Simple Launcher")
    port = create_simple_launcher()
    
    if port:
        print(f"\n🎉 Troubleshooting Complete!")
        print(f"{'='*40}")
        print(f"✅ Everything looks good!")
        print(f"\n🚀 To start the application:")
        print(f"   python3 simple_run.py")
        print(f"\n🌐 Then visit: http://127.0.0.1:{port}")
        print(f"\n📱 Alternative methods:")
        print(f"   • CLI: python3 cli.py")
        print(f"   • Demo: python3 demo.py")
        print(f"   • Test: python3 test_installation.py")
    else:
        print("\n❌ Could not find free port")

if __name__ == "__main__":
    main()
