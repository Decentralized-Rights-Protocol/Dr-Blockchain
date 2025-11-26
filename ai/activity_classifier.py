"""Activity classification and fraud detection."""

from typing import Dict, Any, List, Tuple
import re
from datetime import datetime
from core.models.activity import ActivityType


class ActivityClassifier:
    """Classifies activities and detects fraudulent submissions."""
    
    # Keywords for activity type classification
    TYPE_KEYWORDS = {
        ActivityType.EDUCATION: [
            "school", "education", "learn", "study", "course", "class", "student",
            "teacher", "university", "college", "degree", "certificate", "training"
        ],
        ActivityType.HEALTH: [
            "health", "medical", "hospital", "clinic", "doctor", "nurse", "treatment",
            "care", "wellness", "therapy", "medicine", "patient"
        ],
        ActivityType.ENGINEERING: [
            "engineer", "build", "construct", "design", "develop", "code", "software",
            "hardware", "project", "technical", "programming", "architecture"
        ],
        ActivityType.AGRICULTURE: [
            "farm", "agriculture", "crop", "harvest", "plant", "soil", "irrigation",
            "livestock", "sustainable", "organic", "farming"
        ],
        ActivityType.ENERGY: [
            "energy", "solar", "wind", "renewable", "power", "electricity", "grid",
            "sustainable", "clean energy", "battery", "generation"
        ],
        ActivityType.RESEARCH: [
            "research", "study", "experiment", "analysis", "investigation", "paper",
            "publication", "scientific", "data", "findings"
        ],
        ActivityType.COMMUNITY: [
            "community", "volunteer", "help", "support", "charity", "donation",
            "outreach", "service", "aid", "assistance"
        ],
        ActivityType.GOVERNANCE: [
            "governance", "vote", "decision", "policy", "regulation", "committee",
            "council", "proposal", "governance"
        ]
    }
    
    # Fraud detection patterns
    FRAUD_INDICATORS = [
        r"click here",
        r"free money",
        r"guaranteed",
        r"no risk",
        r"act now",
        r"limited time",
        r"spam",
        r"scam",
        r"fake",
        r"test test test",
        r"asdf",
        r"12345"
    ]
    
    def classify_activity(self, title: str, description: str) -> Tuple[ActivityType, float]:
        """
        Classify activity type based on content.
        
        Args:
            title: Activity title
            description: Activity description
            
        Returns:
            Tuple of (activity_type, confidence_score)
        """
        text = f"{title} {description}".lower()
        
        scores = {}
        for activity_type, keywords in self.TYPE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            scores[activity_type] = score / len(keywords) if keywords else 0
        
        # Get best match
        best_type = max(scores.items(), key=lambda x: x[1])
        
        if best_type[1] > 0.1:
            return best_type[0], best_type[1]
        else:
            return ActivityType.OTHER, 0.1
    
    def detect_fraud(self, title: str, description: str, metadata: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
        """
        Detect fraudulent activity submissions.
        
        Args:
            title: Activity title
            description: Activity description
            metadata: Activity metadata
            
        Returns:
            Tuple of (is_fraud, fraud_score, reasons)
        """
        fraud_score = 0.0
        reasons = []
        
        text = f"{title} {description}".lower()
        
        # Check for fraud indicators
        for pattern in self.FRAUD_INDICATORS:
            if re.search(pattern, text, re.IGNORECASE):
                fraud_score += 0.2
                reasons.append(f"Contains suspicious pattern: {pattern}")
        
        # Check for very short descriptions
        if len(description) < 10:
            fraud_score += 0.3
            reasons.append("Description too short")
        
        # Check for repetitive text
        words = description.split()
        if len(words) > 0:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:
                fraud_score += 0.2
                reasons.append("Repetitive content detected")
        
        # Check for suspicious metadata
        if metadata:
            # Check for unrealistic timestamps
            if "timestamp" in metadata:
                try:
                    ts = datetime.fromisoformat(str(metadata["timestamp"]))
                    now = datetime.utcnow()
                    if ts > now:
                        fraud_score += 0.3
                        reasons.append("Future timestamp detected")
                except:
                    pass
        
        is_fraud = fraud_score > 0.5
        
        return is_fraud, min(fraud_score, 1.0), reasons
    
    def verify_activity(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify an activity (classify + fraud detection).
        
        Args:
            activity: Activity data
            
        Returns:
            Verification result
        """
        title = activity.get("title", "")
        description = activity.get("description", "")
        metadata = activity.get("metadata", {})
        
        # Classify
        activity_type, type_confidence = self.classify_activity(title, description)
        
        # Detect fraud
        is_fraud, fraud_score, reasons = self.detect_fraud(title, description, metadata)
        
        # Calculate verification score
        verification_score = type_confidence * (1.0 - fraud_score)
        
        return {
            "verified": not is_fraud and verification_score > 0.5,
            "verification_score": verification_score,
            "activity_type": activity_type.value,
            "type_confidence": type_confidence,
            "fraud_detected": is_fraud,
            "fraud_score": fraud_score,
            "fraud_reasons": reasons
        }

