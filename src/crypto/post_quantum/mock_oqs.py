"""
Mock implementation of liboqs for Python 3.8 compatibility

This provides a mock implementation of the oqs library for demonstration
purposes when the real liboqs is not available.
"""

import secrets
import hashlib
from typing import Dict, Any


class MockKeyEncapsulation:
    """Mock CRYSTALS-Kyber key encapsulation"""
    
    def __init__(self, algorithm: str):
        self.algorithm = algorithm
    
    def generate_keypair(self) -> bytes:
        """Generate mock public key"""
        return secrets.token_bytes(1568)  # Kyber-768 public key size
    
    def export_secret_key(self) -> bytes:
        """Export mock private key"""
        return secrets.token_bytes(2400)  # Kyber-768 private key size
    
    def import_secret_key(self, key: bytes):
        """Import mock private key"""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass


class MockSignature:
    """Mock CRYSTALS-Dilithium signature"""
    
    def __init__(self, algorithm: str):
        self.algorithm = algorithm
    
    def generate_keypair(self) -> bytes:
        """Generate mock public key"""
        return secrets.token_bytes(1952)  # Dilithium3 public key size
    
    def export_secret_key(self) -> bytes:
        """Export mock private key"""
        return secrets.token_bytes(4000)  # Dilithium3 private key size
    
    def import_secret_key(self, key: bytes):
        """Import mock private key"""
        pass
    
    def import_public_key(self, key: bytes):
        """Import mock public key"""
        pass
    
    def sign(self, message: bytes) -> bytes:
        """Generate mock signature"""
        # Create deterministic mock signature based on message
        sig_data = hashlib.sha256(message + b"mock_signature").digest()
        return sig_data + secrets.token_bytes(3293 - 32)  # Dilithium3 signature size
    
    def verify(self, message: bytes, signature: bytes) -> bool:
        """Verify mock signature"""
        # Mock verification - always returns True for demo
        return len(signature) >= 3293  # Check minimum signature size
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass


# Mock oqs module
class MockOQS:
    """Mock oqs module"""
    
    @staticmethod
    def KeyEncapsulation(algorithm: str) -> MockKeyEncapsulation:
        return MockKeyEncapsulation(algorithm)
    
    @staticmethod
    def Signature(algorithm: str) -> MockSignature:
        return MockSignature(algorithm)


# Replace oqs import
try:
    import oqs
    print("✅ Real liboqs available - using actual post-quantum crypto")
except ImportError:
    print("⚠️  liboqs not available - using mock implementation for demo")
    oqs = MockOQS()
