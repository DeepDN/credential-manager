#!/bin/bash

# Credential Manager Startup Script

echo "🔐 Secure Credential Manager"
echo "=========================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./install.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo "✅ Virtual environment activated"
echo ""

# Show menu
echo "Choose interface:"
echo "1. Web Interface (Recommended)"
echo "2. Command Line Interface"
echo "3. Run Demo"
echo "4. Test Installation"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🌐 Starting Web Interface..."
        echo "Access at: http://127.0.0.1:8000"
        echo "Press Ctrl+C to stop"
        echo ""
        python3 run_web.py
        ;;
    2)
        echo ""
        echo "💻 Starting CLI Interface..."
        echo ""
        python3 cli.py
        ;;
    3)
        echo ""
        echo "🎬 Running Demo..."
        echo ""
        python3 demo.py
        ;;
    4)
        echo ""
        echo "🧪 Testing Installation..."
        echo ""
        python3 test_installation.py
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac
