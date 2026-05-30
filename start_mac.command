#!/bin/bash
# Prompt Rewrite System — macOS launcher
# Usage: double-click in Finder, or run: bash start.sh

set -e
cd "$(dirname "$0")"

echo "====================================================="
echo "  Prompt Rewrite System v0.2.0"
echo "====================================================="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+ first."
    echo "   brew install python3"
    echo "   or download from https://python.org"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Install deps if not already
echo "📦 Checking dependencies..."
python3 -m pip install -r requirements.txt -q 2>/dev/null || true

# Start server
echo "🚀 Starting server..."
echo ""
echo "   Browser will open: http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""

python3 launch_ui.py &

sleep 2
open http://localhost:8000 2>/dev/null || true

# Wait for server process
wait
