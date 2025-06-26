#!/usr/bin/env python3
import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🔐 Starting Credential Manager")
    print("=" * 40)
    print(f"🌐 Web Interface: http://127.0.0.1:8001")
    print("Press Ctrl+C to stop")
    print("=" * 40)
    
    try:
        uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Try running: python3 troubleshoot.py")
