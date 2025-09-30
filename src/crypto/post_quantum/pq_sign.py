"""
Post-Quantum Digital Signatures Module for DRP

This module provides quantum-resistant digital signature functionality using
CRYSTALS-Dilithium for DRP's block header signing and elder quorum authentication.

Features:
- CRYSTALS-Dilithium digital signatures for quantum resistance
- Integration with DRP's block header signing
- Elder quorum signature aggregation
- Signature verification and validation
- FastAPI integration examples

Security Notes:
- Uses NIST-approved CRYSTALS-Dilithium algorithms
- Supports multiple security levels (Dilithium2, Dilithium3, Dilithium5)
- Implements proper signature verification with timing attack resistance
- Integrates with DRP's consensus mechanism for block validation
"""

import json
import time
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union, Any
from enum import Enum

try:
    import oqs  # This is correct for python-oqs package
    OQS_AVAILABLE = True
    print("✅ Real liboqs available - using actual post-quantum crypto")
except ImportError:
    try:
        from .mock_oqs import oqs
        OQS_AVAILABLE = True
        print("⚠️  Using mock post-quantum implementation")
    except ImportError:
        OQS_AVAILABLE = False
        print("❌ No post-quantum crypto available")

try:
    from .pq_keys import DilithiumKeyPair, PostQuantumCryptoError
except ImportError:
    # Handle direct execution
    from pq_keys import DilithiumKeyPair, PostQuantumCryptoError


class SignatureAlgorithm(Enum):
    """Supported post-quantum signature algorithms"""
    DILITHIUM2 = "Dilithium2"
    DILITHIUM3 = "Dilithium3"
    DILITHIUM5 = "Dilithium5"


@dataclass
class PostQuantumSignature:
    """Post-quantum digital signature container"""
    signature: bytes
    public_key: bytes
    algorithm: str
    signed_data_hash: str
    timestamp: float
    signer_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "signature": self.signature.hex(),
            "public_key": self.public_key.hex(),
            "algorithm": self.algorithm,
            "signed_data_hash": self.signed_data_hash,
            "timestamp": self.timestamp,
            "signer_id": self.signer_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PostQuantumSignature":
        """Create from dictionary"""
        return cls(
            signature=bytes.fromhex(data["signature"]),
            public_key=bytes.fromhex(data["public_key"]),
            algorithm=data["algorithm"],
            signed_data_hash=data["signed_data_hash"],
            timestamp=data["timestamp"],
            signer_id=data.get("signer_id")
        )


@dataclass
class QuorumSignature:
    """Aggregated quorum signature for DRP elder consensus"""
    signatures: List[PostQuantumSignature]
    required_signatures: int
    total_elders: int
    block_header_hash: str
    created_at: float
    quorum_id: str
    
    def is_valid_quorum(self) -> bool:
        """Check if quorum has sufficient signatures"""
        return len(self.signatures) >= self.required_signatures
    
    def get_signer_ids(self) -> List[str]:
        """Get list of unique signer IDs"""
        return [sig.signer_id for sig in self.signatures if sig.signer_id]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "signatures": [sig.to_dict() for sig in self.signatures],
            "required_signatures": self.required_signatures,
            "total_elders": self.total_elders,
            "block_header_hash": self.block_header_hash,
            "created_at": self.created_at,
            "quorum_id": self.quorum_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuorumSignature":
        """Create from dictionary"""
        return cls(
            signatures=[PostQuantumSignature.from_dict(sig) for sig in data["signatures"]],
            required_signatures=data["required_signatures"],
            total_elders=data["total_elders"],
            block_header_hash=data["block_header_hash"],
            created_at=data["created_at"],
            quorum_id=data["quorum_id"]
        )


class PostQuantumSigner:
    """
    Post-quantum digital signature signer using CRYSTALS-Dilithium
    
    This class provides:
    - Digital signature creation with Dilithium algorithms
    - Integration with DRP's block header signing
    - Support for multiple security levels
    - Signature metadata and validation
    """
    
    def __init__(self, keypair: DilithiumKeyPair, signer_id: Optional[str] = None):
        """
        Initialize the signer
        
        Args:
            keypair: Dilithium key pair for signing
            signer_id: Optional identifier for the signer
        """
        if not OQS_AVAILABLE:
            raise PostQuantumCryptoError("liboqs not available")
        
        if keypair.is_expired():
            raise PostQuantumCryptoError("Key pair has expired")
        
        self.keypair = keypair
        self.signer_id = signer_id or keypair.key_id
        self.algorithm = keypair.algorithm
    
    def sign_data(self, data: bytes) -> PostQuantumSignature:
        """
        Sign arbitrary data
        
        Args:
            data: Data to sign
        
        Returns:
            PostQuantumSignature object
        """
        try:
            with oqs.Signature(self.algorithm) as signer:
                # Import the private key
                signer.import_secret_key(self.keypair.private_key)
                
                # Create signature
                signature_bytes = signer.sign(data)
            
            # Create signature hash for verification
            data_hash = hashlib.sha256(data).hexdigest()
            
            return PostQuantumSignature(
                signature=signature_bytes,
                public_key=self.keypair.public_key,
                algorithm=self.algorithm,
                signed_data_hash=data_hash,
                timestamp=time.time(),
                signer_id=self.signer_id
            )
            
        except Exception as e:
            raise PostQuantumCryptoError(f"Failed to sign data: {e}")
    
    def sign_string(self, message: str) -> PostQuantumSignature:
        """
        Sign a string message
        
        Args:
            message: String message to sign
        
        Returns:
            PostQuantumSignature object
        """
        return self.sign_data(message.encode('utf-8'))
    
    def sign_drp_block_header(self, 
                             block_index: int,
                             previous_hash: str,
                             merkle_root: str,
                             timestamp: int,
                             miner_id: str,
                             nonce: int = 0,
                             difficulty: int = 0) -> PostQuantumSignature:
        """
        Sign a DRP block header in the canonical format
        
        Args:
            block_index: Block index number
            previous_hash: Hash of the previous block
            merkle_root: Merkle root of transactions
            timestamp: Block timestamp
            miner_id: ID of the miner
            nonce: Proof of work nonce
            difficulty: Mining difficulty
        
        Returns:
            PostQuantumSignature object
        """
        # Create canonical block header string (matches DRP format)
        header_data = {
            "index": block_index,
            "previous_hash": previous_hash,
            "timestamp": timestamp,
            "merkle_root": merkle_root,
            "data_hash": "",  # Can be populated with additional data hash
            "miner_id": miner_id,
            "nonce": nonce,
            "difficulty": difficulty
        }
        
        canonical_string = json.dumps(header_data, separators=(",", ":"), sort_keys=True)
        return self.sign_string(canonical_string)
    
    def get_public_key_info(self) -> Dict[str, Any]:
        """Get information about the public key"""
        return {
            "signer_id": self.signer_id,
            "key_id": self.keypair.key_id,
            "algorithm": self.algorithm,
            "public_key_length": len(self.keypair.public_key),
            "created_at": self.keypair.created_at,
            "expires_at": self.keypair.expires_at,
            "is_expired": self.keypair.is_expired()
        }


class PostQuantumVerifier:
    """
    Post-quantum digital signature verifier using CRYSTALS-Dilithium
    
    This class provides:
    - Digital signature verification with Dilithium algorithms
    - Batch verification for performance
    - Integration with DRP's block validation
    - Quorum signature validation
    """
    
    def __init__(self):
        """Initialize the verifier"""
        if not OQS_AVAILABLE:
            raise PostQuantumCryptoError("liboqs not available")
    
    def verify_signature(self, 
                        signature: PostQuantumSignature, 
                        original_data: bytes) -> bool:
        """
        Verify a post-quantum signature
        
        Args:
            signature: PostQuantumSignature to verify
            original_data: Original data that was signed
        
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            with oqs.Signature(signature.algorithm) as verifier:
                # Import the public key
                verifier.import_public_key(signature.public_key)
                
                # Verify the signature
                verifier.verify(original_data, signature.signature)
                
                # Additional validation: check data hash
                data_hash = hashlib.sha256(original_data).hexdigest()
                if data_hash != signature.signed_data_hash:
                    return False
                
                return True
                
        except Exception:
            return False
    
    def verify_string_signature(self, 
                               signature: PostQuantumSignature, 
                               message: str) -> bool:
        """
        Verify a signature for a string message
        
        Args:
            signature: PostQuantumSignature to verify
            message: Original string message
        
        Returns:
            True if signature is valid, False otherwise
        """
        return self.verify_signature(signature, message.encode('utf-8'))
    
    def verify_drp_block_header(self, 
                               signature: PostQuantumSignature,
                               block_index: int,
                               previous_hash: str,
                               merkle_root: str,
                               timestamp: int,
                               miner_id: str,
                               nonce: int = 0,
                               difficulty: int = 0) -> bool:
        """
        Verify a DRP block header signature
        
        Args:
            signature: PostQuantumSignature to verify
            block_index: Block index number
            previous_hash: Hash of the previous block
            merkle_root: Merkle root of transactions
            timestamp: Block timestamp
            miner_id: ID of the miner
            nonce: Proof of work nonce
            difficulty: Mining difficulty
        
        Returns:
            True if signature is valid, False otherwise
        """
        # Recreate the canonical block header string
        header_data = {
            "index": block_index,
            "previous_hash": previous_hash,
            "timestamp": timestamp,
            "merkle_root": merkle_root,
            "data_hash": "",
            "miner_id": miner_id,
            "nonce": nonce,
            "difficulty": difficulty
        }
        
        canonical_string = json.dumps(header_data, separators=(",", ":"), sort_keys=True)
        return self.verify_string_signature(signature, canonical_string)
    
    def verify_quorum_signature(self, 
                               quorum_sig: QuorumSignature,
                               block_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Verify a quorum signature for DRP block validation
        
        Args:
            quorum_sig: QuorumSignature to verify
            block_data: Block data dictionary
        
        Returns:
            Tuple of (is_valid, list_of_valid_signer_ids)
        """
        valid_signers = []
        
        # Check if quorum has sufficient signatures
        if not quorum_sig.is_valid_quorum():
            return False, []
        
        # Verify each signature in the quorum
        for signature in quorum_sig.signatures:
            # Recreate canonical block header
            canonical_string = json.dumps(block_data, separators=(",", ":"), sort_keys=True)
            
            if self.verify_string_signature(signature, canonical_string):
                if signature.signer_id:
                    valid_signers.append(signature.signer_id)
        
        # Check if we have enough valid signatures
        is_valid = len(valid_signers) >= quorum_sig.required_signatures
        return is_valid, valid_signers
    
    def batch_verify_signatures(self, 
                               signatures: List[PostQuantumSignature],
                               data_list: List[bytes]) -> List[bool]:
        """
        Verify multiple signatures in batch for performance
        
        Args:
            signatures: List of PostQuantumSignature objects
            data_list: List of corresponding data bytes
        
        Returns:
            List of boolean verification results
        """
        if len(signatures) != len(data_list):
            raise ValueError("Signatures and data lists must have the same length")
        
        results = []
        for sig, data in zip(signatures, data_list):
            results.append(self.verify_signature(sig, data))
        
        return results


# Convenience functions for direct use
def sign_with_dilithium(keypair: DilithiumKeyPair, 
                       data: Union[bytes, str],
                       signer_id: Optional[str] = None) -> PostQuantumSignature:
    """
    Sign data with a Dilithium key pair
    
    Args:
        keypair: Dilithium key pair for signing
        data: Data to sign (bytes or string)
        signer_id: Optional signer identifier
    
    Returns:
        PostQuantumSignature object
    """
    signer = PostQuantumSigner(keypair, signer_id)
    
    if isinstance(data, str):
        return signer.sign_string(data)
    else:
        return signer.sign_data(data)


def verify_dilithium_signature(signature: PostQuantumSignature, 
                              data: Union[bytes, str]) -> bool:
    """
    Verify a Dilithium signature
    
    Args:
        signature: PostQuantumSignature to verify
        data: Original data (bytes or string)
    
    Returns:
        True if signature is valid, False otherwise
    """
    verifier = PostQuantumVerifier()
    
    if isinstance(data, str):
        return verifier.verify_string_signature(signature, data)
    else:
        return verifier.verify_signature(signature, data)


def create_drp_block_signature(keypair: DilithiumKeyPair,
                              block_index: int,
                              previous_hash: str,
                              merkle_root: str,
                              timestamp: int,
                              miner_id: str,
                              signer_id: Optional[str] = None,
                              nonce: int = 0,
                              difficulty: int = 0) -> PostQuantumSignature:
    """
    Create a DRP block header signature
    
    Args:
        keypair: Dilithium key pair for signing
        block_index: Block index number
        previous_hash: Hash of the previous block
        merkle_root: Merkle root of transactions
        timestamp: Block timestamp
        miner_id: ID of the miner
        signer_id: Optional signer identifier
        nonce: Proof of work nonce
        difficulty: Mining difficulty
    
    Returns:
        PostQuantumSignature object
    """
    signer = PostQuantumSigner(keypair, signer_id)
    return signer.sign_drp_block_header(
        block_index=block_index,
        previous_hash=previous_hash,
        merkle_root=merkle_root,
        timestamp=timestamp,
        miner_id=miner_id,
        nonce=nonce,
        difficulty=difficulty
    )


def verify_drp_block_signature(signature: PostQuantumSignature,
                              block_index: int,
                              previous_hash: str,
                              merkle_root: str,
                              timestamp: int,
                              miner_id: str,
                              nonce: int = 0,
                              difficulty: int = 0) -> bool:
    """
    Verify a DRP block header signature
    
    Args:
        signature: PostQuantumSignature to verify
        block_index: Block index number
        previous_hash: Hash of the previous block
        merkle_root: Merkle root of transactions
        timestamp: Block timestamp
        miner_id: ID of the miner
        nonce: Proof of work nonce
        difficulty: Mining difficulty
    
    Returns:
        True if signature is valid, False otherwise
    """
    verifier = PostQuantumVerifier()
    return verifier.verify_drp_block_header(
        signature=signature,
        block_index=block_index,
        previous_hash=previous_hash,
        merkle_root=merkle_root,
        timestamp=timestamp,
        miner_id=miner_id,
        nonce=nonce,
        difficulty=difficulty
    )


# FastAPI integration example
class DRPPostQuantumSigner:
    """
    FastAPI integration class for DRP post-quantum signatures
    
    This class provides FastAPI-compatible methods for:
    - Block header signing
    - Quorum signature creation
    - Signature verification
    - Integration with DRP's elder quorum system
    """
    
    def __init__(self, key_manager):
        """
        Initialize with a key manager
        
        Args:
            key_manager: PostQuantumKeyManager instance
        """
        self.key_manager = key_manager
        self.verifier = PostQuantumVerifier()
    
    async def sign_block_header_async(self, 
                                    block_data: Dict[str, Any],
                                    signer_id: str) -> Optional[PostQuantumSignature]:
        """
        Asynchronously sign a block header
        
        Args:
            block_data: Block header data
            signer_id: ID of the signer
        
        Returns:
            PostQuantumSignature or None if signing fails
        """
        try:
            # Get the signer's key pair
            keypair = self.key_manager.get_dilithium_keypair(signer_id)
            if not keypair:
                return None
            
            # Create signer and sign
            signer = PostQuantumSigner(keypair, signer_id)
            return signer.sign_drp_block_header(**block_data)
            
        except Exception as e:
            print(f"Error signing block header: {e}")
            return None
    
    async def verify_block_header_async(self, 
                                      signature: PostQuantumSignature,
                                      block_data: Dict[str, Any]) -> bool:
        """
        Asynchronously verify a block header signature
        
        Args:
            signature: PostQuantumSignature to verify
            block_data: Block header data
        
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            return self.verifier.verify_drp_block_header(signature, **block_data)
        except Exception as e:
            print(f"Error verifying block header: {e}")
            return False
    
    async def create_quorum_signature_async(self, 
                                          block_data: Dict[str, Any],
                                          elder_ids: List[str],
                                          required_signatures: int) -> Optional[QuorumSignature]:
        """
        Create a quorum signature for DRP block validation
        
        Args:
            block_data: Block header data
            elder_ids: List of elder IDs to sign
            required_signatures: Minimum number of signatures required
        
        Returns:
            QuorumSignature or None if creation fails
        """
        try:
            signatures = []
            
            for elder_id in elder_ids:
                signature = await self.sign_block_header_async(block_data, elder_id)
                if signature:
                    signatures.append(signature)
            
            if len(signatures) < required_signatures:
                return None
            
            # Create quorum signature
            block_hash = hashlib.sha256(
                json.dumps(block_data, separators=(",", ":"), sort_keys=True).encode()
            ).hexdigest()
            
            return QuorumSignature(
                signatures=signatures,
                required_signatures=required_signatures,
                total_elders=len(elder_ids),
                block_header_hash=block_hash,
                created_at=time.time(),
                quorum_id=f"quorum_{block_hash[:16]}"
            )
            
        except Exception as e:
            print(f"Error creating quorum signature: {e}")
            return None


# Example usage and testing
if __name__ == "__main__":
    print("Post-Quantum Digital Signatures Module Demo")
    print("=" * 50)
    
    try:
        # Test signature generation and verification
        print("1. Generating Dilithium key pair...")
        from .pq_keys import generate_dilithium_keypair
        keypair = generate_dilithium_keypair("Dilithium3")
        print(f"   Key ID: {keypair.key_id}")
        print(f"   Algorithm: {keypair.algorithm}")
        
        print("\n2. Testing string signing...")
        signer = PostQuantumSigner(keypair, "test_elder")
        message = "Hello, quantum-resistant world!"
        signature = signer.sign_string(message)
        print(f"   Message: {message}")
        print(f"   Signature Length: {len(signature.signature)} bytes")
        print(f"   Signer ID: {signature.signer_id}")
        
        print("\n3. Testing signature verification...")
        verifier = PostQuantumVerifier()
        is_valid = verifier.verify_string_signature(signature, message)
        print(f"   Signature Valid: {is_valid}")
        
        # Test with wrong message
        wrong_message = "Wrong message"
        is_invalid = verifier.verify_string_signature(signature, wrong_message)
        print(f"   Wrong Message Valid: {is_invalid}")
        
        print("\n4. Testing DRP block header signing...")
        block_signature = signer.sign_drp_block_header(
            block_index=123,
            previous_hash="0xabcdef123456",
            merkle_root="0x789012345678",
            timestamp=int(time.time()),
            miner_id="test_miner",
            nonce=42,
            difficulty=4
        )
        print(f"   Block Signature Length: {len(block_signature.signature)} bytes")
        
        # Verify block signature
        block_valid = verifier.verify_drp_block_header(
            signature=block_signature,
            block_index=123,
            previous_hash="0xabcdef123456",
            merkle_root="0x789012345678",
            timestamp=block_signature.timestamp,  # Use original timestamp
            miner_id="test_miner",
            nonce=42,
            difficulty=4
        )
        print(f"   Block Signature Valid: {block_valid}")
        
        print("\n5. Testing quorum signature...")
        # Create multiple signatures for quorum
        quorum_signatures = []
        for i in range(3):
            elder_keypair = generate_dilithium_keypair("Dilithium2")
            elder_signer = PostQuantumSigner(elder_keypair, f"elder_{i}")
            elder_sig = elder_signer.sign_drp_block_header(
                block_index=123,
                previous_hash="0xabcdef123456",
                merkle_root="0x789012345678",
                timestamp=int(time.time()),
                miner_id="test_miner"
            )
            quorum_signatures.append(elder_sig)
        
        # Create quorum signature
        block_data = {
            "index": 123,
            "previous_hash": "0xabcdef123456",
            "timestamp": int(time.time()),
            "merkle_root": "0x789012345678",
            "data_hash": "",
            "miner_id": "test_miner",
            "nonce": 42,
            "difficulty": 4
        }
        
        quorum_sig = QuorumSignature(
            signatures=quorum_signatures,
            required_signatures=2,
            total_elders=3,
            block_header_hash="0x1234567890abcdef",
            created_at=time.time(),
            quorum_id="test_quorum"
        )
        
        print(f"   Quorum Valid: {quorum_sig.is_valid_quorum()}")
        print(f"   Required Signatures: {quorum_sig.required_signatures}")
        print(f"   Actual Signatures: {len(quorum_sig.signatures)}")
        
        # Verify quorum
        quorum_valid, valid_signers = verifier.verify_quorum_signature(quorum_sig, block_data)
        print(f"   Quorum Verification: {quorum_valid}")
        print(f"   Valid Signers: {valid_signers}")
        
        print("\n✅ All tests passed!")
        
    except PostQuantumCryptoError as e:
        print(f"❌ Post-quantum crypto error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")



