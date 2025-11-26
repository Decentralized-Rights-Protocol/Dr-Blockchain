"""Status score evaluation for Proof of Status (PoST)."""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from core.models.status import StatusScore


class StatusEvaluator:
    """Evaluates user status scores based on activity history."""
    
    def calculate_status_score(self, activities: List[Dict[str, Any]], 
                              profile: Dict[str, Any]) -> StatusScore:
        """
        Calculate status score based on activities and profile.
        
        Args:
            activities: List of user activities
            profile: User profile data
            
        Returns:
            StatusScore object
        """
        if not activities:
            return StatusScore(
                overall_score=0.0,
                activity_score=0.0,
                consistency_score=0.0,
                reputation_score=0.0,
                verification_rate=0.0
            )
        
        # Filter verified activities
        verified_activities = [a for a in activities if a.get("verified", False)]
        total_activities = len(activities)
        verified_count = len(verified_activities)
        
        # Verification rate
        verification_rate = verified_count / total_activities if total_activities > 0 else 0.0
        
        # Activity score (based on number of verified activities)
        # Scale: 10 activities = 50 points, 50 activities = 100 points
        activity_score = min(100.0, (verified_count / 50.0) * 100.0)
        
        # Consistency score (based on verification rate and time distribution)
        consistency_score = verification_rate * 100.0
        
        # Check activity distribution over time
        if verified_activities:
            timestamps = [datetime.fromisoformat(a.get("timestamp", "")) 
                         for a in verified_activities if a.get("timestamp")]
            if timestamps:
                timestamps.sort()
                # Check if activities are spread over time
                time_span = (timestamps[-1] - timestamps[0]).days if len(timestamps) > 1 else 1
                if time_span > 0:
                    activity_density = len(timestamps) / time_span
                    # Reward consistent activity over time
                    if activity_density > 0.1:  # At least 1 activity per 10 days
                        consistency_score = min(100.0, consistency_score * 1.1)
        
        # Reputation score (combination of factors)
        achievements = profile.get("achievements", [])
        achievement_bonus = len(achievements) * 5.0
        
        reputation_score = (
            activity_score * 0.4 +
            consistency_score * 0.4 +
            achievement_bonus * 0.2
        )
        
        # Overall score (capped at 100)
        overall_score = min(100.0, reputation_score)
        
        return StatusScore(
            overall_score=round(overall_score, 2),
            activity_score=round(activity_score, 2),
            consistency_score=round(consistency_score, 2),
            reputation_score=round(reputation_score, 2),
            verification_rate=round(verification_rate, 3),
            last_updated=datetime.utcnow()
        )
    
    def evaluate_status_update(self, user_id: str, activities: List[Dict[str, Any]],
                              current_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate and update status score.
        
        Args:
            user_id: User identifier
            activities: List of user activities
            current_profile: Current user profile
            
        Returns:
            Updated status information
        """
        status_score = self.calculate_status_score(activities, current_profile)
        
        return {
            "user_id": user_id,
            "status_score": status_score.dict(),
            "total_activities": len(activities),
            "verified_activities": len([a for a in activities if a.get("verified", False)]),
            "rejected_activities": len([a for a in activities if not a.get("verified", False)]),
            "last_updated": datetime.utcnow().isoformat()
        }

