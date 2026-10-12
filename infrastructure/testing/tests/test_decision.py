import hashlib
import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def decision_service(monkeypatch, tmp_path):
    monkeypatch.setenv("ELDER_PRIVATE_KEY_PATH", str(tmp_path / "elder_private.key"))

    from src.api.ai_transparency_service import db, ipfs_utils

    records = {}
    artifacts = {}

    def fake_encrypt_and_pin(data):
        cid = hashlib.sha256(data).hexdigest()
        artifacts[cid] = data
        return cid

    def insert_record(record):
        records[record["decision_id"]] = dict(record)

    monkeypatch.setattr(db, "ensure_schema", lambda: None)
    monkeypatch.setattr(db, "insert_decision_record", insert_record)
    monkeypatch.setattr(db, "get_decision_record", records.get)
    monkeypatch.setattr(ipfs_utils, "encrypt_and_pin", fake_encrypt_and_pin)

    from src.api.ai_transparency_service import main

    # The endpoint uses the function bound in main, not a lookup on ipfs_utils.
    monkeypatch.setattr(main, "encrypt_and_pin", fake_encrypt_and_pin)
    monkeypatch.setattr(main, "_render_explanation_png", lambda explanation: None)
    with TestClient(main.app) as client:
        yield client, main, records, artifacts


def test_decision_flow(decision_service, monkeypatch):
    client, main, records, artifacts = decision_service
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
    assert data["outcome"] == payload["decision"]
    assert data["confidence"] == payload["confidence"]

    res2 = client.get(f"/api/ai/decision/{data['decision_id']}")
    assert res2.status_code == 200, res2.text
    record = res2.json()
    assert record == records[data["decision_id"]]
    for field, value in data.items():
        assert record[field] == value
    explanation = json.loads(artifacts[data["explanation_cid"]])
    assert explanation["input_commitment"] == payload["input_commitment"]
    proof = json.loads(artifacts[data["zk_proof_cid"]])
    assert proof["decision_id"] == data["decision_id"]
    assert proof["valid"] is True

    unsigned_record = {key: value for key, value in record.items() if key != "signature"}
    main.ELDER_PRIV.public_key().verify(
        bytes.fromhex(record["signature"]),
        json.dumps(unsigned_record, sort_keys=True, separators=(",", ":")).encode(),
    )

    missing = client.get("/api/ai/decision/missing")
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Not found"

    res3 = client.get("/api/ai/health")
    assert res3.status_code == 200
    assert res3.json()["status"] == "ok"

    def fail_insert(record):
        raise RuntimeError("storage unavailable")

    monkeypatch.setattr(main.db, "insert_decision_record", fail_insert)
    failed = client.post("/api/ai/decide", json=payload)
    assert failed.status_code == 500
    assert failed.json()["detail"] == "DB error: storage unavailable"
    assert len(records) == 1
