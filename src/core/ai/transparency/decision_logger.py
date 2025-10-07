"""
AI Transparency & Accountability System - Decision Logger
Implements explainable AI decision logging for DRP Elder nodes
"""

import json
import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# AI/ML libraries for explainability
try:
    import shap
    import lime
    import numpy as np
    EXPLAINABILITY_AVAILABLE = True
except ImportError:
    EXPLAINABILITY_AVAILABLE = False
    print("Warning: SHAP/LIME not available. Install with: pip install shap lime")

# Cryptographic signing
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# IPFS/OrbitDB integration
try:
    import ipfshttpclient
    from orbitdb import OrbitDB
    DECENTRALIZED_STORAGE_AVAILABLE = True
except ImportError:
    DECENTRALIZED_STORAGE_AVAILABLE = False
    print("Warning: IPFS/OrbitDB not available. Install with: pip install ipfshttpclient orbitdb")

class DecisionType(Enum):
    """Types of AI Elder decisions"""
    POST_VERIFICATION = "post_verification"  # Proof of Status
    POAT_VERIFICATION = "poat_verification"  # Proof of Activity
    BIAS_DETECTION = "bias_detection"
    CONTENT_MODERATION = "content_moderation"
    FRAUD_DETECTION = "fraud_detection"

class DecisionOutcome(Enum):
    """Possible decision outcomes"""
    APPROVED = "approved"
    FLAGGED = "flagged"
    DENIED = "denied"
    PENDING_REVIEW = "pending_review"

@dataclass
class ExplainabilityVector:
    """Structured explainability data"""
    method: str  # SHAP, LIME, or custom
    feature_importance: Dict[str, float]
    confidence_breakdown: Dict[str, float]
    decision_factors: List[str]
    uncertainty_metrics: Dict[str, float]

@dataclass
class AIDecisionLog:
    """Structured log entry for AI Elder decisions"""
    # Core identification
    decision_id: str
    model_id: str
    model_version: str
    elder_node_id: str
    
    # Decision metadata
    decision_type: DecisionType
    input_type: str  # image, gps, text, audio
    input_hash: str  # Privacy-preserving hash of input
    
    # Decision results
    outcome: DecisionOutcome
    confidence_score: float
    processing_time_ms: int
    
    # Explainability
    explanation: str
    explainability_vector: Optional[ExplainabilityVector]
    
    # Privacy & Security
    timestamp: str
    signature: str
    privacy_level: str  # public, anonymized, private
    
    # Governance
    review_required: bool
    human_override: Optional[bool]
    dispute_id: Optional[str]

class AITransparencyLogger:
    """
    Main class for logging AI Elder decisions with full transparency
    """
    
    def __init__(self, elder_private_key: bytes, orbitdb_peer_id: Optional[str] = None):
        self.elder_private_key = elder_private_key
        self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(elder_private_key)
        self.public_key = self.private_key.public_key()
        
        # Initialize decentralized storage
        self.orbitdb = None
        self.ipfs_client = None
        if DECENTRALIZED_STORAGE_AVAILABLE:
            try:
                self.ipfs_client = ipfshttpclient.connect()
                if orbitdb_peer_id:
                    self.orbitdb = OrbitDB(orbitdb_peer_id)
            except Exception as e:
                print(f"Warning: Could not connect to IPFS/OrbitDB: {e}")
        
        # Local storage for fallback
        self.local_logs = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def generate_decision_id(self, model_id: str, timestamp: str) -> str:
        """Generate unique decision ID"""
        data = f"{model_id}_{timestamp}_{self.public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def create_explainability_vector(self, model, input_data: Any, prediction: Any) -> Optional[ExplainabilityVector]:
        """Generate explainability vector using SHAP or LIME"""
        if not EXPLAINABILITY_AVAILABLE:
            return None
        
        try:
            # Use SHAP for explainability
            if hasattr(model, 'predict_proba'):
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(input_data)
                
                # Extract feature importance
                if isinstance(shap_values, list):
                    shap_values = shap_values[0]  # For binary classification
                
                feature_importance = {}
                if hasattr(input_data, 'columns'):
                    for i, col in enumerate(input_data.columns):
                        feature_importance[col] = float(shap_values[i])
                else:
                    for i, val in enumerate(shap_values):
                        feature_importance[f"feature_{i}"] = float(val)
                
                # Calculate confidence breakdown
                confidence_breakdown = {
                    "positive_factors": sum(max(0, v) for v in shap_values),
                    "negative_factors": sum(min(0, v) for v in shap_values),
                    "uncertainty": float(np.std(shap_values))
                }
                
                # Generate decision factors
                decision_factors = []
                for feature, importance in sorted(feature_importance.items(), key=lambda x: abs(x[1]), reverse=True)[:5]:
                    if importance > 0:
                        decision_factors.append(f"{feature} contributed positively ({importance:.3f})")
                    else:
                        decision_factors.append(f"{feature} contributed negatively ({importance:.3f})")
                
                return ExplainabilityVector(
                    method="SHAP",
                    feature_importance=feature_importance,
                    confidence_breakdown=confidence_breakdown,
                    decision_factors=decision_factors,
                    uncertainty_metrics={
                        "variance": float(np.var(shap_values)),
                        "entropy": float(-np.sum(shap_values * np.log(np.abs(shap_values) + 1e-10)))
                    }
                )
        
        except Exception as e:
            self.logger.warning(f"Could not generate explainability vector: {e}")
            return None
    
    def anonymize_input(self, input_data: Any, input_type: str) -> str:
        """Create privacy-preserving hash of input data"""
        if input_type == "image":
            # For images, hash the metadata and features, not raw pixels
            if hasattr(input_data, 'shape'):
                data_str = f"{input_data.shape}_{input_data.dtype}_{np.mean(input_data):.6f}"
            else:
                data_str = str(input_data)
        elif input_type == "gps":
            # For GPS, round to ~100m precision for privacy
            if isinstance(input_data, dict) and 'lat' in input_data and 'lon' in input_data:
                lat_rounded = round(input_data['lat'], 2)
                lon_rounded = round(input_data['lon'], 2)
                data_str = f"gps_{lat_rounded}_{lon_rounded}"
            else:
                data_str = str(input_data)
        elif input_type == "text":
            # For text, hash the length and word count, not content
            if isinstance(input_data, str):
                word_count = len(input_data.split())
                char_count = len(input_data)
                data_str = f"text_{char_count}_{word_count}"
            else:
                data_str = str(input_data)
        else:
            data_str = str(input_data)
        
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def sign_decision(self, decision_data: Dict[str, Any]) -> str:
        """Cryptographically sign the decision log"""
        # Create deterministic JSON string for signing
        json_str = json.dumps(decision_data, sort_keys=True, separators=(',', ':'))
        
        # Sign the data
        signature = self.private_key.sign(json_str.encode())
        return signature.hex()
    
    def log_decision(
        self,
        model_id: str,
        model_version: str,
        decision_type: DecisionType,
        input_data: Any,
        input_type: str,
        outcome: DecisionOutcome,
        confidence_score: float,
        explanation: str,
        model: Optional[Any] = None,
        prediction: Optional[Any] = None,
        processing_time_ms: int = 0,
        review_required: bool = False
    ) -> AIDecisionLog:
        """Log an AI Elder decision with full transparency"""
        
        timestamp = datetime.now(timezone.utc).isoformat()
        decision_id = self.generate_decision_id(model_id, timestamp)
        input_hash = self.anonymize_input(input_data, input_type)
        
        # Generate explainability vector if model is provided
        explainability_vector = None
        if model is not None and prediction is not None:
            explainability_vector = self.create_explainability_vector(model, input_data, prediction)
        
        # Create decision log
        decision_log = AIDecisionLog(
            decision_id=decision_id,
            model_id=model_id,
            model_version=model_version,
            elder_node_id=self.public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()[:16],
            decision_type=decision_type,
            input_type=input_type,
            input_hash=input_hash,
            outcome=outcome,
            confidence_score=confidence_score,
            processing_time_ms=processing_time_ms,
            explanation=explanation,
            explainability_vector=explainability_vector,
            timestamp=timestamp,
            signature="",  # Will be set after signing
            privacy_level="anonymized",
            review_required=review_required,
            human_override=None,
            dispute_id=None
        )
        
        # Convert to dict for signing
        decision_dict = asdict(decision_log)
        decision_dict['decision_type'] = decision_type.value
        decision_dict['outcome'] = outcome.value
        if explainability_vector:
            decision_dict['explainability_vector'] = asdict(explainability_vector)
        
        # Sign the decision
        signature = self.sign_decision(decision_dict)
        decision_log.signature = signature
        decision_dict['signature'] = signature
        
        # Store in decentralized storage
        self._store_decision(decision_dict)
        
        # Store locally as backup
        self.local_logs.append(decision_dict)
        
        self.logger.info(f"Logged AI decision {decision_id}: {outcome.value} with confidence {confidence_score}")
        
        return decision_log
    
    def _store_decision(self, decision_dict: Dict[str, Any]) -> None:
        """Store decision in decentralized storage"""
        try:
            if self.orbitdb:
                # Store in OrbitDB
                decision_json = json.dumps(decision_dict)
                self.orbitdb.add(decision_json)
            elif self.ipfs_client:
                # Store in IPFS
                decision_json = json.dumps(decision_dict)
                result = self.ipfs_client.add_str(decision_json)
                self.logger.info(f"Stored decision in IPFS: {result['Hash']}")
        except Exception as e:
            self.logger.warning(f"Could not store in decentralized storage: {e}")
    
    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific decision by ID"""
        # First check local logs
        for log in self.local_logs:
            if log['decision_id'] == decision_id:
                return log
        
        # TODO: Implement retrieval from OrbitDB/IPFS
        return None
    
    def get_decisions_by_model(self, model_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent decisions by model ID"""
        model_decisions = [
            log for log in self.local_logs 
            if log['model_id'] == model_id
        ]
        return sorted(model_decisions, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_decisions_by_type(self, decision_type: DecisionType, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent decisions by type"""
        type_decisions = [
            log for log in self.local_logs 
            if log['decision_type'] == decision_type.value
        ]
        return sorted(type_decisions, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def verify_decision_signature(self, decision_dict: Dict[str, Any]) -> bool:
        """Verify the cryptographic signature of a decision"""
        try:
            # Extract signature
            signature = decision_dict.pop('signature', '')
            if not signature:
                return False
            
            # Recreate the data that was signed
            json_str = json.dumps(decision_dict, sort_keys=True, separators=(',', ':'))
            
            # Verify signature
            signature_bytes = bytes.fromhex(signature)
            self.public_key.verify(signature_bytes, json_str.encode())
            return True
        except Exception as e:
            self.logger.warning(f"Signature verification failed: {e}")
            return False

# Example usage and testing
if __name__ == "__main__":
    # Generate a test private key
    private_key = ed25519.Ed25519PrivateKey.generate()
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Initialize logger
    logger = AITransparencyLogger(private_key_bytes)
    
    # Example decision logging
    decision = logger.log_decision(
        model_id="face_verification_v1",
        model_version="1.2.0",
        decision_type=DecisionType.POST_VERIFICATION,
        input_data={"image_shape": (224, 224, 3), "face_detected": True},
        input_type="image",
        outcome=DecisionOutcome.APPROVED,
        confidence_score=0.94,
        explanation="Face verification passed with high confidence",
        processing_time_ms=150,
        review_required=False
    )
    
    print(f"Logged decision: {decision.decision_id}")
    print(f"Signature: {decision.signature[:16]}...")
