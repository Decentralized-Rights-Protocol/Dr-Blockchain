"""Reward models for DeRi token distribution."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class RewardType(str, Enum):
    """Types of rewards."""
    
    ACTIVITY_VERIFICATION = "activity_verification"
    STATUS_MAINTENANCE = "status_maintenance"
    CONSISTENCY_BONUS = "consistency_bonus"
    ACHIEVEMENT = "achievement"
    REFERRAL = "referral"
    GOVERNANCE = "governance"


class Reward(BaseModel):
    """Individual reward entry."""
    
    reward_id: str = Field(..., description="Unique reward ID")
    user_id: str = Field(..., description="Recipient user ID")
    reward_type: RewardType
    amount: float = Field(..., ge=0.0, description="Reward amount in DeRi")
    multiplier: float = Field(default=1.0, ge=0.0, description="Status multiplier")
    base_amount: float = Field(..., ge=0.0, description="Base reward before multiplier")
    activity_id: Optional[str] = Field(None, description="Related activity ID")
    status_score_at_time: float = Field(..., ge=0.0, le=100.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    transaction_hash: Optional[str] = Field(None, description="Blockchain transaction hash")
    claimed: bool = Field(default=False, description="Whether reward has been claimed")
    
    class Config:
        use_enum_values = True


class RewardSummary(BaseModel):
    """Summary of rewards for a user."""
    
    user_id: str
    total_earned: float = Field(..., ge=0.0, description="Total DeRi earned")
    total_claimed: float = Field(..., ge=0.0, description="Total DeRi claimed")
    pending_rewards: float = Field(..., ge=0.0, description="Pending DeRi")
    rewards: list[Reward] = Field(default_factory=list, description="All rewards")
    current_multiplier: float = Field(default=1.0, ge=0.0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

