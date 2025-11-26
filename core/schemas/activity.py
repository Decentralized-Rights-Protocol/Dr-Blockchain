"""Activity API schemas."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from ..models.activity import ActivityType


class ActivitySubmitRequest(BaseModel):
    """Request to submit an activity."""
    
    user_id: str = Field(..., description="User ID")
    activity_type: ActivityType = Field(..., description="Type of activity")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    location: Optional[str] = Field(None, max_length=200)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    attachments: List[str] = Field(default_factory=list, description="File paths or URLs")


class ActivitySubmitResponse(BaseModel):
    """Response after submitting an activity."""
    
    activity_id: str
    orbitdb_cid: str
    ipfs_cids: List[str] = Field(default_factory=list)
    verification_status: str = Field(default="pending")
    message: str


class ActivityFeedResponse(BaseModel):
    """Activity feed response."""
    
    activities: List[Dict[str, Any]]
    total: int
    page: int = Field(default=1)
    page_size: int = Field(default=20)


class ActivityVerificationRequest(BaseModel):
    """Request to verify an activity."""
    
    activity_id: str
    force_reverify: bool = Field(default=False)

