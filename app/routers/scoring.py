"""DRP Rights Access Scoring API router.

The previous file content was accidentally stored as base64 text and ended
before its endpoint definitions. This repair restores an importable router and
a health endpoint. Household scoring remains unavailable until the model input
schema and trained artifacts are defined and tested; no synthetic score is returned.
"""

import json
import os
from typing import Any

from fastapi import APIRouter

router = APIRouter()
MODEL_DIR = os.getenv("DRP_MODEL_DIR", "drp_model_output")
_models_loaded = False
_load_error: str | None = None
_meta: dict[str, Any] = {"model_version": "1.0.0"}

try:
    import joblib

    _rf = joblib.load(f"{MODEL_DIR}/rf_classifier.joblib")
    _xgb = joblib.load(f"{MODEL_DIR}/xgb_regressor.joblib")
    _scaler = joblib.load(f"{MODEL_DIR}/scaler.joblib")
    with open(f"{MODEL_DIR}/model_metadata.json", encoding="utf-8") as metadata_file:
        _meta = json.load(metadata_file)
    _models_loaded = True
    _load_error = None
except Exception as error:
    _models_loaded = False
    _load_error = str(error)
    _meta = {"model_version": "1.0.0"}


@router.get("/health")
def scoring_health() -> dict[str, Any]:
    """Report whether scoring artifacts are available without exposing paths."""
    return {
        "status": "ready" if _models_loaded else "unavailable",
        "models_loaded": _models_loaded,
        "model_version": _meta.get("model_version", "1.0.0"),
        "scoring_enabled": False,
        "message": (
            "Model artifacts loaded, but scoring is disabled until the feature schema is defined."
            if _models_loaded
            else "Trained model artifacts are not available."
        ),
    }
