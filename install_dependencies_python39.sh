#!/bin/bash

# DRP v0.5 - Dependency Installation Script for Python 3.9
# This script installs dependencies compatible with Python 3.9

set -e  # Exit on any error

echo "🚀 DRP v0.5 - Installing Dependencies (Python 3.9 Compatible)"
echo "============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
print_warning "Using Python $PYTHON_VERSION (Note: Some features require Python 3.10+)"

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
        brew install cmake pkg-config libffi openssl || print_warning "Some packages may already be installed"
        brew install postgresql redis || print_warning "Some packages may already be installed"
        brew install ffmpeg portaudio || print_warning "Some packages may already be installed"
    else
        print_warning "Homebrew not found. Please install system dependencies manually:"
        print_warning "  - cmake, pkg-config, libffi, openssl"
        print_warning "  - postgresql, redis"
        print_warning "  - ffmpeg, portaudio"
    fi
fi

# Install Python dependencies
print_info "Installing Python packages..."

# Install core dependencies first
pip install --upgrade setuptools wheel

# Create Python 3.9 compatible requirements
print_info "Creating Python 3.9 compatible requirements..."
cat > requirements_python39.txt << EOF
# Core dependencies (Python 3.9 compatible)
ecdsa>=0.18.0
base58>=2.1.0
pynacl>=1.5.0
coincurve>=21.0.0
bip-utils>=2.9.0
mnemonic>=0.20
cryptography>=41.0.0
grpcio>=1.74.0
grpcio-tools>=1.74.0
protobuf>=6.31.0

# Web API dependencies
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic[dotenv]>=2.0.0
httpx>=0.24.0

# Testing and linting
pytest>=7.0.0
flake8>=6.0.0
pytest-cov>=4.0.0

# Storage layer dependencies
python-rocksdb>=0.7.0
neo4j>=5.0.0
ipfshttpclient>=0.8.0

# AI Verification Layer dependencies
opencv-python>=4.8.0
face-recognition>=1.3.0
mediapipe>=0.10.0
tensorflow>=2.13.0
transformers>=4.30.0
torch>=2.0.0
sentence-transformers>=2.2.0
scikit-learn>=1.3.0
speechrecognition>=3.10.0
pyaudio>=0.2.11
pydub>=0.25.1
aiohttp>=3.8.0

# Advanced Security & Token Features dependencies
py-ecc>=6.0.0
aioquic>=0.9.20
dnspython>=2.3.0

# Additional dependencies
numpy>=1.21.0
pandas>=1.3.0
matplotlib>=3.5.0
seaborn>=0.11.0
jupyter>=1.0.0
ipython>=7.0.0
black>=22.0.0
isort>=5.0.0
mypy>=1.0.0
bandit>=1.7.0
safety>=2.0.0
pre-commit>=3.0.0
EOF

# Install requirements
print_info "Installing Python 3.9 compatible packages..."
pip install -r requirements_python39.txt

print_status "Python dependencies installed ✓"

echo ""
echo "📦 Installing Node.js Dependencies..."

# Create basic package.json for DRP
print_info "Creating Node.js package configuration..."
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
    "start": "echo 'Start script placeholder'",
    "dev": "nodemon index.js"
  },
  "dependencies": {
    "express": "^4.18.0",
    "cors": "^2.8.5",
    "helmet": "^7.0.0",
    "dotenv": "^16.0.0",
    "ws": "^8.13.0",
    "axios": "^1.4.0",
    "jsonwebtoken": "^9.0.0",
    "bcryptjs": "^2.4.3"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "eslint": "^8.0.0",
    "nodemon": "^3.0.0",
    "@types/node": "^20.0.0"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
EOF

npm install
print_status "Node.js dependencies installed ✓"

echo ""
echo "📦 Installing Rust Dependencies..."

# Create basic Cargo.toml
print_info "Creating Rust package configuration..."
cat > Cargo.toml << EOF
[package]
name = "drp-post-quantum"
version = "0.6.0"
edition = "2021"

[dependencies]
# Basic cryptography (Python 3.9 compatible alternatives)
rand = "0.8"
hex = "0.4"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
sha2 = "0.10"
aes = "0.8"
chacha20poly1305 = "0.10"

[dev-dependencies]
criterion = "0.5"
EOF

# Build Rust dependencies
cargo build --release
print_status "Rust dependencies installed ✓"

echo ""
echo "🐳 Setting up Docker Environment..."

# Create docker-compose.yml for development
print_info "Creating Docker development environment..."
cat > docker-compose.dev.yml << EOF
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: drp_blockchain
      POSTGRES_USER: drp_user
      POSTGRES_PASSWORD: drp_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  postgres_data:
  redis_data:
  grafana_data:
EOF

# Create basic prometheus config
cat > prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'drp-blockchain'
    static_configs:
      - targets: ['localhost:8000']
EOF

print_info "Docker configuration created ✓"

echo ""
echo "🔧 Setting up Development Tools..."

# Create pre-commit configuration
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

# Create .env file
print_info "Creating .env configuration file..."
cat > .env << EOF
# DRP Environment Configuration (Python 3.9 Compatible)
# Copy this file to .env.local and modify as needed

# Network Configuration
NETWORK_ID=drp-testnet
CHAIN_ID=1337
BLOCK_TIME=2

# Database Configuration
POSTGRES_URL=postgresql://drp_user:drp_password@localhost:5432/drp_blockchain
REDIS_URL=redis://localhost:6379

# AI Configuration
AI_ELDER_COUNT=21
QUORUM_THRESHOLD=14
BIAS_DETECTION_ENABLED=true

# Security Configuration
JWT_SECRET=your-jwt-secret-here-change-in-production
ENCRYPTION_KEY=your-encryption-key-here-change-in-production

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
PYTHON_VERSION=3.9
EOF

print_status ".env file created ✓"

echo ""
echo "📝 Creating Development Scripts..."

# Create development scripts
cat > start_dev.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting DRP Development Environment..."

# Activate virtual environment
source venv/bin/activate

# Start Docker services
echo "Starting Docker services..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Start the development server
echo "Starting DRP API server..."
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
EOF

chmod +x start_dev.sh

cat > run_tests.sh << 'EOF'
#!/bin/bash
echo "🧪 Running DRP Tests..."

# Activate virtual environment
source venv/bin/activate

# Run Python tests
echo "Running Python tests..."
pytest tests/ -v --cov=.

# Run Node.js tests
echo "Running Node.js tests..."
npm test

# Run Rust tests
echo "Running Rust tests..."
cargo test

echo "✅ All tests completed!"
EOF

chmod +x run_tests.sh

print_status "Development scripts created ✓"

echo ""
echo "🎉 Installation Complete!"
echo "========================"
print_status "All dependencies installed successfully (Python 3.9 compatible)"
print_info "Virtual environment: venv/"
print_info "Python packages: $(pip list | wc -l) installed"
print_info "Node.js packages: $(npm list --depth=0 2>/dev/null | wc -l) installed"
print_info "Rust packages: $(cargo tree 2>/dev/null | wc -l) installed"

echo ""
echo "⚠️  IMPORTANT NOTES:"
echo "==================="
print_warning "You are using Python 3.9. Some advanced features require Python 3.10+:"
print_warning "  - python-oqs (post-quantum cryptography)"
print_warning "  - Some newer AI/ML libraries"
print_warning "  - Advanced type hints"

echo ""
print_info "To upgrade to Python 3.10+ (recommended):"
print_info "  macOS: brew install python@3.10"
print_info "  Ubuntu: sudo apt install python3.10"
print_info "  Or use pyenv: pyenv install 3.10.0"

echo ""
echo "🚀 Quick Start Commands:"
echo "======================="
echo "1. Activate environment: source venv/bin/activate"
echo "2. Start development: ./start_dev.sh"
echo "3. Run tests: ./run_tests.sh"
echo "4. View API docs: http://localhost:8000/docs"
echo "5. View monitoring: http://localhost:3000 (Grafana)"

echo ""
echo "📚 Documentation:"
echo "- Architecture: docs/architecture/DRP_ARCHITECTURE.md"
echo "- Security: .github/SECURITY.md"
echo "- Key Rotation: KEY_ROTATION.md"

print_status "DRP v0.5 is ready for development! 🎉"







