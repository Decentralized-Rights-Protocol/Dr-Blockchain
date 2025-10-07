# AI Transparency & ZK Explainability PR

## Summary
- FastAPI microservice `ai_transparency_service` with endpoints:
  - POST /api/ai/decide
  - GET  /api/ai/decision/{id}
  - GET  /api/ai/models
  - POST /api/ai/dispute
  - GET  /api/ai/health
- AES-GCM encryption of explanation artifacts + IPFS pinning
- ScyllaDB keyspace/table and CRUD
- Circom circuit `zk/confidence.circom` and SnarkJS instructions
- Dashboard scaffold (/transparency) [if applicable]
- Model card + template, docs, and tests

## Manual Steps
- Set environment variables:
  - SCYLLA_HOST (default 127.0.0.1)
  - SCYLLA_PORT (default 9042)
  - IPFS_API_URL (default local daemon)
  - AI_ENCRYPTION_KEY (32-byte hex)
  - ELDER_PRIVATE_KEY_PATH (default keys/elder_private.key)
- Ensure IPFS daemon is running
- Ensure ScyllaDB is reachable
- (Optional) Install circom/snarkjs and follow zk/README.md

## Testing
- `pytest tests/test_decision.py -q`
