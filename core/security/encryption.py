"""Data encryption utilities."""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import secrets
from typing import Optional
from config import get_settings


def generate_encryption_key(password: Optional[str] = None) -> bytes:
    """
    Generate an encryption key.
    
    Args:
        password: Optional password for key derivation
        
    Returns:
        Encryption key bytes
    """
    if password:
        # Derive key from password
        salt = secrets.token_bytes(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    else:
        # Generate random key
        return Fernet.generate_key()


def derive_key(key_str: str) -> bytes:
    """Derive a secure key from a string using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'static_salt',  # In production, use a unique salt per key/user
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(key_str.encode()))


def encrypt_data(data: str, key: Optional[bytes] = None) -> str:
    """
    Encrypt data using Fernet symmetric encryption.
    
    Args:
        data: Data to encrypt
        key: Encryption key (uses settings default if not provided)
        
    Returns:
        Encrypted data as base64 string
    """
    if key is None:
        settings = get_settings()
        # Use encryption key from settings
        key_str = settings.encryption_key
        if not key_str:
            key = generate_encryption_key()
        else:
            key = derive_key(key_str)
    
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str, key: Optional[bytes] = None) -> str:
    """
    Decrypt data using Fernet symmetric encryption.
    
    Args:
        encrypted_data: Encrypted data as base64 string
        key: Decryption key (uses settings default if not provided)
        
    Returns:
        Decrypted data
    """
    if key is None:
        settings = get_settings()
        key_str = settings.encryption_key
        if not key_str:
            raise ValueError("No encryption key available")
        key = derive_key(key_str)
    
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()

