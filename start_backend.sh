#!/bin/bash
# Start Backend Service

cd "$(dirname "$0")/backend"

echo "🔵 Backend starting..."
source venv/bin/activate
python main.py
