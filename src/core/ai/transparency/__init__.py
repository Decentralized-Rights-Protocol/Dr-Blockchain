"""
AI Transparency & Accountability System
Comprehensive transparency framework for DRP AI Elder decisions
"""

from .decision_logger import (
    AITransparencyLogger,
    AIDecisionLog,
    DecisionType,
    DecisionOutcome,
    ExplainabilityVector
)

from .model_governance import (
    ModelGovernanceManager,
    ModelCard,
    DatasetInfo,
    PerformanceMetrics,
    BiasAssessment,
    AuditStatus,
    BiasLevel
)

from .zkp_explainability import (
    ZKPExplainabilityManager,
    ZKProof,
    ProofType,
    ModelCircuit,
    ZKPResearchRoadmap
)

__version__ = "1.0.0"
__author__ = "DRP AI Team"
__email__ = "ai-team@decentralizedrights.com"

__all__ = [
    # Decision logging
    "AITransparencyLogger",
    "AIDecisionLog", 
    "DecisionType",
    "DecisionOutcome",
    "ExplainabilityVector",
    
    # Model governance
    "ModelGovernanceManager",
    "ModelCard",
    "DatasetInfo",
    "PerformanceMetrics", 
    "BiasAssessment",
    "AuditStatus",
    "BiasLevel",
    
    # ZKP explainability
    "ZKPExplainabilityManager",
    "ZKProof",
    "ProofType",
    "ModelCircuit",
    "ZKPResearchRoadmap"
]
