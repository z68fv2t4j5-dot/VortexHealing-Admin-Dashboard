#!/bin/bash
# Start Frontend Service

cd "$(dirname "$0")/frontend"

echo "🟢 Frontend starting..."
npm run dev
