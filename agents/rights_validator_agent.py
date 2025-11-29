"""Rights Validator Agent for DRP.

Ensures fair allocation of RIGHTS/DeRi tokens based on DRP Proof-of-Status rules.
"""

from __future__ import annotations

from typing import Any, Dict
import logging


logger = logging.getLogger(__name__)


class RightsValidatorAgent:
    """Computes DeRi rewards based on activity type and status.

    Policy (simplified):
    - Base reward determined by ``activity_type``
    - Multiplied by user status score and AI verification score
    """

    BASE_REWARD: Dict[str, float] = {
        "education": 10.0,
        "health": 12.0,
        "governance": 8.0,
        "default": 5.0,
    }

    def compute_reward(
        self,
        activity_type: str,
        status_score: float,
        verification_score: float,
    ) -> Dict[str, Any]:
        """Compute reward for an activity.

        Args:
            activity_type: Category of activity (education, health, etc.).
            status_score: User Proof-of-Status score [0, 100].
            verification_score: AI verification score [0, 1].

        Returns:
            Dict with reward breakdown and final DeRi amount.
        """
        base = self.BASE_REWARD.get(activity_type.lower(), self.BASE_REWARD["default"])

        # Status multiplier: up to +50% at status_score=100
        bounded_status = max(0.0, min(status_score, 100.0))
        status_mult = 1.0 + bounded_status / 100.0 * 0.5

        bounded_verif = max(0.0, min(verification_score, 1.0))
        final_amount = base * status_mult * bounded_verif

        result = {
            "base": base,
            "status_multiplier": status_mult,
            "verification_score": bounded_verif,
            "amount_DERi": round(final_amount, 6),
        }
        logger.info(
            "Reward computed: type=%s base=%.2f status=%.1f verif=%.2f final=%.6f",
            activity_type,
            base,
            status_score,
            verification_score,
            result["amount_DERi"],
        )
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