# AI Transparency & ZK Explainability - Design

This document describes the DRP AI Transparency service design, privacy strategy, storage, and ZK verification steps.

## Goals
- Transparent, explainable AI Elder decisions
- Privacy-first: no raw PII stored; only hashes and encrypted artifacts
- Public auditability via IPFS and ZK proofs

## Architecture
- FastAPI microservice `ai_transparency_service` exposes endpoints
- ScyllaDB stores `decision_records` with commitments and CIDs
- IPFS stores encrypted explanation JSON/PNG artifacts
- ZK (Circom/SnarkJS) produces proof of confidence threshold

## Endpoints
- POST `/api/ai/decide`: submit decision + features for explanation; returns CIDs and signature
- GET  `/api/ai/decision/{id}`: return decision record (no raw data)
- GET  `/api/ai/models`: list model cards
- POST `/api/ai/dispute`: create dispute by decision_id
- GET  `/api/ai/health`: health/status

## Privacy Strategy
- Inputs hashed client-side as `input_commitment`; never send/store raw inputs
- Explanation artifacts are AES-256-GCM encrypted before IPFS pinning
- Server-side AES key via `AI_ENCRYPTION_KEY` env; rotate by:
  1. Pause writes
  2. Re-encrypt artifacts to new key, update CIDs
  3. Rotate key in secret store and redeploy

## Cryptographic Integrity
- Each record signed with Elder Ed25519 private key (file: `keys/elder_private.key`)
- Signature covers all fields including CIDs and timestamp
- Public verifiers can fetch record, reconstruct payload, and verify signature

## ScyllaDB Schema
Keyspace: `drp_transparency`
Table: `decision_records(decision_id PK, model_id, model_version, input_type, input_commitment, outcome, confidence, explanation_cid, explanation_png_cid, zk_proof_cid, elder_pub, signature, timestamp)`

## ZK Proof (Confidence Threshold)
- Circuit: `zk/confidence.circom`
- Build and prove steps in `zk/README.md`
- API returns `zk_proof_cid` (proof.json) after pinning

## Verification Steps
1. Retrieve decision via GET `/api/ai/decision/{id}`
2. Verify Ed25519 signature with `elder_pub`
3. Download `zk_proof_cid` from IPFS and verify with verification key

## Environment Variables
- SCYLLA_HOST, SCYLLA_PORT
- IPFS_API_URL
- AI_ENCRYPTION_KEY (hex 32 bytes)
- ELDER_PRIVATE_KEY_PATH

## Testing
Run unit test `tests/test_decision.py`:
- Simulates decision
- Generates explanation
- Pins artifacts to IPFS
- Writes Scylla record
- Generates a trivial ZK proof (or mocks if not available)
