#!/usr/bin/env bash
set -euo pipefail

# Required tools: protoc 25.3, protoc-gen-gocosmos v1.7.2,
# protoc-gen-grpc-gateway v1.16.0. CI installs these exact versions.
CHAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$CHAIN_DIR"
[[ "$(protoc --version)" == "libprotoc 25.3" ]] || {
  echo "protoc 25.3 is required" >&2
  exit 1
}
SDK_DIR="$(go list -m -f '{{.Dir}}' github.com/cosmos/cosmos-sdk)"
GOGO_DIR="$(go list -m -f '{{.Dir}}' github.com/cosmos/gogoproto)"
GATEWAY_DIR="$(go list -m -f '{{.Dir}}' github.com/grpc-ecosystem/grpc-gateway)"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

for module in deri poat post rights trust evidence; do
  protoc \
    -I ../proto -I "$SDK_DIR/proto" -I "$GOGO_DIR" \
    -I "$GATEWAY_DIR/third_party/googleapis" \
    -I "${PROTOC_INCLUDE:-/usr/local/include}" \
    --gocosmos_out="plugins=grpc,paths=source_relative:$OUT" \
    --grpc-gateway_out="logtostderr=true,paths=source_relative:$OUT" \
    "drp/$module/$module.proto"
  cp "$OUT/drp/$module/$module.pb.go" "x/$module/types/$module.pb.go"
  cp "$OUT/drp/$module/$module.pb.gw.go" "x/$module/types/$module.pb.gw.go"
done
