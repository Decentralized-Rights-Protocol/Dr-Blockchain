"""
Post-Quantum Security Module for DRP (Decentralized Rights Protocol)

This module provides quantum-resistant cryptographic primitives to protect DRP
against future quantum computing attacks. It implements:

- CRYSTALS-Kyber: Post-quantum key encapsulation mechanism (KEM)
- CRYSTALS-Dilithium: Post-quantum digital signature scheme
- Key management utilities for rotation, storage, and revocation
- Integration helpers for DRP's consensus and elder quorum systems

The implementation is designed to be:
- Future-proof against quantum attacks
- Compatible with existing DRP infrastructure
- Modular for easy integration and testing
- Secure with proper key management practices

Author: DRP Development Team
License: See LICENSE file
"""

from .pq_keys import (
    PostQuantumKeyManager,
    KyberKeyPair,
    DilithiumKeyPair,
    KeyRotationManager,
    KeyRevocationManager,
    generate_kyber_keypair,
    generate_dilithium_keypair,
    PostQuantumCryptoError
)

from .pq_sign import (
    PostQuantumSigner,
    PostQuantumVerifier,
    sign_with_dilithium,
    verify_dilithium_signature,
    create_drp_block_signature,
    verify_drp_block_signature
)

from .drp_integration import (
    DRPPostQuantumElderQuorum,
    DRPElder,
    DRPPostQuantumAPI
)

__version__ = "1.0.0"
__all__ = [
    # Key management
    "PostQuantumKeyManager",
    "KyberKeyPair", 
    "DilithiumKeyPair",
    "KeyRotationManager",
    "KeyRevocationManager",
    "generate_kyber_keypair",
    "generate_dilithium_keypair",
    "PostQuantumCryptoError",
    
    # Signing and verification
    "PostQuantumSigner",
    "PostQuantumVerifier", 
    "sign_with_dilithium",
    "verify_dilithium_signature",
    "create_drp_block_signature",
    "verify_drp_block_signature",
    
    # DRP integration
    "DRPPostQuantumElderQuorum",
    "DRPElder",
    "DRPPostQuantumAPI"
]



