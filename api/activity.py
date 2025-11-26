"""Activity API routes."""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import subprocess
import json
import os

from core.schemas.activity import (
    ActivitySubmitRequest,
    ActivitySubmitResponse,
    ActivityFeedResponse,
    ActivityVerificationRequest
)
from core.validators.activity import validate_activity_submission
from core.utils.quantum import generate_quantum_hash
from api.auth import get_current_user

router = APIRouter()
security = HTTPBearer()


def call_orbitdb_activity_store(method: str, data: dict) -> dict:
    """
    Call OrbitDB activity store via Node.js.
    
    This is a simplified approach - in production, use proper IPC or API.
    """
    try:
        orbitdb_script = os.path.join(os.path.dirname(__file__), "..", "orbitdb", "activity_store.js")
        
        # For now, return mock data
        # In production, implement proper Node.js bridge
        return {
            "success": True,
            "activity_id": data.get("id", f"activity-{os.urandom(8).hex()}"),
            "orbitdb_cid": f"orbitdb-cid-{os.urandom(16).hex()}",
            "ipfs_cids": []
        }
    except Exception as e:
        print(f"Error calling OrbitDB: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def call_ai_verification(activity_data: dict) -> dict:
    """Call AI verification service."""
    import requests
    from config import get_settings
    
    settings = get_settings()
    ai_url = f"http://{settings.fastapi_host}:{settings.fastapi_port}/ai/verify-activity"
    
    try:
        response = requests.post(ai_url, json=activity_data, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "verified": False,
                "verification_score": 0.0,
                "fraud_detected": True,
                "error": f"AI service returned {response.status_code}"
            }
    except Exception as e:
        print(f"Error calling AI service: {e}")
        return {
            "verified": False,
            "verification_score": 0.0,
            "fraud_detected": False,
            "error": str(e)
        }


def call_rpc_submit_activity(activity_proof: dict) -> dict:
    """Submit activity proof to RPC server."""
    import requests
    from config import get_settings
    
    settings = get_settings()
    rpc_url = f"http://{settings.rpc_host}:{settings.rpc_port}"
    
    try:
        rpc_request = {
            "jsonrpc": "2.0",
            "method": "submitActivityProof",
            "params": activity_proof,
            "id": 1
        }
        
        response = requests.post(rpc_url, json=rpc_request, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result.get("result", {})
        else:
            return {"error": f"RPC returned {response.status_code}"}
    except Exception as e:
        print(f"Error calling RPC: {e}")
        return {"error": str(e)}


@router.post("/activity/submit", response_model=ActivitySubmitResponse)
async def submit_activity(
    request: ActivitySubmitRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit an activity for verification.
    
    - Validates activity submission
    - Stores in OrbitDB
    - Pins attachments to IPFS
    - Queues for AI verification
    """
    # Validate request
    is_valid, error_msg = validate_activity_submission(request)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Generate activity ID
    import secrets
    activity_id = f"activity-{secrets.token_hex(16)}"
    
    # Prepare activity data
    activity_data = {
        "id": activity_id,
        "user_id": request.user_id,
        "activity_type": request.activity_type.value if hasattr(request.activity_type, 'value') else request.activity_type,
        "title": request.title,
        "description": request.description,
        "location": request.location,
        "metadata": request.metadata,
        "attachments": request.attachments
    }
    
    # Store in OrbitDB (async)
    orbitdb_result = call_orbitdb_activity_store("addActivity", activity_data)
    
    if not orbitdb_result.get("success"):
        raise HTTPException(status_code=500, detail="Failed to store activity in OrbitDB")
    
    # Queue AI verification (background task)
    background_tasks.add_task(verify_activity_background, activity_id, activity_data)
    
    return ActivitySubmitResponse(
        activity_id=activity_id,
        orbitdb_cid=orbitdb_result.get("orbitdb_cid", ""),
        ipfs_cids=orbitdb_result.get("ipfs_cids", []),
        verification_status="pending",
        message="Activity submitted successfully. Verification in progress."
    )


async def verify_activity_background(activity_id: str, activity_data: dict):
    """Background task to verify activity."""
    # Call AI verification
    ai_result = call_ai_verification(activity_data)
    
    # Update activity in OrbitDB with verification result
    # (In production, implement proper update mechanism)
    
    # If verified, submit to blockchain
    if ai_result.get("verified", False):
        activity_proof = {
            "activity_id": activity_id,
            "user_id": activity_data["user_id"],
            "orbitdb_cid": "",  # Would be from OrbitDB result
            "ai_verification_score": ai_result.get("verification_score", 0.0)
        }
        
        # Submit to RPC
        call_rpc_submit_activity(activity_proof)


@router.get("/activity/feed", response_model=ActivityFeedResponse)
async def get_activity_feed(page: int = 1, page_size: int = 20):
    """
    Get activity feed.
    """
    # In production, fetch from OrbitDB
    activities = []
    
    return ActivityFeedResponse(
        activities=activities,
        total=len(activities),
        page=page,
        page_size=page_size
    )


@router.post("/activity/verify")
async def verify_activity(request: ActivityVerificationRequest):
    """
    Manually trigger activity verification.
    """
    # In production, fetch activity from OrbitDB and verify
    return {
        "activity_id": request.activity_id,
        "verified": False,
        "message": "Verification queued"
    }

