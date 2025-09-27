"""
Consensus Oracle Implementation

This module provides consensus mechanisms for oracle services.
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class OracleVote:
    """Oracle vote for consensus"""
    oracle_id: str
    vote: bool
    timestamp: float
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class ConsensusResult:
    """Consensus result from oracles"""
    is_consensus: bool
    total_votes: int
    positive_votes: int
    negative_votes: int
    confidence: float
    required_threshold: float


class ConsensusOracle:
    """Consensus oracle for multi-oracle verification"""
    
    def __init__(self):
        self.registered_oracles: Dict[str, Any] = {}
        self.consensus_threshold = 0.67
        self.vote_timeout = 300  # 5 minutes
    
    async def register_oracle(self, oracle_id: str, oracle_service: Any) -> bool:
        """Register oracle for consensus"""
        self.registered_oracles[oracle_id] = oracle_service
        return True
    
    async def collect_votes(self, verification_data: Any) -> ConsensusResult:
        """Collect votes from all registered oracles"""
        
        votes = []
        
        for oracle_id, oracle in self.registered_oracles.items():
            try:
                # Get vote from oracle
                vote_result = await oracle.verify_data(verification_data)
                
                vote = OracleVote(
                    oracle_id=oracle_id,
                    vote=vote_result,
                    timestamp=time.time(),
                    confidence=0.95,  # Mock confidence
                    metadata={}
                )
                
                votes.append(vote)
                
            except Exception as e:
                print(f"Oracle {oracle_id} failed to vote: {e}")
        
        return await self._calculate_consensus(votes)
    
    async def _calculate_consensus(self, votes: List[OracleVote]) -> ConsensusResult:
        """Calculate consensus from votes"""
        
        if not votes:
            return ConsensusResult(
                is_consensus=False,
                total_votes=0,
                positive_votes=0,
                negative_votes=0,
                confidence=0.0,
                required_threshold=self.consensus_threshold
            )
        
        positive_votes = sum(1 for vote in votes if vote.vote)
        negative_votes = len(votes) - positive_votes
        total_votes = len(votes)
        
        consensus_ratio = positive_votes / total_votes
        is_consensus = consensus_ratio >= self.consensus_threshold
        
        # Calculate confidence based on vote distribution
        confidence = min(consensus_ratio * 2, 1.0) if is_consensus else min((1 - consensus_ratio) * 2, 1.0)
        
        return ConsensusResult(
            is_consensus=is_consensus,
            total_votes=total_votes,
            positive_votes=positive_votes,
            negative_votes=negative_votes,
            confidence=confidence,
            required_threshold=self.consensus_threshold
        )


