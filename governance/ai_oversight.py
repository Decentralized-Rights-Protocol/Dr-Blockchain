"""
Human Oversight & Governance Hooks for AI Decisions
Implements community-driven review and dispute resolution for AI Elder decisions
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from ai.transparency.decision_logger import AIDecisionLog, DecisionOutcome
from ai.transparency.model_governance import ModelCard, ModelGovernanceManager

class DisputeStatus(Enum):
    """Dispute resolution status"""
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    CLOSED = "closed"

class ReviewVote(Enum):
    """Human review vote options"""
    SUPPORT_AI = "support_ai"
    OVERTURN_AI = "overturn_ai"
    ABSTAIN = "abstain"

@dataclass
class DisputeCase:
    """AI decision dispute case"""
    dispute_id: str
    decision_id: str
    model_id: str
    elder_node_id: str
    
    # Dispute details
    dispute_reason: str
    dispute_category: str  # bias, accuracy, fairness, etc.
    submitted_by: str  # user_id or community_member
    submitted_at: str
    
    # Resolution
    status: DisputeStatus
    human_reviewers: List[str]
    votes: Dict[str, ReviewVote]
    resolution: Optional[ReviewVote]
    resolution_notes: Optional[str]
    resolved_at: Optional[str]
    resolved_by: Optional[str]
    
    # Impact
    model_update_required: bool
    policy_change_required: bool

@dataclass
class GovernanceProposal:
    """On-chain governance proposal for AI oversight"""
    proposal_id: str
    proposal_type: str  # "review_elder_decision", "update_model", "revoke_elder", etc.
    title: str
    description: str
    
    # Related entities
    decision_id: Optional[str]
    model_id: Optional[str]
    elder_node_id: Optional[str]
    
    # Proposal details
    proposer: str
    created_at: str
    voting_deadline: str
    
    # Voting
    votes_for: int
    votes_against: int
    votes_abstain: int
    total_votes: int
    quorum_threshold: float
    
    # Status
    status: str  # "active", "passed", "failed", "executed"
    execution_tx_hash: Optional[str]

class AIOversightManager:
    """Manages human oversight and governance for AI decisions"""
    
    def __init__(self, governance_db_path: str = "governance/ai_oversight.json"):
        self.governance_db_path = governance_db_path
        self.disputes: Dict[str, DisputeCase] = {}
        self.proposals: Dict[str, GovernanceProposal] = {}
        self.logger = logging.getLogger(__name__)
        
        # Load existing data
        self._load_governance_data()
    
    def _load_governance_data(self) -> None:
        """Load existing governance data from disk"""
        try:
            with open(self.governance_db_path, 'r') as f:
                data = json.load(f)
                self.disputes = {k: DisputeCase(**v) for k, v in data.get('disputes', {}).items()}
                self.proposals = {k: GovernanceProposal(**v) for k, v in data.get('proposals', {}).items()}
        except FileNotFoundError:
            self.logger.info("No existing governance data found, starting fresh")
        except Exception as e:
            self.logger.error(f"Error loading governance data: {e}")
    
    def _save_governance_data(self) -> None:
        """Save governance data to disk"""
        try:
            data = {
                'disputes': {k: asdict(v) for k, v in self.disputes.items()},
                'proposals': {k: asdict(v) for k, v in self.proposals.items()}
            }
            
            with open(self.governance_db_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving governance data: {e}")
    
    def create_dispute(
        self,
        decision_id: str,
        model_id: str,
        elder_node_id: str,
        dispute_reason: str,
        dispute_category: str,
        submitted_by: str
    ) -> str:
        """Create a new dispute case for an AI decision"""
        try:
            dispute_id = self._generate_dispute_id(decision_id, submitted_by)
            
            dispute = DisputeCase(
                dispute_id=dispute_id,
                decision_id=decision_id,
                model_id=model_id,
                elder_node_id=elder_node_id,
                dispute_reason=dispute_reason,
                dispute_category=dispute_category,
                submitted_by=submitted_by,
                submitted_at=datetime.now(timezone.utc).isoformat(),
                status=DisputeStatus.OPEN,
                human_reviewers=[],
                votes={},
                resolution=None,
                resolution_notes=None,
                resolved_at=None,
                resolved_by=None,
                model_update_required=False,
                policy_change_required=False
            )
            
            self.disputes[dispute_id] = dispute
            self._save_governance_data()
            
            self.logger.info(f"Created dispute {dispute_id} for decision {decision_id}")
            return dispute_id
            
        except Exception as e:
            self.logger.error(f"Error creating dispute: {e}")
            return None
    
    def _generate_dispute_id(self, decision_id: str, submitted_by: str) -> str:
        """Generate unique dispute ID"""
        data = f"{decision_id}_{submitted_by}_{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def assign_human_reviewers(self, dispute_id: str, reviewers: List[str]) -> bool:
        """Assign human reviewers to a dispute case"""
        try:
            dispute = self.disputes.get(dispute_id)
            if not dispute:
                return False
            
            dispute.human_reviewers = reviewers
            dispute.status = DisputeStatus.IN_REVIEW
            self._save_governance_data()
            
            self.logger.info(f"Assigned {len(reviewers)} reviewers to dispute {dispute_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error assigning reviewers: {e}")
            return False
    
    def submit_review_vote(
        self,
        dispute_id: str,
        reviewer_id: str,
        vote: ReviewVote,
        reasoning: str = ""
    ) -> bool:
        """Submit a human review vote for a dispute"""
        try:
            dispute = self.disputes.get(dispute_id)
            if not dispute:
                return False
            
            if reviewer_id not in dispute.human_reviewers:
                self.logger.warning(f"Reviewer {reviewer_id} not assigned to dispute {dispute_id}")
                return False
            
            # Record the vote
            dispute.votes[reviewer_id] = vote
            
            # Check if we have enough votes to resolve
            if len(dispute.votes) >= len(dispute.human_reviewers):
                self._resolve_dispute(dispute_id)
            
            self._save_governance_data()
            
            self.logger.info(f"Recorded vote {vote.value} from reviewer {reviewer_id} for dispute {dispute_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error submitting review vote: {e}")
            return False
    
    def _resolve_dispute(self, dispute_id: str) -> None:
        """Resolve a dispute based on human votes"""
        try:
            dispute = self.disputes.get(dispute_id)
            if not dispute:
                return
            
            # Count votes
            vote_counts = {
                ReviewVote.SUPPORT_AI: 0,
                ReviewVote.OVERTURN_AI: 0,
                ReviewVote.ABSTAIN: 0
            }
            
            for vote in dispute.votes.values():
                vote_counts[vote] += 1
            
            # Determine resolution (majority vote)
            if vote_counts[ReviewVote.OVERTURN_AI] > vote_counts[ReviewVote.SUPPORT_AI]:
                dispute.resolution = ReviewVote.OVERTURN_AI
                dispute.resolution_notes = f"Human reviewers overturned AI decision ({vote_counts[ReviewVote.OVERTURN_AI]} vs {vote_counts[ReviewVote.SUPPORT_AI]})"
            else:
                dispute.resolution = ReviewVote.SUPPORT_AI
                dispute.resolution_notes = f"Human reviewers supported AI decision ({vote_counts[ReviewVote.SUPPORT_AI]} vs {vote_counts[ReviewVote.OVERTURN_AI]})"
            
            dispute.status = DisputeStatus.RESOLVED
            dispute.resolved_at = datetime.now(timezone.utc).isoformat()
            dispute.resolved_by = "human_consensus"
            
            # Determine if model updates are needed
            if dispute.resolution == ReviewVote.OVERTURN_AI:
                dispute.model_update_required = True
                if dispute.dispute_category in ["bias", "fairness"]:
                    dispute.policy_change_required = True
            
            self.logger.info(f"Resolved dispute {dispute_id}: {dispute.resolution.value}")
            
        except Exception as e:
            self.logger.error(f"Error resolving dispute: {e}")
    
    def create_governance_proposal(
        self,
        proposal_type: str,
        title: str,
        description: str,
        proposer: str,
        decision_id: Optional[str] = None,
        model_id: Optional[str] = None,
        elder_node_id: Optional[str] = None,
        voting_days: int = 7
    ) -> str:
        """Create a governance proposal for AI oversight"""
        try:
            proposal_id = self._generate_proposal_id(proposer, proposal_type)
            
            voting_deadline = datetime.now(timezone.utc).replace(
                day=datetime.now().day + voting_days
            ).isoformat()
            
            proposal = GovernanceProposal(
                proposal_id=proposal_id,
                proposal_type=proposal_type,
                title=title,
                description=description,
                decision_id=decision_id,
                model_id=model_id,
                elder_node_id=elder_node_id,
                proposer=proposer,
                created_at=datetime.now(timezone.utc).isoformat(),
                voting_deadline=voting_deadline,
                votes_for=0,
                votes_against=0,
                votes_abstain=0,
                total_votes=0,
                quorum_threshold=0.51,  # 51% majority
                status="active",
                execution_tx_hash=None
            )
            
            self.proposals[proposal_id] = proposal
            self._save_governance_data()
            
            self.logger.info(f"Created governance proposal {proposal_id}: {title}")
            return proposal_id
            
        except Exception as e:
            self.logger.error(f"Error creating governance proposal: {e}")
            return None
    
    def _generate_proposal_id(self, proposer: str, proposal_type: str) -> str:
        """Generate unique proposal ID"""
        data = f"{proposer}_{proposal_type}_{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def vote_on_proposal(
        self,
        proposal_id: str,
        voter: str,
        vote: str  # "for", "against", "abstain"
    ) -> bool:
        """Vote on a governance proposal"""
        try:
            proposal = self.proposals.get(proposal_id)
            if not proposal:
                return False
            
            if proposal.status != "active":
                self.logger.warning(f"Proposal {proposal_id} is not active")
                return False
            
            # Check if voting deadline has passed
            deadline = datetime.fromisoformat(proposal.voting_deadline.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > deadline:
                self.logger.warning(f"Voting deadline passed for proposal {proposal_id}")
                return False
            
            # Record vote (simplified - in production would use blockchain voting)
            if vote == "for":
                proposal.votes_for += 1
            elif vote == "against":
                proposal.votes_against += 1
            elif vote == "abstain":
                proposal.votes_abstain += 1
            else:
                return False
            
            proposal.total_votes += 1
            
            # Check if proposal passed
            if proposal.votes_for > proposal.votes_against and proposal.total_votes >= 100:  # Minimum participation
                proposal.status = "passed"
                self._execute_proposal(proposal_id)
            
            self._save_governance_data()
            
            self.logger.info(f"Recorded vote {vote} from {voter} for proposal {proposal_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error voting on proposal: {e}")
            return False
    
    def _execute_proposal(self, proposal_id: str) -> None:
        """Execute a passed governance proposal"""
        try:
            proposal = self.proposals.get(proposal_id)
            if not proposal:
                return
            
            # Execute based on proposal type
            if proposal.proposal_type == "review_elder_decision":
                self._execute_decision_review(proposal)
            elif proposal.proposal_type == "update_model":
                self._execute_model_update(proposal)
            elif proposal.proposal_type == "revoke_elder":
                self._execute_elder_revocation(proposal)
            
            proposal.status = "executed"
            proposal.execution_tx_hash = f"0x{hashlib.sha256(proposal_id.encode()).hexdigest()[:16]}"
            
            self.logger.info(f"Executed proposal {proposal_id}")
            
        except Exception as e:
            self.logger.error(f"Error executing proposal: {e}")
    
    def _execute_decision_review(self, proposal: GovernanceProposal) -> None:
        """Execute a decision review proposal"""
        if proposal.decision_id:
            # Flag decision for human review
            self.logger.info(f"Flagging decision {proposal.decision_id} for human review")
    
    def _execute_model_update(self, proposal: GovernanceProposal) -> None:
        """Execute a model update proposal"""
        if proposal.model_id:
            # Trigger model update process
            self.logger.info(f"Triggering update for model {proposal.model_id}")
    
    def _execute_elder_revocation(self, proposal: GovernanceProposal) -> None:
        """Execute an elder revocation proposal"""
        if proposal.elder_node_id:
            # Revoke elder node
            self.logger.info(f"Revoking elder node {proposal.elder_node_id}")
    
    def get_dispute(self, dispute_id: str) -> Optional[DisputeCase]:
        """Get dispute case by ID"""
        return self.disputes.get(dispute_id)
    
    def get_disputes_by_status(self, status: DisputeStatus) -> List[DisputeCase]:
        """Get disputes by status"""
        return [d for d in self.disputes.values() if d.status == status]
    
    def get_proposal(self, proposal_id: str) -> Optional[GovernanceProposal]:
        """Get governance proposal by ID"""
        return self.proposals.get(proposal_id)
    
    def get_active_proposals(self) -> List[GovernanceProposal]:
        """Get active governance proposals"""
        return [p for p in self.proposals.values() if p.status == "active"]
    
    def get_ai_human_agreement_stats(self) -> Dict[str, Any]:
        """Get statistics on AI vs Human agreement"""
        resolved_disputes = [d for d in self.disputes.values() if d.status == DisputeStatus.RESOLVED]
        
        ai_supported = len([d for d in resolved_disputes if d.resolution == ReviewVote.SUPPORT_AI])
        ai_overturned = len([d for d in resolved_disputes if d.resolution == ReviewVote.OVERTURN_AI])
        
        total_resolved = len(resolved_disputes)
        ai_accuracy = (ai_supported / total_resolved * 100) if total_resolved > 0 else 0
        
        return {
            "total_disputes": len(self.disputes),
            "resolved_disputes": total_resolved,
            "ai_supported": ai_supported,
            "ai_overturned": ai_overturned,
            "ai_accuracy_percent": round(ai_accuracy, 2),
            "pending_disputes": len([d for d in self.disputes.values() if d.status == DisputeStatus.OPEN])
        }

# Example usage
if __name__ == "__main__":
    # Initialize oversight manager
    oversight = AIOversightManager()
    
    # Create example dispute
    dispute_id = oversight.create_dispute(
        decision_id="dec_123456",
        model_id="face_verification_v1",
        elder_node_id="elder_001",
        dispute_reason="Potential bias against certain demographic groups",
        dispute_category="bias",
        submitted_by="community_member_001"
    )
    
    print(f"Created dispute: {dispute_id}")
    
    # Assign reviewers and vote
    oversight.assign_human_reviewers(dispute_id, ["reviewer_001", "reviewer_002", "reviewer_003"])
    oversight.submit_review_vote(dispute_id, "reviewer_001", ReviewVote.OVERTURN_AI, "Clear bias detected")
    oversight.submit_review_vote(dispute_id, "reviewer_002", ReviewVote.OVERTURN_AI, "Agree with bias assessment")
    oversight.submit_review_vote(dispute_id, "reviewer_003", ReviewVote.SUPPORT_AI, "Decision seems fair")
    
    # Get stats
    stats = oversight.get_ai_human_agreement_stats()
    print(f"AI-Human agreement stats: {stats}")
