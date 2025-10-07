#!/bin/bash

# DRP v0.6 - Complete Dependency Installation Script
# This script installs all dependencies required to run DRP programs and workflows

set -e  # Exit on any error

echo "🚀 DRP v0.6 - Installing All Dependencies"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check system requirements
echo "🔍 Checking System Requirements..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    print_error "Python 3.10+ required, found Python $PYTHON_VERSION"
    print_info "Please upgrade Python to 3.10 or higher"
    exit 1
else
    print_status "Python $PYTHON_VERSION ✓"
fi

# Check Node.js version
NODE_VERSION=$(node --version 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1)
if [ -z "$NODE_VERSION" ]; then
    print_error "Node.js not found. Please install Node.js 18+"
    exit 1
elif [ "$NODE_VERSION" -lt 18 ]; then
    print_error "Node.js 18+ required, found Node.js $(node --version)"
    exit 1
else
    print_status "Node.js $(node --version) ✓"
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker not found. Please install Docker"
    exit 1
else
    print_status "Docker $(docker --version | cut -d' ' -f3 | cut -d',' -f1) ✓"
fi

# Check Rust/Cargo
if ! command -v cargo &> /dev/null; then
    print_warning "Rust/Cargo not found. Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source ~/.cargo/env
    print_status "Rust installed ✓"
else
    print_status "Rust $(cargo --version | cut -d' ' -f2) ✓"
fi

echo ""
echo "📦 Installing Python Dependencies..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate
print_status "Virtual environment activated"

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip

# Install system dependencies for Python packages
print_info "Installing system dependencies..."

# macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    if command -v brew &> /dev/null; then
        print_info "Installing macOS dependencies via Homebrew..."
        brew install cmake pkg-config libffi openssl
        brew install postgresql redis
        brew install ffmpeg portaudio
    else
        print_warning "Homebrew not found. Please install system dependencies manually:"
        print_warning "  - cmake, pkg-config, libffi, openssl"
        print_warning "  - postgresql, redis"
        print_warning "  - ffmpeg, portaudio"
    fi
# Ubuntu/Debian
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    print_info "Installing Linux dependencies..."
    sudo apt-get update
    sudo apt-get install -y \
        build-essential \
        cmake \
        pkg-config \
        libffi-dev \
        libssl-dev \
        libpq-dev \
        redis-server \
        ffmpeg \
        portaudio19-dev \
        python3-dev \
        python3-pip
fi

# Install Python dependencies
print_info "Installing Python packages..."

# Install core dependencies first
pip install --upgrade setuptools wheel

# Install requirements
if [ -f "requirements.txt" ]; then
    print_info "Installing from requirements.txt..."
    pip install -r requirements.txt
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Install additional dependencies that might be missing
print_info "Installing additional Python dependencies..."
pip install \
    numpy \
    pandas \
    matplotlib \
    seaborn \
    jupyter \
    ipython \
    black \
    isort \
    mypy \
    bandit \
    safety \
    pre-commit

print_status "Python dependencies installed ✓"

echo ""
echo "📦 Installing Node.js Dependencies..."

# Check if package.json exists
if [ -f "package.json" ]; then
    print_info "Installing Node.js packages..."
    npm install
    print_status "Node.js dependencies installed ✓"
else
    print_warning "No package.json found. Creating basic Node.js setup..."
    
    # Create basic package.json for DRP
    cat > package.json << EOF
{
  "name": "drp-blockchain",
  "version": "0.6.0",
  "description": "Decentralized Rights Protocol - Blockchain Platform",
  "main": "index.js",
  "scripts": {
    "test": "jest",
    "lint": "eslint .",
    "build": "echo 'Build script placeholder'",
    "start": "echo 'Start script placeholder'"
  },
  "dependencies": {
    "express": "^4.18.0",
    "cors": "^2.8.5",
    "helmet": "^7.0.0",
    "dotenv": "^16.0.0"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "eslint": "^8.0.0",
    "nodemon": "^3.0.0"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
EOF
    
    npm install
    print_status "Basic Node.js setup created ✓"
fi

echo ""
echo "📦 Installing Rust Dependencies..."

# Install Rust dependencies for post-quantum cryptography
print_info "Installing Rust packages for post-quantum crypto..."

# Create basic Cargo.toml if it doesn't exist
if [ ! -f "Cargo.toml" ]; then
    cat > Cargo.toml << EOF
[package]
name = "drp-post-quantum"
version = "0.6.0"
edition = "2021"

[dependencies]
# Post-quantum cryptography
pqcrypto-kyber = "0.7"
pqcrypto-dilithium = "0.5"
rand = "0.8"
hex = "0.4"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

[dev-dependencies]
criterion = "0.5"
EOF
fi

# Build Rust dependencies
cargo build --release
print_status "Rust dependencies installed ✓"

echo ""
echo "🐳 Setting up Docker Environment..."

# Check if docker-compose files exist
if [ -f "scripts/docker-compose.yml" ]; then
    print_info "Setting up Docker containers..."
    cd scripts
    docker-compose pull
    print_status "Docker images pulled ✓"
    cd ..
else
    print_warning "Docker compose files not found in scripts/"
fi

echo ""
echo "🔧 Setting up Development Tools..."

# Install pre-commit hooks
if [ -f ".pre-commit-config.yaml" ]; then
    print_info "Installing pre-commit hooks..."
    pre-commit install
    print_status "Pre-commit hooks installed ✓"
else
    print_info "Creating pre-commit configuration..."
    cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
EOF
    pre-commit install
    print_status "Pre-commit configuration created ✓"
fi

echo ""
echo "🧪 Running Basic Tests..."

# Run basic tests to verify installation
print_info "Testing Python installation..."
python -c "import cryptography, fastapi, uvicorn, pytest; print('Core Python packages working ✓')"

print_info "Testing Node.js installation..."
node -e "console.log('Node.js working ✓')"

print_info "Testing Rust installation..."
cargo --version > /dev/null && echo "Rust working ✓"

echo ""
echo "📋 Creating Environment Configuration..."

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_info "Creating .env configuration file..."
    cat > .env << EOF
# DRP Environment Configuration
# Copy this file to .env.local and modify as needed

# Network Configuration
NETWORK_ID=drp-testnet
CHAIN_ID=1337
BLOCK_TIME=2

# Database Configuration
POSTGRES_URL=postgresql://drp_user:password@localhost:5432/drp_blockchain
REDIS_URL=redis://localhost:6379

# AI Configuration
AI_ELDER_COUNT=21
QUORUM_THRESHOLD=14
BIAS_DETECTION_ENABLED=true

# Security Configuration
JWT_SECRET=your-jwt-secret-here
ENCRYPTION_KEY=your-encryption-key-here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Development
DEBUG=true
LOG_LEVEL=INFO
EOF
    print_status ".env file created ✓"
fi

echo ""
echo "🎉 Installation Complete!"
echo "========================"
print_status "All dependencies installed successfully"
print_info "Virtual environment: venv/"
print_info "Python packages: $(pip list | wc -l) installed"
print_info "Node.js packages: $(npm list --depth=0 2>/dev/null | wc -l) installed"
print_info "Rust packages: $(cargo tree 2>/dev/null | wc -l) installed"

echo ""
echo "🚀 Next Steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Configure environment: cp .env .env.local && edit .env.local"
echo "3. Start development server: python -m uvicorn main:app --reload"
echo "4. Run tests: pytest"
echo "5. Start Docker services: cd scripts && docker-compose up -d"

echo ""
echo "📚 Documentation:"
echo "- Architecture: docs/architecture/DRP_ARCHITECTURE.md"
echo "- Security: .github/SECURITY.md"
echo "- Key Rotation: KEY_ROTATION.md"
echo "- API Docs: http://localhost:8000/docs (after starting server)"

print_status "DRP v0.6 is ready for development! 🎉"







