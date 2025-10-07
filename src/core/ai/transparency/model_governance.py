"""
AI Model Governance & Metadata System
Manages model cards, audit scores, and governance metadata for AI Elders
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import os
import logging

class AuditStatus(Enum):
    """Model audit status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    REQUIRES_UPDATE = "requires_update"

class BiasLevel(Enum):
    """Bias severity levels"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class DatasetInfo:
    """Information about training dataset"""
    name: str
    source: str
    size: int
    diversity_score: float
    bias_indicators: List[str]
    privacy_compliance: str
    last_updated: str

@dataclass
class PerformanceMetrics:
    """Model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    false_negative_rate: float
    processing_time_ms: float
    memory_usage_mb: float

@dataclass
class BiasAssessment:
    """Bias assessment results"""
    overall_bias_level: BiasLevel
    demographic_parity: float
    equalized_odds: float
    calibration: float
    bias_indicators: List[str]
    mitigation_measures: List[str]
    last_assessment: str

@dataclass
class ModelCard:
    """Complete model card with governance metadata"""
    # Basic information
    model_id: str
    version: str
    name: str
    description: str
    created_date: str
    last_updated: str
    
    # Intended use and limitations
    intended_use: str
    limitations: List[str]
    use_cases: List[str]
    prohibited_uses: List[str]
    
    # Technical details
    model_type: str
    architecture: str
    input_format: str
    output_format: str
    model_size_mb: float
    
    # Dataset information
    dataset: DatasetInfo
    
    # Performance metrics
    performance_metrics: PerformanceMetrics
    
    # Bias and fairness
    bias_assessment: BiasAssessment
    
    # Governance and compliance
    audit_score: float
    audit_status: AuditStatus
    last_audit_date: str
    next_audit_date: str
    compliance_frameworks: List[str]
    
    # Security and privacy
    privacy_impact_assessment: str
    security_audit_status: str
    encryption_at_rest: bool
    encryption_in_transit: bool
    
    # Deployment information
    deployment_environment: str
    scaling_requirements: Dict[str, Any]
    monitoring_requirements: List[str]
    
    # Contact and maintenance
    maintainer: str
    contact_email: str
    documentation_url: str
    model_card_url: str

class ModelGovernanceManager:
    """Manages AI model governance and metadata"""
    
    def __init__(self, models_dir: str = "ai/models"):
        self.models_dir = models_dir
        self.models: Dict[str, ModelCard] = {}
        self.logger = logging.getLogger(__name__)
        
        # Ensure models directory exists
        os.makedirs(models_dir, exist_ok=True)
        
        # Load existing models
        self._load_models()
    
    def _load_models(self) -> None:
        """Load existing model cards from disk"""
        try:
            for filename in os.listdir(self.models_dir):
                if filename.endswith('.json'):
                    model_id = filename[:-5]  # Remove .json extension
                    model_path = os.path.join(self.models_dir, filename)
                    
                    with open(model_path, 'r') as f:
                        model_data = json.load(f)
                    
                    # Convert to ModelCard object
                    model_card = self._dict_to_model_card(model_data)
                    self.models[model_id] = model_card
                    
        except Exception as e:
            self.logger.warning(f"Error loading models: {e}")
    
    def _dict_to_model_card(self, data: Dict[str, Any]) -> ModelCard:
        """Convert dictionary to ModelCard object"""
        # Convert nested objects
        dataset = DatasetInfo(**data['dataset']) if 'dataset' in data else None
        performance = PerformanceMetrics(**data['performance_metrics']) if 'performance_metrics' in data else None
        bias = BiasAssessment(**data['bias_assessment']) if 'bias_assessment' in data else None
        
        # Convert enums
        if 'audit_status' in data:
            data['audit_status'] = AuditStatus(data['audit_status'])
        if 'bias_assessment' in data and 'overall_bias_level' in data['bias_assessment']:
            data['bias_assessment']['overall_bias_level'] = BiasLevel(data['bias_assessment']['overall_bias_level'])
        
        return ModelCard(
            dataset=dataset,
            performance_metrics=performance,
            bias_assessment=bias,
            **{k: v for k, v in data.items() if k not in ['dataset', 'performance_metrics', 'bias_assessment']}
        )
    
    def register_model(self, model_card: ModelCard) -> bool:
        """Register a new model with governance metadata"""
        try:
            # Validate model card
            if not self._validate_model_card(model_card):
                return False
            
            # Store model
            self.models[model_card.model_id] = model_card
            
            # Save to disk
            self._save_model_card(model_card)
            
            self.logger.info(f"Registered model: {model_card.model_id} v{model_card.version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering model: {e}")
            return False
    
    def _validate_model_card(self, model_card: ModelCard) -> bool:
        """Validate model card completeness and correctness"""
        required_fields = [
            'model_id', 'version', 'name', 'description',
            'intended_use', 'model_type', 'performance_metrics',
            'bias_assessment', 'audit_score'
        ]
        
        for field in required_fields:
            if not hasattr(model_card, field) or getattr(model_card, field) is None:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        # Validate audit score range
        if not 0 <= model_card.audit_score <= 1:
            self.logger.error("Audit score must be between 0 and 1")
            return False
        
        # Validate performance metrics
        if model_card.performance_metrics:
            metrics = model_card.performance_metrics
            if not all(0 <= getattr(metrics, field, 0) <= 1 for field in ['accuracy', 'precision', 'recall', 'f1_score']):
                self.logger.error("Performance metrics must be between 0 and 1")
                return False
        
        return True
    
    def _save_model_card(self, model_card: ModelCard) -> None:
        """Save model card to disk"""
        model_path = os.path.join(self.models_dir, f"{model_card.model_id}.json")
        
        # Convert to dictionary
        model_dict = asdict(model_card)
        
        # Convert enums to strings
        model_dict['audit_status'] = model_card.audit_status.value
        if model_card.bias_assessment:
            model_dict['bias_assessment']['overall_bias_level'] = model_card.bias_assessment.overall_bias_level.value
        
        with open(model_path, 'w') as f:
            json.dump(model_dict, f, indent=2, default=str)
    
    def get_model(self, model_id: str) -> Optional[ModelCard]:
        """Get model card by ID"""
        return self.models.get(model_id)
    
    def list_models(self) -> List[ModelCard]:
        """List all registered models"""
        return list(self.models.values())
    
    def update_model_audit(self, model_id: str, audit_score: float, audit_status: AuditStatus, notes: str = "") -> bool:
        """Update model audit information"""
        try:
            model = self.get_model(model_id)
            if not model:
                return False
            
            # Update audit information
            model.audit_score = audit_score
            model.audit_status = audit_status
            model.last_audit_date = datetime.now(timezone.utc).isoformat()
            
            # Calculate next audit date (6 months from now)
            next_audit = datetime.now(timezone.utc).replace(month=datetime.now().month + 6)
            model.next_audit_date = next_audit.isoformat()
            
            # Save updated model
            self._save_model_card(model)
            
            self.logger.info(f"Updated audit for model {model_id}: {audit_status.value} (score: {audit_score})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating model audit: {e}")
            return False
    
    def update_bias_assessment(self, model_id: str, bias_assessment: BiasAssessment) -> bool:
        """Update model bias assessment"""
        try:
            model = self.get_model(model_id)
            if not model:
                return False
            
            model.bias_assessment = bias_assessment
            self._save_model_card(model)
            
            self.logger.info(f"Updated bias assessment for model {model_id}: {bias_assessment.overall_bias_level.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating bias assessment: {e}")
            return False
    
    def get_models_requiring_audit(self) -> List[ModelCard]:
        """Get models that require audit"""
        now = datetime.now(timezone.utc)
        models_needing_audit = []
        
        for model in self.models.values():
            try:
                next_audit = datetime.fromisoformat(model.next_audit_date.replace('Z', '+00:00'))
                if now >= next_audit or model.audit_status == AuditStatus.PENDING:
                    models_needing_audit.append(model)
            except:
                # If date parsing fails, include in audit list
                models_needing_audit.append(model)
        
        return models_needing_audit
    
    def get_models_by_bias_level(self, bias_level: BiasLevel) -> List[ModelCard]:
        """Get models by bias level"""
        return [
            model for model in self.models.values()
            if model.bias_assessment and model.bias_assessment.overall_bias_level == bias_level
        ]
    
    def generate_model_card_json(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Generate model card JSON for public consumption"""
        model = self.get_model(model_id)
        if not model:
            return None
        
        # Convert to public format
        model_dict = asdict(model)
        
        # Convert enums to strings
        model_dict['audit_status'] = model.audit_status.value
        if model.bias_assessment:
            model_dict['bias_assessment']['overall_bias_level'] = model.bias_assessment.overall_bias_level.value
        
        # Add metadata
        model_dict['_metadata'] = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'schema_version': '1.0.0',
            'governance_framework': 'DRP AI Ethics Framework'
        }
        
        return model_dict
    
    def export_model_cards(self, output_dir: str = "ai/models/public") -> bool:
        """Export all model cards to public directory"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            for model_id, model in self.models.items():
                # Generate public model card
                model_card_json = self.generate_model_card_json(model_id)
                if model_card_json:
                    output_path = os.path.join(output_dir, f"{model_id}-model-card.json")
                    with open(output_path, 'w') as f:
                        json.dump(model_card_json, f, indent=2, default=str)
            
            self.logger.info(f"Exported {len(self.models)} model cards to {output_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting model cards: {e}")
            return False

# Example usage and model creation
def create_example_models():
    """Create example model cards for demonstration"""
    manager = ModelGovernanceManager()
    
    # Example face verification model
    face_model = ModelCard(
        model_id="face_verification_v1",
        version="1.2.0",
        name="DRP Face Verification Model",
        description="AI model for verifying human identity in Proof of Status (PoST)",
        created_date="2024-01-15T00:00:00Z",
        last_updated="2024-10-04T00:00:00Z",
        intended_use="Identity verification for DRP network participants",
        limitations=[
            "May have reduced accuracy for certain demographic groups",
            "Requires good lighting conditions",
            "Not suitable for real-time video verification"
        ],
        use_cases=["PoST verification", "Identity confirmation", "Access control"],
        prohibited_uses=["Surveillance", "Facial recognition without consent", "Discrimination"],
        model_type="Deep Learning",
        architecture="ResNet-50 with custom head",
        input_format="224x224x3 RGB image",
        output_format="Binary classification (verified/not_verified)",
        model_size_mb=98.5,
        dataset=DatasetInfo(
            name="DRP Face Dataset",
            source="Consented participants from DRP community",
            size=50000,
            diversity_score=0.85,
            bias_indicators=["Age distribution", "Ethnicity representation"],
            privacy_compliance="GDPR compliant, anonymized",
            last_updated="2024-01-10T00:00:00Z"
        ),
        performance_metrics=PerformanceMetrics(
            accuracy=0.94,
            precision=0.93,
            recall=0.95,
            f1_score=0.94,
            false_positive_rate=0.05,
            false_negative_rate=0.03,
            processing_time_ms=150,
            memory_usage_mb=45.2
        ),
        bias_assessment=BiasAssessment(
            overall_bias_level=BiasLevel.LOW,
            demographic_parity=0.92,
            equalized_odds=0.89,
            calibration=0.91,
            bias_indicators=["Slight underperformance on older age groups"],
            mitigation_measures=["Data augmentation", "Adversarial training"],
            last_assessment="2024-09-15T00:00:00Z"
        ),
        audit_score=0.87,
        audit_status=AuditStatus.PASSED,
        last_audit_date="2024-09-15T00:00:00Z",
        next_audit_date="2025-03-15T00:00:00Z",
        compliance_frameworks=["GDPR", "AI Act", "DRP Ethics Framework"],
        privacy_impact_assessment="Low risk - no personal data stored",
        security_audit_status="Passed",
        encryption_at_rest=True,
        encryption_in_transit=True,
        deployment_environment="Production",
        scaling_requirements={"min_instances": 2, "max_instances": 10},
        monitoring_requirements=["Accuracy monitoring", "Bias detection", "Performance metrics"],
        maintainer="DRP AI Team",
        contact_email="ai-team@decentralizedrights.com",
        documentation_url="https://docs.decentralizedrights.com/ai/face-verification",
        model_card_url="https://github.com/decentralizedrights/DRP/ai/models/face_verification_v1-model-card.json"
    )
    
    # Register the model
    manager.register_model(face_model)
    
    return manager

if __name__ == "__main__":
    # Create example models
    manager = create_example_models()
    
    # Export model cards
    manager.export_model_cards()
    
    print("Model governance system initialized with example models")
