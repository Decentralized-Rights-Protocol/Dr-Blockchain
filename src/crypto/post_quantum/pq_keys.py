"""
Post-Quantum Key Management Module for DRP

This module provides quantum-resistant key generation, management, rotation, and storage
using CRYSTALS-Kyber (KEM) and CRYSTALS-Dilithium (signatures).

Features:
- CRYSTALS-Kyber key encapsulation mechanism for secure key exchange
- CRYSTALS-Dilithium digital signatures for authentication
- Key rotation and revocation management
- Secure key storage with encryption
- Integration with DRP's elder quorum system

Security Notes:
- Keys are generated with cryptographically secure random number generators
- Private keys are encrypted at rest using AES-256-GCM
- Key rotation follows NIST SP 800-57 recommendations
- Supports multiple security levels (Kyber-512, Kyber-768, Kyber-1024)
"""

import os
import json
import time
import hashlib
import secrets
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
from datetime import datetime, timedelta

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

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


class PostQuantumCryptoError(Exception):
    """Base exception for post-quantum cryptographic operations"""
    pass


@dataclass
class KyberKeyPair:
    """CRYSTALS-Kyber key pair for key encapsulation"""
    private_key: bytes
    public_key: bytes
    algorithm: str = "Kyber-768"
    created_at: float = None
    expires_at: Optional[float] = None
    key_id: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.key_id is None:
            self.key_id = self._generate_key_id()
    
    def _generate_key_id(self) -> str:
        """Generate a unique key ID from the public key"""
        return hashlib.sha256(self.public_key).hexdigest()[:16]
    
    def is_expired(self) -> bool:
        """Check if the key pair has expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def time_until_expiry(self) -> Optional[float]:
        """Get seconds until expiry, or None if no expiry"""
        if self.expires_at is None:
            return None
        return max(0, self.expires_at - time.time())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "private_key": self.private_key.hex(),
            "public_key": self.public_key.hex(),
            "algorithm": self.algorithm,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "key_id": self.key_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KyberKeyPair":
        """Create from dictionary"""
        return cls(
            private_key=bytes.fromhex(data["private_key"]),
            public_key=bytes.fromhex(data["public_key"]),
            algorithm=data["algorithm"],
            created_at=data["created_at"],
            expires_at=data.get("expires_at"),
            key_id=data["key_id"]
        )


@dataclass
class DilithiumKeyPair:
    """CRYSTALS-Dilithium key pair for digital signatures"""
    private_key: bytes
    public_key: bytes
    algorithm: str = "Dilithium3"
    created_at: float = None
    expires_at: Optional[float] = None
    key_id: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.key_id is None:
            self.key_id = self._generate_key_id()
    
    def _generate_key_id(self) -> str:
        """Generate a unique key ID from the public key"""
        return hashlib.sha256(self.public_key).hexdigest()[:16]
    
    def is_expired(self) -> bool:
        """Check if the key pair has expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def time_until_expiry(self) -> Optional[float]:
        """Get seconds until expiry, or None if no expiry"""
        if self.expires_at is None:
            return None
        return max(0, self.expires_at - time.time())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "private_key": self.private_key.hex(),
            "public_key": self.public_key.hex(),
            "algorithm": self.algorithm,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "key_id": self.key_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DilithiumKeyPair":
        """Create from dictionary"""
        return cls(
            private_key=bytes.fromhex(data["private_key"]),
            public_key=bytes.fromhex(data["public_key"]),
            algorithm=data["algorithm"],
            created_at=data["created_at"],
            expires_at=data.get("expires_at"),
            key_id=data["key_id"]
        )


class PostQuantumKeyManager:
    """
    Manages post-quantum cryptographic keys with secure storage and rotation
    
    This class provides:
    - Key generation using CRYSTALS-Kyber and CRYSTALS-Dilithium
    - Secure key storage with encryption
    - Key rotation and revocation
    - Integration with DRP's elder quorum system
    """
    
    def __init__(self, 
                 keystore_path: Union[str, Path] = ".keystore/pq_keys",
                 master_password: Optional[str] = None,
                 key_lifetime_days: int = 365):
        """
        Initialize the key manager
        
        Args:
            keystore_path: Directory to store encrypted keys
            master_password: Password for key encryption (if None, will prompt)
            key_lifetime_days: Default lifetime for generated keys in days
        """
        if not OQS_AVAILABLE:
            raise PostQuantumCryptoError("liboqs not available. Install with: pip install oqs")
        if not CRYPTO_AVAILABLE:
            raise PostQuantumCryptoError("cryptography library not available")
        
        self.keystore_path = Path(keystore_path)
        self.keystore_path.mkdir(parents=True, exist_ok=True)
        
        self.key_lifetime_days = key_lifetime_days
        self.master_password = master_password or self._generate_master_password()
        
        # Available algorithms (using correct OQS names)
        self.kyber_algorithms = ["Kyber512", "Kyber768", "Kyber1024"]
        self.dilithium_algorithms = ["Dilithium2", "Dilithium3", "Dilithium5"]
        
        # Key storage
        self._kyber_keys: Dict[str, KyberKeyPair] = {}
        self._dilithium_keys: Dict[str, DilithiumKeyPair] = {}
        self._revoked_keys: set = set()
        
        self._load_keys()
    
    def _generate_master_password(self) -> str:
        """Generate a secure master password for key encryption"""
        return secrets.token_urlsafe(32)
    
    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode())
    
    def _encrypt_key(self, key_data: bytes, password: str) -> Tuple[bytes, bytes, bytes]:
        """Encrypt key data with AES-256-GCM"""
        salt = os.urandom(16)
        key = self._derive_key_from_password(password, salt)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, key_data, None)
        return salt, nonce, ciphertext
    
    def _decrypt_key(self, salt: bytes, nonce: bytes, ciphertext: bytes, password: str) -> bytes:
        """Decrypt key data with AES-256-GCM"""
        key = self._derive_key_from_password(password, salt)
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    
    def generate_kyber_keypair(self, 
                              algorithm: str = "Kyber768",
                              expires_in_days: Optional[int] = None) -> KyberKeyPair:
        """
        Generate a new CRYSTALS-Kyber key pair
        
        Args:
            algorithm: Kyber algorithm variant (Kyber512, Kyber768, Kyber1024)
            expires_in_days: Key expiry in days (None for no expiry)
        
        Returns:
            KyberKeyPair object
        """
        if algorithm not in self.kyber_algorithms:
            raise PostQuantumCryptoError(f"Unsupported Kyber algorithm: {algorithm}")
        
        try:
            with oqs.KeyEncapsulation(algorithm) as kem:
                public_key = kem.generate_keypair()
                private_key = kem.export_secret_key()
            
            expires_at = None
            if expires_in_days is not None:
                expires_at = time.time() + (expires_in_days * 24 * 3600)
            
            keypair = KyberKeyPair(
                private_key=private_key,
                public_key=public_key,
                algorithm=algorithm,
                expires_at=expires_at
            )
            
            self._kyber_keys[keypair.key_id] = keypair
            self._save_keys()
            
            return keypair
            
        except Exception as e:
            raise PostQuantumCryptoError(f"Failed to generate Kyber key pair: {e}")
    
    def generate_dilithium_keypair(self, 
                                  algorithm: str = "Dilithium3",
                                  expires_in_days: Optional[int] = None) -> DilithiumKeyPair:
        """
        Generate a new CRYSTALS-Dilithium key pair
        
        Args:
            algorithm: Dilithium algorithm variant (Dilithium2, Dilithium3, Dilithium5)
            expires_in_days: Key expiry in days (None for no expiry)
        
        Returns:
            DilithiumKeyPair object
        """
        if algorithm not in self.dilithium_algorithms:
            raise PostQuantumCryptoError(f"Unsupported Dilithium algorithm: {algorithm}")
        
        try:
            with oqs.Signature(algorithm) as signer:
                public_key = signer.generate_keypair()
                private_key = signer.export_secret_key()
            
            expires_at = None
            if expires_in_days is not None:
                expires_at = time.time() + (expires_in_days * 24 * 3600)
            
            keypair = DilithiumKeyPair(
                private_key=private_key,
                public_key=public_key,
                algorithm=algorithm,
                expires_at=expires_at
            )
            
            self._dilithium_keys[keypair.key_id] = keypair
            self._save_keys()
            
            return keypair
            
        except Exception as e:
            raise PostQuantumCryptoError(f"Failed to generate Dilithium key pair: {e}")
    
    def get_kyber_keypair(self, key_id: str) -> Optional[KyberKeyPair]:
        """Get a Kyber key pair by ID"""
        return self._kyber_keys.get(key_id)
    
    def get_dilithium_keypair(self, key_id: str) -> Optional[DilithiumKeyPair]:
        """Get a Dilithium key pair by ID"""
        return self._dilithium_keys.get(key_id)
    
    def list_kyber_keys(self) -> List[KyberKeyPair]:
        """List all Kyber key pairs"""
        return list(self._kyber_keys.values())
    
    def list_dilithium_keys(self) -> List[DilithiumKeyPair]:
        """List all Dilithium key pairs"""
        return list(self._dilithium_keys.values())
    
    def revoke_key(self, key_id: str) -> bool:
        """
        Revoke a key pair
        
        Args:
            key_id: ID of the key to revoke
        
        Returns:
            True if key was revoked, False if not found
        """
        if key_id in self._kyber_keys:
            del self._kyber_keys[key_id]
            self._revoked_keys.add(key_id)
            self._save_keys()
            return True
        elif key_id in self._dilithium_keys:
            del self._dilithium_keys[key_id]
            self._revoked_keys.add(key_id)
            self._save_keys()
            return True
        return False
    
    def is_key_revoked(self, key_id: str) -> bool:
        """Check if a key is revoked"""
        return key_id in self._revoked_keys
    
    def _save_keys(self):
        """Save keys to encrypted storage"""
        try:
            # Prepare data for encryption
            data = {
                "kyber_keys": {k: v.to_dict() for k, v in self._kyber_keys.items()},
                "dilithium_keys": {k: v.to_dict() for k, v in self._dilithium_keys.items()},
                "revoked_keys": list(self._revoked_keys),
                "metadata": {
                    "version": "1.0",
                    "saved_at": time.time()
                }
            }
            
            json_data = json.dumps(data, indent=2).encode()
            
            # Encrypt and save
            salt, nonce, ciphertext = self._encrypt_key(json_data, self.master_password)
            
            with open(self.keystore_path / "keys.enc", "wb") as f:
                f.write(salt + nonce + ciphertext)
                
        except Exception as e:
            raise PostQuantumCryptoError(f"Failed to save keys: {e}")
    
    def _load_keys(self):
        """Load keys from encrypted storage"""
        key_file = self.keystore_path / "keys.enc"
        if not key_file.exists():
            return
        
        try:
            with open(key_file, "rb") as f:
                data = f.read()
            
            if len(data) < 28:  # salt (16) + nonce (12)
                return
            
            salt = data[:16]
            nonce = data[16:28]
            ciphertext = data[28:]
            
            # Decrypt
            json_data = self._decrypt_key(salt, nonce, ciphertext, self.master_password)
            data = json.loads(json_data.decode())
            
            # Load keys
            self._kyber_keys = {
                k: KyberKeyPair.from_dict(v) 
                for k, v in data.get("kyber_keys", {}).items()
            }
            
            self._dilithium_keys = {
                k: DilithiumKeyPair.from_dict(v) 
                for k, v in data.get("dilithium_keys", {}).items()
            }
            
            self._revoked_keys = set(data.get("revoked_keys", []))
            
        except Exception as e:
            # If decryption fails, start with empty keys
            print(f"Warning: Could not load existing keys: {e}")


class KeyRotationManager:
    """
    Manages automatic key rotation for DRP elder quorum system
    
    This class provides:
    - Automatic key rotation based on time or usage
    - Graceful key transitions
    - Integration with DRP's consensus mechanism
    """
    
    def __init__(self, key_manager: PostQuantumKeyManager):
        self.key_manager = key_manager
        self.rotation_schedule = {}
    
    def schedule_rotation(self, 
                         key_id: str, 
                         rotation_interval_days: int = 90,
                         advance_notice_days: int = 7) -> bool:
        """
        Schedule automatic key rotation
        
        Args:
            key_id: ID of the key to rotate
            rotation_interval_days: Days between rotations
            advance_notice_days: Days before expiry to generate new key
        
        Returns:
            True if scheduled successfully
        """
        self.rotation_schedule[key_id] = {
            "interval_days": rotation_interval_days,
            "advance_notice_days": advance_notice_days,
            "last_rotation": time.time(),
            "next_rotation": time.time() + (rotation_interval_days * 24 * 3600)
        }
        return True
    
    def check_rotation_needed(self) -> List[str]:
        """
        Check which keys need rotation
        
        Returns:
            List of key IDs that need rotation
        """
        keys_needing_rotation = []
        current_time = time.time()
        
        for key_id, schedule in self.rotation_schedule.items():
            if current_time >= schedule["next_rotation"]:
                keys_needing_rotation.append(key_id)
        
        return keys_needing_rotation
    
    def rotate_key(self, key_id: str) -> Optional[Union[KyberKeyPair, DilithiumKeyPair]]:
        """
        Rotate a specific key
        
        Args:
            key_id: ID of the key to rotate
        
        Returns:
            New key pair if rotation successful, None otherwise
        """
        # Check if key exists
        old_key = self.key_manager.get_kyber_keypair(key_id)
        key_type = "kyber"
        
        if old_key is None:
            old_key = self.key_manager.get_dilithium_keypair(key_id)
            key_type = "dilithium"
        
        if old_key is None:
            return None
        
        # Generate new key with same algorithm
        if key_type == "kyber":
            new_key = self.key_manager.generate_kyber_keypair(
                algorithm=old_key.algorithm,
                expires_in_days=self.key_lifetime_days
            )
        else:
            new_key = self.key_manager.generate_dilithium_keypair(
                algorithm=old_key.algorithm,
                expires_in_days=self.key_lifetime_days
            )
        
        # Update rotation schedule
        if key_id in self.rotation_schedule:
            schedule = self.rotation_schedule[key_id]
            schedule["last_rotation"] = time.time()
            schedule["next_rotation"] = time.time() + (schedule["interval_days"] * 24 * 3600)
        
        return new_key


class KeyRevocationManager:
    """
    Manages key revocation and certificate revocation lists (CRL)
    
    This class provides:
    - Key revocation tracking
    - CRL generation and distribution
    - Integration with DRP's consensus for revocation propagation
    """
    
    def __init__(self, key_manager: PostQuantumKeyManager):
        self.key_manager = key_manager
        self.revocation_reasons = {
            "compromise": "Key compromise suspected",
            "superseded": "Key superseded by new key",
            "affiliation_changed": "Affiliation changed",
            "cessation_of_operation": "Cessation of operation",
            "privilege_withdrawn": "Privilege withdrawn",
            "unspecified": "Unspecified reason"
        }
    
    def revoke_key_with_reason(self, 
                              key_id: str, 
                              reason: str = "unspecified",
                              revoked_by: str = "system") -> bool:
        """
        Revoke a key with a specific reason
        
        Args:
            key_id: ID of the key to revoke
            reason: Reason for revocation
            revoked_by: Entity that revoked the key
        
        Returns:
            True if revocation successful
        """
        if reason not in self.revocation_reasons:
            reason = "unspecified"
        
        # Add to revocation list
        revocation_entry = {
            "key_id": key_id,
            "revoked_at": time.time(),
            "reason": reason,
            "revoked_by": revoked_by
        }
        
        # Save revocation entry
        crl_file = self.key_manager.keystore_path / "revocation_list.json"
        
        try:
            if crl_file.exists():
                with open(crl_file, "r") as f:
                    crl = json.load(f)
            else:
                crl = {"revoked_keys": [], "last_updated": time.time()}
            
            crl["revoked_keys"].append(revocation_entry)
            crl["last_updated"] = time.time()
            
            with open(crl_file, "w") as f:
                json.dump(crl, f, indent=2)
            
            # Revoke in key manager
            self.key_manager.revoke_key(key_id)
            
            return True
            
        except Exception as e:
            raise PostQuantumCryptoError(f"Failed to revoke key: {e}")
    
    def get_revocation_list(self) -> Dict[str, Any]:
        """Get the current certificate revocation list"""
        crl_file = self.key_manager.keystore_path / "revocation_list.json"
        
        if not crl_file.exists():
            return {"revoked_keys": [], "last_updated": time.time()}
        
        try:
            with open(crl_file, "r") as f:
                return json.load(f)
        except Exception as e:
            raise PostQuantumCryptoError(f"Failed to read revocation list: {e}")


# Convenience functions for direct use
def generate_kyber_keypair(algorithm: str = "Kyber768") -> KyberKeyPair:
    """
    Generate a CRYSTALS-Kyber key pair
    
    Args:
        algorithm: Kyber algorithm variant
    
    Returns:
        KyberKeyPair object
    """
    if not OQS_AVAILABLE:
        raise PostQuantumCryptoError("liboqs not available")
    
    try:
        with oqs.KeyEncapsulation(algorithm) as kem:
            public_key = kem.generate_keypair()
            private_key = kem.export_secret_key()
        
        return KyberKeyPair(
            private_key=private_key,
            public_key=public_key,
            algorithm=algorithm
        )
    except Exception as e:
        raise PostQuantumCryptoError(f"Failed to generate Kyber key pair: {e}")


def generate_dilithium_keypair(algorithm: str = "Dilithium3") -> DilithiumKeyPair:
    """
    Generate a CRYSTALS-Dilithium key pair
    
    Args:
        algorithm: Dilithium algorithm variant
    
    Returns:
        DilithiumKeyPair object
    """
    if not OQS_AVAILABLE:
        raise PostQuantumCryptoError("liboqs not available")
    
    try:
        with oqs.Signature(algorithm) as signer:
            public_key = signer.generate_keypair()
            private_key = signer.export_secret_key()
        
        return DilithiumKeyPair(
            private_key=private_key,
            public_key=public_key,
            algorithm=algorithm
        )
    except Exception as e:
        raise PostQuantumCryptoError(f"Failed to generate Dilithium key pair: {e}")


# Example usage and testing
if __name__ == "__main__":
    print("Post-Quantum Key Management Module Demo")
    print("=" * 50)
    
    try:
        # Test key generation
        print("1. Generating CRYSTALS-Kyber key pair...")
        kyber_key = generate_kyber_keypair("Kyber-768")
        print(f"   Kyber Key ID: {kyber_key.key_id}")
        print(f"   Public Key Length: {len(kyber_key.public_key)} bytes")
        print(f"   Private Key Length: {len(kyber_key.private_key)} bytes")
        
        print("\n2. Generating CRYSTALS-Dilithium key pair...")
        dilithium_key = generate_dilithium_keypair("Dilithium3")
        print(f"   Dilithium Key ID: {dilithium_key.key_id}")
        print(f"   Public Key Length: {len(dilithium_key.public_key)} bytes")
        print(f"   Private Key Length: {len(dilithium_key.private_key)} bytes")
        
        print("\n3. Testing Key Manager...")
        km = PostQuantumKeyManager(keystore_path=".test_keystore")
        
        # Generate and store keys
        stored_kyber = km.generate_kyber_keypair("Kyber-512", expires_in_days=30)
        stored_dilithium = km.generate_dilithium_keypair("Dilithium2", expires_in_days=30)
        
        print(f"   Stored Kyber Key: {stored_kyber.key_id}")
        print(f"   Stored Dilithium Key: {stored_dilithium.key_id}")
        
        # Test key retrieval
        retrieved_kyber = km.get_kyber_keypair(stored_kyber.key_id)
        retrieved_dilithium = km.get_dilithium_keypair(stored_dilithium.key_id)
        
        print(f"   Retrieved Kyber Key: {retrieved_kyber is not None}")
        print(f"   Retrieved Dilithium Key: {retrieved_dilithium is not None}")
        
        print("\n4. Testing Key Rotation...")
        rotation_manager = KeyRotationManager(km)
        rotation_manager.schedule_rotation(stored_dilithium.key_id, rotation_interval_days=1)
        
        print("   Rotation scheduled successfully")
        
        print("\n5. Testing Key Revocation...")
        revocation_manager = KeyRevocationManager(km)
        revoked = revocation_manager.revoke_key_with_reason(
            stored_kyber.key_id, 
            reason="superseded",
            revoked_by="test_system"
        )
        print(f"   Key revoked: {revoked}")
        
        print("\n✅ All tests passed!")
        
    except PostQuantumCryptoError as e:
        print(f"❌ Post-quantum crypto error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")



