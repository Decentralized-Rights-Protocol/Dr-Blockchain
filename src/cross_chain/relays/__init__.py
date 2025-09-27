"""
DRP Cross-Chain Relay and Oracle System

This module provides relay and oracle services for cross-chain interoperability,
enabling verification of external blockchain states and Merkle proofs.

Components:
- RelayManager: Central relay coordination
- OracleService: Blockchain state verification
- MerkleProofVerifier: Merkle proof validation
- HeaderVerifier: Blockchain header verification
- ConsensusOracle: Multi-oracle consensus mechanism

Features:
- Multi-chain header verification
- Merkle proof validation
- Oracle consensus mechanisms
- Quantum-resistant verification
- Security-first design
"""

from .relay_manager import RelayManager
from .oracle_service import OracleService
from .merkle_verifier import MerkleProofVerifier
from .header_verifier import HeaderVerifier
from .consensus_oracle import ConsensusOracle

__version__ = "1.0.0"
__all__ = [
    "RelayManager",
    "OracleService",
    "MerkleProofVerifier",
    "HeaderVerifier",
    "ConsensusOracle"
]


