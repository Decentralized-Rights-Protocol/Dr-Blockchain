"""
DRP Cross-Chain Interoperability Layer

This module provides a standardized interface for DRP to communicate with
external blockchains including Ethereum, Bitcoin, and Polkadot.

Key Features:
- Cross-chain bridge contracts for smart contract platforms
- Relay/oracle system for external blockchain verification
- Multi-cryptographic scheme support (ECDSA, Ed25519, Schnorr)
- Security checks against common cross-chain attacks
- Extensible API for adding new blockchain integrations
- Quantum-resistant upgrade path

Architecture:
- bridges/: Bridge implementations for different chains
- relays/: Oracle and relay mechanisms
- crypto/: Cryptographic layer with multi-scheme support
- tests/: Comprehensive test suite

Future-Proof Design:
- Modular architecture allows easy addition of new chains
- Cryptographic layer supports quantum-resistant algorithms
- Bridge contracts designed for upgradeability
- Security-first approach with comprehensive attack protection
"""

from .bridges import BitcoinBridge, BridgeManager, EthereumBridge, PolkadotBridge
from .core import (
    BridgeConfig,
    ChainType,
    CrossChainError,
    CrossChainManager,
    RelayConfig,
    TransactionStatus,
)
from .crypto import CryptoScheme, MultiSchemeSigner, MultiSchemeVerifier, QuantumResistantUpgrade
from .relays import HeaderVerifier, MerkleProofVerifier, OracleService, RelayManager

__version__ = "1.0.0"
__author__ = "DRP Development Team"
__all__ = [
    # Core interfaces
    "CrossChainManager",
    "CrossChainError",
    "ChainType",
    "TransactionStatus",
    "BridgeConfig",
    "RelayConfig",
    # Cryptographic layer
    "MultiSchemeSigner",
    "MultiSchemeVerifier",
    "CryptoScheme",
    "QuantumResistantUpgrade",
    # Relay system
    "RelayManager",
    "OracleService",
    "MerkleProofVerifier",
    "HeaderVerifier",
    # Bridge implementations
    "BridgeManager",
    "EthereumBridge",
    "PolkadotBridge",
    "BitcoinBridge",
]
