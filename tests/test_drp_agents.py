"""Basic tests for DRP blockchain client and AI agents."""

from __future__ import annotations

from agents import (
    ActivityVerificationAgent,
    FraudDetectionAgent,
    RightsValidatorAgent,
)


def test_activity_verification_basic():
    agent = ActivityVerificationAgent()
    result = agent.verify(
        {
            "title": "Teaching renewable energy",
            "description": "Conducted a 2-hour workshop on sustainable energy systems.",
        }
    )
    assert 0.0 <= result["score"] <= 1.0


def test_fraud_detection_basic():
    agent = FraudDetectionAgent()
    result = agent.score_activity(
        {"description": "This is a normal description of honest work and contribution."}
    )
    assert 0.0 <= result["score"] <= 1.0


def test_rights_validator_basic():
    agent = RightsValidatorAgent()
    reward = agent.compute_reward("education", status_score=70.0, verification_score=0.8)
    assert reward["amount_DERi"] > 0


