"""FastAPI server for AI verification services."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from config import get_settings
from ai.activity_classifier import ActivityClassifier
from ai.status_evaluator import StatusEvaluator
from ai.quantum_security import QuantumSecurity

app = FastAPI(
    title="DRP AI Verification Service",
    description="AI-powered activity verification and status evaluation",
    version="1.0.0"
)

# Initialize AI components
classifier = ActivityClassifier()
evaluator = StatusEvaluator()
quantum = QuantumSecurity()

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ActivityVerificationRequest(BaseModel):
    """Request to verify an activity."""
    activity_id: str
    user_id: str
    title: str
    description: str
    activity_type: Optional[str] = None
    metadata: Dict[str, Any] = {}


class ActivityVerificationResponse(BaseModel):
    """Response from activity verification."""
    verified: bool
    verification_score: float
    activity_type: str
    type_confidence: float
    fraud_detected: bool
    fraud_score: float
    fraud_reasons: List[str]
    quantum_hash: Optional[str] = None


class StatusScoreRequest(BaseModel):
    """Request to score user status."""
    user_id: str
    activities: List[Dict[str, Any]]
    profile: Dict[str, Any] = {}


class StatusScoreResponse(BaseModel):
    """Response from status scoring."""
    user_id: str
    status_score: Dict[str, Any]
    total_activities: int
    verified_activities: int
    rejected_activities: int


class QuantumProofRequest(BaseModel):
    """Request to generate quantum proof."""
    data: str
    salt: Optional[str] = None


class QuantumProofResponse(BaseModel):
    """Response with quantum proof."""
    quantum_hash: str
    salt: str
    algorithm: str


@app.post("/ai/verify-activity", response_model=ActivityVerificationResponse)
async def verify_activity(request: ActivityVerificationRequest):
    """
    Verify an activity submission.
    
    - Classifies activity type
    - Detects fraudulent submissions
    - Returns verification score
    """
    try:
        activity_data = {
            "title": request.title,
            "description": request.description,
            "metadata": request.metadata
        }
        
        # Verify activity
        verification_result = classifier.verify_activity(activity_data)
        
        # Generate quantum hash if verified
        quantum_hash = None
        if verification_result["verified"]:
            proof_data = f"{request.activity_id}:{request.user_id}:{verification_result['verification_score']}"
            proof = quantum.generate_proof_hash(proof_data)
            quantum_hash = proof["quantum_hash"]
        
        return ActivityVerificationResponse(
            verified=verification_result["verified"],
            verification_score=verification_result["verification_score"],
            activity_type=verification_result["activity_type"],
            type_confidence=verification_result["type_confidence"],
            fraud_detected=verification_result["fraud_detected"],
            fraud_score=verification_result["fraud_score"],
            fraud_reasons=verification_result["fraud_reasons"],
            quantum_hash=quantum_hash
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@app.post("/ai/score-status", response_model=StatusScoreResponse)
async def score_status(request: StatusScoreRequest):
    """
    Calculate status score for a user.
    
    - Evaluates activity history
    - Calculates reputation metrics
    - Returns comprehensive status score
    """
    try:
        result = evaluator.evaluate_status_update(
            request.user_id,
            request.activities,
            request.profile
        )
        
        return StatusScoreResponse(
            user_id=result["user_id"],
            status_score=result["status_score"],
            total_activities=result["total_activities"],
            verified_activities=result["verified_activities"],
            rejected_activities=result["rejected_activities"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status scoring failed: {str(e)}")


@app.post("/ai/quantum-proof", response_model=QuantumProofResponse)
async def generate_quantum_proof(request: QuantumProofRequest):
    """
    Generate a quantum-secure hash proof.
    
    - Uses SHA3-512 + BLAKE2b + Lattice padding
    - Post-quantum resistant
    """
    try:
        proof = quantum.generate_proof_hash(request.data, request.salt)
        
        return QuantumProofResponse(
            quantum_hash=proof["quantum_hash"],
            salt=proof["salt"],
            algorithm=proof["algorithm"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quantum proof generation failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "DRP AI Verification",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(app, host=settings.fastapi_host, port=settings.fastapi_port)

