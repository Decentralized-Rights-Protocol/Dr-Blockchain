"""
AI Verification Layer for DRP Blockchain

This package implements AI-powered verification modules for the Decentralized Rights Protocol (DRP):
- Face verification for Proof of Status (PoST)
- Activity detection for Proof of Activity (PoAT)
- Voice command processing for blockchain interactions
- Text analysis for authenticity verification
- Blockchain integration for AI verification results

All modules are designed to:
- Run on mobile/low-resource devices
- Anonymize sensitive data before blockchain submission
- Generate cryptographic hashes for blockchain logging
- Provide comprehensive error handling and logging
"""

from .cv_face_verification import FaceVerificationEngine
from .cv_activity_detection import ActivityDetectionEngine
from .nlp_voice_command import VoiceCommandEngine
from .nlp_text_analysis import TextAnalysisEngine
from .integration import AIVerificationIntegrator, DRPBlockchainClient, BlockchainTransaction

__version__ = "1.0.0"
__author__ = "DRP Development Team"

__all__ = [
    "FaceVerificationEngine",
    "ActivityDetectionEngine", 
    "VoiceCommandEngine",
    "TextAnalysisEngine",
    "AIVerificationIntegrator",
    "DRPBlockchainClient",
    "BlockchainTransaction"
]
