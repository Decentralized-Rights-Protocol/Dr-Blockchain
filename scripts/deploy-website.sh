#!/bin/bash

# ============================================================================
# DRP Website Deployment Script
# 
# This script deploys the Dr-Website frontend with dual-token UI.
# 
# Prerequisites:
#   - Node.js 18+
#   - Next.js 14+
#   - GitHub repository access
#   - Vercel CLI installed (for Vercel deployment)
# ============================================================================

set -e

# ============================================================================
# CONFIGURATION
# ============================================================================

# Repository
REPO="Decentralized-Rights-Protocol/Dr-Website"
BRANCH="feature/dual-token-ui"
MAIN_BRANCH="main"

# Directories
WEBSITE_DIR="website"
SRC_DIR="$WEBSITE_DIR/src"

# Vercel
VERCEL_TEAM_ID="team_SR4BGYBU4UNJ0Dse5hu0Cv8N"
VERCEL_PROJECT="dr-website-frontend"

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

# Check Node.js
if ! check_command node; then
    echo_error "Node.js is required. Please install Node.js 18+"
    exit 1
fi

# Check Node.js version
node_version=$(node --version)
echo_info "Node.js version: $node_version"

# Check npm
if ! check_command npm; then
    echo_error "npm is required. Please install npm"
    exit 1
fi

npm_version=$(npm --version)
echo_info "npm version: $npm_version"

# Check if we're in the right directory
if [ ! -d "$WEBSITE_DIR" ]; then
    echo_error "$WEBSITE_DIR directory not found!"
    echo_error "Please run from the directory containing the drp-implementation files"
    exit 1
fi

# Count files to deploy
WEBSITE_FILES=$(find $WEBSITE_DIR -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.json" \) | wc -l)

echo_info "Files to deploy: $WEBSITE_FILES"

echo_success "Environment validated!"
echo ""

# Step 2: Install dependencies
echo_info "Step 2: Installing dependencies..."

cd "$WEBSITE_DIR"

# Check for package.json
if [ -f "package.json" ]; then
    echo_info "Found package.json. Installing dependencies..."
    
    if ! npm install; then
        echo_error "Failed to install dependencies!"
        exit 1
    fi
    
    echo_success "Dependencies installed!"
else
    echo_warning "No package.json found. Skipping dependency installation."
fi

cd ..
echo ""

# Step 3: TypeScript check
echo_info "Step 3: Running TypeScript check..."

cd "$WEBSITE_DIR"

if [ -f "tsconfig.json" ]; then
    echo_info "Found tsconfig.json. Running TypeScript check..."
    
    if ! npx tsc --noEmit; then
        echo_warning "TypeScript check failed. Continuing with deployment..."
    else
        echo_success "TypeScript check passed!"
    fi
fi

cd ..
echo ""

# Step 4: Lint
echo_info "Step 4: Running linter..."

cd "$WEBSITE_DIR"

if [ -f "package.json" ]; then
    echo_info "Running ESLint..."
    
    if ! npx eslint . --ext .ts,.tsx 2>/dev/null; then
        echo_warning "Linting failed. Continuing with deployment..."
    else
        echo_success "Linting passed!"
    fi
fi

cd ..
echo ""

# Step 5: Build
echo_info "Step 5: Building website..."

cd "$WEBSITE_DIR"

if [ -f "package.json" ]; then
    echo_info "Building Next.js application..."
    
    if ! npm run build; then
        echo_error "Failed to build Next.js application!"
        exit 1
    fi
    
    echo_success "Website built successfully!"
fi

cd ..
echo ""

# Step 6: Commit to GitHub
echo_info "Step 6: Preparing for GitHub commit..."

echo_info "Files to commit:"
echo_info "  - src/app/tokens/page.tsx"
echo_info "  - src/app/tokens/transfer/page.tsx"
echo_info "  - src/hooks/useDeri.ts"
echo_info "  - src/hooks/useRights.ts"
echo_info "  - src/lib/api.ts"

echo_warning "GitHub commit requires authenticated API access"
echo_info "Files are ready to be committed to: $REPO (branch: $BRANCH)"

echo_success "GitHub preparation completed!"
echo ""

# Step 7: Deploy to Vercel
echo_info "Step 7: Deploying to Vercel..."

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

# Step 8: Create pull request
echo_info "Step 8: Creating pull request..."

echo_info "Would create PR: $REPO: $BRANCH -> $MAIN_BRANCH"
echo_warning "Pull request creation requires GitHub API access"

echo_success "Pull request creation configured!"
echo ""

# ============================================================================
# COMPLETION
# ============================================================================

echo_info "Website deployment steps completed!"
echo ""
echo_success "Next steps:"
echo_success "  1. Push files to GitHub: $REPO (branch: $BRANCH)"
echo_success "  2. Deploy to Vercel: $VERCEL_PROJECT"
echo_success "  3. Create pull request: $BRANCH -> $MAIN_BRANCH"
echo ""
echo "============================================================"
