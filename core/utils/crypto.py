"""Cryptographic utilities."""

import hashlib
import secrets
from typing import Tuple, Optional
from eth_keys import keys
from eth_utils import to_checksum_address


def generate_wallet() -> Tuple[str, str, str]:
    """
    Generate a new cryptographic wallet.
    
    Returns:
        Tuple of (address, public_key, private_key)
    """
    private_key_bytes = secrets.token_bytes(32)
    private_key = keys.PrivateKey(private_key_bytes)
    public_key = private_key.public_key
    address = public_key.to_checksum_address()
    
    return address, str(public_key), private_key_bytes.hex()


def sign_message(message: str, private_key: str) -> str:
    """
    Sign a message with a private key.
    
    Args:
        message: Message to sign
        private_key: Hex-encoded private key
        
    Returns:
        Hex-encoded signature
    """
    private_key_obj = keys.PrivateKey(bytes.fromhex(private_key))
    message_hash = hashlib.sha256(message.encode()).digest()
    signature = private_key_obj.sign_msg_hash(message_hash)
    return signature.to_hex()


def verify_signature(message: str, signature: str, public_key: str) -> bool:
    """
    Verify a message signature.
    
    Args:
        message: Original message
        signature: Hex-encoded signature
        public_key: Public key
        
    Returns:
        True if signature is valid
    """
    try:
        message_hash = hashlib.sha256(message.encode()).digest()
        sig = keys.Signature(bytes.fromhex(signature))
        pub_key = keys.PublicKey(bytes.fromhex(public_key))
        return pub_key.verify_msg_hash(message_hash, sig)
    except Exception:
        return False


def hash_data(data: str) -> str:
    """
    Hash data using SHA-256.
    
    Args:
        data: Data to hash
        
    Returns:
        Hex-encoded hash
    """
    return hashlib.sha256(data.encode()).hexdigest()


from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

def derive_key_from_password(password: str) -> bytes:
    """Derive a key from a password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'static_salt',  # In production, use a unique salt
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_private_key(private_key: str, password: str) -> str:
    """
    Encrypt a private key with a password.
    
    Args:
        private_key: Hex-encoded private key
        password: Encryption password
        
    Returns:
        Encrypted private key
    """
    key = derive_key_from_password(password)
    f = Fernet(key)
    return f.encrypt(private_key.encode()).decode()


def decrypt_private_key(encrypted_key: str, password: str) -> Optional[str]:
    """
    Decrypt a private key with a password.
    
    Args:
        encrypted_key: Encrypted private key
        password: Decryption password
        
    Returns:
        Decrypted private key or None if failed
    """
    key = derive_key_from_password(password)
    f = Fernet(key)
    try:
        return f.decrypt(encrypted_key.encode()).decode()
    except Exception:
        return None

