# DRP Blockchain Language Modernization Plan

**Status:** Proposal / staged migration plan — not a claim that the migration is implemented.  
**Scope:** `Decentralized-Rights-Protocol/Dr-Blockchain` and its integration with `Dr-Protocol`.

## Decision

Modernize incrementally. Do not rewrite the whole repository or remove working Python code in one pass.

The current `Dr-Blockchain` repository contains a mixed codebase (the current default-branch tree includes roughly 202 `.py` files and 60 `.go` files). That count is a first-pass inventory only; it does not identify which files are production-critical, duplicate, generated, or experimental.

Target language ownership:

| Area | Preferred language | Boundary |
|---|---|---|
| Authoritative blockchain node, deterministic transaction/state logic, node CLI | Go | Keep the chain's consensus-critical execution deterministic and reproducible. |
| DRP verification network and signed attestations | Go, aligned with `Dr-Protocol` | Reuse existing Go protocol primitives where compatible; define a versioned interface before moving code. |
| AI/model inference, evidence analysis, experiments | Python | Off-chain service only; AI outputs are proposals/evidence, not consensus decisions. |
| Web UI and developer-facing wallet integration | TypeScript | Client and API integration; never hold server secrets in browser code. |
| Indexing and application records | SQL/PostgreSQL | Derived/indexed data is not authoritative chain state. |
| Security/performance-critical cryptographic components | Go initially; Rust only when a measured need exists | No Rust rewrite without benchmarks, audits, and a stable interface. |

## Non-negotiable safety rules

1. **First identify the authoritative chain implementation.** Compare the Go and Python paths, startup commands, state models, consensus code, transaction formats, and tests. Do not infer authority from file counts or README claims.
2. **Do not run two competing production ledgers.** Legacy Python code may remain as a research/reference implementation until parity tests prove what can be retired.
3. **Do not change consensus, chain ID, address formats, key formats, transaction encoding, genesis, or token denominations as part of a language cleanup.** Any such change needs a separate migration proposal and compatibility plan.
4. **AI must not independently determine consensus, identity, eligibility, or rights-affecting outcomes.** Use deterministic validation, signed evidence, transparent policy, appeal/review paths, and human oversight where decisions affect people.
5. **Do not add a new dependency or replace a subsystem solely because it is written in Python.** Migrate only when there is a clear ownership, security, reliability, or maintainability benefit.
6. **Never commit credentials, mnemonics, private keys, API tokens, or production data.**

## Staged execution

### Phase 0 — Baseline and inventory (first)
- Map Go/Python entry points, packages, services, APIs, storage, networking, and consensus-related code.
- Identify the actual node binary and how a local multi-node testnet is started.
- Record tests, CI workflows, dependency manifests, known security findings, and current build status.
- Label code as: authoritative, shared library, adapter, research/experimental, legacy, generated, or unknown.
- Document the current transaction/evidence formats and any public API consumers.

**Exit criteria:** a reviewed inventory; a reproducible baseline build/test; no destructive changes.

### Phase 1 — Establish interfaces and conformance tests
- Specify versioned interfaces for transactions, signatures, attestations, RPC, events, and storage.
- Add golden test vectors for signature verification, serialization, and validation rules.
- Add integration tests that compare old and new implementations where both exist.
- Make CI explicitly test the supported Go and Python components without silently skipping failures.

**Exit criteria:** interface contracts and tests exist before moving responsibilities between languages.

### Phase 2 — Go owns consensus-critical paths
- If the audit confirms the Go chain is authoritative, keep consensus-critical state transitions and validation in Go.
- Move or reimplement only clearly identified production-critical Python responsibilities, behind stable interfaces and with parity tests.
- Keep AI inference and exploratory algorithms in Python services; submit signed, schema-validated evidence to the protocol.
- Preserve backward compatibility or provide a separately reviewed migration plan.

**Exit criteria:** parity tests pass; node startup, transactions, persistence, restart/recovery, and multi-node behavior are verified.

### Phase 3 — Security, performance, and release hardening
- Add fuzz/property tests for transaction parsing and protocol boundaries.
- Add dependency scanning, secret scanning, race tests where applicable, and reproducible CI builds.
- Benchmark before considering Rust or other low-level rewrites.
- Test adversarial verifier behavior, replay, duplicate submissions, key revocation, partitions, and recovery.
- Publish an operator runbook, upgrade/rollback procedure, and testnet release notes.

**Exit criteria:** independent review, documented known limitations, and testnet validation before any production migration.

## First implementation ticket

Start with Phase 0. Produce a factual inventory and baseline report before changing source files. The report must cite file paths and commands/results, and clearly distinguish verified behavior from assumptions. Do not claim the network is production-ready merely because unit tests pass.

## References

- Go modules and testing: https://go.dev/doc/
- Cosmos SDK framework and module architecture: https://github.com/cosmos/cosmos-sdk
