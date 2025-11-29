"""Fraud Detection Agent for DRP.

Detects multi-accounting, fake submissions, or suspicious transactions.
"""

from __future__ import annotations

from typing import Any, Dict, List
import logging


logger = logging.getLogger(__name__)


class FraudDetectionAgent:
    """Heuristic fraud detection agent.

    Can be extended with ML/LLM-based anomaly detection.
    """

    def score_activity(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Score an activity for fraud likelihood.

        Returns:
            Dict with keys: ``score`` (0-1), ``suspicious`` (bool), ``flags`` (list[str]).
        """
        description = (activity.get("description") or "").lower()
        flags: List[str] = []

        # Very basic keyword heuristics
        scam_keywords = ["free money", "guaranteed", "no risk", "act now"]
        if any(kw in description for kw in scam_keywords):
            flags.append("scam-like language detected")

        words = description.split()
        if words:
            unique_ratio = len(set(words)) / float(len(words))
            if unique_ratio < 0.4:
                flags.append("highly repetitive content")

        score = min(1.0, 0.3 * len(flags))
        suspicious = score > 0.3

        result = {"score": score, "suspicious": suspicious, "flags": flags}
        logger.info("Fraud score: %.2f suspicious=%s flags=%s", score, suspicious, flags)
        return result

    def score_transfers(self, transfers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Score a batch of token transfers for suspicious patterns."""
        from_counts: Dict[str, int] = {}
        for t in transfers:
            sender = t.get("from", "").lower()
            from_counts[sender] = from_counts.get(sender, 0) + 1

        flags: List[str] = []
        for addr, count in from_counts.items():
            if count > 20:
                flags.append(f"Address {addr} has {count} transfers in window")

        score = min(1.0, 0.1 * len(flags))
        suspicious = score > 0.3
        result = {"score": score, "suspicious": suspicious, "flags": flags}
        logger.info("Transfer fraud score: %.2f suspicious=%s flags=%s", score, suspicious, flags)
        return result

{
  "cells": [],
  "metadata": {
    "language_info": {
      "name": "python"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 2
}