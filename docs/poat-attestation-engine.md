# PoAT signed attestation engine

## Purpose

This package is the deterministic cryptographic core for evaluating Proof-of-Activity attestations. It is intentionally isolated from Cosmos SDK state and off-chain services so its behavior can be tested without network or clock dependencies.

## Trust model

- The active verifier set, Ed25519 public keys, voting weights, and quorum threshold are supplied by consensus state.
- Verifiers cannot add themselves to the trusted set through this package.
- Every attestation is bound to a proof ID, verifier ID, decision, and non-zero nonce.
- Signatures use the domain `drp/poat/attestation/v1` and length-prefixed fields.
- At most one attestation per verifier is accepted for a given proof evaluation.
- Invalid, duplicate, mismatched, or unauthorized attestations fail closed.

## Decision rule

Let (W) be the sum of configured verifier weights and (Q) the configured threshold. Policy validation requires (W/2 < Q \leq W).

```
accept  if accepted_weight >= Q
reject  if rejected_weight >= Q
pending otherwise
```

Because the threshold is a strict weighted majority, accept and reject cannot both reach quorum in the same evaluation.

## Explicit integration boundary

This package does not yet:
- persist verifier membership, attestation records, or nonce history in the PoAT KV store;
- expose Cosmos SDK transaction/query messages for attestation submission;
- implement governance updates for verifier membership or quorum policy;
- retrieve IPFS evidence or establish that evidence is truthful;
- implement an Elder identity/reputation system.

The Cosmos module must load its verifier policy from deterministic on-chain state, persist each accepted vote before recomputing status, and expose immutable audit history. Do not use local configuration, wall-clock time, HTTP calls, or nondeterministic AI decisions in consensus execution.
