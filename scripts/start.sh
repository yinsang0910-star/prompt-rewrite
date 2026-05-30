#!/bin/bash
cd "$(dirname "$0")/.."

echo "====================================================="
echo "  Prompt Rewrite System  v0.2.0"
echo "  Smart Prompt Optimization"
echo "====================================================="
echo
echo "  Installing dependencies..."
pip install -r requirements.txt -q
echo
echo "  Starting server..."
echo
python3 launch_ui.py
