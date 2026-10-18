# DRP launch-readiness audit — 2026-10-18

## Purpose and scope

This is a source-level audit of the current `Dr-Blockchain` default branch, focused on the shortest path to one real PoAT transaction. It is not a claim that the repository has been built or run in this audit session. CI and a local clean-room run must verify the findings and proposed fixes.

## Executive finding

**The Cosmos SDK node scaffold exists, but the on-chain PoAT/PoST path is not yet wired as a usable transaction path.** Prioritize making a single local chain boot, then register one minimal deterministic PoAT message end-to-end before building the app integration or public testnet.

## Findings

### P0 — PoAT/PoST modules are not wired into the app

Evidence:
- `chain/app/app.go` explicitly comments that DRP protocol modules are temporarily disabled and its `DRPApp` has no DRP protocol keepers.
- `chain/app/modules.go` registers standard Cosmos SDK modules only; the DRP PoAT/PoST modules are not in `ModuleBasics`.
- `chain/x/poat/module.go` and `chain/x/post/module.go` return nil transaction/query CLI commands, have empty legacy routes, and no-op `RegisterServices`.
- `chain/x/poat/types/msgs.go` labels the message structs as scaffolds that will be replaced by generated protobuf types.

Impact: a running CometBFT/Cosmos node is not proof that PoAT or PoST transactions can be accepted, committed, queried, and persisted in application state.

Next action: finish the minimum supported Cosmos SDK message/service implementation for PoAT, wire the keeper/store/module into the app and genesis, and add an end-to-end transaction test before implementing PoST.

### P0 — The current localnet script can delete existing node state

Evidence: `chain/scripts/localnet.sh` previously executed `rm -rf "$HOME_DIR"` unconditionally; the default is `$PWD/.drpd`.

Impact: running the localnet target again could silently erase local keys and state.

Change in this branch: the script now refuses an existing node home by default and only deletes it when `RESET_HOME=1` is explicitly set. It also rejects an empty path, `/`, and the user's home directory. This remains a local-development helper and must never be pointed at a production validator home.

### P1 — Chain initialization has no verified end-to-end acceptance test in the roadmap evidence

The localnet script performs `init`, test key creation, genesis account setup, gentx collection, and `start`. The launch criterion must additionally verify:
1. `/status` reports the expected chain ID and increasing block height.
2. A signed transaction is broadcast and returns a transaction hash.
3. The transaction is included in a committed block.
4. The application query returns the resulting state after a restart.
5. A second clean node can join or sync before calling the network multi-node capable.

These checks have not been executed as part of this source review.

### P1 — Evidence commitment storage needs strict validation and authorization tests

The PoAT message scaffold checks that submitter is a Bech32 address and that CID/hash fields are non-empty. Before enabling it, validate CID syntax, constrain proof-type and hash encodings, reject duplicates, enforce the configured proof-type/rate limits, and ensure revocation authority is explicit and tested. Never put raw personal evidence on-chain.

### P1 — Chain dependency and protocol compatibility must be pinned

The chain module declares Cosmos SDK v0.47.14 and CometBFT v0.37.5, with Go 1.24.4 toolchain. Keep this set pinned while making the first transaction work; do not perform an untested framework upgrade as part of launch plumbing. Record the exact Go version and CI run used for every release candidate.

### P2 — Existing multi-repo launch plans must converge on the Cosmos chain as the source of truth

The explorer/indexer and app/API must read transaction hashes, heights, and status from the actual chain. Convex may store application state, but it must not simulate canonical chain success. Production paths must fail closed when the configured chain/RPC is missing or unavailable.

## Recommended next milestones (one task at a time)

1. **Build/test baseline:** run `cd chain && go test ./... -count=1 && go build -o build/drpd ./cmd/drpd` on CI and a clean local checkout; capture failures rather than suppressing them.
2. **Safe localnet:** verify the updated script on a disposable home, confirm the existing-home guard, then query status and observe at least two blocks.
3. **Minimal PoAT transaction:** wire PoAT into the app, use supported SDK message/service registration, and test submit → block → query → restart. Do not enable a scaffold that lacks real message routing.
4. **Deterministic PoST:** implement only after PoAT's transaction pattern and state tests are stable.
5. **Evidence anchoring:** store only validated CID/hash commitments; test that raw evidence never enters tx events or on-chain state.
6. **App/API:** connect one real PoAT submission to the chain and display the actual tx hash, block height, and confirmation state.
7. **Explorer/indexer:** index committed chain events; reorg/restart/replay behavior must be tested.
8. **Production hardening:** remove mocks, add observability, secure backups/key rotation, firewall/TLS and restore drills.
9. **Public testnet:** deploy multiple independently operated validators only after clean local and multi-node acceptance tests pass.
10. **PQC and security review:** continue the separate post-quantum branch, but do not label the whole network quantum-safe until every relevant signing/transport/validator path and trust distribution is addressed and independently reviewed.

## Acceptance criteria for the first real PoAT transaction

- [ ] Fresh local node initializes and produces blocks.
- [ ] A valid wallet-signed PoAT transaction is accepted and committed.
- [ ] Invalid address, malformed CID/hash, duplicate proof, unauthorized revocation, and malformed signatures are rejected.
- [ ] Query returns exactly the committed record and remains correct after restart.
- [ ] App/API returns the real transaction hash, block height, and chain-derived status.
- [ ] Explorer displays the same transaction from chain data, not a mock.
- [ ] CI tests and build pass on the exact commit; logs and commit SHA are recorded.
