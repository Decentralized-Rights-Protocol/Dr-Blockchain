"""Rewards API schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field
from ..models.rewards import Reward, RewardSummary


class RewardClaimRequest(BaseModel):
    """Request to claim rewards."""
    
    user_id: str
    reward_ids: Optional[List[str]] = Field(None, description="Specific reward IDs, or all if None")


class RewardClaimResponse(BaseModel):
    """Reward claim response."""
    
    success: bool
    transaction_hash: Optional[str] = None
    total_claimed: float
    message: str


class RewardSummaryResponse(BaseModel):
    """Reward summary response."""
    
    summary: RewardSummary
    message: str

