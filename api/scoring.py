"""
DRP PoAT Scoring Engine
=======================
Weighted scoring for all activity types. Used by activity.py and verification.py.
Anti-gaming, tier assignment, $DeRi reward calculation.
"""

import hashlib
import math
import re
import time
from collections import defaultdict
from typing import Any, Dict, List, Tuple

# Scoring weights (sum = 1.0)
WEIGHTS = {
    "comprehension": 0.35,
    "effort": 0.30,
    "consistency": 0.20,
    "novelty": 0.15,
}

TIER_THRESHOLDS = [
    (0.85, "platinum"),
    (0.70, "gold"),
    (0.50, "silver"),
    (0.30, "bronze"),
    (0.00, "unranked"),
]

DERI_RATE = 10.0  # $DeRi per 1.0 final_score

# In-memory anti-gaming state (stateless on restart; use Redis for persistence)
_velocity: Dict[str, List[float]] = defaultdict(list)
_content_hashes: Dict[str, List[str]] = defaultdict(list)


def score_activity(
    activity_type: str,
    content: str,
    context: str,
    metadata: Dict[str, Any],
    user_id: str,
) -> Dict[str, Any]:
    """
    Main scoring entrypoint. Returns a full score dict.

    Args:
        activity_type: One of reading/writing/community/code/physical/other
        content: The submitted text/response
        context: Source material or prompt
        metadata: time_spent_seconds, word_count, verified_by_device, etc.
        user_id: Used for anti-gaming tracking
    """
    notes: List[str] = []
    wc = len(content.split())
    ts = int(metadata.get("time_spent_seconds", 0))

    if activity_type == "reading":
        comp = _kw_overlap(content, context)
        if wc < 20: comp *= 0.5; notes.append("Response too short.")
        effort = min(1.0, ts / max(len(context.split()) * 0.5, 30))
        cons = _consistency(content)
        nov = _novelty(content)

    elif activity_type == "writing":
        comp = _kw_overlap(content, context) if context else 0.6
        effort = min(1.0, (wc / 200) * 0.5 + (ts / 300) * 0.5)
        cons = _consistency(content)
        nov = _novelty(content)

    elif activity_type == "community":
        helpful_kw = ["help", "support", "answer", "solution", "because", "reason", "explain"]
        comp = min(1.0, sum(1 for w in helpful_kw if w in content.lower()) / 4)
        effort = min(1.0, wc / 100)
        cons = _consistency(content)
        nov = 0.65

    elif activity_type == "code":
        lines = [l for l in content.split("\n") if l.strip()]
        has_comments = any(l.strip().startswith(("#", "//", "/*")) for l in lines)
        has_fns = bool(re.search(r"(def |function |async |class )", content))
        comp = 0.90 if (has_comments and has_fns) else (0.70 if has_fns else 0.45)
        effort = min(1.0, len(lines) / 50)
        cons = _consistency(content)
        nov = _novelty(content)
        if has_comments: notes.append("Code includes documentation — quality bonus.")

    elif activity_type == "physical":
        duration = float(metadata.get("duration_minutes", 0))
        verified = bool(metadata.get("verified_by_device", False))
        hr = int(metadata.get("heart_rate_avg", 0))
        comp = 0.85
        effort = min(1.0, duration / 60)
        if hr > 140: effort = min(1.0, effort + 0.15); notes.append("High intensity bonus.")
        cons = 0.90 if verified else 0.50
        nov = 0.50
        if not verified: notes.append("Not device-verified — consistency reduced.")

    else:
        comp, effort, cons, nov = 0.1, 0.1, 0.1, 0.0
        notes.append(f"Unknown activity type: {activity_type}")

    # Gaming detection
    gaming = _detect_gaming(user_id, content, ts)
    gaming_risk = gaming["risk"]

    # Weighted raw score
    raw = (
        comp * WEIGHTS["comprehension"]
        + effort * WEIGHTS["effort"]
        + cons * WEIGHTS["consistency"]
        + nov * WEIGHTS["novelty"]
    )
    final = round(max(0.0, raw * (1.0 - gaming_risk * 0.5)), 4)
    tier = _tier(final)
    deri = round(final * DERI_RATE, 4)

    return {
        "comprehension": round(comp, 3),
        "effort": round(effort, 3),
        "consistency": round(cons, 3),
        "novelty": round(nov, 3),
        "gaming_risk": round(gaming_risk, 3),
        "gaming_flags": gaming["flags"],
        "raw_score": round(raw, 3),
        "final_score": final,
        "tier": tier,
        "deri_reward": deri,
        "notes": notes,
        "scored_at": time.time(),
    }


def _tier(score: float) -> str:
    for threshold, name in TIER_THRESHOLDS:
        if score >= threshold:
            return name
    return "unranked"


def _kw_overlap(response: str, source: str) -> float:
    if not source:
        return 0.5
    sw = set(re.findall(r'\b\w{4,}\b', source.lower()))
    rw = set(re.findall(r'\b\w{4,}\b', response.lower()))
    return min(1.0, (len(sw & rw) / max(len(sw), 1)) * 2.0)


def _consistency(text: str) -> float:
    sents = [s.strip() for s in text.split(".") if s.strip()]
    if not sents:
        return 0.1
    return min(1.0, (sum(len(s.split()) for s in sents) / len(sents)) / 15)


def _novelty(text: str) -> float:
    words = text.lower().split()
    if not words:
        return 0.0
    return min(1.0, (len(set(words)) / len(words)) * 1.2)


def _entropy(text: str) -> float:
    freq: Dict[str, int] = {}
    for c in text:
        freq[c] = freq.get(c, 0) + 1
    t = len(text)
    if not t:
        return 0.0
    return -sum((v / t) * math.log2(v / t) for v in freq.values())


def _detect_gaming(user_id: str, content: str, time_spent: int) -> Dict[str, Any]:
    """Velocity + duplicate + entropy checks."""
    flags: List[str] = []
    risk = 0.0
    now = time.time()

    # Velocity: >5 submissions per 60s
    times = _velocity[user_id]
    times.append(now)
    _velocity[user_id] = [t for t in times if now - t < 60]
    if len(_velocity[user_id]) > 5:
        flags.append("high_velocity")
        risk += 0.40

    # Time threshold
    if time_spent < 8:
        flags.append("too_fast")
        risk += 0.30

    # Duplicate content
    ch = hashlib.sha3_256(content.encode()).hexdigest()
    past = _content_hashes[user_id]
    if ch in past:
        flags.append("duplicate_content")
        risk += 0.50
    else:
        past.append(ch)
        if len(past) > 100:
            past.pop(0)

    # Low entropy (spam)
    if content and _entropy(content) < 1.5:
        flags.append("low_entropy")
        risk += 0.30

    return {"risk": round(min(1.0, risk), 3), "flags": flags}


def post_level(total_score: float) -> int:
    """Compute Proof of Status level (0-10) from cumulative score."""
    thresholds = [5, 15, 30, 50, 80, 120, 180, 260, 360, 500]
    for lvl, t in enumerate(thresholds, 1):
        if total_score < t:
            return lvl - 1
    return 10
