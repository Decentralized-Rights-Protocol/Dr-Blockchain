#!/usr/bin/env bash
set -euo pipefail

# Simple DRP RPC smoke test against CometBFT RPC.
# Verifies the /status and /health endpoints respond locally.
#
# Usage:
#   ./scripts/smoke_rpc.sh [rpc_host] [rpc_port]
# Defaults:
#   rpc_host=127.0.0.1
#   rpc_port=26657

RPC_HOST="${1:-127.0.0.1}"
RPC_PORT="${2:-26657}"
BASE_URL="http://${RPC_HOST}:${RPC_PORT}"

echo "==> DRP RPC smoke: ${BASE_URL}"

echo "-- /status"
curl -fsSL "${BASE_URL}/status" | jq -r '.result.node_info.network, .result.sync_info.catching_up' || {
  echo "ERROR: /status failed"
  exit 1
}

echo "-- /health"
curl -fsS "${BASE_URL}/health" >/dev/null || {
  echo "ERROR: /health failed"
  exit 1
}

echo "OK: DRP RPC responding at ${BASE_URL}"

