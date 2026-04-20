"""
DRP Backend — Core API Tests
Run: pytest tests/ -v
"""

import os
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("SECRET_KEY", "test-secret-key-ci")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-ci")
os.environ.setdefault("API_HOST", "0.0.0.0")
os.environ.setdefault("API_PORT", "8000")
os.environ.setdefault("BLOCKCHAIN_NETWORK", "drp-testnet")

import pytest
from httpx import AsyncClient, ASGITransport

try:
    from api.router import app
    APP_AVAILABLE = True
except Exception:
    APP_AVAILABLE = False


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
async def client():
    if not APP_AVAILABLE:
        pytest.skip("App not fully importable in this environment")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "DRP" in data.get("name", "") or "DRP" in data.get("protocol", "")


# ── Scoring Engine ────────────────────────────────────────────────────────────

def test_scoring_reading():
    from api.scoring import score_activity
    result = score_activity(
        activity_type="reading",
        content="Decentralized systems distribute trust across many nodes using cryptographic proofs. "
                "This eliminates single points of failure and ensures privacy is preserved.",
        context="Decentralized systems use cryptographic proofs to distribute trust.",
        metadata={"time_spent_seconds": 120},
        user_id="test-scorer-001",
    )
    assert "final_score" in result
    assert result["final_score"] >= 0.0
    assert result["tier"] in ["platinum", "gold", "silver", "bronze", "unranked"]
    assert "deri_reward" in result


def test_scoring_code():
    from api.scoring import score_activity
    result = score_activity(
        activity_type="code",
        content="""# DRP PoAT hasher
import hashlib

def hash_poat(record: dict) -> str:
    # Generate SHA3-256 hash for PoAT record
    import json
    canonical = json.dumps(record, sort_keys=True)
    return hashlib.sha3_256(canonical.encode()).hexdigest()
""",
        context="",
        metadata={"time_spent_seconds": 300},
        user_id="test-scorer-002",
    )
    assert result["comprehension"] >= 0.7  # has functions + comments
    assert result["final_score"] >= 0.0


def test_gaming_detection_duplicate():
    from api.scoring import score_activity
    # First submission
    score_activity("writing", "test content abc", "", {"time_spent_seconds": 5}, "gamer-test")
    # Duplicate submission should raise gaming flags
    result = score_activity("writing", "test content abc", "", {"time_spent_seconds": 5}, "gamer-test")
    assert "duplicate_content" in result["gaming_flags"] or result["gaming_risk"] > 0


def test_post_level():
    from api.scoring import post_level
    assert post_level(0) == 0
    assert post_level(5) == 1
    assert post_level(1000) == 10


# ── Quantum hashing ───────────────────────────────────────────────────────────

def test_quantum_hash_generate():
    from core.utils.quantum import generate_quantum_hash, verify_quantum_hash
    salt = "a" * 64
    h = generate_quantum_hash("DRP test data", salt)
    assert len(h) == 128  # SHA3-512 hex = 128 chars
    assert verify_quantum_hash("DRP test data", h, salt)
    assert not verify_quantum_hash("tampered data", h, salt)


def test_quantum_hash_auto_salt():
    from core.utils.quantum import generate_quantum_hash
    h1 = generate_quantum_hash("same input")
    h2 = generate_quantum_hash("same input")
    # Different salts → different hashes
    assert h1 != h2


def test_proof_bundle():
    from core.utils.quantum import generate_proof_bundle
    bundle = generate_proof_bundle("act-001", "user-001", "payload")
    assert "quantum_hash" in bundle
    assert "salt" in bundle
    assert "integrity_check" in bundle
    assert bundle["algorithm"] == "SHA3-512+BLAKE2b+LatticePadding"


# ── Verification endpoint ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_questions(client):
    resp = await client.post("/api/verify/questions", json={
        "source_text": (
            "The Decentralized Rights Protocol converts human activity into cryptographic proofs. "
            "AI evaluation ensures fair scoring while privacy is preserved through selective disclosure. "
            "Rewards are distributed as $DeRi tokens proportional to verified contribution."
        ),
        "count": 3,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 3
    assert len(data["questions"]) == 3


@pytest.mark.asyncio
async def test_reading_verification(client):
    resp = await client.post("/api/verify/reading", json={
        "user_id": "test-verify-user",
        "source_text": (
            "Cryptographic proofs allow systems to verify claims without revealing private data. "
            "This is fundamental to privacy-preserving systems like DRP. "
            "Zero-knowledge principles ensure accountability without surveillance."
        ),
        "responses": {
            "q1": "Cryptographic proofs verify claims without exposing private data, enabling privacy.",
            "q2": "DRP uses zero-knowledge principles to maintain accountability without surveillance.",
            "q3": "The system allows verification of human activity while preserving user dignity.",
        },
        "time_spent_seconds": 180,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "final_score" in data
    assert "poat_id" in data
    assert "record_hash" in data
    assert len(data["record_hash"]) == 64
    assert isinstance(data["passed"], bool)
