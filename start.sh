#!/bin/bash
echo "====================================================="
echo "  🪄  Prompt Rewrite System  v0.2.0"
echo "  Smart Prompt Optimization"
echo "====================================================="
echo
echo "  Installing dependencies..."
pip install -r requirements.txt -q
echo
echo "  Starting server..."
echo
python launch_ui.py
