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
            # Derive key from settings
            key = base64.urlsafe_b64encode(key_str.encode()[:32].ljust(32, b'0'))
    
    f = Fernet(key)
    encrypted = f.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


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
        key = base64.urlsafe_b64encode(key_str.encode()[:32].ljust(32, b'0'))
    
    f = Fernet(key)
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
    decrypted = f.decrypt(encrypted_bytes)
    return decrypted.decode()

