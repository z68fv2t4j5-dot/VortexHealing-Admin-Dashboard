#!/bin/bash
# Start VortexHealing Admin Dashboard - All Services
# Usage: ./start.sh

echo "🚀 Starting VortexHealing Admin Dashboard..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

# Create a new window/tab for each service
echo -e "${BLUE}Starting Backend...${NC}"
open -a Terminal "$(pwd)/start_backend.sh"
sleep 2

echo -e "${BLUE}Starting Frontend...${NC}"
open -a Terminal "$(pwd)/start_frontend.sh"
sleep 2

echo ""
echo -e "${GREEN}✅ All services starting!${NC}"
echo ""
echo "Access the application:"
echo "  • Frontend: http://localhost:3000"
echo "  • Backend API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo ""
echo "Services will auto-reload on file changes."
echo "Close terminal windows to stop services."
