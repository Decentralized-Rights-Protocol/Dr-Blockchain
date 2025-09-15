"""
DRP AI Agents  Starter Microservice
------------------------------------
FastAPI microservice that implements the first two DRP agents:
  1) AI Elder (signs/attests compliant block headers)
  2) Activity Verifier (assesses activity claims for Proof of Activities/Status)

Features
- Ed25519 signatures for fast, modern signing
- Policy engine stub (human-rights, sustainability, anti-abuse)
- Deterministic dev key or persisted keypair (filesystem)
- JSON schemas for blocks & activities
- Clean, versioned HTTP API

How to run (dev)
----------------
1) pip install fastapi uvicorn cryptography pydantic[dotenv]
2) export DRP_DEV_SEED="change-me-for-prod"   # optional deterministic key in dev
3) uvicorn drp_ai_agents:app --reload --port 8088

Security notes
--------------
- For production, set DRP_KEYSTORE_DIR to a secure path and DO NOT use DRP_DEV_SEED.
- Put this service behind mTLS and an allowlist (seed nodes, validators, auditors).
- Enable request signing & auditing (not implemented in this starter).

"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization

# -----------------------------
# Key Management
# -----------------------------
KEY_DIR = Path(os.getenv("DRP_KEYSTORE_DIR", ".keystore"))
KEY_DIR.mkdir(parents=True, exist_ok=True)
PRIV_PATH = KEY_DIR / "elder_ed25519_private.key"
PUB_PATH = KEY_DIR / "elder_ed25519_public.key"


def _derive_seed_from_passphrase(passphrase: str) -> bytes:
    """Derive a 32-byte seed from a passphrase for deterministic dev keys.
    WARNING: For development only. Use an HSM or KMS in production.
    """
    return hashlib.sha256(passphrase.encode("utf-8")).digest()


def _load_or_create_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    dev_seed = os.getenv("DRP_DEV_SEED")

    if PRIV_PATH.exists() and PUB_PATH.exists():
        priv_bytes = PRIV_PATH.read_bytes()
        pub_bytes = PUB_PATH.read_bytes()
        private_key = Ed25519PrivateKey.from_private_bytes(priv_bytes)
        public_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
        return private_key, public_key

    if dev_seed:
        seed32 = _derive_seed_from_passphrase(dev_seed)
        private_key = Ed25519PrivateKey.from_private_bytes(seed32)
    else:
        private_key = Ed25519PrivateKey.generate()

    public_key = private_key.public_key()

    # Persist raw key bytes (locked-down directory recommended)
    PRIV_PATH.write_bytes(private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    ))
    PUB_PATH.write_bytes(public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ))

    return private_key, public_key


PRIVATE_KEY, PUBLIC_KEY = _load_or_create_keypair()


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64d(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


# -----------------------------
# Data Models
# -----------------------------
class BlockHeader(BaseModel):
    index: int = Field(..., ge=0)
    previous_hash: str
    timestamp: int = Field(..., description="seconds since epoch (UTC)")
    merkle_root: str = Field("", description="optional: merkle root of txs")
    data_hash: str = Field("", description="hash of block body (policies may require)")
    miner_id: str = Field("", description="node or agent id building this block")
    nonce: int = 0
    difficulty: int = 0
    # Proof-of-Status/Activities proto fields (to be attached post-signing)
    status_metadata: Optional[Dict[str, Any]] = None

    def canonical_string(self) -> str:
        # Canonical representation for signing/hashing
        payload = {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "merkle_root": self.merkle_root,
            "data_hash": self.data_hash,
            "miner_id": self.miner_id,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
        }
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)


class ActivityEvidence(BaseModel):
    kind: str = Field(..., examples=["learning", "renewable_energy", "healthcare", "civic_work"]) 
    description: str
    proofs: List[str] = Field(default_factory=list, description="URIs or opaque attestations")
    energy_kwh: Optional[float] = None
    geo_hint: Optional[str] = None  # region/country (privacy-first; no exact coords)


class ActivityClaim(BaseModel):
    actor_id: str
    timestamp: int
    evidences: List[ActivityEvidence]


class AssessResponse(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    verdict: str = Field(..., pattern=r"^(approve|review|reject)$")
    rationale: str
    obligations: List[str] = []  # follow-ups required
    policy_tags: List[str] = []


class SignRequest(BaseModel):
    header: BlockHeader
    attach_metadata: bool = True


class SignResponse(BaseModel):
    signature: str  # base64
    signer: str     # base64 raw public key
    metadata: Optional[Dict[str, Any]] = None
    signed_at: int


class VerifyRequest(BaseModel):
    header_canonical: str
    signature: str
    signer: Optional[str] = None  # if omitted, use current public key


class VerifyResponse(BaseModel):
    valid: bool
    signer_fingerprint: str


# -----------------------------
# Policy Engine (stub)
# -----------------------------
class PolicyEngine:
    """Rule-based stub. Replace with ML/LLM pipeline & auditors later."""

    def __init__(self):
        # simple weights; tune per network governance
        self.base_weights = {
            "learning": 0.25,
            "renewable_energy": 0.4,
            "healthcare": 0.2,
            "civic_work": 0.15,
        }

    def assess_activity(self, claim: ActivityClaim) -> AssessResponse:
        now = int(time.time())
        recency_penalty = 0.0 if (now - claim.timestamp) < 90 * 24 * 3600 else 0.1

        score = 0.0
        tags: List[str] = []

        if not claim.evidences:
            return AssessResponse(
                score=0.0,
                verdict="reject",
                rationale="No evidences provided.",
                obligations=["Provide at least one verifiable proof"],
                policy_tags=["insufficient_evidence"],
            )

        for ev in claim.evidences:
            w = self.base_weights.get(ev.kind, 0.05)
            partial = w
            if ev.energy_kwh is not None and ev.kind == "renewable_energy":
                partial += min(ev.energy_kwh / 100.0, 0.3)  # bonus up to +0.3
                tags.append("energy_bonus")
            if ev.proofs:
                partial += 0.1  # having at least one proof gets a bonus
                tags.append("has_proof")
            score += partial

        score = min(1.0, max(0.0, score - recency_penalty))

        if score >= 0.6:
            verdict = "approve"
            rationale = "Sufficient diversified evidence meeting policy thresholds."
        elif score >= 0.35:
            verdict = "review"
            rationale = "Moderate evidence; requires human/AI auditor review."
        else:
            verdict = "reject"
            rationale = "Evidence insufficient versus policy thresholds."

        obligations = []
        if verdict != "approve":
            obligations.append("Submit stronger or more recent proofs")
        if "geo_hint" in claim.model_dump_json():
            obligations.append("If possible, add regional sustainability context")

        return AssessResponse(
            score=round(score, 3),
            verdict=verdict,
            rationale=rationale,
            obligations=obligations,
            policy_tags=list(set(tags)),
        )


POLICY = PolicyEngine()


# -----------------------------
# AI Elder: Sign/Verify
# -----------------------------

def sign_canonical(canonical: str) -> bytes:
    return PRIVATE_KEY.sign(canonical.encode("utf-8"))


def verify_signature(canonical: str, signature: bytes, pubkey_bytes: Optional[bytes] = None) -> bool:
    pub = PUBLIC_KEY if pubkey_bytes is None else Ed25519PublicKey.from_public_bytes(pubkey_bytes)
    try:
        pub.verify(signature, canonical.encode("utf-8"))
        return True
    except Exception:
        return False


def pubkey_fingerprint(pub: Ed25519PublicKey) -> str:
    raw = pub.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    return hashlib.sha256(raw).hexdigest()[:16]


# -----------------------------
# API
# -----------------------------
app = FastAPI(title="DRP AI Agents", version="0.1.0")


@app.get("/v1/agent/public-key")
def get_public_key() -> Dict[str, str]:
    raw = PUBLIC_KEY.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    return {
        "algorithm": "Ed25519",
        "public_key_b64": b64(raw),
        "fingerprint": pubkey_fingerprint(PUBLIC_KEY),
    }


@app.post("/v1/agent/assess-activity", response_model=AssessResponse)
def assess_activity_api(claim: ActivityClaim):
    return POLICY.assess_activity(claim)


@app.post("/v1/agent/sign-block", response_model=SignResponse)
def sign_block(req: SignRequest):
    header = req.header

    # Minimal sanity checks
    if header.index < 0 or not header.previous_hash:
        raise HTTPException(status_code=400, detail="Invalid header fields")

    canonical = header.canonical_string()
    sig = sign_canonical(canonical)

    metadata = None
    if req.attach_metadata:
        assessment = {
            "status": "ok",
            "policies": ["human_rights_root", "sustainability_root"],
            "assessed_at": int(time.time()),
        }
        metadata = assessment

    pub_raw = PUBLIC_KEY.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)

    return SignResponse(
        signature=b64(sig),
        signer=b64(pub_raw),
        metadata=metadata,
        signed_at=int(time.time()),
    )


@app.post("/v1/agent/verify-signature", response_model=VerifyResponse)
def verify_signature_api(req: VerifyRequest):
    pub_bytes = b64d(req.signer) if req.signer else PUBLIC_KEY.public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )
    ok = verify_signature(req.header_canonical, b64d(req.signature), pub_bytes)
    fp = hashlib.sha256(pub_bytes).hexdigest()[:16]
    return VerifyResponse(valid=ok, signer_fingerprint=fp)


# -----------------------------
# DEV: Example payloads (curl)
# -----------------------------
EXAMPLE_CANONICAL = json.dumps({
    "index": 0,
    "previous_hash": "0",
    "timestamp": 1735142096,
    "merkle_root": "",
    "data_hash": "",
    "miner_id": "genesis",
    "nonce": 0,
    "difficulty": 0
}, separators=(",", ":"), sort_keys=True)

"""
# Get public key
curl -s http://localhost:8088/v1/agent/public-key | jq

# Sign a block header (genesis)
curl -s -X POST http://localhost:8088/v1/agent/sign-block \
  -H 'Content-Type: application/json' \
  -d '{
        "header": {
          "index": 0,
          "previous_hash": "0",
          "timestamp": 1735142096,
          "merkle_root": "",
          "data_hash": "",
          "miner_id": "genesis",
          "nonce": 0,
          "difficulty": 0
        },
        "attach_metadata": true
      }' | jq

# Verify signature (using canonical string)
curl -s -X POST http://localhost:8088/v1/agent/verify-signature \
  -H 'Content-Type: application/json' \
  -d "{\n  \"header_canonical\": \"%s\",\n  \"signature\": \"<paste-from-sign-response>\"\n}" | jq

# Assess activity claim
curl -s -X POST http://localhost:8088/v1/agent/assess-activity \
  -H 'Content-Type: application/json' \
  -d '{
    "actor_id": "did:drp:alice",
    "timestamp": 1735000000,
    "evidences": [
      {"kind": "renewable_energy", "description": "Used solar for home", "energy_kwh": 120, "proofs": ["att://meter/123"]},
      {"kind": "learning", "description": "Completed cryptography course", "proofs": ["cred://course/abc"]}
    ]
  }' | jq
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8088)
