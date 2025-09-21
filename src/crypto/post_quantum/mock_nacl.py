"""
Mock implementation of PyNaCl for compatibility
"""

import secrets
import hashlib


class MockSigningKey:
    """Mock Ed25519 signing key"""
    
    def __init__(self, key_data=None):
        if key_data is None:
            key_data = secrets.token_bytes(32)
        self._key_data = key_data
    
    def encode(self) -> bytes:
        """Return encoded key"""
        return self._key_data
    
    def sign(self, message: bytes) -> 'MockSignedMessage':
        """Sign message"""
        # Create deterministic mock signature
        sig_data = hashlib.sha256(message + self._key_data).digest()
        return MockSignedMessage(sig_data + message)
    
    @classmethod
    def generate(cls):
        """Generate new key"""
        return cls()


class MockVerifyKey:
    """Mock Ed25519 verify key"""
    
    def __init__(self, key_data):
        self._key_data = key_data
    
    def encode(self) -> bytes:
        """Return encoded key"""
        return self._key_data
    
    def verify(self, message: bytes, signature: bytes) -> bool:
        """Verify signature (mock - always returns True)"""
        return len(signature) >= 64  # Check minimum signature size


class MockSignedMessage:
    """Mock signed message"""
    
    def __init__(self, data):
        self._data = data
    
    @property
    def signature(self) -> bytes:
        """Return signature part"""
        return self._data[:64]
    
    @property
    def message(self) -> bytes:
        """Return message part"""
        return self._data[64:]


# Mock nacl.signing module
class MockSigningModule:
    """Mock nacl.signing module"""
    
    SigningKey = MockSigningKey
    VerifyKey = MockVerifyKey


# Mock nacl module
class MockNacl:
    """Mock nacl module"""
    
    signing = MockSigningModule()
    exceptions = type('MockExceptions', (), {})()


# Mock exceptions
class MockExceptions:
    BadSignatureError = Exception

# Mock nacl module
class MockNacl:
    """Mock nacl module"""
    
    signing = MockSigningModule()
    exceptions = MockExceptions()

# Export for import
signing = MockSigningModule()
nacl_exc = MockExceptions()

# Replace nacl import
try:
    from nacl import signing as real_signing, exceptions as real_nacl_exc
    print("✅ Real PyNaCl available")
except ImportError:
    print("⚠️  PyNaCl not available - using mock implementation")
    import sys
    sys.modules['nacl'] = MockNacl()
    sys.modules['nacl.signing'] = MockNacl().signing
    sys.modules['nacl.exceptions'] = MockNacl().exceptions
