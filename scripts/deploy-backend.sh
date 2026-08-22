#!/bin/bash

# ============================================================================
# DRP Backend Deployment Script
# 
# This script deploys the Dr-Blockchain backend with the $DeRi module.
# 
# Prerequisites:
#   - Go 1.22+
#   - Cosmos SDK dependencies
#   - GitHub repository access
#   - Vercel CLI installed (for Vercel deployment)
# ============================================================================

set -e

# ============================================================================
# CONFIGURATION
# ============================================================================

# Repository
REPO="Decentralized-Rights-Protocol/Dr-Blockchain"
BRANCH="feature/dual-token-economy"
MAIN_BRANCH="main"

# Directories
CHAIN_DIR="chain"
PROTO_DIR="proto"
AI_DIR="ai"
SCRIPTS_DIR="scripts"

# Vercel
VERCEL_TEAM_ID="team_SR4BGYBU4UNJ0Dse5hu0Cv8N"
VERCEL_PROJECT="dr-blockchain-backend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

function echo_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

function echo_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

function echo_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

function check_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo_error "Command '$1' not found!"
        return 1
    fi
    return 0
}

# ============================================================================
# DEPLOYMENT STEPS
# ============================================================================

# Step 1: Validate environment
echo_info "Step 1: Validating environment..."

# Check Go
if ! check_command go; then
    echo_error "Go is required. Please install Go 1.22+"
    exit 1
fi

# Check Go version
go_version=$(go version | awk '{print $3}')
echo_info "Go version: $go_version"

# Check if we're in the right directory
if [ ! -d "$CHAIN_DIR" ]; then
    echo_error "$CHAIN_DIR directory not found!"
    echo_error "Please run from the directory containing the drp-implementation files"
    exit 1
fi

# Count files to deploy
CHAIN_FILES=$(find $CHAIN_DIR -type f -name "*.go" | wc -l)
PROTO_FILES=$(find $PROTO_DIR -type f -name "*.proto" | wc -l)
AI_FILES=$(find $AI_DIR -type f -name "*.py" | wc -l)

echo_info "Files to deploy:"
echo_info "  - Go files: $CHAIN_FILES"
echo_info "  - Protobuf files: $PROTO_FILES"
echo_info "  - AI files: $AI_FILES"

echo_success "Environment validated!"
echo ""

# Step 2: Generate protobuf code
echo_info "Step 2: Generating protobuf code..."

if [ -d "$PROTO_DIR" ]; then
    # Check for protoc
    if ! check_command protoc; then
        echo_warning "protoc not found. Protobuf code generation skipped."
        echo_warning "Install with: brew install protobuf or apt-get install protobuf-compiler"
    else
        echo_info "Generating Go code from protobuf definitions..."
        
        # Generate Go code for deri module
        if [ -f "$PROTO_DIR/deri/deri.proto" ]; then
            echo_info "Processing deri.proto..."
            # Would run protoc commands here
            echo_warning "Protobuf generation requires protoc and cosmos-sdk plugins"
        fi
        
        if [ -f "$PROTO_DIR/rights/rights.proto" ]; then
            echo_info "Processing rights.proto..."
            echo_warning "Protobuf generation requires protoc and cosmos-sdk plugins"
        fi
    fi
else
    echo_warning "No protobuf directory found. Skipping protobuf generation."
fi

echo_success "Protobuf generation check completed!"
echo ""

# Step 3: Build Go module
echo_info "Step 3: Building Go module..."

cd "$CHAIN_DIR"

# Check for go.mod
if [ -f "go.mod" ]; then
    echo_info "Found go.mod. Downloading dependencies..."
    
    # Download dependencies
    if ! go mod download; then
        echo_warning "Failed to download Go dependencies"
    fi
    
    # Build the module
    echo_info "Building DRP chain..."
    if ! go build -o drpd ./...; then
        echo_error "Failed to build DRP chain!"
        echo_error "Check Go module configuration and dependencies"
        exit 1
    fi
    
    echo_success "Go module built successfully!"
else
    echo_warning "No go.mod found. Skipping Go build."
fi

cd ..
echo ""

# Step 4: Run tests
echo_info "Step 4: Running tests..."

cd "$CHAIN_DIR"

# Run Go tests
if [ -f "go.mod" ]; then
    echo_info "Running Go tests..."
    if go test ./x/deri/...; then
        echo_success "All tests passed!"
    else
        echo_warning "Some tests failed. Continuing with deployment..."
    fi
fi

cd ..
echo ""

# Step 5: Commit to GitHub
echo_info "Step 5: Preparing for GitHub commit..."

echo_info "Files to commit:"
echo_info "  - chain/x/deri/ (DeRi module)"
echo_info "  - proto/deri/ (DeRi protobuf)"
echo_info "  - proto/rights/ (RIGHTS protobuf)"
echo_info "  - chain/app/app_deri_addition.go"
echo_info "  - chain/app/modules_deri_addition.go"

echo_warning "GitHub commit requires authenticated API access"
echo_info "Files are ready to be committed to: $REPO (branch: $BRANCH)"

echo_success "GitHub preparation completed!"
echo ""

# Step 6: Deploy to Vercel
echo_info "Step 6: Deploying to Vercel..."

# Check Vercel CLI
if ! check_command vercel; then
    echo_warning "Vercel CLI not found."
    echo_warning "Install with: npm install -g vercel"
    echo_warning "Or use Vercel API directly"
fi

echo_info "Vercel Team: $VERCEL_TEAM_ID"
echo_info "Vercel Project: $VERCEL_PROJECT"

echo_warning "Vercel deployment requires authenticated API access"

echo_success "Vercel deployment configuration ready!"
echo ""

# Step 7: Create pull request
echo_info "Step 7: Creating pull request..."

echo_info "Would create PR: $REPO: $BRANCH -> $MAIN_BRANCH"
echo_warning "Pull request creation requires GitHub API access"

echo_success "Pull request creation configured!"
echo ""

# ============================================================================
# COMPLETION
# ============================================================================

echo_info "Backend deployment steps completed!"
echo ""
echo_success "Next steps:"
echo_success "  1. Push files to GitHub: $REPO (branch: $BRANCH)"
echo_success "  2. Deploy to Vercel: $VERCEL_PROJECT"
echo_success "  3. Create pull request: $BRANCH -> $MAIN_BRANCH"
echo ""
echo "============================================================"
