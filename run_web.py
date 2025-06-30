#!/usr/bin/env python3
"""
Web server launcher for Credential Manager
"""
import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🔐 Starting Secure Credential Manager Web Interface")
    print("=" * 50)
    
    # Get host and port from environment variables (for Docker)
    host = os.getenv("SECUREVAULT_HOST", "127.0.0.1")
    port = int(os.getenv("SECUREVAULT_PORT", "8000"))
    
    print(f"Access the application at: http://{host}:{port}")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )
