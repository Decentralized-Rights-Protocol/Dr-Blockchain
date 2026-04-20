"""
DRP Verification API
====================
Endpoints for reading comprehension verification and PoAT generation.
Works alongside existing api/activity.py without duplication.
"""

import hashlib
import re
import time
import uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/verify", tags=["Verification"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class VerificationRequest(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=128)
    source_text: str = Field(..., min_length=100, max_length=10_000)
    responses: Dict[str, str] = Field(..., description="question_id -> answer text")
    time_spent_seconds: Optional[int] = Field(None, ge=0)


class VerificationResult(BaseModel):
    user_id: str
    comprehension_score: float
    effort_score: float
    consistency_score: float
    final_score: float
    tier: str
    poat_id: str
    passed: bool
    feedback: str
    record_hash: str


class QuestionRequest(BaseModel):
    source_text: str = Field(..., min_length=100, max_length=10_000)
    count: int = Field(default=3, ge=1, le=5)


# ── Scoring helpers ───────────────────────────────────────────────────────────

def _kw_overlap(response: str, source: str) -> float:
    source_words = set(re.findall(r'\b\w{4,}\b', source.lower()))
    resp_words = set(re.findall(r'\b\w{4,}\b', response.lower()))
    if not source_words:
        return 0.5
    return min(1.0, (len(source_words & resp_words) / len(source_words)) * 2.0)


def _consistency(text: str) -> float:
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    if not sentences:
        return 0.1
    avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
    return min(1.0, avg_len / 15)


def _entropy(text: str) -> float:
    import math
    freq: Dict[str, int] = {}
    for c in text:
        freq[c] = freq.get(c, 0) + 1
    total = len(text)
    if not total:
        return 0.0
    return -sum((v / total) * math.log2(v / total) for v in freq.values())


def _score_to_tier(score: float) -> str:
    if score >= 0.85: return "platinum"
    if score >= 0.70: return "gold"
    if score >= 0.50: return "silver"
    if score >= 0.30: return "bronze"
    return "unranked"


def _score_responses(
    combined: str, source: str, time_spent: int
) -> Dict[str, float]:
    word_count = len(combined.split())
    src_wc = len(source.split()) if source else 100

    comprehension = _kw_overlap(combined, source) if source else 0.5
    if word_count < 30:
        comprehension *= 0.6

    effort = min(1.0, time_spent / max(src_wc * 0.5, 30))
    if time_spent < 10:
        effort *= 0.3

    consistency = _consistency(combined)

    # Gaming: low entropy = spam/filler
    gaming_penalty = 0.0
    if _entropy(combined) < 1.5:
        gaming_penalty = 0.4

    raw = comprehension * 0.40 + effort * 0.30 + consistency * 0.20 + 0.10
    final = max(0.0, raw * (1.0 - gaming_penalty))

    return {
        "comprehension": round(comprehension, 3),
        "effort": round(effort, 3),
        "consistency": round(consistency, 3),
        "gaming_penalty": round(gaming_penalty, 3),
        "raw": round(raw, 3),
        "final": round(final, 3),
    }


def _hash_record(data: dict) -> str:
    import json
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha3_256(canonical.encode()).hexdigest()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/reading", response_model=VerificationResult, status_code=201)
async def verify_reading(req: VerificationRequest):
    """
    Score reading comprehension responses and generate a signed PoAT record.
    Integrates with the existing activity pipeline.
    """
    combined = "\n".join(f"Q{k}: {v}" for k, v in req.responses.items())
    scores = _score_responses(combined, req.source_text, req.time_spent_seconds or 0)

    final = scores["final"]
    passed = final >= 0.40
    tier = _score_to_tier(final)
    poat_id = str(uuid.uuid4())
    created_at = time.time()

    # Build tamper-evident hash
    record_hash = _hash_record({
        "id": poat_id,
        "user_id": req.user_id,
        "type": "reading_verification",
        "final_score": final,
        "created_at": created_at,
    })

    feedback = _build_feedback(scores, passed, tier)

    return VerificationResult(
        user_id=req.user_id,
        comprehension_score=scores["comprehension"],
        effort_score=scores["effort"],
        consistency_score=scores["consistency"],
        final_score=final,
        tier=tier,
        poat_id=poat_id,
        passed=passed,
        feedback=feedback,
        record_hash=record_hash,
    )


@router.post("/questions")
async def generate_questions(req: QuestionRequest):
    """Generate comprehension questions for a source text."""
    templates = [
        ("What is the central argument or main idea presented?", "open"),
        ("Explain in your own words the key concept described.", "open"),
        ("What conclusion or insight can you draw from this text?", "open"),
        ("Identify one thing that surprised you or that you found new.", "reflection"),
        ("How would you apply or relate this to real-world situations?", "application"),
    ]
    sentences = [s.strip() for s in req.source_text.split(".") if len(s.strip()) > 40]
    questions = []
    for i, (q, qt) in enumerate(templates[: req.count]):
        hint = sentences[i % max(len(sentences), 1)][:120] if sentences else ""
        questions.append({"id": f"q{i+1}", "question": q, "type": qt, "hint": hint})
    return {"count": len(questions), "questions": questions}


@router.get("/record/{record_hash}/check")
async def check_record_integrity(record_hash: str):
    """Verify a record hash format (cryptographic structure check)."""
    valid = len(record_hash) == 64 and all(c in "0123456789abcdef" for c in record_hash)
    return {
        "record_hash": record_hash,
        "format_valid": valid,
        "algorithm": "SHA3-256",
        "note": "Full integrity verification requires fetching the original record from OrbitDB.",
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_feedback(scores: dict, passed: bool, tier: str) -> str:
    if not passed:
        return (
            f"Score {scores['final']:.2f} did not meet the 0.40 threshold. "
            "Spend more time reading the material carefully before responding."
        )
    msgs = {
        "platinum": "Outstanding! Exceptional comprehension and engagement.",
        "gold": "Excellent work — strong understanding demonstrated.",
        "silver": "Good job. Solid grasp of the material.",
        "bronze": "Passed. Keep engaging deeply to improve your tier.",
    }
    return msgs.get(tier, "Passed.")
