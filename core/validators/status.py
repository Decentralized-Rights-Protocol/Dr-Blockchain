"""Status validation utilities."""

from typing import Optional
from ..models.status import StatusScore


def validate_status_score(score: StatusScore) -> tuple[bool, Optional[str]]:
    """
    Validate status score.
    
    Args:
        score: Status score object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if score.overall_score < 0 or score.overall_score > 100:
        return False, "overall_score must be between 0 and 100"
    
    if score.activity_score < 0 or score.activity_score > 100:
        return False, "activity_score must be between 0 and 100"
    
    if score.consistency_score < 0 or score.consistency_score > 100:
        return False, "consistency_score must be between 0 and 100"
    
    if score.reputation_score < 0 or score.reputation_score > 100:
        return False, "reputation_score must be between 0 and 100"
    
    if score.verification_rate < 0 or score.verification_rate > 1.0:
        return False, "verification_rate must be between 0 and 1.0"
    
    return True, None


def validate_status_update(user_id: str) -> tuple[bool, Optional[str]]:
    """
    Validate status update request.
    
    Args:
        user_id: User identifier
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not user_id or len(user_id) < 1:
        return False, "user_id is required"
    
    return True, None

