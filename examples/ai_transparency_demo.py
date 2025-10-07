#!/usr/bin/env python3
"""
AI Transparency & Accountability System Demo
Demonstrates the complete transparency framework for DRP AI Elder decisions
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any

# Import DRP AI Transparency modules
from ai.transparency import (
    AITransparencyLogger,
    DecisionType,
    DecisionOutcome,
    ModelGovernanceManager,
    ModelCard,
    DatasetInfo,
    PerformanceMetrics,
    BiasAssessment,
    AuditStatus,
    BiasLevel,
    ZKPExplainabilityManager,
    ProofType
)

from governance.ai_oversight import (
    AIOversightManager,
    DisputeStatus,
    ReviewVote
)

async def demo_ai_transparency_system():
    """
    Comprehensive demo of the AI Transparency & Accountability System
    """
    print("🔬 DRP AI Transparency & Accountability System Demo")
    print("=" * 60)
    
    # Initialize components
    print("\n1. Initializing AI Transparency Components...")
    
    # Mock elder private key for demo
    elder_private_key = b"mock_elder_private_key_32_bytes_long"
    
    # Initialize decision logger
    decision_logger = AITransparencyLogger(elder_private_key)
    print("✅ Decision Logger initialized")
    
    # Initialize model governance manager
    model_governance = ModelGovernanceManager()
    print("✅ Model Governance Manager initialized")
    
    # Initialize human oversight manager
    oversight_manager = AIOversightManager()
    print("✅ Human Oversight Manager initialized")
    
    # Initialize ZKP explainability manager
    zkp_manager = ZKPExplainabilityManager()
    print("✅ ZKP Explainability Manager initialized")
    
    # Create and register example models
    print("\n2. Creating and Registering AI Models...")
    
    # Face verification model
    face_model = create_example_face_model()
    model_governance.register_model(face_model)
    print(f"✅ Registered model: {face_model.model_id}")
    
    # Activity detection model
    activity_model = create_example_activity_model()
    model_governance.register_model(activity_model)
    print(f"✅ Registered model: {activity_model.model_id}")
    
    # Compile ZK circuits for models
    print("\n3. Compiling ZK Circuits for Models...")
    
    face_circuit = zkp_manager.compile_model_circuit(
        "face_verification_v1",
        {"input_size": 224, "output_size": 2, "layer_count": 5, "parameter_count": 1000000}
    )
    print(f"✅ Face verification circuit compiled: {face_circuit}")
    
    activity_circuit = zkp_manager.compile_model_circuit(
        "activity_detection_v1", 
        {"input_size": 1024, "output_size": 10, "layer_count": 8, "parameter_count": 2000000}
    )
    print(f"✅ Activity detection circuit compiled: {activity_circuit}")
    
    # Simulate AI decisions
    print("\n4. Simulating AI Elder Decisions...")
    
    decisions = []
    
    # Face verification decisions
    for i in range(5):
        decision = decision_logger.log_decision(
            model_id="face_verification_v1",
            model_version="1.2.0",
            decision_type=DecisionType.POST_VERIFICATION,
            input_data={"image_shape": (224, 224, 3), "face_detected": True},
            input_type="image",
            outcome=DecisionOutcome.APPROVED if i < 4 else DecisionOutcome.FLAGGED,
            confidence_score=0.85 + (i * 0.02),
            explanation=f"Face verification {'passed' if i < 4 else 'flagged for review'}",
            processing_time_ms=120 + (i * 10)
        )
        decisions.append(decision)
        print(f"✅ Logged face verification decision: {decision.decision_id}")
    
    # Activity detection decisions
    for i in range(3):
        decision = decision_logger.log_decision(
            model_id="activity_detection_v1",
            model_version="1.1.0",
            decision_type=DecisionType.POAT_VERIFICATION,
            input_data={"sensor_data": [0.1, 0.2, 0.3], "timestamp": datetime.now().isoformat()},
            input_type="sensor",
            outcome=DecisionOutcome.APPROVED,
            confidence_score=0.90 + (i * 0.01),
            explanation=f"Activity pattern verified: {'walking' if i == 0 else 'running' if i == 1 else 'cycling'}",
            processing_time_ms=80 + (i * 5)
        )
        decisions.append(decision)
        print(f"✅ Logged activity detection decision: {decision.decision_id}")
    
    # Generate ZK proofs for decisions
    print("\n5. Generating Zero-Knowledge Proofs...")
    
    zk_proofs = []
    for decision in decisions[:3]:  # Generate proofs for first 3 decisions
        zk_proof = zkp_manager.generate_decision_proof(
            model_id=decision.model_id,
            input_data={"shape": (224, 224, 3)},
            prediction="verified",
            confidence=decision.confidence_score,
            decision_outcome=decision.outcome.value
        )
        
        if zk_proof:
            zk_proofs.append(zk_proof)
            verification = zkp_manager.verify_decision_proof(zk_proof)
            print(f"✅ Generated ZK proof {zk_proof.proof_id}: {'Verified' if verification else 'Failed'}")
    
    # Generate bias absence proof
    bias_proof = zkp_manager.generate_bias_absence_proof(
        model_id="face_verification_v1",
        demographic_groups=["age_18_30", "age_31_50", "age_51_70"],
        decision_outcomes={
            "age_18_30": {"approval_rate": 0.92, "total_decisions": 100},
            "age_31_50": {"approval_rate": 0.89, "total_decisions": 150},
            "age_51_70": {"approval_rate": 0.91, "total_decisions": 80}
        }
    )
    
    if bias_proof:
        print(f"✅ Generated bias absence proof: {bias_proof.proof_id}")
    
    # Simulate human oversight and disputes
    print("\n6. Simulating Human Oversight and Disputes...")
    
    # Create a dispute for the flagged decision
    flagged_decision = next(d for d in decisions if d.outcome == DecisionOutcome.FLAGGED)
    dispute_id = oversight_manager.create_dispute(
        decision_id=flagged_decision.decision_id,
        model_id=flagged_decision.model_id,
        elder_node_id=flagged_decision.elder_node_id,
        dispute_reason="Potential bias detected in face verification",
        dispute_category="bias",
        submitted_by="community_member_001"
    )
    print(f"✅ Created dispute: {dispute_id}")
    
    # Assign human reviewers
    oversight_manager.assign_human_reviewers(dispute_id, ["reviewer_001", "reviewer_002", "reviewer_003"])
    print("✅ Assigned human reviewers")
    
    # Submit review votes
    oversight_manager.submit_review_vote(dispute_id, "reviewer_001", ReviewVote.OVERTURN_AI, "Clear bias detected")
    oversight_manager.submit_review_vote(dispute_id, "reviewer_002", ReviewVote.OVERTURN_AI, "Agree with bias assessment")
    oversight_manager.submit_review_vote(dispute_id, "reviewer_003", ReviewVote.SUPPORT_AI, "Decision seems fair")
    print("✅ Submitted review votes")
    
    # Create governance proposal
    proposal_id = oversight_manager.create_governance_proposal(
        proposal_type="review_elder_decision",
        title="Review Face Verification Bias",
        description="Community proposal to review potential bias in face verification model",
        proposer="community_member_002",
        decision_id=flagged_decision.decision_id,
        model_id=flagged_decision.model_id
    )
    print(f"✅ Created governance proposal: {proposal_id}")
    
    # Simulate voting on proposal
    oversight_manager.vote_on_proposal(proposal_id, "voter_001", "for")
    oversight_manager.vote_on_proposal(proposal_id, "voter_002", "for")
    oversight_manager.vote_on_proposal(proposal_id, "voter_003", "against")
    print("✅ Simulated governance voting")
    
    # Generate transparency reports
    print("\n7. Generating Transparency Reports...")
    
    # Get AI statistics
    ai_stats = oversight_manager.get_ai_human_agreement_stats()
    print(f"📊 AI-Human Agreement: {ai_stats['ai_accuracy_percent']}%")
    print(f"📊 Total Disputes: {ai_stats['total_disputes']}")
    print(f"📊 Resolved Disputes: {ai_stats['resolved_disputes']}")
    
    # Get model audit information
    models = model_governance.list_models()
    print(f"📊 Registered Models: {len(models)}")
    
    for model in models:
        print(f"   • {model.model_id}: Audit Score {model.audit_score:.2f}, Bias Level {model.bias_assessment.overall_bias_level.value}")
    
    # Export model cards
    model_governance.export_model_cards()
    print("✅ Exported model cards to public directory")
    
    # Demonstrate API endpoints (mock)
    print("\n8. Demonstrating API Endpoints...")
    
    # Mock API responses
    api_responses = {
        "decisions": len(decisions),
        "models": len(models),
        "disputes": ai_stats['total_disputes'],
        "zk_proofs": len(zk_proofs),
        "bias_alerts": 1,  # The flagged decision
        "average_confidence": sum(d.confidence_score for d in decisions) / len(decisions)
    }
    
    print("📡 Mock API Responses:")
    for endpoint, value in api_responses.items():
        print(f"   • /api/v1/ai/{endpoint}: {value}")
    
    # Generate final summary
    print("\n9. System Summary...")
    print("=" * 40)
    print(f"✅ AI Decisions Logged: {len(decisions)}")
    print(f"✅ ZK Proofs Generated: {len(zk_proofs)}")
    print(f"✅ Models Registered: {len(models)}")
    print(f"✅ Disputes Created: {ai_stats['total_disputes']}")
    print(f"✅ Governance Proposals: 1")
    print(f"✅ Average Decision Confidence: {api_responses['average_confidence']:.2f}")
    print(f"✅ AI-Human Agreement Rate: {ai_stats['ai_accuracy_percent']}%")
    
    print("\n🎉 AI Transparency & Accountability System Demo Complete!")
    print("\nNext Steps:")
    print("1. Access the transparency dashboard at /transparency")
    print("2. Query decisions via API endpoints")
    print("3. Review model cards and audit scores")
    print("4. Monitor bias alerts and disputes")
    print("5. Participate in governance proposals")

def create_example_face_model() -> ModelCard:
    """Create example face verification model card"""
    return ModelCard(
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

def create_example_activity_model() -> ModelCard:
    """Create example activity detection model card"""
    return ModelCard(
        model_id="activity_detection_v1",
        version="1.1.0",
        name="DRP Activity Detection Model",
        description="AI model for detecting human activities in Proof of Activity (PoAT)",
        created_date="2024-02-01T00:00:00Z",
        last_updated="2024-10-04T00:00:00Z",
        intended_use="Activity verification for DRP network participants",
        limitations=[
            "Requires sensor data from approved devices",
            "May not detect subtle activities",
            "Performance depends on data quality"
        ],
        use_cases=["PoAT verification", "Activity monitoring", "Health tracking"],
        prohibited_uses=["Surveillance", "Unauthorized tracking", "Discrimination"],
        model_type="Deep Learning",
        architecture="LSTM with attention mechanism",
        input_format="Time series sensor data (accelerometer, gyroscope)",
        output_format="Multi-class classification (10 activity types)",
        model_size_mb=45.2,
        dataset=DatasetInfo(
            name="DRP Activity Dataset",
            source="Consented participants with wearable devices",
            size=100000,
            diversity_score=0.88,
            bias_indicators=["Activity type distribution", "Age group representation"],
            privacy_compliance="GDPR compliant, anonymized",
            last_updated="2024-02-01T00:00:00Z"
        ),
        performance_metrics=PerformanceMetrics(
            accuracy=0.91,
            precision=0.89,
            recall=0.92,
            f1_score=0.90,
            false_positive_rate=0.08,
            false_negative_rate=0.05,
            processing_time_ms=80,
            memory_usage_mb=25.1
        ),
        bias_assessment=BiasAssessment(
            overall_bias_level=BiasLevel.LOW,
            demographic_parity=0.89,
            equalized_odds=0.87,
            calibration=0.90,
            bias_indicators=["Slight underperformance on elderly participants"],
            mitigation_measures=["Data augmentation", "Ensemble methods"],
            last_assessment="2024-09-20T00:00:00Z"
        ),
        audit_score=0.84,
        audit_status=AuditStatus.PASSED,
        last_audit_date="2024-09-20T00:00:00Z",
        next_audit_date="2025-03-20T00:00:00Z",
        compliance_frameworks=["GDPR", "AI Act", "DRP Ethics Framework"],
        privacy_impact_assessment="Low risk - sensor data anonymized",
        security_audit_status="Passed",
        encryption_at_rest=True,
        encryption_in_transit=True,
        deployment_environment="Production",
        scaling_requirements={"min_instances": 3, "max_instances": 15},
        monitoring_requirements=["Accuracy monitoring", "Bias detection", "Performance metrics"],
        maintainer="DRP AI Team",
        contact_email="ai-team@decentralizedrights.com",
        documentation_url="https://docs.decentralizedrights.com/ai/activity-detection",
        model_card_url="https://github.com/decentralizedrights/DRP/ai/models/activity_detection_v1-model-card.json"
    )

if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_ai_transparency_system())
