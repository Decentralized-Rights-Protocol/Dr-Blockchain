#!/bin/bash

# Run local DRP network
# Starts FastAPI, OrbitDB, and RPC server

set -e

echo "🚀 Starting DRP Local Network..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed."
    exit 1
fi

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
fi

# Set defaults
export BLOCKCHAIN_NETWORK="${BLOCKCHAIN_NETWORK:-drp-testnet}"
export ORBITDB_DIR="${ORBITDB_DIR:-$PROJECT_ROOT/orbitdb}"
export IPFS_API_URL="${IPFS_API_URL:-http://localhost:5001/api/v0}"
export FASTAPI_HOST="${FASTAPI_HOST:-0.0.0.0}"
export FASTAPI_PORT="${FASTAPI_PORT:-8000}"
export RPC_HOST="${RPC_HOST:-0.0.0.0}"
export RPC_PORT="${RPC_PORT:-8545}"

echo "📋 Configuration:"
echo "  Blockchain Network: $BLOCKCHAIN_NETWORK"
echo "  OrbitDB Directory: $ORBITDB_DIR"
echo "  IPFS API: $IPFS_API_URL"
echo "  FastAPI: http://$FASTAPI_HOST:$FASTAPI_PORT"
echo "  RPC Server: http://$RPC_HOST:$RPC_PORT"
echo ""

# Create necessary directories
mkdir -p "$ORBITDB_DIR"
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/network"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $FASTAPI_PID $RPC_PID $ORBITDB_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start OrbitDB (in background)
echo "🌐 Starting OrbitDB..."
cd "$PROJECT_ROOT/orbitdb"
if [ ! -d "node_modules" ]; then
    npm install --silent
fi
node orbit_manager.js &
ORBITDB_PID=$!
echo "  OrbitDB PID: $ORBITDB_PID"
sleep 2

# Start RPC Server (in background)
echo "⛓️  Starting RPC Server..."
cd "$PROJECT_ROOT"
python3 -m network.rpc_server &
RPC_PID=$!
echo "  RPC Server PID: $RPC_PID"
sleep 2

# Start FastAPI AI Service (in background)
echo "🤖 Starting FastAPI AI Service..."
cd "$PROJECT_ROOT"
python3 -m ai.fastapi_server &
FASTAPI_PID=$!
echo "  FastAPI PID: $FASTAPI_PID"
sleep 2

# Start Main API Server (foreground)
echo "🌍 Starting Main API Server..."
echo ""
echo "✅ All services started!"
echo ""
echo "📍 Endpoints:"
echo "  Main API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  AI Service: http://localhost:8000/ai"
echo "  RPC Server: http://localhost:8545"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

cd "$PROJECT_ROOT"
python3 -m api.router

