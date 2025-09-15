"""
DRP AI Agents – Quorum Edition (m-of-n Elders)
----------------------------------------------
FastAPI microservice that implements multi-Elder quorum signatures for DRP:
  1) AI Elders registry (n elders loaded from keystore or deterministically derived)
  2) Activity Verifier (policy stub)
  3) Quorum signing & verification (m-of-n, simple multi-sig with Ed25519)

Why simple multi-sig (not threshold crypto)?
- Ed25519 doesn't natively support threshold aggregation without extra protocols.
- For launch, we accept independent signatures from distinct Elders and enforce m-of-n.
- Later, you can swap in true threshold Schnorr/BLS.

How to run (dev)
----------------
1) pip install fastapi uvicorn cryptography pydantic[dotenv]
2) export DRP_DEV_SEED="change-me-for-prod"    # optional deterministic keys
3) export DRP_ELDERS=5                          # total elders (n)
4) export DRP_QUORUM_M=3                        # required signatures (m)
5) uvicorn drp_ai_agents:app --reload --port 8088

Security notes
--------------
- For production, split Elders across machines/HSMs; do not co-host all keys.
- Protect keystore with filesystem perms, mTLS on ingress, and signed requests.
- Enable audit logging and rotation policies.

"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization

# -----------------------------
# Helpers
# -----------------------------

def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64d(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# -----------------------------
# Config
# -----------------------------
KEY_DIR = Path(os.getenv("DRP_KEYSTORE_DIR", ".keystore"))
KEY_DIR.mkdir(parents=True, exist_ok=True)
N_ELDERS = int(os.getenv("DRP_ELDERS", "1"))
M_REQUIRED = int(os.getenv("DRP_QUORUM_M", str(min(1, N_ELDERS))))
DEV_SEED = os.getenv("DRP_DEV_SEED")

if M_REQUIRED > N_ELDERS:
    raise RuntimeError("DRP_QUORUM_M cannot exceed DRP_ELDERS")


# -----------------------------
# Key Management (multiple Elders)
# -----------------------------
@dataclass
class Elder:
    id: str                 # e.g., elder-0
    private: Ed25519PrivateKey
    public: Ed25519PublicKey
    pub_b64: str
    fingerprint: str        # first 16 hex of sha256(pub)


def derive_seed32(namespace: str, idx: int) -> bytes:
    assert DEV_SEED is not None
    material = f"{DEV_SEED}:{namespace}:{idx}".encode("utf-8")
    return hashlib.sha256(material).digest()


def load_or_create_elder(idx: int) -> Elder:
    priv_path = KEY_DIR / f"elder_{idx}.priv"
    pub_path = KEY_DIR / f"elder_{idx}.pub"

    if priv_path.exists() and pub_path.exists():
        priv = Ed25519PrivateKey.from_private_bytes(priv_path.read_bytes())
        pub = Ed25519PublicKey.from_public_bytes(pub_path.read_bytes())
    else:
        if DEV_SEED:
            seed = derive_seed32("elder", idx)
            priv = Ed25519PrivateKey.from_private_bytes(seed)
        else:
            priv = Ed25519PrivateKey.generate()
        pub = priv.public_key()
        priv_path.write_bytes(priv.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        ))
        pub_path.write_bytes(pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ))

    pub_raw = pub.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    return Elder(
        id=f"elder-{idx}",
        private=priv,
        public=pub,
        pub_b64=b64(pub_raw),
        fingerprint=sha256_hex(pub_raw)[:16],
    )


ELDERS: List[Elder] = [load_or_create_elder(i) for i in range(N_ELDERS)]


# -----------------------------
# Data Models
# -----------------------------
class BlockHeader(BaseModel):
    index: int = Field(..., ge=0)
    previous_hash: str
    timestamp: int = Field(..., description="seconds since epoch (UTC)")
    merkle_root: str = ""
    data_hash: str = ""
    miner_id: str = ""
    nonce: int = 0
    difficulty: int = 0

    def canonical_string(self) -> str:
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
    kind: str
    description: str
    proofs: List[str] = []
    energy_kwh: Optional[float] = None
    geo_hint: Optional[str] = None


class ActivityClaim(BaseModel):
    actor_id: str
    timestamp: int
    evidences: List[ActivityEvidence]


class AssessResponse(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    verdict: str = Field(..., pattern=r"^(approve|review|reject)$")
    rationale: str
    obligations: List[str] = []
    policy_tags: List[str] = []


class SignRequest(BaseModel):
    header: BlockHeader
    elder_ids: Optional[List[str]] = None  # If omitted, all elders sign


class SingleSignature(BaseModel):
    elder_id: str
    signer: str  # base64 public key
    signature: str  # base64 signature
    signed_at: int


class QuorumSignature(BaseModel):
    signatures: List[SingleSignature]
    policy: Dict[str, int]  # {"m": 2, "n": 3}


class VerifyQuorumRequest(BaseModel):
    header_canonical: str
    quorum: QuorumSignature


class VerifyQuorumResponse(BaseModel):
    valid: bool
    valid_signers: List[str]
    required_m: int
    total_distinct: int


# -----------------------------
# Policy Engine (stub)
# -----------------------------
class PolicyEngine:
    def __init__(self):
        self.base_weights = {
            "learning": 0.25,
            "renewable_energy": 0.4,
            "healthcare": 0.2,
            "civic_work": 0.15,
        }

    def assess_activity(self, claim: ActivityClaim) -> AssessResponse:
        now = int(time.time())
        recency_penalty = 0.0 if (now - claim.timestamp) < 90 * 24 * 3600 else 0.1

        if not claim.evidences:
            return AssessResponse(
                score=0.0,
                verdict="reject",
                rationale="No evidences provided.",
                obligations=["Provide at least one verifiable proof"],
                policy_tags=["insufficient_evidence"],
            )

        score = 0.0
        tags: List[str] = []
        for ev in claim.evidences:
            w = self.base_weights.get(ev.kind, 0.05)
            partial = w
            if ev.energy_kwh is not None and ev.kind == "renewable_energy":
                partial += min(ev.energy_kwh / 100.0, 0.3)
                tags.append("energy_bonus")
            if ev.proofs:
                partial += 0.1
                tags.append("has_proof")
            score += partial

        score = min(1.0, max(0.0, score - recency_penalty))
        if score >= 0.6:
            verdict, rationale = "approve", "Sufficient diversified evidence meeting policy thresholds."
        elif score >= 0.35:
            verdict, rationale = "review", "Moderate evidence; requires human/AI auditor review."
        else:
            verdict, rationale = "reject", "Evidence insufficient versus policy thresholds."

        obligations = [] if verdict == "approve" else ["Submit stronger or more recent proofs"]
        if "geo_hint" in claim.model_dump_json():
            obligations.append("If possible, add regional sustainability context")

        return AssessResponse(
            score=round(score, 3), verdict=verdict, rationale=rationale,
            obligations=obligations, policy_tags=list(set(tags))
        )


POLICY = PolicyEngine()


# -----------------------------
# Signing / Verification
# -----------------------------

def sign_with_elder(elder: Elder, canonical: str) -> SingleSignature:
    sig = elder.private.sign(canonical.encode("utf-8"))
    pub_raw = elder.public.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    return SingleSignature(
        elder_id=elder.id,
        signer=b64(pub_raw),
        signature=b64(sig),
        signed_at=int(time.time()),
    )


def verify_single(pub_b64: str, canonical: str, sig_b64: str) -> bool:
    pub = Ed25519PublicKey.from_public_bytes(b64d(pub_b64))
    try:
        pub.verify(b64d(sig_b64), canonical.encode("utf-8"))
        return True
    except Exception:
        return False


def verify_quorum(canonical: str, qs: QuorumSignature, m_required: int) -> Tuple[bool, List[str]]:
    valid_ids: List[str] = []
    seen_pubkeys: set[str] = set()

    for s in qs.signatures:
        if verify_single(s.signer, canonical, s.signature):
            if s.signer not in seen_pubkeys:
                seen_pubkeys.add(s.signer)
                valid_ids.append(s.elder_id)

    return (len(valid_ids) >= m_required), valid_ids


# -----------------------------
# API
# -----------------------------
app = FastAPI(title="DRP AI Agents (Quorum Edition)", version="0.2.0")


@app.get("/v1/elders")
def list_elders() -> Dict[str, Any]:
    return {
        "n": len(ELDERS),
        "m_required": M_REQUIRED,
        "elders": [
            {"elder_id": e.id, "public_key_b64": e.pub_b64, "fingerprint": e.fingerprint}
            for e in ELDERS
        ],
    }


@app.post("/v1/agent/assess-activity", response_model=AssessResponse)
def assess_activity_api(claim: ActivityClaim):
    return POLICY.assess_activity(claim)


@app.post("/v1/elders/sign-block", response_model=QuorumSignature)
def sign_block_quorum(req: SignRequest):
    header = req.header
    if header.index < 0 or not header.previous_hash:
        raise HTTPException(status_code=400, detail="Invalid header fields")

    canonical = header.canonical_string()

    to_sign: List[Elder]
    if req.elder_ids:
        selected = {e.id: e for e in ELDERS}
        missing = [i for i in req.elder_ids if i not in selected]
        if missing:
            raise HTTPException(status_code=404, detail=f"Unknown elders: {missing}")
        to_sign = [selected[i] for i in req.elder_ids]
    else:
        to_sign = ELDERS

    sigs = [sign_with_elder(e, canonical) for e in to_sign]
    return QuorumSignature(signatures=sigs, policy={"m": M_REQUIRED, "n": len(ELDERS)})


@app.post("/v1/elders/verify-quorum", response_model=VerifyQuorumResponse)
def verify_quorum_api(req: VerifyQuorumRequest):
    valid, ids = verify_quorum(req.header_canonical, req.quorum, M_REQUIRED)
    distinct = len(set(ids))
    return VerifyQuorumResponse(valid=valid, valid_signers=ids, required_m=M_REQUIRED, total_distinct=distinct)


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
# List elders (see fingerprints & m)
curl -s http://localhost:8088/v1/elders | jq

# Ask a subset of elders to sign a genesis header (e.g., elder-0, elder-2, elder-4)
curl -s -X POST http://localhost:8088/v1/elders/sign-block \
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
        "elder_ids": ["elder-0", "elder-2", "elder-4"]
      }' | jq

# Verify the quorum for a canonical header string
curl -s -X POST http://localhost:8088/v1/elders/verify-quorum \
  -H 'Content-Type: application/json' \
  -d '{
        "header_canonical": "$(python - <<'PY'
import json;print(json.dumps({"index":0,"previous_hash":"0","timestamp":1735142096,"merkle_root":"","data_hash":"","miner_id":"genesis","nonce":0,"difficulty":0},separators=(",",":"),sort_keys=True))
PY)",
        "quorum": {"signatures": [
            {"elder_id": "elder-0", "signer": "<pub_b64>", "signature": "<sig_b64>", "signed_at": 1735142100},
            {"elder_id": "elder-2", "signer": "<pub_b64>", "signature": "<sig_b64>", "signed_at": 1735142101}
        ], "policy": {"m": 3, "n": 5}}
      }' | jq
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8088)
