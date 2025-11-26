"""Rewards API routes."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import os

from core.schemas.rewards import RewardClaimRequest, RewardClaimResponse, RewardSummaryResponse
from core.models.rewards import Reward, RewardType, RewardSummary
from api.auth import get_current_user

router = APIRouter()
security = HTTPBearer()

# In-memory rewards store (in production, use database)
rewards_db = {}


def calculate_reward_amount(activity_type: str, verification_score: float, status_score: float) -> float:
    """
    Calculate reward amount based on activity and status.
    
    Args:
        activity_type: Type of activity
        verification_score: AI verification score
        status_score: User status score
        
    Returns:
        Reward amount in DeRi
    """
    # Base rewards by activity type
    base_rewards = {
        "education": 10.0,
        "health": 15.0,
        "engineering": 12.0,
        "agriculture": 10.0,
        "energy": 15.0,
        "research": 12.0,
        "community": 8.0,
        "governance": 10.0,
        "other": 5.0
    }
    
    base_amount = base_rewards.get(activity_type.lower(), 5.0)
    
    # Apply verification score multiplier
    verified_multiplier = verification_score
    
    # Apply status score multiplier (higher status = higher rewards)
    status_multiplier = 1.0 + (status_score / 100.0) * 0.5  # Up to 1.5x
    
    final_amount = base_amount * verified_multiplier * status_multiplier
    
    return round(final_amount, 2)


@router.get("/rewards/{user_id}/summary", response_model=RewardSummaryResponse)
async def get_reward_summary(user_id: str):
    """
    Get reward summary for a user.
    """
    user_rewards = rewards_db.get(user_id, [])
    
    total_earned = sum(r.get("amount", 0) for r in user_rewards)
    total_claimed = sum(r.get("amount", 0) for r in user_rewards if r.get("claimed", False))
    pending_rewards = total_earned - total_claimed
    
    # Get current multiplier (would be from status score)
    current_multiplier = 1.0
    
    summary = RewardSummary(
        user_id=user_id,
        total_earned=total_earned,
        total_claimed=total_claimed,
        pending_rewards=pending_rewards,
        rewards=[Reward(**r) for r in user_rewards],
        current_multiplier=current_multiplier
    )
    
    return RewardSummaryResponse(
        summary=summary,
        message="Reward summary retrieved successfully"
    )


@router.post("/rewards/claim", response_model=RewardClaimResponse)
async def claim_rewards(
    request: RewardClaimRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Claim pending rewards.
    """
    user_id = request.user_id
    user_rewards = rewards_db.get(user_id, [])
    
    # Filter rewards to claim
    if request.reward_ids:
        rewards_to_claim = [r for r in user_rewards if r.get("reward_id") in request.reward_ids and not r.get("claimed", False)]
    else:
        rewards_to_claim = [r for r in user_rewards if not r.get("claimed", False)]
    
    if not rewards_to_claim:
        raise HTTPException(status_code=400, detail="No rewards to claim")
    
    # Calculate total
    total_claimed = sum(r.get("amount", 0) for r in rewards_to_claim)
    
    # Mark as claimed
    for reward in rewards_to_claim:
        reward["claimed"] = True
    
    # In production, create blockchain transaction
    transaction_hash = f"0x{os.urandom(32).hex()}"
    
    return RewardClaimResponse(
        success=True,
        transaction_hash=transaction_hash,
        total_claimed=total_claimed,
        message=f"Successfully claimed {len(rewards_to_claim)} rewards"
    )


@router.post("/rewards/calculate")
async def calculate_reward(
    activity_id: str,
    user_id: str,
    activity_type: str,
    verification_score: float,
    status_score: float
):
    """
    Calculate reward for an activity.
    """
    import os
    import secrets
    
    amount = calculate_reward_amount(activity_type, verification_score, status_score)
    
    reward = {
        "reward_id": f"reward-{secrets.token_hex(16)}",
        "user_id": user_id,
        "reward_type": RewardType.ACTIVITY_VERIFICATION.value,
        "amount": amount,
        "multiplier": 1.0 + (status_score / 100.0) * 0.5,
        "base_amount": amount / (1.0 + (status_score / 100.0) * 0.5),
        "activity_id": activity_id,
        "status_score_at_time": status_score,
        "claimed": False
    }
    
    # Store reward
    if user_id not in rewards_db:
        rewards_db[user_id] = []
    rewards_db[user_id].append(reward)
    
    return {
        "reward_id": reward["reward_id"],
        "amount": amount,
        "multiplier": reward["multiplier"],
        "message": "Reward calculated and stored"
    }

