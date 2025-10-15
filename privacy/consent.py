"""
Privacy and Consent Manager for DRP
Handles user consent tokens, privacy-preserving operations, and GDPR compliance
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Set
from uuid import uuid4
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

class ConsentToken:
    """Represents a user consent token"""
    
    def __init__(self, 
                 token_id: str,
                 user_id: str,
                 consent_types: List[str],
                 granted_at: datetime,
                 expires_at: Optional[datetime] = None,
                 signature: str = None):
        self.token_id = token_id
        self.user_id = user_id
        self.consent_types = consent_types
        self.granted_at = granted_at
        self.expires_at = expires_at
        self.signature = signature
        self.is_revoked = False
        self.revoked_at: Optional[datetime] = None

class ConsentManager:
    """Manages user consent tokens and privacy operations"""
    
    def __init__(self, 
                 consent_db_file: str = None,
                 private_key_file: str = None,
                 token_expiry_days: int = 365):
        self.consent_db_file = consent_db_file or os.getenv("CONSENT_DB_FILE", "consent_tokens.json")
        self.private_key_file = private_key_file or os.getenv("CONSENT_PRIVATE_KEY_FILE", "consent_key.pem")
        self.token_expiry_days = token_expiry_days
        self.private_key: Optional[ed25519.Ed25519PrivateKey] = None
        self.public_key: Optional[ed25519.Ed25519PublicKey] = None
        self.consent_tokens: Dict[str, ConsentToken] = {}
        self.ready = False
        
    async def initialize(self):
        """Initialize consent manager"""
        try:
            # Load or generate signing key
            await self._load_signing_key()
            
            # Load existing consent tokens
            await self._load_consent_tokens()
            
            self.ready = True
            logger.info("Consent manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize consent manager: {e}")
            self.ready = False
            raise
    
    async def _load_signing_key(self):
        """Load or generate signing key for consent tokens"""
        try:
            if os.path.exists(self.private_key_file):
                with open(self.private_key_file, 'rb') as f:
                    private_key_bytes = f.read()
                self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
                self.public_key = self.private_key.public_key()
                logger.info(f"Loaded consent signing key from {self.private_key_file}")
            else:
                # Generate new signing key
                self.private_key = ed25519.Ed25519PrivateKey.generate()
                self.public_key = self.private_key.public_key()
                await self._save_signing_key()
                logger.info(f"Generated new consent signing key and saved to {self.private_key_file}")
                
        except Exception as e:
            logger.error(f"Error loading signing key: {e}")
            raise
    
    async def _save_signing_key(self):
        """Save signing key to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.private_key_file), exist_ok=True)
            
            private_key_bytes = self.private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            with open(self.private_key_file, 'wb') as f:
                f.write(private_key_bytes)
            logger.info(f"Consent signing key saved to {self.private_key_file}")
        except Exception as e:
            logger.error(f"Error saving signing key: {e}")
            raise
    
    async def _load_consent_tokens(self):
        """Load existing consent tokens from file"""
        try:
            if os.path.exists(self.consent_db_file):
                with open(self.consent_db_file, 'r') as f:
                    tokens_data = json.load(f)
                
                for token_id, token_data in tokens_data.items():
                    consent_token = ConsentToken(
                        token_id=token_data["token_id"],
                        user_id=token_data["user_id"],
                        consent_types=token_data["consent_types"],
                        granted_at=datetime.fromisoformat(token_data["granted_at"]),
                        expires_at=datetime.fromisoformat(token_data["expires_at"]) if token_data.get("expires_at") else None,
                        signature=token_data.get("signature")
                    )
                    consent_token.is_revoked = token_data.get("is_revoked", False)
                    if token_data.get("revoked_at"):
                        consent_token.revoked_at = datetime.fromisoformat(token_data["revoked_at"])
                    
                    self.consent_tokens[token_id] = consent_token
                
                logger.info(f"Loaded {len(self.consent_tokens)} consent tokens")
            else:
                logger.info("No existing consent tokens found")
                
        except Exception as e:
            logger.error(f"Error loading consent tokens: {e}")
            raise
    
    async def _save_consent_tokens(self):
        """Save consent tokens to file"""
        try:
            tokens_data = {}
            for token_id, token in self.consent_tokens.items():
                tokens_data[token_id] = {
                    "token_id": token.token_id,
                    "user_id": token.user_id,
                    "consent_types": token.consent_types,
                    "granted_at": token.granted_at.isoformat(),
                    "expires_at": token.expires_at.isoformat() if token.expires_at else None,
                    "signature": token.signature,
                    "is_revoked": token.is_revoked,
                    "revoked_at": token.revoked_at.isoformat() if token.revoked_at else None
                }
            
            with open(self.consent_db_file, 'w') as f:
                json.dump(tokens_data, f, indent=2)
            logger.info(f"Saved {len(self.consent_tokens)} consent tokens")
        except Exception as e:
            logger.error(f"Error saving consent tokens: {e}")
            raise
    
    async def create_consent_token(self, 
                                 user_id: str, 
                                 consent_types: List[str],
                                 expires_in_days: int = None) -> str:
        """
        Create a new consent token for a user
        
        Args:
            user_id: User identifier
            consent_types: List of consent types (e.g., ["data_processing", "analytics"])
            expires_in_days: Token expiry in days (default: token_expiry_days)
            
        Returns:
            str: Signed consent token
        """
        if not self.ready:
            raise Exception("Consent manager not ready")
        
        try:
            # Generate token ID
            token_id = str(uuid4())
            
            # Set expiry
            expires_in_days = expires_in_days or self.token_expiry_days
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            
            # Create consent token
            consent_token = ConsentToken(
                token_id=token_id,
                user_id=user_id,
                consent_types=consent_types,
                granted_at=datetime.now(timezone.utc),
                expires_at=expires_at
            )
            
            # Sign the token
            signature = await self._sign_consent_token(consent_token)
            consent_token.signature = signature
            
            # Store token
            self.consent_tokens[token_id] = consent_token
            await self._save_consent_tokens()
            
            logger.info(f"Created consent token {token_id} for user {user_id}")
            return token_id
            
        except Exception as e:
            logger.error(f"Error creating consent token: {e}")
            raise
    
    async def _sign_consent_token(self, consent_token: ConsentToken) -> str:
        """Sign a consent token"""
        try:
            # Create message to sign
            message_data = {
                "token_id": consent_token.token_id,
                "user_id": consent_token.user_id,
                "consent_types": consent_token.consent_types,
                "granted_at": consent_token.granted_at.isoformat(),
                "expires_at": consent_token.expires_at.isoformat() if consent_token.expires_at else None
            }
            
            message_json = json.dumps(message_data, sort_keys=True)
            message_bytes = message_json.encode('utf-8')
            
            # Sign message
            signature = self.private_key.sign(message_bytes)
            return signature.hex()
            
        except Exception as e:
            logger.error(f"Error signing consent token: {e}")
            raise
    
    async def validate_consent_token(self, token_id: str, user_id: str) -> bool:
        """
        Validate a consent token
        
        Args:
            token_id: Consent token ID
            user_id: User ID to validate against
            
        Returns:
            bool: True if token is valid
        """
        if not self.ready:
            raise Exception("Consent manager not ready")
        
        try:
            # Check if token exists
            if token_id not in self.consent_tokens:
                logger.warning(f"Consent token {token_id} not found")
                return False
            
            consent_token = self.consent_tokens[token_id]
            
            # Check if token is revoked
            if consent_token.is_revoked:
                logger.warning(f"Consent token {token_id} is revoked")
                return False
            
            # Check if token is expired
            if consent_token.expires_at and datetime.now(timezone.utc) > consent_token.expires_at:
                logger.warning(f"Consent token {token_id} is expired")
                return False
            
            # Check user ID matches
            if consent_token.user_id != user_id:
                logger.warning(f"Consent token {token_id} user mismatch: {consent_token.user_id} != {user_id}")
                return False
            
            # Verify signature
            if not await self._verify_consent_token_signature(consent_token):
                logger.warning(f"Consent token {token_id} has invalid signature")
                return False
            
            logger.info(f"Consent token {token_id} is valid for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating consent token: {e}")
            return False
    
    async def _verify_consent_token_signature(self, consent_token: ConsentToken) -> bool:
        """Verify consent token signature"""
        try:
            # Recreate message that was signed
            message_data = {
                "token_id": consent_token.token_id,
                "user_id": consent_token.user_id,
                "consent_types": consent_token.consent_types,
                "granted_at": consent_token.granted_at.isoformat(),
                "expires_at": consent_token.expires_at.isoformat() if consent_token.expires_at else None
            }
            
            message_json = json.dumps(message_data, sort_keys=True)
            message_bytes = message_json.encode('utf-8')
            
            # Verify signature
            signature_bytes = bytes.fromhex(consent_token.signature)
            self.public_key.verify(signature_bytes, message_bytes)
            
            return True
            
        except Exception as e:
            logger.warning(f"Consent token signature verification failed: {e}")
            return False
    
    async def revoke_consent_token(self, token_id: str, user_id: str) -> bool:
        """
        Revoke a consent token
        
        Args:
            token_id: Consent token ID to revoke
            user_id: User ID (for verification)
            
        Returns:
            bool: True if token was revoked successfully
        """
        if not self.ready:
            raise Exception("Consent manager not ready")
        
        try:
            # Check if token exists
            if token_id not in self.consent_tokens:
                logger.warning(f"Consent token {token_id} not found")
                return False
            
            consent_token = self.consent_tokens[token_id]
            
            # Check user ID matches
            if consent_token.user_id != user_id:
                logger.warning(f"Consent token {token_id} user mismatch")
                return False
            
            # Revoke token
            consent_token.is_revoked = True
            consent_token.revoked_at = datetime.now(timezone.utc)
            
            await self._save_consent_tokens()
            
            logger.info(f"Revoked consent token {token_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking consent token: {e}")
            return False
    
    async def get_user_consent_tokens(self, user_id: str) -> List[ConsentToken]:
        """Get all consent tokens for a user"""
        if not self.ready:
            raise Exception("Consent manager not ready")
        
        try:
            user_tokens = []
            for token in self.consent_tokens.values():
                if token.user_id == user_id:
                    user_tokens.append(token)
            
            logger.info(f"Retrieved {len(user_tokens)} consent tokens for user {user_id}")
            return user_tokens
            
        except Exception as e:
            logger.error(f"Error getting user consent tokens: {e}")
            return []
    
    async def cleanup_expired_tokens(self) -> int:
        """Remove expired consent tokens"""
        if not self.ready:
            raise Exception("Consent manager not ready")
        
        try:
            current_time = datetime.now(timezone.utc)
            expired_tokens = []
            
            for token_id, token in self.consent_tokens.items():
                if token.expires_at and current_time > token.expires_at:
                    expired_tokens.append(token_id)
            
            # Remove expired tokens
            for token_id in expired_tokens:
                del self.consent_tokens[token_id]
            
            if expired_tokens:
                await self._save_consent_tokens()
                logger.info(f"Cleaned up {len(expired_tokens)} expired consent tokens")
            
            return len(expired_tokens)
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            return 0
    
    async def get_consent_statistics(self) -> Dict[str, Any]:
        """Get consent statistics"""
        if not self.ready:
            raise Exception("Consent manager not ready")
        
        try:
            current_time = datetime.now(timezone.utc)
            
            total_tokens = len(self.consent_tokens)
            active_tokens = 0
            expired_tokens = 0
            revoked_tokens = 0
            
            consent_types_count = {}
            unique_users = set()
            
            for token in self.consent_tokens.values():
                unique_users.add(token.user_id)
                
                if token.is_revoked:
                    revoked_tokens += 1
                elif token.expires_at and current_time > token.expires_at:
                    expired_tokens += 1
                else:
                    active_tokens += 1
                
                for consent_type in token.consent_types:
                    consent_types_count[consent_type] = consent_types_count.get(consent_type, 0) + 1
            
            stats = {
                "total_tokens": total_tokens,
                "active_tokens": active_tokens,
                "expired_tokens": expired_tokens,
                "revoked_tokens": revoked_tokens,
                "unique_users": len(unique_users),
                "consent_types": consent_types_count
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting consent statistics: {e}")
            return {}
    
    def is_ready(self) -> bool:
        """Check if consent manager is ready"""
        return self.ready
    
    async def close(self):
        """Close consent manager"""
        self.ready = False
        logger.info("Consent manager closed")

# Utility functions
async def create_consent_manager(consent_db_file: str = None) -> ConsentManager:
    """Create and initialize consent manager"""
    manager = ConsentManager(consent_db_file)
    await manager.initialize()
    return manager

async def create_user_consent(user_id: str, consent_types: List[str]) -> str:
    """Utility function to create user consent token"""
    manager = await create_consent_manager()
    try:
        token_id = await manager.create_consent_token(user_id, consent_types)
        return token_id
    finally:
        await manager.close()

async def validate_user_consent(token_id: str, user_id: str) -> bool:
    """Utility function to validate user consent token"""
    manager = await create_consent_manager()
    try:
        is_valid = await manager.validate_consent_token(token_id, user_id)
        return is_valid
    finally:
        await manager.close()
