#!/usr/bin/env python3
"""
Web server launcher for Credential Manager (alternative port)
"""
import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🔐 Starting Secure Credential Manager Web Interface")
    print("=" * 50)
    print("Access the application at: http://127.0.0.1:8080")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8080,
        log_level="info",
        access_log=True
    )
