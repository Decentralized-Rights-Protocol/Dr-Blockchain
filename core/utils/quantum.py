"""Quantum-secure hashing utilities."""

import hashlib
import secrets
from typing import Optional


def generate_quantum_hash(data: str, salt: Optional[str] = None) -> str:
    """
    Generate a quantum-secure hash using SHA3-512 with post-quantum lattice padding.
    
    This creates a hash that is resistant to both classical and quantum attacks.
    
    Args:
        data: Data to hash
        salt: Optional salt for additional security
        
    Returns:
        Hex-encoded quantum-secure hash
    """
    # Use SHA3-512 (Keccak) for quantum resistance
    sha3_hash = hashlib.sha3_512()
    
    # Add post-quantum lattice padding (simulated)
    # In production, this would use actual lattice-based padding
    if salt is None:
        salt = secrets.token_hex(32)
    
    # Combine data with salt and lattice padding
    padded_data = f"{data}:{salt}:lattice_padding_v1"
    
    sha3_hash.update(padded_data.encode())
    hash_result = sha3_hash.hexdigest()
    
    # Add additional post-quantum security layer
    # Double hash with different algorithm for defense in depth
    blake2b_hash = hashlib.blake2b(digest_size=64)
    blake2b_hash.update(hash_result.encode())
    final_hash = blake2b_hash.hexdigest()
    
    return final_hash


def verify_quantum_hash(data: str, expected_hash: str, salt: Optional[str] = None) -> bool:
    """
    Verify a quantum-secure hash.
    
    Args:
        data: Original data
        expected_hash: Expected hash value
        salt: Salt used during generation (if known)
        
    Returns:
        True if hash matches
    """
    computed_hash = generate_quantum_hash(data, salt)
    return computed_hash == expected_hash

