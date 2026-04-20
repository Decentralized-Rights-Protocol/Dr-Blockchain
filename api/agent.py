"""Agent-focused API endpoints for Dr-Blockchain.

These endpoints are designed for consumption by:
- decentralizedrights.com
- explorer.decentralizedrights.com
- app.decentralizedrights.com
- api.decentralizedrights.com
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from blockchain import DRPBlockchainClient
from agents import (
    ActivityVerificationAgent,
    RightsValidatorAgent,
    FraudDetectionAgent,
    GovernanceAgent,
)


router = APIRouter()

_client = DRPBlockchainClient()
_activity_agent = ActivityVerificationAgent()
_rights_agent = RightsValidatorAgent()
_fraud_agent = FraudDetectionAgent()
_gov_agent = GovernanceAgent()


class UserStatusRequest(BaseModel):
    """Request payload for /get_user_status."""

    address: str = Field(..., description="User wallet address")


class UserStatusResponse(BaseModel):
    """Response payload for /get_user_status."""

    address: str
    rights_balance: float
    deri_balance: float
    status_score: float = Field(0.0, description="Simplified Proof-of-Status score")


class ActivityVerificationRequest(BaseModel):
    """Request payload for /verify_activity."""

    user_id: str
    activity_type: str
    title: str
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ActivityVerificationResponse(BaseModel):
    """Response payload for /verify_activity."""

    verified: bool
    verification_score: float
    fraud_score: float
    fraud_flags: List[str]
    reward_estimate_DERi: float


class TokenBalanceRequest(BaseModel):
    """Request payload for /get_token_balance."""

    address: str
    token: str = Field(..., pattern="^(RIGHTS|DeRi)$")


class TokenBalanceResponse(BaseModel):
    """Response payload for /get_token_balance."""

    address: str
    token: str
    balance: float


class GovernanceProposalsResponse(BaseModel):
    """Response payload for /get_governance_proposals."""

    proposals: List[Dict[str, Any]]


@router.post("/get_user_status", response_model=UserStatusResponse)
async def get_user_status(payload: UserStatusRequest) -> UserStatusResponse:
    """Return a user's token balances and a simple status score."""
    try:
        rights = _client.get_token_balance("RIGHTS", payload.address)
        deri = _client.get_token_balance("DERI", payload.address)

        # Simple derived status score: a placeholder for full PoST computation
        status_score = min(100.0, (rights + deri))

        return UserStatusResponse(
            address=payload.address,
            rights_balance=rights,
            deri_balance=deri,
            status_score=status_score,
        )
    except Exception as exc:  # pragma: no cover - external dependency
        raise HTTPException(status_code=500, detail=f"Failed to get status: {exc}") from exc


@router.post("/verify_activity", response_model=ActivityVerificationResponse)
async def verify_activity(payload: ActivityVerificationRequest) -> ActivityVerificationResponse:
    """Verify an activity and estimate rewards & fraud risk."""
    activity_dict = payload.model_dump()

    verif = _activity_agent.verify(activity_dict)
    fraud = _fraud_agent.score_activity(activity_dict)

    # Example status score stub; in production query OrbitDB / PoST engine
    status_score = 70.0

    reward = _rights_agent.compute_reward(
        activity_type=payload.activity_type,
        status_score=status_score,
        verification_score=verif["score"],
    )

    verified = verif["verified"] and not fraud["suspicious"]

    return ActivityVerificationResponse(
        verified=verified,
        verification_score=verif["score"],
        fraud_score=fraud["score"],
        fraud_flags=fraud["flags"],
        reward_estimate_DERi=reward["amount_DERi"],
    )


@router.post("/get_token_balance", response_model=TokenBalanceResponse)
async def get_token_balance(payload: TokenBalanceRequest) -> TokenBalanceResponse:
    """Return token balance for RIGHTS or DeRi."""
    try:
        balance = _client.get_token_balance(payload.token, payload.address)
        return TokenBalanceResponse(
            address=payload.address,
            token=payload.token,
            balance=balance,
        )
    except Exception as exc:  # pragma: no cover - external dependency
        raise HTTPException(status_code=500, detail=f"Failed to get balance: {exc}") from exc


@router.get("/get_governance_proposals", response_model=GovernanceProposalsResponse)
async def get_governance_proposals() -> GovernanceProposalsResponse:
    """Return governance proposals evaluated by the GovernanceAgent.

    In production, proposals would be fetched from the DRP governance contract
    or an indexed data store; here we provide a static sample.
    """
    proposals: list[Dict[str, Any]] = [
        {
            "id": "prop-1",
            "title": "Increase DeRi rewards for SDG-aligned activities",
            "impact": 8,
            "sdg_alignment": 9,
            "complexity": 3,
        },
        {
            "id": "prop-2",
            "title": "Reduce fees for education-related submissions",
            "impact": 7,
            "sdg_alignment": 8,
            "complexity": 2,
        },
    ]
    enriched: list[Dict[str, Any]] = []
    for p in proposals:
        score = _gov_agent.evaluate_proposal(p)
        enriched.append({**p, **score})
    return GovernanceProposalsResponse(proposals=enriched)


