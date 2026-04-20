#!/usr/bin/env bash
# =============================================================================
# DRP Multi-Validator Local Testnet (2-node)
# =============================================================================
# Launches two DRP validator nodes on localhost using separate home directories
# and port offsets. Useful for testing consensus, IBC, and slashing behaviour.
#
# Usage:
#   ./scripts/multivalidator.sh           # start 2 validators
#   ./scripts/multivalidator.sh stop      # stop all background validators
#
# Architecture:
#   Node 0 — ~/.drpd/node0 — RPC :26657, P2P :26656, API :1317
#   Node 1 — ~/.drpd/node1 — RPC :36657, P2P :36656, API :1327
# =============================================================================
set -euo pipefail

CHAIN_ID="${CHAIN_ID:-drp-testnet-1}"
DRPD="${DRPD:-$(dirname "$0")/../bin/drpd}"
BASE_HOME="${HOME}/.drpd"
N0_HOME="${BASE_HOME}/node0"
N1_HOME="${BASE_HOME}/node1"
PID_FILE="/tmp/drp-multivalidator.pids"

log() { echo "[DRP multi] $*"; }

if [[ "${1:-start}" == "stop" ]]; then
  log "Stopping all validator nodes..."
  if [[ -f "$PID_FILE" ]]; then
    while IFS= read -r pid; do
      kill "$pid" 2>/dev/null && log "Killed PID $pid" || true
    done < "$PID_FILE"
    rm -f "$PID_FILE"
  fi
  log "Done."
  exit 0
fi

[[ -x "$DRPD" ]] || { log "Building drpd..."; (cd "$(dirname "$0")/.." && go build -o bin/drpd ./cmd/drpd); }

# ── Init both nodes ───────────────────────────────────────────────────────────
for i in 0 1; do
  HOME_DIR="${BASE_HOME}/node${i}"
  log "Initialising node${i} at $HOME_DIR..."
  rm -rf "$HOME_DIR"
  "$DRPD" init "drp-validator-${i}" --chain-id "$CHAIN_ID" --home "$HOME_DIR"
done

# ── Create keys ───────────────────────────────────────────────────────────────
for i in 0 1; do
  "$DRPD" keys add "val${i}" --keyring-backend test --home "${BASE_HOME}/node${i}" 2>&1
done

ADDR0=$("$DRPD" keys show val0 -a --keyring-backend test --home "$N0_HOME")
ADDR1=$("$DRPD" keys show val1 -a --keyring-backend test --home "$N1_HOME")
log "Node0 address: $ADDR0"
log "Node1 address: $ADDR1"

# ── Genesis setup on node0 ────────────────────────────────────────────────────
python3 -c "
import json
with open('${N0_HOME}/config/genesis.json') as f: g = json.load(f)
g['app_state']['staking']['params']['bond_denom'] = 'udrp'
g['app_state']['mint']['params']['mint_denom'] = 'udrp'
g['app_state']['crisis']['constant_fee'] = {'denom':'udrp','amount':'1000'}
with open('${N0_HOME}/config/genesis.json','w') as f: json.dump(g, f, indent=2)
"

"$DRPD" add-genesis-account "$ADDR0" 10000000000udrp --home "$N0_HOME"
"$DRPD" add-genesis-account "$ADDR1" 10000000000udrp --home "$N0_HOME"

# ── gentxs ───────────────────────────────────────────────────────────────────
"$DRPD" gentx val0 1000000000udrp --chain-id "$CHAIN_ID" --keyring-backend test --home "$N0_HOME"
# Node1 gentx needs the genesis from node0 to validate
cp "${N0_HOME}/config/genesis.json" "${N1_HOME}/config/genesis.json"
"$DRPD" gentx val1 1000000000udrp --chain-id "$CHAIN_ID" --keyring-backend test --home "$N1_HOME" \
  --output-document "${N0_HOME}/config/gentx/gentx-node1.json"

"$DRPD" collect-gentxs --home "$N0_HOME"
"$DRPD" validate-genesis --home "$N0_HOME"

# ── Distribute final genesis ─────────────────────────────────────────────────
cp "${N0_HOME}/config/genesis.json" "${N1_HOME}/config/genesis.json"

# ── Configure node1 ports ────────────────────────────────────────────────────
NODE0_ID=$("$DRPD" tendermint show-node-id --home "$N0_HOME")
sed -i.bak \
  -e 's|laddr = "tcp://127.0.0.1:26657"|laddr = "tcp://127.0.0.1:36657"|' \
  -e 's|laddr = "tcp://0.0.0.0:26656"|laddr = "tcp://0.0.0.0:36656"|' \
  -e "s|persistent_peers = \"\"|persistent_peers = \"${NODE0_ID}@127.0.0.1:26656\"|" \
  "${N1_HOME}/config/config.toml"

sed -i.bak \
  -e 's|address = "0.0.0.0:9090"|address = "0.0.0.0:9091"|' \
  -e 's|address = "0.0.0.0:9091"|address = "0.0.0.0:9092"|' \
  -e 's|address = "tcp://0.0.0.0:1317"|address = "tcp://0.0.0.0:1327"|' \
  "${N1_HOME}/config/app.toml"

# ── Start nodes ───────────────────────────────────────────────────────────────
log "Starting node0 (RPC :26657)..."
"$DRPD" start --home "$N0_HOME" --minimum-gas-prices "0.001udrp" --log_level info &> "/tmp/drp-node0.log" &
echo $! > "$PID_FILE"

sleep 2
log "Starting node1 (RPC :36657)..."
"$DRPD" start --home "$N1_HOME" --minimum-gas-prices "0.001udrp" --log_level info &> "/tmp/drp-node1.log" &
echo $! >> "$PID_FILE"

log ""
log "=== DRP 2-validator testnet running ==="
log "  Node0 RPC: http://localhost:26657  | Logs: /tmp/drp-node0.log"
log "  Node1 RPC: http://localhost:36657  | Logs: /tmp/drp-node1.log"
log "  Stop: $0 stop"
