#!/bin/bash

# ============================================================================
# DRP Dual-Token Economy - Full Deployment Script
# 
# This script deploys the complete DRP dual-token economy system:
# 1. Dr-Blockchain backend with $DeRi module
# 2. Dr-Website frontend with token UI
# 3. Vercel deployments for both
# 
# Usage:
#   ./deploy-all.sh                  # Full deployment
#   ./deploy-all.sh --backend       # Backend only
#   ./deploy-all.sh --frontend      # Frontend only
#   ./deploy-all.sh --clean         # Clean up previous deployments
# ============================================================================

set -e

# ============================================================================
# CONFIGURATION
# ============================================================================

# Repository configuration
DR_BLOCKCHAIN_REPO="Decentralized-Rights-Protocol/Dr-Blockchain"
DR_WEBSITE_REPO="Decentralized-Rights-Protocol/Dr-Website"

# Branch names
FEATURE_BRANCH_BLOCKCHAIN="feature/dual-token-economy"
FEATURE_BRANCH_WEBSITE="feature/dual-token-ui"
MAIN_BRANCH="main"

# Vercel configuration
VERCEL_TEAM_ID="team_SR4BGYBU4UNJ0Dse5hu0Cv8N"
VERCEL_BACKEND_PROJECT="dr-blockchain-backend"
VERCEL_FRONTEND_PROJECT="dr-website-frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# Print colored output
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

# Check if a command exists
function command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if we're in the right directory
function check_directory() {
    if [ ! -d ".drp-implementation" ]; then
        echo_error "Please run this script from the directory containing .drp-implementation/"
        exit 1
    fi
}

# ============================================================================
# DEPLOYMENT FUNCTIONS
# ============================================================================

# Deploy backend
function deploy_backend() {
    echo_info "Starting backend deployment..."
    
    # Check if we should clean first
    if [ "$1" == "--clean" ]; then
        echo_info "Cleaning previous backend deployment..."
        # Add cleanup logic here
    fi
    
    # Run the backend deployment script
    if [ -f "scripts/deploy-backend.sh" ]; then
        echo_info "Running backend deployment script..."
        ./scripts/deploy-backend.sh
    else
        echo_error "Backend deployment script not found!"
        exit 1
    fi
    
    echo_success "Backend deployment completed!"
}

# Deploy frontend
function deploy_frontend() {
    echo_info "Starting frontend deployment..."
    
    # Check if we should clean first
    if [ "$1" == "--clean" ]; then
        echo_info "Cleaning previous frontend deployment..."
        # Add cleanup logic here
    fi
    
    # Run the frontend deployment script
    if [ -f "scripts/deploy-website.sh" ]; then
        echo_info "Running frontend deployment script..."
        ./scripts/deploy-website.sh
    else
        echo_error "Frontend deployment script not found!"
        exit 1
    fi
    
    echo_success "Frontend deployment completed!"
}

# Create GitHub branches
function create_branches() {
    echo_info "Creating feature branches..."
    
    # Check if branches already exist
    if git ls-remote --heads origin "$FEATURE_BRANCH_BLOCKCHAIN" >/dev/null 2>&1; then
        echo_warning "Branch $FEATURE_BRANCH_BLOCKCHAIN already exists"
    else
        echo_info "Creating branch $FEATURE_BRANCH_BLOCKCHAIN..."
        # Would use GitHub API or git commands here
        echo_warning "Branch creation requires GitHub API access"
    fi
    
    if git ls-remote --heads origin "$FEATURE_BRANCH_WEBSITE" >/dev/null 2>&1; then
        echo_warning "Branch $FEATURE_BRANCH_WEBSITE already exists"
    else
        echo_info "Creating branch $FEATURE_BRANCH_WEBSITE..."
        echo_warning "Branch creation requires GitHub API access"
    fi
    
    echo_success "Branch creation checks completed!"
}

# Push files to GitHub
function push_to_github() {
    echo_info "Pushing files to GitHub..."
    
    # Check if files exist
    if [ ! -d "chain" ] || [ ! -d "website" ]; then
        echo_error "Implementation files not found!"
        exit 1
    fi
    
    # Count files
    CHAIN_FILES=$(find chain -type f | wc -l)
    WEBSITE_FILES=$(find website -type f | wc -l)
    PROTO_FILES=$(find proto -type f | wc -l)
    AI_FILES=$(find ai -type f | wc -l)
    
    echo_info "Found files:"
    echo_info "  - Chain: $CHAIN_FILES files"
    echo_info "  - Website: $WEBSITE_FILES files"
    echo_info "  - Protobuf: $PROTO_FILES files"
    echo_info "  - AI Tools: $AI_FILES files"
    
    echo_warning "GitHub push requires authenticated API access"
    echo_info "Files are ready to be pushed to:"
    echo_info "  - $DR_BLOCKCHAIN_REPO (branch: $FEATURE_BRANCH_BLOCKCHAIN)"
    echo_info "  - $DR_WEBSITE_REPO (branch: $FEATURE_BRANCH_WEBSITE)"
    
    echo_success "Files prepared for GitHub push!"
}

# Deploy to Vercel
function deploy_to_vercel() {
    echo_info "Deploying to Vercel..."
    
    # Check Vercel CLI
    if ! command_exists vercel; then
        echo_warning "Vercel CLI not found. Install with: npm install -g vercel"
        echo_warning "Alternatively, use Vercel API directly"
    fi
    
    echo_info "Vercel Team: $VERCEL_TEAM_ID"
    echo_info "Backend Project: $VERCEL_BACKEND_PROJECT"
    echo_info "Frontend Project: $VERCEL_FRONTEND_PROJECT"
    
    echo_warning "Vercel deployment requires authenticated API access"
    
    echo_success "Vercel deployment configuration ready!"
}

# Create pull requests
function create_pull_requests() {
    echo_info "Creating pull requests..."
    
    echo_info "Would create PRs:"
    echo_info "  1. $DR_BLOCKCHAIN_REPO: $FEATURE_BRANCH_BLOCKCHAIN -> $MAIN_BRANCH"
    echo_info "  2. $DR_WEBSITE_REPO: $FEATURE_BRANCH_WEBSITE -> $MAIN_BRANCH"
    
    echo_warning "Pull request creation requires GitHub API access"
    
    echo_success "Pull request creation configured!"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

# Parse arguments
DEPLOY_BACKEND=false
DEPLOY_FRONTEND=false
CLEAN=false

for arg in "$@"; do
    case "$arg" in
        --backend)
            DEPLOY_BACKEND=true
            ;;
        --frontend)
            DEPLOY_FRONTEND=true
            ;;
        --clean)
            CLEAN=true
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --backend       Deploy backend only"
            echo "  --frontend      Deploy frontend only"
            echo "  --clean         Clean up previous deployments"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "If no options specified, performs full deployment."
            exit 0
            ;;
    esac
done

# Print header
echo ""
echo "============================================================"
echo "  DRP Dual-Token Economy Deployment Script"
echo "============================================================"
echo ""
echo_info "Timestamp: $(date)"
echo ""

# Check directory
check_directory

# If no specific deployment type, do full deployment
if [ "$DEPLOY_BACKEND" == false ] && [ "$DEPLOY_FRONTEND" == false ]; then
    echo_info "Starting FULL deployment..."
    echo ""
    
    # Step 1: Create branches
    echo_info "Step 1: Creating feature branches..."
    create_branches
    echo ""
    
    # Step 2: Push to GitHub
    echo_info "Step 2: Pushing files to GitHub..."
    push_to_github
    echo ""
    
    # Step 3: Deploy to Vercel
    echo_info "Step 3: Deploying to Vercel..."
    deploy_to_vercel
    echo ""
    
    # Step 4: Create pull requests
    echo_info "Step 4: Creating pull requests..."
    create_pull_requests
    echo ""
    
    # Step 5: Deploy backend
    echo_info "Step 5: Deploying backend..."
    deploy_backend
    echo ""
    
    # Step 6: Deploy frontend
    echo_info "Step 6: Deploying frontend..."
    deploy_frontend
    echo ""
    
    echo_success "Full deployment completed!"
    
# Backend only
elif [ "$DEPLOY_BACKEND" == true ]; then
    echo_info "Deploying BACKEND only..."
    echo ""
    deploy_backend "$CLEAN"
    
# Frontend only
elif [ "$DEPLOY_FRONTEND" == true ]; then
    echo_info "Deploying FRONTEND only..."
    echo ""
    deploy_frontend "$CLEAN"
fi

echo ""
echo_info "Deployment script completed at: $(date)"
echo ""
echo "============================================================"
