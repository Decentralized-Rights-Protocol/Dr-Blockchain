"""
Security and Encryption Manager for DRP
Handles client-side encryption, server-side verification, and key management
"""

import asyncio
import hashlib
import json
import logging
import os
import secrets
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Manages encryption, decryption, and key operations for DRP"""
    
    def __init__(self, 
                 master_key_file: str = None,
                 key_rotation_days: int = 90):
        self.master_key_file = master_key_file or os.getenv("MASTER_KEY_FILE", "master_key.key")
        self.key_rotation_days = key_rotation_days
        self.master_key: Optional[bytes] = None
        self.fernet: Optional[Fernet] = None
        self.ready = False
        
    async def initialize(self):
        """Initialize encryption manager"""
        try:
            # Load or generate master key
            await self._load_master_key()
            
            # Initialize Fernet with master key
            self.fernet = Fernet(self.master_key)
            
            self.ready = True
            logger.info("Encryption manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption manager: {e}")
            self.ready = False
            raise
    
    async def _load_master_key(self):
        """Load master key from file or generate new one"""
        try:
            if os.path.exists(self.master_key_file):
                with open(self.master_key_file, 'rb') as f:
                    self.master_key = f.read()
                logger.info(f"Loaded master key from {self.master_key_file}")
            else:
                # Generate new master key
                self.master_key = Fernet.generate_key()
                await self._save_master_key()
                logger.info(f"Generated new master key and saved to {self.master_key_file}")
                
        except Exception as e:
            logger.error(f"Error loading master key: {e}")
            raise
    
    async def _save_master_key(self):
        """Save master key to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.master_key_file), exist_ok=True)
            
            with open(self.master_key_file, 'wb') as f:
                f.write(self.master_key)
            logger.info(f"Master key saved to {self.master_key_file}")
        except Exception as e:
            logger.error(f"Error saving master key: {e}")
            raise
    
    async def encrypt_proof_data(self, proof_data: Dict[str, Any], user_hash: str) -> Dict[str, Any]:
        """
        Encrypt proof data for storage
        
        Args:
            proof_data: Proof data to encrypt
            user_hash: User hash for key derivation
            
        Returns:
            Dict: Encrypted proof data
        """
        if not self.ready:
            raise Exception("Encryption manager not ready")
        
        try:
            # Derive user-specific key
            user_key = await self._derive_user_key(user_hash)
            
            # Encrypt sensitive fields
            encrypted_data = {}
            for key, value in proof_data.items():
                if self._is_sensitive_field(key):
                    encrypted_value = await self._encrypt_field(value, user_key)
                    encrypted_data[f"{key}_encrypted"] = encrypted_value
                else:
                    encrypted_data[key] = value
            
            # Add encryption metadata
            encrypted_data["encryption_metadata"] = {
                "algorithm": "Fernet",
                "user_hash": user_hash,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "1.0"
            }
            
            logger.info(f"Encrypted proof data for user {user_hash}")
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Error encrypting proof data: {e}")
            raise
    
    async def decrypt_proof_data(self, encrypted_data: Dict[str, Any], user_hash: str) -> Dict[str, Any]:
        """
        Decrypt proof data
        
        Args:
            encrypted_data: Encrypted proof data
            user_hash: User hash for key derivation
            
        Returns:
            Dict: Decrypted proof data
        """
        if not self.ready:
            raise Exception("Encryption manager not ready")
        
        try:
            # Derive user-specific key
            user_key = await self._derive_user_key(user_hash)
            
            # Decrypt sensitive fields
            decrypted_data = {}
            for key, value in encrypted_data.items():
                if key.endswith("_encrypted"):
                    original_key = key[:-10]  # Remove "_encrypted" suffix
                    decrypted_value = await self._decrypt_field(value, user_key)
                    decrypted_data[original_key] = decrypted_value
                elif key != "encryption_metadata":
                    decrypted_data[key] = value
            
            logger.info(f"Decrypted proof data for user {user_hash}")
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Error decrypting proof data: {e}")
            raise
    
    async def _derive_user_key(self, user_hash: str) -> bytes:
        """Derive user-specific encryption key"""
        try:
            # Use HKDF to derive key from master key and user hash
            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'drp_user_key_salt',
                info=user_hash.encode('utf-8'),
                backend=default_backend()
            )
            
            user_key = hkdf.derive(self.master_key)
            return user_key
            
        except Exception as e:
            logger.error(f"Error deriving user key: {e}")
            raise
    
    async def _encrypt_field(self, value: Any, key: bytes) -> str:
        """Encrypt a single field"""
        try:
            # Convert value to JSON string
            value_json = json.dumps(value, sort_keys=True)
            value_bytes = value_json.encode('utf-8')
            
            # Encrypt with Fernet
            fernet = Fernet(key)
            encrypted_bytes = fernet.encrypt(value_bytes)
            
            # Return base64 encoded
            return base64.b64encode(encrypted_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error encrypting field: {e}")
            raise
    
    async def _decrypt_field(self, encrypted_value: str, key: bytes) -> Any:
        """Decrypt a single field"""
        try:
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_value.encode('utf-8'))
            
            # Decrypt with Fernet
            fernet = Fernet(key)
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            
            # Parse JSON
            value_json = decrypted_bytes.decode('utf-8')
            return json.loads(value_json)
            
        except Exception as e:
            logger.error(f"Error decrypting field: {e}")
            raise
    
    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if a field contains sensitive data"""
        sensitive_fields = {
            'personal_data', 'biometric_data', 'location_data', 
            'contact_info', 'financial_data', 'medical_data',
            'private_notes', 'internal_metadata'
        }
        return field_name.lower() in sensitive_fields
    
    async def generate_key_pair(self, key_type: str = "ed25519") -> Tuple[bytes, bytes]:
        """
        Generate a new key pair for client-side encryption
        
        Args:
            key_type: Type of key to generate ("ed25519" or "rsa")
            
        Returns:
            Tuple[bytes, bytes]: (private_key, public_key)
        """
        try:
            if key_type.lower() == "ed25519":
                private_key = ed25519.Ed25519PrivateKey.generate()
                public_key = private_key.public_key()
                
                private_bytes = private_key.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption()
                )
                
                public_bytes = public_key.public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )
                
            elif key_type.lower() == "rsa":
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                    backend=default_backend()
                )
                public_key = private_key.public_key()
                
                private_bytes = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                
                public_bytes = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
            else:
                raise ValueError(f"Unsupported key type: {key_type}")
            
            logger.info(f"Generated {key_type} key pair")
            return private_bytes, public_bytes
            
        except Exception as e:
            logger.error(f"Error generating key pair: {e}")
            raise
    
    async def sign_data(self, data: Any, private_key: bytes, key_type: str = "ed25519") -> str:
        """
        Sign data with private key
        
        Args:
            data: Data to sign
            private_key: Private key bytes
            key_type: Type of key ("ed25519" or "rsa")
            
        Returns:
            str: Signature in hex format
        """
        try:
            # Convert data to bytes
            if isinstance(data, dict):
                data_json = json.dumps(data, sort_keys=True)
                data_bytes = data_json.encode('utf-8')
            else:
                data_bytes = str(data).encode('utf-8')
            
            if key_type.lower() == "ed25519":
                private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(private_key)
                signature = private_key_obj.sign(data_bytes)
                
            elif key_type.lower() == "rsa":
                private_key_obj = serialization.load_pem_private_key(
                    private_key, password=None, backend=default_backend()
                )
                signature = private_key_obj.sign(
                    data_bytes,
                    padding=serialization.PSS(
                        mgf=serialization.MGF1(hashes.SHA256()),
                        salt_length=serialization.PSS.MAX_LENGTH
                    ),
                    algorithm=hashes.SHA256()
                )
            else:
                raise ValueError(f"Unsupported key type: {key_type}")
            
            return signature.hex()
            
        except Exception as e:
            logger.error(f"Error signing data: {e}")
            raise
    
    async def verify_signature(self, data: Any, signature: str, public_key: bytes, key_type: str = "ed25519") -> bool:
        """
        Verify signature with public key
        
        Args:
            data: Original data
            signature: Signature in hex format
            public_key: Public key bytes
            key_type: Type of key ("ed25519" or "rsa")
            
        Returns:
            bool: True if signature is valid
        """
        try:
            # Convert data to bytes
            if isinstance(data, dict):
                data_json = json.dumps(data, sort_keys=True)
                data_bytes = data_json.encode('utf-8')
            else:
                data_bytes = str(data).encode('utf-8')
            
            signature_bytes = bytes.fromhex(signature)
            
            if key_type.lower() == "ed25519":
                public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(public_key)
                public_key_obj.verify(signature_bytes, data_bytes)
                
            elif key_type.lower() == "rsa":
                public_key_obj = serialization.load_pem_public_key(
                    public_key, backend=default_backend()
                )
                public_key_obj.verify(
                    signature_bytes,
                    data_bytes,
                    padding=serialization.PSS(
                        mgf=serialization.MGF1(hashes.SHA256()),
                        salt_length=serialization.PSS.MAX_LENGTH
                    ),
                    algorithm=hashes.SHA256()
                )
            else:
                raise ValueError(f"Unsupported key type: {key_type}")
            
            return True
            
        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return False
    
    async def hash_privacy_preserving(self, data: Any, salt: str = None) -> str:
        """
        Create privacy-preserving hash of data
        
        Args:
            data: Data to hash
            salt: Optional salt for hashing
            
        Returns:
            str: Privacy-preserving hash
        """
        try:
            # Convert data to string
            if isinstance(data, dict):
                data_str = json.dumps(data, sort_keys=True)
            else:
                data_str = str(data)
            
            # Add salt if provided
            if salt:
                data_str = f"{data_str}:{salt}"
            
            # Create hash
            hash_obj = hashlib.sha256()
            hash_obj.update(data_str.encode('utf-8'))
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            logger.error(f"Error creating privacy-preserving hash: {e}")
            raise
    
    def is_ready(self) -> bool:
        """Check if encryption manager is ready"""
        return self.ready
    
    async def close(self):
        """Close encryption manager"""
        self.ready = False
        logger.info("Encryption manager closed")

# Utility functions
async def create_encryption_manager(master_key_file: str = None) -> EncryptionManager:
    """Create and initialize encryption manager"""
    manager = EncryptionManager(master_key_file)
    await manager.initialize()
    return manager

async def encrypt_proof_for_storage(proof_data: Dict[str, Any], user_hash: str) -> Dict[str, Any]:
    """Utility function to encrypt proof data"""
    manager = await create_encryption_manager()
    try:
        encrypted_data = await manager.encrypt_proof_data(proof_data, user_hash)
        return encrypted_data
    finally:
        await manager.close()

async def decrypt_proof_for_reading(encrypted_data: Dict[str, Any], user_hash: str) -> Dict[str, Any]:
    """Utility function to decrypt proof data"""
    manager = await create_encryption_manager()
    try:
        decrypted_data = await manager.decrypt_proof_data(encrypted_data, user_hash)
        return decrypted_data
    finally:
        await manager.close()
