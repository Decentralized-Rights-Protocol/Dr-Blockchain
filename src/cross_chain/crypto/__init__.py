"""
DRP Cross-Chain Cryptographic Layer

This module provides multi-scheme cryptographic support for cross-chain
interoperability, including support for quantum-resistant algorithms.

Supported Schemes:
- ECDSA (secp256k1, secp256r1)
- Ed25519
- Schnorr signatures
- Quantum-resistant algorithms (future)

Features:
- Multi-scheme signing and verification
- Quantum-resistant upgrade path
- Cross-chain signature compatibility
- Security-first design
"""

from .multi_scheme import (
    MultiSchemeSigner,
    MultiSchemeVerifier,
    CryptoScheme,
    SignatureResult,
    VerificationResult
)

from .quantum_resistant import (
    QuantumResistantUpgrade,
    PostQuantumSigner,
    PostQuantumVerifier,
    HybridSigner,
    HybridVerifier
)

from .schemes import (
    ECDSAScheme,
    Ed25519Scheme,
    SchnorrScheme,
    BLS12Scheme,
    DilithiumScheme
)

__version__ = "1.0.0"
__all__ = [
    # Multi-scheme support
    "MultiSchemeSigner",
    "MultiSchemeVerifier", 
    "CryptoScheme",
    "SignatureResult",
    "VerificationResult",
    
    # Quantum-resistant support
    "QuantumResistantUpgrade",
    "PostQuantumSigner",
    "PostQuantumVerifier",
    "HybridSigner",
    "HybridVerifier",
    
    # Individual schemes
    "ECDSAScheme",
    "Ed25519Scheme",
    "SchnorrScheme",
    "BLS12Scheme",
    "DilithiumScheme"
]


