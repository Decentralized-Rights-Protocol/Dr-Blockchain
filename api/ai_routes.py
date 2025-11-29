"""
AI ElderCore API endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel

from ai.elder_core import AIElderCore

router = APIRouter()
ai_elder = AIElderCore()


class ActivityVerificationRequest(BaseModel):
    activity_id: str
    user_id: str
    activity_type: str
    title: str
    description: str
    metadata: Dict[str, Any] = {}


class StatusVerificationRequest(BaseModel):
    user_id: str
    activities: list
    current_score: float
    profile: Dict[str, Any] = {}


@router.post("/ai/verify/activity")
async def verify_activity(request: ActivityVerificationRequest):
    """Verify a PoAT activity."""
    activity = request.dict()
    result = ai_elder.verify_activity(activity)
    return result


@router.post("/ai/verify/status")
async def verify_status(request: StatusVerificationRequest):
    """Verify a PoST status claim."""
    status_data = request.dict()
    result = ai_elder.verify_status(status_data)
    return result


@router.get("/ai/analytics/summary")
async def get_analytics_summary(time_range: str = "24h"):
    """Get AI analytics summary."""
    summary = ai_elder.get_analytics_summary(time_range)
    return summary

