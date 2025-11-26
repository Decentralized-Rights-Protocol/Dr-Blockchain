"""User API routes."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from core.schemas.status import StatusProfileRequest, StatusProfileResponse
from core.models.user import User, UserProfile, Wallet
from core.validators.user import validate_user_id
from api.auth import get_current_user

router = APIRouter()
security = HTTPBearer()

# In-memory user store (in production, use database)
users_db = {}


@router.post("/user/create")
async def create_user(user_id: str, wallet_address: Optional[str] = None):
    """
    Create a new user profile.
    """
    if not validate_user_id(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    if user_id in users_db:
        raise HTTPException(status_code=409, detail="User already exists")
    
    # Generate wallet if not provided
    if not wallet_address:
        from core.utils.crypto import generate_wallet
        address, public_key, private_key = generate_wallet()
        wallet_address = address
    
    # Create user profile
    wallet = Wallet(
        address=wallet_address,
        public_key="",  # Would be set from wallet
        encrypted_private_key=None
    )
    
    profile = UserProfile(
        user_id=user_id,
        wallet=wallet,
        metadata={}
    )
    
    user = User(
        user_id=user_id,
        profile=profile,
        is_active=True,
        is_verified=False
    )
    
    users_db[user_id] = user.dict()
    
    return {
        "user_id": user_id,
        "wallet_address": wallet_address,
        "message": "User created successfully"
    }


@router.get("/user/{user_id}/status", response_model=StatusProfileResponse)
async def get_user_status(user_id: str):
    """
    Get user status profile.
    """
    if not validate_user_id(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    # In production, fetch from OrbitDB status store
    # For now, return mock data
    from core.models.status import StatusScore
    
    status_score = StatusScore(
        overall_score=75.0,
        activity_score=80.0,
        consistency_score=70.0,
        reputation_score=75.0,
        verification_rate=0.85
    )
    
    return StatusProfileResponse(
        user_id=user_id,
        status_score=status_score,
        total_activities=50,
        verified_activities=42,
        rejected_activities=8,
        achievements=["early_adopter", "verified_user"],
        orbitdb_cid=None
    )


@router.get("/user/{user_id}/profile")
async def get_user_profile(user_id: str):
    """
    Get user profile.
    """
    if not validate_user_id(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = users_db[user_id]
    return {
        "user_id": user_data["user_id"],
        "profile": user_data["profile"],
        "is_active": user_data.get("is_active", True),
        "is_verified": user_data.get("is_verified", False)
    }


@router.get("/user/{user_id}/achievements")
async def get_user_achievements(user_id: str):
    """
    Get user achievements.
    """
    if not validate_user_id(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    # In production, fetch from database
    return {
        "user_id": user_id,
        "achievements": [
            {
                "id": "early_adopter",
                "name": "Early Adopter",
                "description": "Joined DRP in early stages",
                "earned_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "verified_user",
                "name": "Verified User",
                "description": "Completed identity verification",
                "earned_at": "2024-01-15T00:00:00Z"
            }
        ]
    }

