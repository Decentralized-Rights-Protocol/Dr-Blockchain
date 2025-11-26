"""Activity validation utilities."""

from typing import Dict, Any, Optional, Tuple
from ..models.activity import ActivityType
from ..schemas.activity import ActivitySubmitRequest


def validate_activity_type(activity_type: str) -> bool:
    """
    Validate activity type.
    
    Args:
        activity_type: Activity type string
        
    Returns:
        True if valid
    """
    try:
        ActivityType(activity_type)
        return True
    except ValueError:
        return False


def validate_activity_submission(request: ActivitySubmitRequest) -> tuple[bool, Optional[str]]:
    """
    Validate activity submission request.
    
    Args:
        request: Activity submission request
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not request.user_id or len(request.user_id) < 1:
        return False, "user_id is required"
    
    if not validate_activity_type(request.activity_type):
        return False, f"Invalid activity_type: {request.activity_type}"
    
    if not request.title or len(request.title) < 1:
        return False, "title is required"
    
    if not request.description or len(request.description) < 1:
        return False, "description is required"
    
    if len(request.title) > 200:
        return False, "title exceeds maximum length of 200 characters"
    
    if len(request.description) > 5000:
        return False, "description exceeds maximum length of 5000 characters"
    
    return True, None

