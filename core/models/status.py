"""Status models for Proof of Status (PoST)."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class StatusScore(BaseModel):
    """Computed status score for a user."""
    
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall status score")
    activity_score: float = Field(..., ge=0.0, le=100.0, description="Activity contribution")
    consistency_score: float = Field(..., ge=0.0, le=100.0, description="Consistency metric")
    reputation_score: float = Field(..., ge=0.0, le=100.0, description="Reputation metric")
    verification_rate: float = Field(..., ge=0.0, le=1.0, description="Verification success rate")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class StatusProfile(BaseModel):
    """User status profile for long-term tracking."""
    
    user_id: str = Field(..., description="User identifier")
    status_score: StatusScore = Field(..., description="Current status score")
    total_activities: int = Field(default=0, description="Total verified activities")
    verified_activities: int = Field(default=0, description="Number of verified activities")
    rejected_activities: int = Field(default=0, description="Number of rejected activities")
    activity_history: list[str] = Field(default_factory=list, description="Activity IDs")
    achievements: list[str] = Field(default_factory=list, description="Achievement badges")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    orbitdb_cid: Optional[str] = Field(None, description="OrbitDB entry CID")


class StatusProof(BaseModel):
    """Proof of Status for blockchain submission."""
    
    user_id: str
    status_score: StatusScore
    orbitdb_cid: str
    quantum_hash: str = Field(..., description="Quantum-secure hash")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    signature: Optional[str] = Field(None, description="Cryptographic signature")

