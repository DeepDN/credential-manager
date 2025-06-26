#!/bin/bash

# Foolproof script to run the Credential Manager

echo "🔐 Starting Credential Manager"
echo "=============================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Please run this from the credential-manager directory"
    echo "💡 Try: cd /home/deepak/credential-manager && ./run_now.sh"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found"
    echo "💡 Run: ./install.sh first"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if activation worked
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated"

# Test if app can be imported
echo "🧪 Testing application..."
python3 -c "from app.main import app; print('✅ Application ready')" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Application test failed"
    echo "💡 Try: pip install -r requirements.txt"
    exit 1
fi

# Find available port
echo "🔍 Finding available port..."
PORT=8000
while true; do
    if ! netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
        break
    fi
    PORT=$((PORT + 1))
    if [ $PORT -gt 8100 ]; then
        echo "❌ No available ports found"
        exit 1
    fi
done

echo "✅ Using port $PORT"

# Create temporary run script
cat > temp_run.py << EOF
#!/usr/bin/env python3
import uvicorn
from app.main import app

print("🌐 Credential Manager Web Interface")
print("=" * 40)
print(f"🔗 Open in browser: http://127.0.0.1:$PORT")
print("🛑 Press Ctrl+C to stop")
print("=" * 40)

try:
    uvicorn.run(app, host="127.0.0.1", port=$PORT, log_level="warning")
except KeyboardInterrupt:
    print("\n👋 Goodbye!")
except Exception as e:
    print(f"❌ Error: {e}")
EOF

# Run the application
echo "🚀 Starting web server..."
echo ""
python3 temp_run.py

# Cleanup
rm -f temp_run.py
