"""
DRP Scoring API --- FastAPI Router
=====================================
Ghana AI Innovation Challenge 2026
Decentralized Rights Protocol

Usage --- add to app/main.py:
    from app.routers.scoring import router as scoring_router
    app.include_router(scoring_router, prefix="/api/v1/score", tags=["Scoring"])

Endpoints:
    POST /api/v1/score/household      Score a single household
    GET  /api/v1/score/verify/{hash}  Verify a score attestation
    GET  3 /api/v1/score/health        Model health check
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Optional
import joblib, numpy as np, hashlib, json, os
from datetime import datetime, timezone

router = APIRouter()

MODEL_DIR = os.getenv("DRP_MODEL_DIR", "drp_model_output")

try:
    _rf     = joblib.load(f"{MODEL_DIR}/rf_classifier.joblib")
    _xgb    = joblib.load(f"{MODEL_DIR}/xgb_regressor.joblib")
    _scaler = joblib.load(f"{MODEL_DIR}/scaler.joblib")
    with open(f"{MODEL_DIR}/model_metadata.json") as f:
        _meta = json.load(f)
    _models_loaded = True
    _load_error = None
except Exception as e:
    _models_loaded = False
    _load_error = str(e)
    _meta = {"model_version": "1.0.0"}

TIER_LABELS   = ["Critical", "Moderate", "Adequate", "Secure"]
LOCALITYMAP  = {"Urban": 2, "Peri-urban": 1, "Rural": 0}


class HouseholdScoreRequest(BaseModel):
    household_size: int = Field(ge=1, le=100)
    income: float = Field(ge=0)
    locality: Literal["Urban","Peri-urban","Rural"] = "Rural"

@app_placeholder = None

@router.get("/health")
def model_health():
    return {"status": "ok" if _models_loaded else "degraded", "model_version": _meta.get("model_version"), "loaded": _models_loaded, "error": _load_error}
