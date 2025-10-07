import os
import json
from fastapi.testclient import TestClient

from ai_transparency_service.main import app


client = TestClient(app)


def test_decision_flow(monkeypatch):
    # Mock IPFS if not available by short-circuiting encrypt_and_pin
    from ai_transparency_service import ipfs_utils

    def fake_encrypt_and_pin(data):
        # return pseudo CID (sha-like)
        import hashlib
        return hashlib.sha256((data or b'').hex().encode()).hexdigest()[:46]

    monkeypatch.setattr(ipfs_utils, "encrypt_and_pin", fake_encrypt_and_pin)

    payload = {
        "model_id": "face_verification_v1",
        "model_version": "1.2.0",
        "input_type": "image",
        "input_commitment": "abc123commitment",
        "features": {"quality": 0.5, "lighting": 0.4, "angle": -0.2},
        "confidence": 0.92,
        "decision": "approved",
    }

    res = client.post("/api/ai/decide", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["decision_id"]
    assert data["explanation_cid"]
    assert data["zk_proof_cid"]

    # Fetch the decision
    res2 = client.get(f"/api/ai/decision/{data['decision_id']}")
    assert res2.status_code == 200, res2.text

    # Health check
    res3 = client.get("/api/ai/health")
    assert res3.status_code == 200


