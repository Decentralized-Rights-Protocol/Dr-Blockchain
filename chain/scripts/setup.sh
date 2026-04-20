#!/usr/bin/env bash
# =============================================================================
# DRP Chain Development Setup Script
# =============================================================================
# Sets up the Go toolchain and downloads Cosmos SDK dependencies.
# Run this once after cloning the repo (or when updating Go version).
#
# Requirements: Go 1.21+, git
# Usage: cd chain && ./scripts/setup.sh
# =============================================================================
set -euo pipefail

log()  { echo "[setup] $*"; }
err()  { echo "[setup ERROR] $*" >&2; exit 1; }
check_cmd() { command -v "$1" &>/dev/null || err "$1 is required but not found. Please install it."; }

log "=== DRP Chain Setup ==="

# ── Prerequisites ─────────────────────────────────────────────────────────────
check_cmd go
check_cmd git

GO_VERSION=$(go version | awk '{print $3}')
log "Go version: $GO_VERSION"

REQUIRED_MINOR=21
ACTUAL_MINOR=$(go version | grep -oE 'go[0-9]+\.[0-9]+' | grep -oE '[0-9]+\.[0-9]+$' | cut -d. -f2)
if (( ACTUAL_MINOR < REQUIRED_MINOR )); then
  err "Go 1.${REQUIRED_MINOR}+ is required (found $GO_VERSION). Please upgrade: https://go.dev/dl/"
fi

# ── Change to chain directory ─────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAIN_DIR="$(dirname "$SCRIPT_DIR")"
cd "$CHAIN_DIR"
log "Working directory: $CHAIN_DIR"

# ── Download dependencies ─────────────────────────────────────────────────────
log "Running go mod tidy (downloads all Cosmos SDK dependencies)..."
log "This may take several minutes on first run..."
go mod tidy

log "go mod tidy complete."

# ── Build the binary ─────────────────────────────────────────────────────────
log "Building drpd binary..."
mkdir -p bin
go build -o bin/drpd ./cmd/drpd
log "Binary built: chain/bin/drpd"

# ── Verify ────────────────────────────────────────────────────────────────────
log ""
./bin/drpd version 2>/dev/null && log "Build successful!" || log "Binary built (version command not available yet)"
log ""
log "=== Setup Complete ==="
log ""
log "Next steps:"
log "  1. Start a local testnet:   ./scripts/localnet.sh"
log "  2. Or use the Makefile:     make localnet"
log "  3. See chain/README.md for full documentation."
