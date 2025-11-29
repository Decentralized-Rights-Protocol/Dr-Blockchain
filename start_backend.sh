#!/bin/bash
# Start DRP Backend Server

echo "🚀 Starting DRP Backend..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

# Check dependencies
echo "📦 Checking dependencies..."
python3 -c "import fastapi, uvicorn" 2>/dev/null || {
    echo "⚠️  Installing dependencies..."
    pip install -q fastapi uvicorn pydantic-settings
}

# Create directories
mkdir -p data/chain orbitdb logs

# Set environment variables if not set
export API_HOST=${API_HOST:-0.0.0.0}
export API_PORT=${API_PORT:-8000}
export BLOCKCHAIN_NETWORK=${BLOCKCHAIN_NETWORK:-drp-testnet}
export CHAIN_ID=${CHAIN_ID:-drp-testnet}
export LOG_LEVEL=${LOG_LEVEL:-INFO}

echo "📍 Starting server on http://${API_HOST}:${API_PORT}"
echo "📍 Network: ${BLOCKCHAIN_NETWORK}"
echo ""
echo "✅ Backend ready! Press Ctrl+C to stop"
echo ""

# Start server
python3 main.py

