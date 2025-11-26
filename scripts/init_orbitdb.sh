#!/bin/bash

# Initialize OrbitDB for DRP
# This script sets up OrbitDB and IPFS for local development

set -e

echo "🚀 Initializing OrbitDB for DRP..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ is required. Current version: $(node -v)"
    exit 1
fi

# Navigate to orbitdb directory
cd "$(dirname "$0")/../orbitdb"

# Install npm dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing OrbitDB dependencies..."
    npm install
fi

# Create orbitdb data directory
ORBITDB_DIR="${ORBITDB_DIR:-$(pwd)/../orbitdb}"
mkdir -p "$ORBITDB_DIR"

echo "✅ OrbitDB initialization complete!"
echo ""
echo "To start OrbitDB, run:"
echo "  cd orbitdb && node orbit_manager.js"

