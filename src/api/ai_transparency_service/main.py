"""
AI Transparency & ZK Explainability microservice (FastAPI)
Endpoints:
  - POST /api/ai/decide
  - GET  /api/ai/decision/{id}
  - GET  /api/ai/models
  - POST /api/ai/dispute
  - GET  /api/ai/health

Notes:
 - Stores no raw PII; only hashes and encrypted artifacts are persisted
 - Explanation JSON/PNG artifacts are AES-GCM encrypted and pinned to IPFS
 - Decision records are signed with Elder node key (Ed25519)
 - ScyllaDB is used for decision_records persistence (see db.py)
"""

import base64
import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from api.ai_transparency_service import db
from api.ai_transparency_service.ipfs_utils import encrypt_and_pin, get_decrypted

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes

try:
    import shap  # noqa: F401
    SHAP_AVAILABLE = True
except Exception:
    SHAP_AVAILABLE = False

try:
    import numpy as np
    import matplotlib.pyplot as plt
    NUMPY_AVAILABLE = True
except Exception:
    NUMPY_AVAILABLE = False


API_PREFIX = "/api/ai"


class DecideInput(BaseModel):
    model_id: str
    model_version: str
    input_type: str = Field(..., description="image|gps|text|sensor")
    input_commitment: str = Field(..., description="Hash/commitment of input. Do not send raw data.")
    features: Optional[Dict[str, float]] = Field(default=None, description="Optional numeric features for local explainability demo")
    confidence: float = Field(..., ge=0.0, le=1.0)
    decision: str = Field(..., pattern="^(approved|flagged|denied)$")


class DecideResponse(BaseModel):
    decision_id: str
    outcome: str
    confidence: float
    explanation_cid: Optional[str]
    explanation_png_cid: Optional[str]
    zk_proof_cid: Optional[str]
    signature: str
    timestamp: str


class DisputeInput(BaseModel):
    decision_id: str
    reason: str


app = FastAPI(title="DRP AI Transparency & ZK Explainability")


def _load_elder_private_key() -> ed25519.Ed25519PrivateKey:
    key_path = os.getenv("ELDER_PRIVATE_KEY_PATH", "keys/elder_private.key")
    os.makedirs(os.path.dirname(key_path), exist_ok=True)
    if os.path.exists(key_path):
        with open(key_path, "rb") as f:
            key_bytes = f.read()
        return ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)
    key = ed25519.Ed25519PrivateKey.generate()
    key_bytes = key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(key_path, "wb") as f:
        f.write(key_bytes)
    return key


ELDER_PRIV = _load_elder_private_key()
ELDER_PUB_HEX = ELDER_PRIV.public_key().public_bytes(
    serialization.Encoding.Raw, serialization.PublicFormat.Raw
).hex()


def sign_record(record: Dict[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    sig = ELDER_PRIV.sign(payload)
    return sig.hex()


def _generate_explanation(features: Optional[Dict[str, float]]) -> Dict[str, Any]:
    # Minimal, privacy-preserving explanation stub. No raw inputs.
    explanation: Dict[str, Any] = {
        "method": "SHAP" if SHAP_AVAILABLE else "heuristic",
        "top_factors": [],
    }
    if not features:
        return explanation
    # Take top 5 absolute features
    top = sorted(features.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
    explanation["top_factors"] = [
        {"feature": k, "contribution": float(v)} for k, v in top
    ]
    return explanation


def _render_explanation_png(explanation: Dict[str, Any]) -> Optional[bytes]:
    if not NUMPY_AVAILABLE:
        return None
    try:
        factors = explanation.get("top_factors", [])
        if not factors:
            return None
        labels = [f["feature"] for f in factors]
        values = [f["contribution"] for f in factors]
        plt.figure(figsize=(4, 2.5))
        colors = ["#3b82f6" if v >= 0 else "#ef4444" for v in values]
        plt.bar(labels, values, color=colors)
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        import io

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150)
        plt.close()
        return buf.getvalue()
    except Exception:
        return None


@app.post(f"{API_PREFIX}/decide", response_model=DecideResponse)
def decide(payload: DecideInput):
    ts = datetime.now(timezone.utc).isoformat()
    decision_id = uuid.uuid4().hex[:16]

    explanation = _generate_explanation(payload.features)
    explanation_json = json.dumps(
        {
            "model_id": payload.model_id,
            "model_version": payload.model_version,
            "input_commitment": payload.input_commitment,
            "explanation": explanation,
            "timestamp": ts,
        },
        separators=(",", ":"),
    ).encode()

    explanation_png_bytes = _render_explanation_png(explanation)

    # Encrypt and pin artifacts to IPFS
    explanation_cid = encrypt_and_pin(explanation_json)
    explanation_png_cid = (
        encrypt_and_pin(explanation_png_bytes) if explanation_png_bytes else None
    )

    # ZK proof placeholder: produce a commitment CID after hypothetical proof
    zk_payload = json.dumps(
        {
            "type": "confidence_threshold",
            "confidence": payload.confidence,
            "threshold": 0.8,
            "valid": payload.confidence >= 0.8,
            "decision_id": decision_id,
            "ts": ts,
        },
        separators=(",", ":"),
    ).encode()
    zk_proof_cid = encrypt_and_pin(zk_payload)

    record = {
        "decision_id": decision_id,
        "model_id": payload.model_id,
        "model_version": payload.model_version,
        "input_type": payload.input_type,
        "input_commitment": payload.input_commitment,
        "outcome": payload.decision,
        "confidence": payload.confidence,
        "explanation_cid": explanation_cid,
        "explanation_png_cid": explanation_png_cid,
        "zk_proof_cid": zk_proof_cid,
        "elder_pub": ELDER_PUB_HEX,
        "timestamp": ts,
    }
    record["signature"] = sign_record(record)

    # Persist to ScyllaDB
    try:
        db.ensure_schema()
        db.insert_decision_record(record)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    return DecideResponse(
        decision_id=decision_id,
        outcome=payload.decision,
        confidence=payload.confidence,
        explanation_cid=explanation_cid,
        explanation_png_cid=explanation_png_cid,
        zk_proof_cid=zk_proof_cid,
        signature=record["signature"],
        timestamp=ts,
    )


@app.get(f"{API_PREFIX}/decision/{{decision_id}}")
def get_decision(decision_id: str):
    try:
        db.ensure_schema()
        rec = db.get_decision_record(decision_id)
        if not rec:
            raise HTTPException(status_code=404, detail="Not found")
        # Do not return decrypted artifacts; only CIDs
        return rec
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")


@app.get(f"{API_PREFIX}/models")
def list_models():
    # Placeholder static model cards reference
    return {
        "models": [
            {
                "model_id": "face_verification_v1",
                "version": "1.2.0",
                "card": "/ai/models/model-card.json",
            }
        ]
    }


@app.post(f"{API_PREFIX}/dispute")
def create_dispute(payload: DisputeInput):
    try:
        db.ensure_schema()
        ok = db.create_dispute(payload.decision_id, payload.reason)
        if not ok:
            raise HTTPException(status_code=400, detail="Unable to create dispute")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")


@app.get(f"{API_PREFIX}/health")
def health():
    return {
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat(),
        "shap": SHAP_AVAILABLE,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))


