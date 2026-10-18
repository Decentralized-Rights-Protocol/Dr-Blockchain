#!/usr/bin/env bash
set -euo pipefail

# DRP local single-validator network bootstrap.
# This script never deletes an existing node home unless RESET_HOME=1 is set.
# Do not use this script with a production validator home.

CHAIN_ID="${CHAIN_ID:-drp-testnet-1}"
MONIKER="${MONIKER:-drp-validator-1}"
DENOM="${DENOM:-udrp}"
KEY_NAME="${KEY_NAME:-validator}"
HOME_DIR="${HOME_DIR:-$PWD/.drpd}"
BIN="${BIN:-$PWD/build/drpd}"

if [[ ! -x "$BIN" ]]; then
  echo "drpd binary not found at $BIN" >&2
  echo "Build first: make build" >&2
  exit 1
fi

if [[ -z "$HOME_DIR" || "$HOME_DIR" == "/" || "$HOME_DIR" == "$HOME" ]]; then
  echo "Refusing unsafe HOME_DIR: '$HOME_DIR'" >&2
  exit 1
fi

if [[ -e "$HOME_DIR" ]]; then
  if [[ "${RESET_HOME:-0}" != "1" ]]; then
    echo "Node home already exists: $HOME_DIR" >&2
    echo "To preserve existing state, choose a new HOME_DIR, e.g. HOME_DIR=./.drpd-fresh make localnet." >&2
    echo "To explicitly reset this LOCAL DEVELOPMENT home, rerun with RESET_HOME=1." >&2
    exit 1
  fi
  echo "WARNING: RESET_HOME=1 will permanently delete this local development directory:" >&2
  echo "  $HOME_DIR" >&2
  rm -rf "$HOME_DIR"
fi

echo "==> Initializing chain (chain-id=$CHAIN_ID, moniker=$MONIKER)"
"$BIN" init "$MONIKER" --chain-id "$CHAIN_ID" --home "$HOME_DIR" >/dev/null

echo "==> Patching genesis denoms to $DENOM"
HOME_DIR="$HOME_DIR" DENOM="$DENOM" python3 - <<'PY'
import json, os

home = os.environ["HOME_DIR"]
denom = os.environ["DENOM"]
gen_path = os.path.join(home, "config", "genesis.json")

with open(gen_path, "r", encoding="utf-8") as f:
    gen = json.load(f)

app_state = gen.get("app_state", {})

def set_path(obj, path, value):
    cur = obj
    for key in path[:-1]:
        if key not in cur or cur[key] is None:
            cur[key] = {}
        cur = cur[key]
    cur[path[-1]] = value

set_path(app_state, ["staking", "params", "bond_denom"], denom)
set_path(app_state, ["mint", "params", "mint_denom"], denom)
set_path(app_state, ["crisis", "constant_fee", "denom"], denom)

gov_params = app_state.get("gov", {}).get("params", {})
min_deposit = gov_params.get("min_deposit", [])
for c in min_deposit:
    if isinstance(c, dict) and "denom" in c:
        c["denom"] = denom

gen["app_state"] = app_state

with open(gen_path, "w", encoding="utf-8") as f:
    json.dump(gen, f, indent=2, sort_keys=True)
PY

echo "==> Creating key: $KEY_NAME"
"$BIN" keys add "$KEY_NAME" --keyring-backend test --home "$HOME_DIR" >/dev/null
VAL_ADDR=$("$BIN" keys show "$KEY_NAME" --keyring-backend test --home "$HOME_DIR" -a)

echo "==> Adding genesis account (stake placeholder denom=$DENOM)"
"$BIN" add-genesis-account "$VAL_ADDR" "1000000000$DENOM" --home "$HOME_DIR"

echo "==> Creating gentx"
"$BIN" gentx "$KEY_NAME" "700000000$DENOM" \
  --keyring-backend test \
  --chain-id "$CHAIN_ID" \
  --home "$HOME_DIR"

echo "==> Collecting gentxs"
"$BIN" collect-gentxs --home "$HOME_DIR"

echo "==> Starting node"
echo "    HOME=$HOME_DIR"
echo "    CometBFT RPC: http://127.0.0.1:26657"
"$BIN" start --home "$HOME_DIR" --minimum-gas-prices "0.0$DENOM"
