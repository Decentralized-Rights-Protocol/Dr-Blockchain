## DRP Chain (Sovereign L1) — Cosmos SDK + CometBFT

This directory contains the **sovereign Decentralized Rights Protocol (DRP) L1 blockchain** built with **Cosmos SDK** and **CometBFT**.

It is intentionally isolated under `chain/` so it can coexist with the repository’s existing backend/storage services without coupling the L1 implementation to any single off-chain stack.

### Chain identity (defaults)

- **Name**: Decentralized Rights Protocol
- **Binary**: `drpd`
- **Symbol / short**: DRP
- **Base denom (placeholder)**: `udrp`
- **Chain ID (example)**: `drp-testnet-1`
- **Moniker (example)**: `drp-validator-1`

### Endpoints (local defaults)

- **CometBFT RPC**: `http://127.0.0.1:26657`
  - Health: `GET /health`
  - Status: `GET /status`
- **IPFS API**: `http://127.0.0.1:5001`
  - Version: `POST /api/v0/version`
  - Add: `POST /api/v0/add`
  - Cat: `POST /api/v0/cat?arg=<CID>`
- **IPFS Gateway**: `http://127.0.0.1:8080` (public HTTP gateway)
- **Cassandra CQL**: `127.0.0.1:9042`

### DRP module layout (scaffold)

This chain is scaffolded to keep **module boundaries clean** and privacy-aware:

- `x/poat`: Proof-of-Activity (abstract activity proofs; no identity exposure)
- `x/post`: Proof-of-Status (non-transferable status/trust representation)
- `x/trust`: trust / contribution state (future-proof; avoids hard-coded formulas)
- `x/evidence`: privacy-preserving evidence commitments (CID / hash metadata only)
- `x/rights`: DRP governance/rights extension point (placeholder)

### Evidence + IPFS pattern (privacy-preserving)

On-chain stores **only commitments**, never raw private data:

- `cid`: content identifier (IPFS CID or compatible)
- `commitment`: hash/commitment string (optional; for non-IPFS stores or extra binding)
- `meta_hash`: hash of any structured metadata stored off-chain
- `submitter`: account that anchored the commitment
- `timestamp`: block time

**IPFS endpoint configuration** is intentionally **off-chain** (relayers/clients). See `.env.example` at repo root and `chain/scripts/` for how to pass `DRP_IPFS_API`/`DRP_IPFS_GATEWAY` to tooling.

### Quick start (single validator)

Prereqs:
- Go (>= 1.22)

Build:

```bash
cd chain
make build
```

Init + start:

```bash
cd chain
./scripts/localnet.sh
```

You should then have:
- CometBFT RPC at `tcp://127.0.0.1:26657`
- Tendermint P2P at `tcp://127.0.0.1:26656`
- Cosmos REST (if enabled) and gRPC ports as per config

### Smoke tests (RPC, IPFS, Cassandra)

With Docker storage stack (`docker-compose.storage.yml`) running `ipfs` and `cassandra`:

```bash
# DRP RPC health
cd chain
./scripts/smoke_rpc.sh

# IPFS API (add + cat roundtrip)
./scripts/smoke_ipfs.sh            # uses DRP_IPFS_API if set, else http://127.0.0.1:5001

# Cassandra CQL (creates temp keyspace/table then drops it)
./scripts/smoke_cassandra.sh       # requires local cqlsh; see script for container fallback
```

### Notes

- DRP is **sovereign** by default (no shared security assumptions).
- This is a **foundation**: modules are scaffolded for clean wiring; business logic will evolve iteratively.

