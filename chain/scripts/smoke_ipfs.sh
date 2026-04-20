#!/usr/bin/env bash
set -euo pipefail

# IPFS API smoke: checks API /api/v0/version and optionally adds a small temp file.
#
# Usage:
#   ./scripts/smoke_ipfs.sh [ipfs_api_url]
# Default:
#   ipfs_api_url=${DRP_IPFS_API:-http://127.0.0.1:5001}

API_URL="${1:-${DRP_IPFS_API:-http://127.0.0.1:5001}}"

echo "==> IPFS API smoke at ${API_URL}"

echo "-- version"
curl -fsSL "${API_URL}/api/v0/version" | jq -r '.Version' || {
  echo "ERROR: IPFS /version failed"
  exit 1
}

TMPFILE="$(mktemp)"
echo "drp-ipfs-smoke-$(date -u +%s)" > "${TMPFILE}"
echo "-- add (temp file)"
CID="$(curl -fsS -F "file=@${TMPFILE}" "${API_URL}/api/v0/add" | jq -r '.Hash')"
rm -f "${TMPFILE}"
if [[ -z "${CID}" || "${CID}" == "null" ]]; then
  echo "ERROR: add failed"
  exit 1
fi
echo "Added CID: ${CID}"

echo "-- cat"
OUT="$(curl -fsS "${API_URL}/api/v0/cat?arg=${CID}")"
[[ -n "${OUT}" ]] || {
  echo "ERROR: cat failed"
  exit 1
}

echo "OK: IPFS API operational; sample CID=${CID}"

