# DRP Storage and Data-Layer Architecture

**Status:** Proposed architecture decision; implementation must follow a repository audit and tests.
**Scope:** `Dr-Blockchain/chain`, `Dr-Protocol/internal/store`, off-chain verification services, and future DRP clients.

## Decision in brief

DRP will separate authoritative consensus state from evidence blobs and application data. No single database technology is expected to serve every layer.

| Layer | Initial direction | Authority and limits |
|---|---|---|
| Consensus state | Cosmos SDK application state, persisted through the chain's supported store/DB backend | The chain state transition is authoritative. A local embedded DB is not itself a distributed database. |
| Node-local key/value persistence | Keep the Cosmos SDK/CometBFT-supported backend initially; evaluate LevelDB only as a backend choice after checking the pinned versions and operational requirements | One database instance belongs to one node. Consensus replication comes from CometBFT and deterministic state execution, not from LevelDB peer replication. |
| Evidence files | IPFS or compatible content-addressed storage; place only CIDs, hashes/commitments, and minimum necessary metadata on-chain | Encrypt sensitive evidence before upload; a CID is not access control, and availability requires pinning/retention planning. |
| P2P application data | Evaluate GUN, OrbitDB, Ceramic, and any precisely identified LevelDB-based replication layer against real DRP requirements | Suitable for replicated feeds, drafts, and app indexes only when conflict resolution, authorization, availability, and abuse resistance are specified. Must not override finalized chain state. |
| Query/index layer | Optional replaceable indexer; SQL/PostgreSQL is allowed but not mandatory | Derived and rebuildable from chain events. It is not the source of truth. |
| AI and evidence analysis | Python services behind versioned APIs | AI outputs are claims or recommendations. Deterministic validation, signatures, policy, review, and appeal paths govern accepted protocol results. |
| Client and SDK | TypeScript | Client-side cache is untrusted; signatures and server/chain validation remain necessary. |

## Important distinction: LevelDB

LevelDB is an embedded key-value storage engine, not a decentralized database network by itself. Multiple DRP nodes can each use a local LevelDB-compatible backend while CometBFT handles consensus and blocks are replayed/applied deterministically. That is different from having LevelDB automatically replicate application records between peers.

The chain's pinned Go module includes Cosmos SDK and CometBFT DB dependencies. We must inspect the actual app configuration and pinned backend options before selecting or changing a backend. Do not add a second independent ledger just to adopt LevelDB.

## Data placement rules

1. **On-chain:** finalized protocol transitions, accepted verification-result commitments, revocation/status transitions, governance outcomes, and the minimum data required for deterministic validation.
2. **Evidence storage:** encrypted evidence blobs and larger files; anchor a content identifier and cryptographic commitment when a claim is submitted. Never place raw sensitive evidence on-chain.
3. **P2P app database:** optional user-controlled profiles, drafts, community feeds, relationship data, and replicated application records. Define ownership, signed updates, versioning, conflict handling, deletion/tombstone behavior, and access control before implementation.
4. **Indexer/cache:** fast search and API query models that can be rebuilt from authoritative events.
5. **Secrets:** never store plaintext mnemonics, private keys, access tokens, or credentials in a general database or public evidence store.

## Required storage interface

Before adding a database adapter, define a small versioned interface and conformance tests. Keep adapter capabilities explicit instead of pretending every backend has identical semantics.

Minimum contract:
- deterministic key encoding and canonical serialization;
- schema/version fields and migration policy;
- authenticated writes (signer, signature, authorization scope);
- idempotency and replay protection for signed updates;
- conflict policy and monotonic versioning where applicable;
- integrity verification, error semantics, and observable availability;
- revocation/tombstones and retention rules;
- pagination/query limits and denial-of-service protections;
- backup/recovery and rebuild procedures.

An adapter must declare whether it supports strong consistency, eventual consistency, offline writes, peer replication, access-controlled reads, and durable retention. Tests must fail if an implementation silently lacks a required capability.

## Phased implementation plan

### Storage Phase A — Audit and baseline
- Inspect the Cosmos app wiring, store configuration, dependency versions, genesis/localnet scripts, and current chain tests.
- Inspect `Dr-Protocol/internal/store`: it currently uses in-memory Go maps, so it is not durable across process restarts.
- Inventory existing IPFS, Cassandra, LevelDB/RocksDB, OrbitDB, and other references; distinguish live integrations from docs, optional dependencies, and placeholders.
- Record reproducible build/test commands and current results before editing runtime code.

### Storage Phase B — Protect the protocol contract
- Specify canonical claim, evidence-reference, attestation, verification-result, and revocation records.
- Add golden vectors and tests for serialization, signatures, authorization, replay prevention, and invalid updates.
- Define which facts must be finalized on-chain and which are rebuildable off-chain records.

### Storage Phase C — Durable local MVP store
- Add a storage interface to `Dr-Protocol` while preserving the existing in-memory adapter for unit tests.
- Implement a durable adapter only after selecting a suitable engine; add restart/recovery and corruption/error tests.
- Keep this MVP store distinct from Cosmos chain state unless a deliberate integration is specified.

### Storage Phase D — Evidence and optional P2P data
- Verify encrypted IPFS add/get/pinning behavior and CID/commitment validation.
- Benchmark GUN, OrbitDB, Ceramic, and any proposed LevelDB replication project using a DRP-specific test matrix.
- Choose one P2P adapter only if it provides a clear benefit. Keep it out of consensus-critical execution.

### Storage Phase E — Indexing, operations, and security
- Add a rebuildable indexer only when query needs justify it.
- Test node restart, backup/restore, replay, offline peers, partitions, conflicting writes, revoked keys, missing evidence, and storage outages.
- Document data retention, privacy, access control, disaster recovery, and monitoring.

## Acceptance criteria before production

- One documented authoritative chain and a clear separation between finalized state and derived data.
- Repeatable tests for deterministic state transitions and cryptographic verification.
- No raw sensitive evidence or secrets on-chain or in public storage.
- Durable stores survive restart and have tested recovery procedures.
- P2P database behavior under partitions/conflicts is documented and tested.
- AI failures or outages cannot silently finalize rights-affecting outcomes.
- Every claim about implemented storage is backed by code and passing tests, not README architecture diagrams alone.
