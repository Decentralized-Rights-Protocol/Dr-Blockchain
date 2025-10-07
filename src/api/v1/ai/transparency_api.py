"""
AI Transparency API - Public endpoints for querying AI Elder decisions
Provides privacy-preserving access to AI decision logs
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json
import hashlib
from enum import Enum

from ai.transparency.decision_logger import AITransparencyLogger, DecisionType, DecisionOutcome
from ai.transparency.model_governance import ModelCard, ModelGovernanceManager

router = APIRouter(prefix="/api/v1/ai", tags=["AI Transparency"])

class PrivacyLevel(str, Enum):
    """Privacy levels for data exposure"""
    PUBLIC = "public"
    ANONYMIZED = "anonymized"
    PRIVATE = "private"

class TransparencyResponse:
    """Standardized response format for transparency API"""
    
    @staticmethod
    def decision_summary(decision_log: Dict[str, Any], privacy_level: PrivacyLevel = PrivacyLevel.ANONYMIZED) -> Dict[str, Any]:
        """Create privacy-preserving decision summary"""
        
        # Base response
        response = {
            "decision_id": decision_log.get("decision_id"),
            "model_version": decision_log.get("model_version"),
            "decision": decision_log.get("outcome"),
            "confidence": decision_log.get("confidence_score"),
            "explanation": decision_log.get("explanation"),
            "timestamp": decision_log.get("timestamp"),
            "signature": decision_log.get("signature", "")[:16] + "...",  # Truncated for privacy
            "elder_node": decision_log.get("elder_node_id", "")[:8] + "...",  # Truncated
            "decision_type": decision_log.get("decision_type"),
            "processing_time_ms": decision_log.get("processing_time_ms"),
            "review_required": decision_log.get("review_required", False)
        }
        
        # Add explainability data based on privacy level
        if privacy_level in [PrivacyLevel.PUBLIC, PrivacyLevel.ANONYMIZED]:
            explainability = decision_log.get("explainability_vector")
            if explainability:
                response["explainability"] = {
                    "method": explainability.get("method"),
                    "decision_factors": explainability.get("decision_factors", [])[:3],  # Top 3 factors
                    "confidence_breakdown": {
                        "positive_factors": explainability.get("confidence_breakdown", {}).get("positive_factors", 0),
                        "negative_factors": explainability.get("confidence_breakdown", {}).get("negative_factors", 0),
                        "uncertainty": explainability.get("confidence_breakdown", {}).get("uncertainty", 0)
                    }
                }
        
        # Add governance data
        if privacy_level == PrivacyLevel.PUBLIC:
            response["governance"] = {
                "human_override": decision_log.get("human_override"),
                "dispute_id": decision_log.get("dispute_id"),
                "model_audit_score": decision_log.get("model_audit_score")
            }
        
        return response

# Dependency to get transparency logger
def get_transparency_logger() -> AITransparencyLogger:
    """Get configured transparency logger"""
    # In production, this would be injected from app context
    # For now, create a mock instance
    import os
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519
    
    # Load or generate elder private key
    elder_key_path = os.getenv("ELDER_PRIVATE_KEY_PATH", "keys/elder_private.key")
    try:
        with open(elder_key_path, "rb") as f:
            private_key_bytes = f.read()
    except FileNotFoundError:
        # Generate new key for development
        private_key = ed25519.Ed25519PrivateKey.generate()
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        os.makedirs("keys", exist_ok=True)
        with open(elder_key_path, "wb") as f:
            f.write(private_key_bytes)
    
    return AITransparencyLogger(private_key_bytes)

@router.get("/decision/{decision_id}")
async def get_decision(
    decision_id: str,
    privacy_level: PrivacyLevel = Query(PrivacyLevel.ANONYMIZED, description="Privacy level for data exposure"),
    logger: AITransparencyLogger = Depends(get_transparency_logger)
):
    """
    Get a specific AI decision by ID with privacy controls
    """
    try:
        decision = logger.get_decision(decision_id)
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        # Verify signature
        if not logger.verify_decision_signature(decision):
            raise HTTPException(status_code=400, detail="Invalid decision signature")
        
        return TransparencyResponse.decision_summary(decision, privacy_level)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving decision: {str(e)}")

@router.get("/decisions")
async def get_decisions(
    model_id: Optional[str] = Query(None, description="Filter by model ID"),
    decision_type: Optional[DecisionType] = Query(None, description="Filter by decision type"),
    outcome: Optional[DecisionOutcome] = Query(None, description="Filter by outcome"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of decisions to return"),
    offset: int = Query(0, ge=0, description="Number of decisions to skip"),
    privacy_level: PrivacyLevel = Query(PrivacyLevel.ANONYMIZED, description="Privacy level for data exposure"),
    logger: AITransparencyLogger = Depends(get_transparency_logger)
):
    """
    Get AI decisions with filtering and pagination
    """
    try:
        decisions = []
        
        if model_id:
            decisions = logger.get_decisions_by_model(model_id, limit + offset)
        elif decision_type:
            decisions = logger.get_decisions_by_type(decision_type, limit + offset)
        else:
            # Get all decisions (limited by local storage for now)
            decisions = logger.local_logs[-limit-offset:]
        
        # Apply additional filters
        if outcome:
            decisions = [d for d in decisions if d.get("outcome") == outcome.value]
        
        # Apply pagination
        decisions = decisions[offset:offset + limit]
        
        # Convert to response format
        response_decisions = [
            TransparencyResponse.decision_summary(decision, privacy_level)
            for decision in decisions
        ]
        
        return {
            "decisions": response_decisions,
            "total": len(response_decisions),
            "limit": limit,
            "offset": offset,
            "filters": {
                "model_id": model_id,
                "decision_type": decision_type.value if decision_type else None,
                "outcome": outcome.value if outcome else None,
                "privacy_level": privacy_level.value
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving decisions: {str(e)}")

@router.get("/models")
async def get_models(
    governance_manager: ModelGovernanceManager = Depends(lambda: ModelGovernanceManager())
):
    """
    Get information about deployed AI models
    """
    try:
        models = governance_manager.list_models()
        
        # Convert to public format
        public_models = []
        for model in models:
            public_models.append({
                "model_id": model.model_id,
                "version": model.version,
                "description": model.description,
                "intended_use": model.intended_use,
                "last_audit_date": model.last_audit_date,
                "audit_score": model.audit_score,
                "bias_assessment": model.bias_assessment,
                "limitations": model.limitations,
                "dataset_origin": model.dataset_origin,
                "performance_metrics": model.performance_metrics
            })
        
        return {
            "models": public_models,
            "total": len(public_models)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving models: {str(e)}")

@router.get("/models/{model_id}")
async def get_model_details(
    model_id: str,
    governance_manager: ModelGovernanceManager = Depends(lambda: ModelGovernanceManager())
):
    """
    Get detailed information about a specific model
    """
    try:
        model = governance_manager.get_model(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return {
            "model_id": model.model_id,
            "version": model.version,
            "description": model.description,
            "intended_use": model.intended_use,
            "last_audit_date": model.last_audit_date,
            "audit_score": model.audit_score,
            "bias_assessment": model.bias_assessment,
            "limitations": model.limitations,
            "dataset_origin": model.dataset_origin,
            "performance_metrics": model.performance_metrics,
            "model_card_url": f"/ai/models/{model_id}/model-card.json"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving model: {str(e)}")

@router.get("/stats")
async def get_ai_stats(
    time_period: str = Query("24h", description="Time period for statistics (1h, 24h, 7d, 30d)"),
    logger: AITransparencyLogger = Depends(get_transparency_logger)
):
    """
    Get aggregated AI decision statistics
    """
    try:
        # Calculate time threshold
        now = datetime.now(timezone.utc)
        if time_period == "1h":
            threshold = now.replace(hour=now.hour-1)
        elif time_period == "24h":
            threshold = now.replace(day=now.day-1)
        elif time_period == "7d":
            threshold = now.replace(day=now.day-7)
        elif time_period == "30d":
            threshold = now.replace(month=now.month-1)
        else:
            threshold = now.replace(day=now.day-1)  # Default to 24h
        
        # Filter decisions by time
        recent_decisions = [
            d for d in logger.local_logs
            if datetime.fromisoformat(d['timestamp'].replace('Z', '+00:00')) >= threshold
        ]
        
        # Calculate statistics
        total_decisions = len(recent_decisions)
        
        # Decision outcomes
        outcomes = {}
        for decision in recent_decisions:
            outcome = decision.get("outcome", "unknown")
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
        
        # Decision types
        types = {}
        for decision in recent_decisions:
            decision_type = decision.get("decision_type", "unknown")
            types[decision_type] = types.get(decision_type, 0) + 1
        
        # Confidence statistics
        confidences = [d.get("confidence_score", 0) for d in recent_decisions if d.get("confidence_score")]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Processing time statistics
        processing_times = [d.get("processing_time_ms", 0) for d in recent_decisions if d.get("processing_time_ms")]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Review requirements
        review_required = sum(1 for d in recent_decisions if d.get("review_required", False))
        
        return {
            "time_period": time_period,
            "total_decisions": total_decisions,
            "outcomes": outcomes,
            "decision_types": types,
            "average_confidence": round(avg_confidence, 3),
            "average_processing_time_ms": round(avg_processing_time, 2),
            "review_required": review_required,
            "review_rate": round(review_required / total_decisions * 100, 2) if total_decisions > 0 else 0
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating statistics: {str(e)}")

@router.get("/bias-alerts")
async def get_bias_alerts(
    logger: AITransparencyLogger = Depends(get_transparency_logger)
):
    """
    Get bias detection alerts and statistics
    """
    try:
        # Get bias detection decisions
        bias_decisions = logger.get_decisions_by_type(DecisionType.BIAS_DETECTION, 1000)
        
        # Analyze bias patterns
        bias_alerts = []
        for decision in bias_decisions:
            if decision.get("outcome") == DecisionOutcome.FLAGGED.value:
                bias_alerts.append({
                    "decision_id": decision.get("decision_id"),
                    "timestamp": decision.get("timestamp"),
                    "model_id": decision.get("model_id"),
                    "bias_type": decision.get("explanation", "Unknown bias detected"),
                    "confidence": decision.get("confidence_score"),
                    "severity": "high" if decision.get("confidence_score", 0) > 0.8 else "medium"
                })
        
        # Calculate bias statistics
        total_bias_checks = len(bias_decisions)
        bias_detected = len(bias_alerts)
        bias_rate = (bias_detected / total_bias_checks * 100) if total_bias_checks > 0 else 0
        
        return {
            "bias_alerts": bias_alerts,
            "statistics": {
                "total_bias_checks": total_bias_checks,
                "bias_detected": bias_detected,
                "bias_rate_percent": round(bias_rate, 2),
                "high_severity_alerts": len([a for a in bias_alerts if a["severity"] == "high"])
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving bias alerts: {str(e)}")

@router.get("/disputes")
async def get_disputes(
    status: Optional[str] = Query(None, description="Filter by dispute status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of disputes to return"),
    logger: AITransparencyLogger = Depends(get_transparency_logger)
):
    """
    Get AI vs Human dispute statistics and cases
    """
    try:
        # Get decisions with disputes
        disputed_decisions = [
            d for d in logger.local_logs
            if d.get("dispute_id") is not None
        ]
        
        # Filter by status if provided
        if status:
            disputed_decisions = [
                d for d in disputed_decisions
                if d.get("human_override") is not None and (
                    (status == "resolved" and d.get("human_override") is not None) or
                    (status == "pending" and d.get("human_override") is None)
                )
            ]
        
        # Apply limit
        disputed_decisions = disputed_decisions[:limit]
        
        # Calculate dispute statistics
        total_disputes = len(disputed_decisions)
        resolved_disputes = len([d for d in disputed_decisions if d.get("human_override") is not None])
        pending_disputes = total_disputes - resolved_disputes
        
        # AI vs Human agreement rate
        ai_correct = len([d for d in disputed_decisions if d.get("human_override") == False])
        human_correct = len([d for d in disputed_decisions if d.get("human_override") == True])
        
        return {
            "disputes": [
                {
                    "decision_id": d.get("decision_id"),
                    "dispute_id": d.get("dispute_id"),
                    "timestamp": d.get("timestamp"),
                    "ai_decision": d.get("outcome"),
                    "human_override": d.get("human_override"),
                    "status": "resolved" if d.get("human_override") is not None else "pending"
                }
                for d in disputed_decisions
            ],
            "statistics": {
                "total_disputes": total_disputes,
                "resolved_disputes": resolved_disputes,
                "pending_disputes": pending_disputes,
                "ai_correct": ai_correct,
                "human_correct": human_correct,
                "ai_accuracy": round(ai_correct / resolved_disputes * 100, 2) if resolved_disputes > 0 else 0
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving disputes: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for AI transparency API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }
