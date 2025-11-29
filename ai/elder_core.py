"""
AI ElderCore - Lightweight AI verification system for DRP.
Uses local models and heuristics (no expensive cloud AI).
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
import hashlib

from agents.activity_verification_agent import ActivityVerificationAgent
from agents.fraud_detection_agent import FraudDetectionAgent
from agents.status_evaluator import StatusEvaluator

logger = logging.getLogger(__name__)


class AIElderCore:
    """
    Central AI verification system for DRP.
    Coordinates all AI agents for PoAT and PoST verification.
    """
    
    def __init__(self):
        self.activity_verifier = ActivityVerificationAgent()
        self.fraud_detector = FraudDetectionAgent()
        self.status_evaluator = StatusEvaluator()
        
        # Store verification results
        self.verification_cache: Dict[str, Dict[str, Any]] = {}
    
    def verify_activity(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a PoAT submission.
        
        Args:
            activity: {
                'activity_id': str,
                'user_id': str,
                'activity_type': str,
                'title': str,
                'description': str,
                'metadata': dict
            }
        
        Returns:
            {
                'verified': bool,
                'verification_score': float,
                'fraud_score': float,
                'fraud_flags': list,
                'quantum_hash': str,
                'timestamp': str
            }
        """
        activity_id = activity.get('activity_id', '')
        
        # Check cache
        if activity_id in self.verification_cache:
            return self.verification_cache[activity_id]
        
        # Run verification
        verification = self.activity_verifier.verify(activity)
        fraud_check = self.fraud_detector.score_activity(activity)
        
        # Generate quantum hash
        proof_data = f"{activity_id}:{activity.get('user_id')}:{verification['score']}:{fraud_check['score']}"
        quantum_hash = self._generate_quantum_hash(proof_data)
        
        result = {
            'verified': verification['verified'] and not fraud_check['suspicious'],
            'verification_score': verification['score'],
            'fraud_score': fraud_check['score'],
            'fraud_flags': fraud_check['flags'],
            'quantum_hash': quantum_hash,
            'timestamp': datetime.utcnow().isoformat(),
            'activity_id': activity_id
        }
        
        # Cache result
        self.verification_cache[activity_id] = result
        
        logger.info(f"Activity {activity_id} verified: {result['verified']}, score: {result['verification_score']}")
        
        return result
    
    def verify_status(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a PoST claim.
        
        Args:
            status_data: {
                'user_id': str,
                'activities': list,
                'current_score': float,
                'profile': dict
            }
        
        Returns:
            {
                'verified': bool,
                'calculated_score': float,
                'status_score': dict,
                'quantum_hash': str
            }
        """
        user_id = status_data.get('user_id', '')
        
        # Evaluate status
        activities = status_data.get('activities', [])
        profile = status_data.get('profile', {})
        
        status_score = self.status_evaluator.calculate_status_score(activities, profile)
        
        # Compare with claimed score
        claimed_score = status_data.get('current_score', 0.0)
        score_diff = abs(status_score.overall_score - claimed_score)
        verified = score_diff < 10.0  # Allow 10 point variance
        
        # Generate quantum hash
        proof_data = f"{user_id}:{status_score.overall_score}:{claimed_score}"
        quantum_hash = self._generate_quantum_hash(proof_data)
        
        result = {
            'verified': verified,
            'calculated_score': status_score.overall_score,
            'claimed_score': claimed_score,
            'status_score': status_score.dict(),
            'quantum_hash': quantum_hash,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Status verified for user {user_id}: {result['verified']}, calculated: {result['calculated_score']}")
        
        return result
    
    def get_analytics_summary(self, time_range: str = "24h") -> Dict[str, Any]:
        """
        Get analytics summary.
        
        Args:
            time_range: "24h", "7d", "30d"
        
        Returns:
            Analytics summary
        """
        # Count verifications
        total_verified = sum(1 for v in self.verification_cache.values() if v.get('verified'))
        total_rejected = len(self.verification_cache) - total_verified
        
        avg_score = sum(v.get('verification_score', 0) for v in self.verification_cache.values()) / max(1, len(self.verification_cache))
        
        return {
            'time_range': time_range,
            'total_verifications': len(self.verification_cache),
            'verified_count': total_verified,
            'rejected_count': total_rejected,
            'verification_rate': total_verified / max(1, len(self.verification_cache)),
            'average_score': avg_score,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _generate_quantum_hash(self, data: str) -> str:
        """Generate quantum-secure hash."""
        from core.utils.quantum import generate_quantum_hash
        return generate_quantum_hash(data)

