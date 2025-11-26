"""Status API schemas."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from ..models.status import StatusScore


class StatusProfileRequest(BaseModel):
    """Request to get status profile."""
    
    user_id: str = Field(..., description="User ID")


class StatusProfileResponse(BaseModel):
    """Status profile response."""
    
    user_id: str
    status_score: StatusScore
    total_activities: int
    verified_activities: int
    rejected_activities: int
    achievements: List[str] = Field(default_factory=list)
    orbitdb_cid: Optional[str] = None


class StatusUpdateRequest(BaseModel):
    """Request to update status."""
    
    user_id: str
    force_recalculate: bool = Field(default=False)

