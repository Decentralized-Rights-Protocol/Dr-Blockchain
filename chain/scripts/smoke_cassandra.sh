#!/usr/bin/env bash
set -euo pipefail

# Cassandra smoke: ensures CQL port reachable and creates a temp keyspace/table,
# writes and reads a test row, then drops the keyspace.
#
# Prereq: local Docker compose cassandra exposes 9042.
# Default contact points: 127.0.0.1:9042 (no auth on dev image).
#
# Usage:
#   ./scripts/smoke_cassandra.sh [host] [port]

HOST="${1:-127.0.0.1}"
PORT="${2:-9042}"

echo "==> Cassandra smoke at ${HOST}:${PORT}"

which cqlsh >/dev/null 2>&1 || {
  echo "ERROR: cqlsh not found. Install cassandra-cqlsh or run via container:"
  echo "  docker run --rm -it --network host nuvo/docker-cqlsh cqlsh ${HOST} ${PORT}"
  exit 1
}

KS="drp_smoke_ks"
TABLE="kv"
KEY="$(date -u +%s)"
VAL="ok-${KEY}"

cat >/tmp/drp_smoke.cql <<EOF
CREATE KEYSPACE IF NOT EXISTS ${KS} WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 1};
CREATE TABLE IF NOT EXISTS ${KS}.${TABLE} (k text PRIMARY KEY, v text);
INSERT INTO ${KS}.${TABLE} (k, v) VALUES ('${KEY}', '${VAL}');
SELECT * FROM ${KS}.${TABLE} WHERE k='${KEY}';
DROP KEYSPACE ${KS};
EOF

cqlsh "${HOST}" "${PORT}" -f /tmp/drp_smoke.cql | sed -n '1,200p'
rm -f /tmp/drp_smoke.cql

echo "OK: Cassandra CQL roundtrip succeeded"

