"""Activity models for Proof of Activity (PoA)."""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ActivityType(str, Enum):
    """Types of activities that can be verified."""
    
    EDUCATION = "education"
    HEALTH = "health"
    ENGINEERING = "engineering"
    AGRICULTURE = "agriculture"
    ENERGY = "energy"
    RESEARCH = "research"
    COMMUNITY = "community"
    GOVERNANCE = "governance"
    OTHER = "other"


class Activity(BaseModel):
    """Activity log entry."""
    
    id: str = Field(..., description="Unique activity ID")
    user_id: str = Field(..., description="User who performed the activity")
    activity_type: ActivityType = Field(..., description="Type of activity")
    title: str = Field(..., description="Activity title")
    description: str = Field(..., description="Detailed description")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location: Optional[str] = Field(None, description="Geographic location")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    attachments: list[str] = Field(default_factory=list, description="IPFS CIDs of attachments")
    verified: bool = Field(default=False, description="AI verification status")
    verification_score: float = Field(default=0.0, ge=0.0, le=1.0)
    orbitdb_cid: Optional[str] = Field(None, description="OrbitDB entry CID")
    
    class Config:
        use_enum_values = True


class ActivityProof(BaseModel):
    """Proof of Activity for blockchain submission."""
    
    activity_id: str
    user_id: str
    orbitdb_cid: str
    ipfs_cid: Optional[str] = None
    quantum_hash: str = Field(..., description="Quantum-secure hash")
    ai_verification_score: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    signature: Optional[str] = Field(None, description="Cryptographic signature")

