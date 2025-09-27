"""
Multi-Scheme Cryptographic Support

This module provides a unified interface for multiple cryptographic schemes
used in cross-chain interoperability.
"""

import hashlib
import time
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Any
from abc import ABC, abstractmethod


class CryptoScheme(Enum):
    """Supported cryptographic schemes"""
    ECDSA_SECP256K1 = "ecdsa_secp256k1"  # Bitcoin, Ethereum
    ECDSA_SECP256R1 = "ecdsa_secp256r1"  # NIST P-256
    ED25519 = "ed25519"                  # High-performance curves
    SCHNORR = "schnorr"                  # Bitcoin Taproot
    BLS12_381 = "bls12_381"              # Aggregate signatures
    DILITHIUM2 = "dilithium2"            # Quantum-resistant
    DILITHIUM3 = "dilithium3"            # Quantum-resistant
    FALCON512 = "falcon512"              # Quantum-resistant
    SPHINCS_PLUS = "sphincs_plus"        # Quantum-resistant


@dataclass
class SignatureResult:
    """Result of a signature operation"""
    signature: bytes
    scheme: CryptoScheme
    public_key: bytes
    signature_id: str
    timestamp: float
    metadata: Dict[str, Any]


@dataclass
class VerificationResult:
    """Result of a verification operation"""
    is_valid: bool
    scheme: CryptoScheme
    public_key: bytes
    signature_id: str
    verification_timestamp: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class ISignatureScheme(ABC):
    """Abstract interface for signature schemes"""
    
    @abstractmethod
    async def generate_keypair(self) -> tuple[bytes, bytes]:
        """Generate a key pair (private_key, public_key)"""
        pass
    
    @abstractmethod
    async def sign(self, message: bytes, private_key: bytes) -> bytes:
        """Sign a message with private key"""
        pass
    
    @abstractmethod
    async def verify(self, message: bytes, signature: bytes, 
                    public_key: bytes) -> bool:
        """Verify a signature"""
        pass
    
    @abstractmethod
    async def get_scheme_info(self) -> Dict[str, Any]:
        """Get information about the signature scheme"""
        pass


class MultiSchemeSigner:
    """
    Multi-scheme signer for cross-chain interoperability
    
    This class provides a unified interface for signing transactions
    using different cryptographic schemes based on the target blockchain.
    """
    
    def __init__(self):
        self.schemes: Dict[CryptoScheme, ISignatureScheme] = {}
        self.default_scheme = CryptoScheme.ECDSA_SECP256K1
        self.quantum_resistant_schemes = {
            CryptoScheme.DILITHIUM2,
            CryptoScheme.DILITHIUM3,
            CryptoScheme.FALCON512,
            CryptoScheme.SPHINCS_PLUS
        }
    
    async def register_scheme(self, scheme: CryptoScheme, 
                            implementation: ISignatureScheme) -> bool:
        """Register a signature scheme implementation"""
        try:
            self.schemes[scheme] = implementation
            return True
        except Exception as e:
            print(f"Failed to register scheme {scheme}: {e}")
            return False
    
    async def sign_transaction(self, 
                             message: bytes,
                             private_key: bytes,
                             scheme: Optional[CryptoScheme] = None,
                             target_chain: Optional[str] = None) -> SignatureResult:
        """
        Sign a transaction using the appropriate scheme
        
        Args:
            message: Transaction data to sign
            private_key: Private key for signing
            scheme: Specific scheme to use (auto-detect if None)
            target_chain: Target blockchain (for scheme selection)
            
        Returns:
            SignatureResult with signature and metadata
            
        Raises:
            ValueError: If scheme is not supported
            RuntimeError: If signing fails
        """
        
        # Auto-detect scheme based on target chain
        if scheme is None:
            scheme = await self._detect_scheme_for_chain(target_chain)
        
        if scheme not in self.schemes:
            raise ValueError(f"Signature scheme {scheme} not registered")
        
        try:
            # Get signature scheme implementation
            signature_scheme = self.schemes[scheme]
            
            # Sign the message
            signature = await signature_scheme.sign(message, private_key)
            
            # Generate public key from private key (if needed)
            public_key = await self._derive_public_key(private_key, scheme)
            
            # Create signature result
            signature_id = self._generate_signature_id(signature, scheme)
            
            result = SignatureResult(
                signature=signature,
                scheme=scheme,
                public_key=public_key,
                signature_id=signature_id,
                timestamp=time.time(),
                metadata={
                    "target_chain": target_chain,
                    "message_hash": hashlib.sha256(message).hexdigest(),
                    "signature_size": len(signature),
                    "quantum_resistant": scheme in self.quantum_resistant_schemes
                }
            )
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Failed to sign transaction: {e}")
    
    async def _detect_scheme_for_chain(self, target_chain: Optional[str]) -> CryptoScheme:
        """Detect the appropriate signature scheme for a target chain"""
        
        if target_chain is None:
            return self.default_scheme
        
        # Chain-specific scheme mapping
        chain_schemes = {
            "bitcoin": CryptoScheme.SCHNORR,  # Taproot preferred
            "ethereum": CryptoScheme.ECDSA_SECP256K1,
            "polkadot": CryptoScheme.ED25519,
            "bsc": CryptoScheme.ECDSA_SECP256K1,
            "polygon": CryptoScheme.ECDSA_SECP256K1,
            "avalanche": CryptoScheme.ECDSA_SECP256K1,
            "arbitrum": CryptoScheme.ECDSA_SECP256K1,
            "optimism": CryptoScheme.ECDSA_SECP256K1,
            "drp": CryptoScheme.ED25519  # DRP uses Ed25519
        }
        
        return chain_schemes.get(target_chain.lower(), self.default_scheme)
    
    async def _derive_public_key(self, private_key: bytes, 
                               scheme: CryptoScheme) -> bytes:
        """Derive public key from private key"""
        
        if scheme not in self.schemes:
            raise ValueError(f"Scheme {scheme} not registered")
        
        signature_scheme = self.schemes[scheme]
        
        # For most schemes, we need to generate a keypair to get the public key
        # This is a simplified approach - in practice, you'd implement proper key derivation
        try:
            _, public_key = await signature_scheme.generate_keypair()
            return public_key
        except Exception:
            # Fallback: return the private key as public key (not secure, just for demo)
            return private_key
    
    def _generate_signature_id(self, signature: bytes, scheme: CryptoScheme) -> str:
        """Generate a unique signature ID"""
        signature_hash = hashlib.sha256(signature).hexdigest()[:16]
        return f"{scheme.value}_{signature_hash}_{int(time.time())}"


class MultiSchemeVerifier:
    """
    Multi-scheme verifier for cross-chain interoperability
    
    This class provides a unified interface for verifying signatures
    using different cryptographic schemes.
    """
    
    def __init__(self):
        self.schemes: Dict[CryptoScheme, ISignatureScheme] = {}
        self.verification_cache: Dict[str, VerificationResult] = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def register_scheme(self, scheme: CryptoScheme, 
                            implementation: ISignatureScheme) -> bool:
        """Register a signature scheme implementation"""
        try:
            self.schemes[scheme] = implementation
            return True
        except Exception as e:
            print(f"Failed to register scheme {scheme}: {e}")
            return False
    
    async def verify_signature(self, 
                             message: bytes,
                             signature: bytes,
                             public_key: bytes,
                             scheme: CryptoScheme,
                             signature_id: Optional[str] = None) -> VerificationResult:
        """
        Verify a signature using the specified scheme
        
        Args:
            message: Original message that was signed
            signature: Signature to verify
            public_key: Public key for verification
            scheme: Signature scheme used
            signature_id: Optional signature ID for caching
            
        Returns:
            VerificationResult with verification status and metadata
        """
        
        # Check cache first
        if signature_id and signature_id in self.verification_cache:
            cached_result = self.verification_cache[signature_id]
            if time.time() - cached_result.verification_timestamp < self.cache_ttl:
                return cached_result
        
        if scheme not in self.schemes:
            return VerificationResult(
                is_valid=False,
                scheme=scheme,
                public_key=public_key,
                signature_id=signature_id or "",
                verification_timestamp=time.time(),
                error_message=f"Scheme {scheme} not registered"
            )
        
        try:
            # Get signature scheme implementation
            signature_scheme = self.schemes[scheme]
            
            # Verify the signature
            is_valid = await signature_scheme.verify(message, signature, public_key)
            
            # Create verification result
            result = VerificationResult(
                is_valid=is_valid,
                scheme=scheme,
                public_key=public_key,
                signature_id=signature_id or "",
                verification_timestamp=time.time(),
                metadata={
                    "message_hash": hashlib.sha256(message).hexdigest(),
                    "signature_size": len(signature),
                    "public_key_size": len(public_key),
                    "quantum_resistant": scheme in {
                        CryptoScheme.DILITHIUM2,
                        CryptoScheme.DILITHIUM3,
                        CryptoScheme.FALCON512,
                        CryptoScheme.SPHINCS_PLUS
                    }
                }
            )
            
            # Cache the result
            if signature_id:
                self.verification_cache[signature_id] = result
            
            return result
            
        except Exception as e:
            return VerificationResult(
                is_valid=False,
                scheme=scheme,
                public_key=public_key,
                signature_id=signature_id or "",
                verification_timestamp=time.time(),
                error_message=f"Verification failed: {e}"
            )
    
    async def verify_cross_chain_signature(self, 
                                         message: bytes,
                                         signature_result: SignatureResult,
                                         source_chain: str,
                                         target_chain: str) -> VerificationResult:
        """
        Verify a cross-chain signature with chain-specific validation
        
        Args:
            message: Original message
            signature_result: Signature result from signing
            source_chain: Source blockchain
            target_chain: Target blockchain
            
        Returns:
            VerificationResult with cross-chain specific validation
        """
        
        # Basic signature verification
        basic_result = await self.verify_signature(
            message=message,
            signature=signature_result.signature,
            public_key=signature_result.public_key,
            scheme=signature_result.scheme,
            signature_id=signature_result.signature_id
        )
        
        if not basic_result.is_valid:
            return basic_result
        
        # Cross-chain specific validation
        cross_chain_valid = await self._validate_cross_chain_signature(
            signature_result, source_chain, target_chain
        )
        
        # Update result with cross-chain validation
        basic_result.metadata.update({
            "cross_chain_valid": cross_chain_valid,
            "source_chain": source_chain,
            "target_chain": target_chain,
            "chain_compatibility": await self._check_chain_compatibility(
                signature_result.scheme, source_chain, target_chain
            )
        })
        
        basic_result.is_valid = basic_result.is_valid and cross_chain_valid
        
        return basic_result
    
    async def _validate_cross_chain_signature(self, 
                                            signature_result: SignatureResult,
                                            source_chain: str,
                                            target_chain: str) -> bool:
        """Validate cross-chain specific signature requirements"""
        
        # Check if the signature scheme is compatible with both chains
        source_compatible = await self._is_scheme_compatible_with_chain(
            signature_result.scheme, source_chain
        )
        target_compatible = await self._is_scheme_compatible_with_chain(
            signature_result.scheme, target_chain
        )
        
        # Check signature size constraints
        size_valid = await self._check_signature_size_constraints(
            signature_result.signature, target_chain
        )
        
        # Check quantum resistance requirements
        quantum_valid = await self._check_quantum_resistance_requirements(
            signature_result.scheme, target_chain
        )
        
        return source_compatible and target_compatible and size_valid and quantum_valid
    
    async def _is_scheme_compatible_with_chain(self, 
                                             scheme: CryptoScheme, 
                                             chain: str) -> bool:
        """Check if a signature scheme is compatible with a blockchain"""
        
        chain_schemes = {
            "bitcoin": {CryptoScheme.SCHNORR, CryptoScheme.ECDSA_SECP256K1},
            "ethereum": {CryptoScheme.ECDSA_SECP256K1, CryptoScheme.ED25519},
            "polkadot": {CryptoScheme.ED25519, CryptoScheme.SR25519},
            "drp": {CryptoScheme.ED25519, CryptoScheme.DILITHIUM3}
        }
        
        supported_schemes = chain_schemes.get(chain.lower(), set())
        return scheme in supported_schemes
    
    async def _check_signature_size_constraints(self, 
                                              signature: bytes, 
                                              chain: str) -> bool:
        """Check if signature size is within chain constraints"""
        
        max_sizes = {
            "bitcoin": 64,  # Schnorr signature size
            "ethereum": 65,  # ECDSA signature size
            "polkadot": 64,  # Ed25519 signature size
            "drp": 4096  # Quantum-resistant signatures can be larger
        }
        
        max_size = max_sizes.get(chain.lower(), 128)
        return len(signature) <= max_size
    
    async def _check_quantum_resistance_requirements(self, 
                                                   scheme: CryptoScheme, 
                                                   chain: str) -> bool:
        """Check quantum resistance requirements for a chain"""
        
        # Future chains may require quantum resistance
        quantum_required_chains = {"drp", "future_quantum_chain"}
        
        if chain.lower() in quantum_required_chains:
            quantum_resistant_schemes = {
                CryptoScheme.DILITHIUM2,
                CryptoScheme.DILITHIUM3,
                CryptoScheme.FALCON512,
                CryptoScheme.SPHINCS_PLUS
            }
            return scheme in quantum_resistant_schemes
        
        return True  # No quantum resistance required
    
    async def _check_chain_compatibility(self, 
                                       scheme: CryptoScheme,
                                       source_chain: str,
                                       target_chain: str) -> Dict[str, bool]:
        """Check compatibility between chains for a signature scheme"""
        
        return {
            "source_compatible": await self._is_scheme_compatible_with_chain(
                scheme, source_chain
            ),
            "target_compatible": await self._is_scheme_compatible_with_chain(
                scheme, target_chain
            ),
            "cross_chain_supported": source_chain != target_chain
        }
    
    async def clear_verification_cache(self) -> int:
        """Clear expired verification cache entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, result in self.verification_cache.items():
            if current_time - result.verification_timestamp > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.verification_cache[key]
        
        return len(expired_keys)
    
    async def get_supported_schemes(self) -> List[CryptoScheme]:
        """Get list of supported signature schemes"""
        return list(self.schemes.keys())
    
    async def get_scheme_info(self, scheme: CryptoScheme) -> Optional[Dict[str, Any]]:
        """Get detailed information about a signature scheme"""
        if scheme not in self.schemes:
            return None
        
        signature_scheme = self.schemes[scheme]
        return await signature_scheme.get_scheme_info()


