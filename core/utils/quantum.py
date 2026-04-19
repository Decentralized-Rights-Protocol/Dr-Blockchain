"""
DRP Quantum-Resistant Hashing Utilities
========================================
Implements SHA3-512 + BLAKE2b hybrid hashing used throughout the system.
This is the module imported by ai/quantum_security.py.

Algorithm: SHA3-512(BLAKE2b(data + salt)) with lattice-inspired padding.
Quantum-resistant for collision and preimage attacks.
Upgrade path: swap for CRYSTALS-Dilithium via liboqs-python when available.
"""

import hashlib
import hmac
import secrets
from typing import Optional


def generate_quantum_hash(data: str, salt: Optional[str] = None) -> str:
    """
    Generate a quantum-resistant hash using SHA3-512 + BLAKE2b hybrid.

    Args:
        data: Input string to hash
        salt: Optional hex salt (64 chars). Auto-generated if None.

    Returns:
        Hex-encoded quantum hash string
    """
    if salt is None:
        salt = secrets.token_hex(32)

    # Layer 1: BLAKE2b with salt-derived key
    salt_bytes = bytes.fromhex(salt) if len(salt) == 64 else salt.encode()
    blake_key = hashlib.sha256(salt_bytes).digest()[:32]  # BLAKE2b key max 64B
    blake_hash = hashlib.blake2b(
        data.encode("utf-8"),
        key=blake_key,
        digest_size=64,
    ).digest()

    # Layer 2: SHA3-512 over the BLAKE2b output + lattice padding
    lattice_pad = _lattice_padding(salt_bytes)
    sha3_input = blake_hash + lattice_pad
    quantum_hash = hashlib.sha3_512(sha3_input).hexdigest()

    return quantum_hash


def verify_quantum_hash(
    data: str,
    expected_hash: str,
    salt: Optional[str] = None,
) -> bool:
    """
    Verify a quantum-resistant hash using constant-time comparison.

    Args:
        data: Original input string
        expected_hash: Previously generated quantum hash
        salt: Salt used during generation

    Returns:
        True if hash matches
    """
    if not expected_hash or not data:
        return False

    try:
        recomputed = generate_quantum_hash(data, salt)
        return hmac.compare_digest(recomputed, expected_hash)
    except Exception:
        return False


def generate_proof_bundle(
    activity_id: str,
    user_id: str,
    payload: str,
) -> dict:
    """
    Generate a full quantum-secure proof bundle for a PoAT/PoST record.

    Returns dict with: quantum_hash, salt, algorithm, integrity_check
    """
    salt = secrets.token_hex(32)
    combined = f"{activity_id}:{user_id}:{payload}"
    q_hash = generate_quantum_hash(combined, salt)

    # Integrity check: SHA3-256 of the quantum hash itself
    integrity = hashlib.sha3_256(q_hash.encode()).hexdigest()

    return {
        "quantum_hash": q_hash,
        "salt": salt,
        "algorithm": "SHA3-512+BLAKE2b+LatticePadding",
        "integrity_check": integrity,
    }


def _lattice_padding(salt_bytes: bytes) -> bytes:
    """
    Lattice-inspired deterministic padding.
    Derives structured noise from the salt to resist lattice attacks.
    Not a full lattice scheme — acts as computational padding for now.
    Upgrade: replace with actual NTRU/Kyber output when liboqs available.
    """
    # Use salt to seed a deterministic pseudo-noise sequence
    seed = hashlib.sha3_256(salt_bytes).digest()
    pad = bytearray()
    for i in range(8):
        block = hashlib.sha3_256(seed + i.to_bytes(1, "big")).digest()
        pad.extend(block)
    return bytes(pad[:64])  # 64-byte lattice pad
