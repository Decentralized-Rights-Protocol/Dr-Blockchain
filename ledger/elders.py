"""
Elder Verification System for DRP
Handles Elder quorum verification and BLS signature aggregation
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import secrets

logger = logging.getLogger(__name__)

class ElderNode:
    """Represents an Elder node in the DRP network"""
    
    def __init__(self, elder_id: str, public_key: bytes, weight: int = 1):
        self.elder_id = elder_id
        self.public_key = public_key
        self.weight = weight
        self.is_active = True
        self.last_seen = datetime.now(timezone.utc)
        self.signature_count = 0

class ElderVerification:
    """Handles Elder quorum verification and signature aggregation"""
    
    def __init__(self, 
                 quorum_threshold: int = 3,
                 total_elders: int = 5,
                 elder_keys_file: str = None):
        self.quorum_threshold = quorum_threshold
        self.total_elders = total_elders
        self.elder_keys_file = elder_keys_file or os.getenv("ELDER_KEYS_FILE", "elder_keys.json")
        self.elders: Dict[str, ElderNode] = {}
        self.elder_revocation_list: List[str] = []
        self.ready = False
        
    async def initialize(self):
        """Initialize Elder verification system"""
        try:
            # Load or generate Elder keys
            await self._load_elder_keys()
            
            # Initialize Elder nodes
            await self._initialize_elder_nodes()
            
            self.ready = True
            logger.info(f"Elder verification initialized with {len(self.elders)} elders, threshold: {self.quorum_threshold}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Elder verification: {e}")
            self.ready = False
            raise
    
    async def _load_elder_keys(self):
        """Load Elder keys from file or generate new ones"""
        try:
            if os.path.exists(self.elder_keys_file):
                with open(self.elder_keys_file, 'r') as f:
                    keys_data = json.load(f)
                    self.elder_keys = keys_data
                logger.info(f"Loaded Elder keys from {self.elder_keys_file}")
            else:
                # Generate new Elder keys
                self.elder_keys = await self._generate_elder_keys()
                await self._save_elder_keys()
                logger.info(f"Generated new Elder keys and saved to {self.elder_keys_file}")
                
        except Exception as e:
            logger.error(f"Error loading Elder keys: {e}")
            raise
    
    async def _generate_elder_keys(self) -> Dict[str, Dict[str, str]]:
        """Generate new Elder key pairs"""
        elder_keys = {}
        
        for i in range(self.total_elders):
            elder_id = f"elder_{i+1}"
            
            # Generate Ed25519 key pair
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
            
            # Serialize keys
            private_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            
            elder_keys[elder_id] = {
                "private_key": private_bytes.hex(),
                "public_key": public_bytes.hex(),
                "weight": 1,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        
        return elder_keys
    
    async def _save_elder_keys(self):
        """Save Elder keys to file"""
        try:
            with open(self.elder_keys_file, 'w') as f:
                json.dump(self.elder_keys, f, indent=2)
            logger.info(f"Elder keys saved to {self.elder_keys_file}")
        except Exception as e:
            logger.error(f"Error saving Elder keys: {e}")
            raise
    
    async def _initialize_elder_nodes(self):
        """Initialize Elder node objects"""
        for elder_id, key_data in self.elder_keys.items():
            public_key = bytes.fromhex(key_data["public_key"])
            weight = key_data.get("weight", 1)
            
            elder_node = ElderNode(elder_id, public_key, weight)
            self.elders[elder_id] = elder_node
    
    async def get_quorum_signatures(self, anchor_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get quorum signatures for anchor payload
        
        Args:
            anchor_payload: Data to be signed
            
        Returns:
            List[Dict]: List of Elder signatures
        """
        if not self.ready:
            raise Exception("Elder verification not ready")
        
        try:
            # Create message to sign
            message = self._create_signature_message(anchor_payload)
            
            # Get active Elders
            active_elders = [elder for elder in self.elders.values() 
                           if elder.is_active and elder.elder_id not in self.elder_revocation_list]
            
            if len(active_elders) < self.quorum_threshold:
                raise Exception(f"Insufficient active Elders: {len(active_elders)} < {self.quorum_threshold}")
            
            # Select Elders for quorum (in production, this would be deterministic)
            selected_elders = active_elders[:self.quorum_threshold]
            
            signatures = []
            for elder in selected_elders:
                signature = await self._sign_with_elder(elder.elder_id, message)
                signatures.append({
                    "elder_id": elder.elder_id,
                    "signature": signature,
                    "public_key": elder.public_key.hex(),
                    "weight": elder.weight,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # Update Elder stats
                elder.signature_count += 1
                elder.last_seen = datetime.now(timezone.utc)
            
            logger.info(f"Generated quorum signatures from {len(signatures)} Elders")
            return signatures
            
        except Exception as e:
            logger.error(f"Error getting quorum signatures: {e}")
            raise
    
    def _create_signature_message(self, anchor_payload: Dict[str, Any]) -> bytes:
        """Create message for Elder signatures"""
        # Create deterministic message from anchor payload
        message_data = {
            "proof_id": anchor_payload["proof_id"],
            "cid": anchor_payload["cid"],
            "metadata_hash": anchor_payload["metadata_hash"],
            "timestamp": anchor_payload["timestamp"]
        }
        
        message_json = json.dumps(message_data, sort_keys=True)
        return message_json.encode('utf-8')
    
    async def _sign_with_elder(self, elder_id: str, message: bytes) -> str:
        """Sign message with specific Elder's private key"""
        try:
            if elder_id not in self.elder_keys:
                raise Exception(f"Elder {elder_id} not found")
            
            private_key_hex = self.elder_keys[elder_id]["private_key"]
            private_key_bytes = bytes.fromhex(private_key_hex)
            
            # Create private key object
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
            
            # Sign message
            signature = private_key.sign(message)
            
            return signature.hex()
            
        except Exception as e:
            logger.error(f"Error signing with Elder {elder_id}: {e}")
            raise
    
    async def verify_quorum_signatures(self, 
                                     anchor_payload: Dict[str, Any], 
                                     signatures: List[Dict[str, Any]]) -> bool:
        """
        Verify quorum signatures for anchor payload
        
        Args:
            anchor_payload: Original data that was signed
            signatures: List of Elder signatures to verify
            
        Returns:
            bool: True if quorum is valid
        """
        if not self.ready:
            raise Exception("Elder verification not ready")
        
        try:
            # Create message that was signed
            message = self._create_signature_message(anchor_payload)
            
            # Check if we have enough signatures
            if len(signatures) < self.quorum_threshold:
                logger.warning(f"Insufficient signatures: {len(signatures)} < {self.quorum_threshold}")
                return False
            
            # Verify each signature
            valid_signatures = 0
            total_weight = 0
            
            for sig_data in signatures:
                elder_id = sig_data["elder_id"]
                
                # Check if Elder is active and not revoked
                if elder_id not in self.elders:
                    logger.warning(f"Unknown Elder: {elder_id}")
                    continue
                
                elder = self.elders[elder_id]
                if not elder.is_active or elder_id in self.elder_revocation_list:
                    logger.warning(f"Inactive or revoked Elder: {elder_id}")
                    continue
                
                # Verify signature
                try:
                    signature_bytes = bytes.fromhex(sig_data["signature"])
                    public_key_bytes = bytes.fromhex(sig_data["public_key"])
                    
                    # Create public key object
                    public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
                    
                    # Verify signature
                    public_key.verify(signature_bytes, message)
                    
                    valid_signatures += 1
                    total_weight += elder.weight
                    
                    logger.debug(f"Valid signature from Elder {elder_id}")
                    
                except Exception as e:
                    logger.warning(f"Invalid signature from Elder {elder_id}: {e}")
                    continue
            
            # Check if we have enough valid signatures by weight
            required_weight = sum(elder.weight for elder in self.elders.values() 
                                if elder.is_active and elder.elder_id not in self.elder_revocation_list) // 2 + 1
            
            is_valid = total_weight >= required_weight
            
            logger.info(f"Quorum verification: {valid_signatures} valid signatures, "
                       f"total weight: {total_weight}/{required_weight}, valid: {is_valid}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying quorum signatures: {e}")
            return False
    
    async def add_elder(self, elder_id: str, public_key: bytes, weight: int = 1) -> bool:
        """Add new Elder to the network"""
        try:
            if elder_id in self.elders:
                logger.warning(f"Elder {elder_id} already exists")
                return False
            
            elder_node = ElderNode(elder_id, public_key, weight)
            self.elders[elder_id] = elder_node
            
            # Update keys file
            self.elder_keys[elder_id] = {
                "public_key": public_key.hex(),
                "weight": weight,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await self._save_elder_keys()
            
            logger.info(f"Added new Elder: {elder_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding Elder {elder_id}: {e}")
            return False
    
    async def revoke_elder(self, elder_id: str) -> bool:
        """Revoke Elder from the network"""
        try:
            if elder_id not in self.elders:
                logger.warning(f"Elder {elder_id} not found")
                return False
            
            # Add to revocation list
            if elder_id not in self.elder_revocation_list:
                self.elder_revocation_list.append(elder_id)
            
            # Mark as inactive
            self.elders[elder_id].is_active = False
            
            logger.info(f"Revoked Elder: {elder_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking Elder {elder_id}: {e}")
            return False
    
    async def get_elder_status(self) -> Dict[str, Any]:
        """Get status of all Elders"""
        try:
            status = {
                "total_elders": len(self.elders),
                "active_elders": len([e for e in self.elders.values() if e.is_active]),
                "revoked_elders": len(self.elder_revocation_list),
                "quorum_threshold": self.quorum_threshold,
                "elders": []
            }
            
            for elder_id, elder in self.elders.items():
                elder_status = {
                    "elder_id": elder_id,
                    "is_active": elder.is_active,
                    "is_revoked": elder_id in self.elder_revocation_list,
                    "weight": elder.weight,
                    "signature_count": elder.signature_count,
                    "last_seen": elder.last_seen.isoformat()
                }
                status["elders"].append(elder_status)
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting Elder status: {e}")
            return {}
    
    def is_ready(self) -> bool:
        """Check if Elder verification is ready"""
        return self.ready
    
    async def close(self):
        """Close Elder verification system"""
        self.ready = False
        logger.info("Elder verification system closed")

# Utility functions
async def create_elder_verification(quorum_threshold: int = 3) -> ElderVerification:
    """Create and initialize Elder verification system"""
    verification = ElderVerification(quorum_threshold)
    await verification.initialize()
    return verification

async def verify_elder_quorum(anchor_payload: Dict[str, Any], 
                            signatures: List[Dict[str, Any]],
                            quorum_threshold: int = 3) -> bool:
    """Utility function to verify Elder quorum"""
    verification = await create_elder_verification(quorum_threshold)
    try:
        is_valid = await verification.verify_quorum_signatures(anchor_payload, signatures)
        return is_valid
    finally:
        await verification.close()
