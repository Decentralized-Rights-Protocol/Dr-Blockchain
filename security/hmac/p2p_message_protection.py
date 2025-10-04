#!/usr/bin/env python3
"""
HMAC Protection for DRP P2P Messages
Implements HMAC-SHA256 protection with session keys for node-to-node communication
"""

import hmac
import hashlib
import json
import logging
import secrets
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of P2P messages"""
    HANDSHAKE = "handshake"
    BLOCK_PROPOSAL = "block_proposal"
    TRANSACTION = "transaction"
    CONSENSUS_VOTE = "consensus_vote"
    PEER_DISCOVERY = "peer_discovery"
    HEARTBEAT = "heartbeat"
    AI_VERIFICATION = "ai_verification"
    ELDER_QUORUM = "elder_quorum"


class SessionStatus(Enum):
    """Session status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class SessionKey:
    """Represents a session key for HMAC protection"""
    key_id: str
    key_value: bytes
    created_at: str
    expires_at: str
    status: SessionStatus
    peer_id: str
    usage_count: int = 0
    last_used: Optional[str] = None


@dataclass
class ProtectedMessage:
    """Represents a protected P2P message"""
    message_id: str
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: str
    sender_id: str
    recipient_id: str
    hmac_signature: str
    session_key_id: str
    nonce: str
    version: str = "1.0"


@dataclass
class MessageValidationResult:
    """Result of message validation"""
    is_valid: bool
    error_message: Optional[str] = None
    message: Optional[ProtectedMessage] = None
    session_key: Optional[SessionKey] = None


class SessionKeyManager:
    """
    Manages session keys for HMAC protection
    """
    
    def __init__(self, key_expiry_hours: int = 24):
        """
        Initialize session key manager
        
        Args:
            key_expiry_hours: Hours until session keys expire
        """
        self.key_expiry_hours = key_expiry_hours
        self.session_keys: Dict[str, SessionKey] = {}
        self.peer_sessions: Dict[str, List[str]] = {}  # peer_id -> list of key_ids
        
        logger.info(f"Session Key Manager initialized with {key_expiry_hours}h expiry")
    
    def generate_session_key(self, peer_id: str, key_length: int = 32) -> SessionKey:
        """
        Generate a new session key for a peer
        
        Args:
            peer_id: ID of the peer
            key_length: Length of the key in bytes
            
        Returns:
            New session key
        """
        try:
            # Generate unique key ID
            key_id = hashlib.sha256(
                f"{peer_id}_{secrets.token_hex(16)}_{time.time()}".encode()
            ).hexdigest()[:16]
            
            # Generate random key
            key_value = secrets.token_bytes(key_length)
            
            # Set expiry time
            created_at = datetime.utcnow()
            expires_at = created_at + timedelta(hours=self.key_expiry_hours)
            
            session_key = SessionKey(
                key_id=key_id,
                key_value=key_value,
                created_at=created_at.isoformat(),
                expires_at=expires_at.isoformat(),
                status=SessionStatus.ACTIVE,
                peer_id=peer_id
            )
            
            # Store session key
            self.session_keys[key_id] = session_key
            
            # Update peer sessions
            if peer_id not in self.peer_sessions:
                self.peer_sessions[peer_id] = []
            self.peer_sessions[peer_id].append(key_id)
            
            logger.info(f"Generated session key {key_id} for peer {peer_id}")
            return session_key
            
        except Exception as e:
            logger.error(f"Error generating session key: {e}")
            raise
    
    def get_session_key(self, key_id: str) -> Optional[SessionKey]:
        """Get session key by ID"""
        return self.session_keys.get(key_id)
    
    def get_active_session_key(self, peer_id: str) -> Optional[SessionKey]:
        """Get active session key for a peer"""
        if peer_id not in self.peer_sessions:
            return None
        
        for key_id in self.peer_sessions[peer_id]:
            session_key = self.session_keys.get(key_id)
            if session_key and session_key.status == SessionStatus.ACTIVE:
                # Check if key is expired
                expires_at = datetime.fromisoformat(session_key.expires_at)
                if datetime.utcnow() < expires_at:
                    return session_key
                else:
                    session_key.status = SessionStatus.EXPIRED
        
        return None
    
    def revoke_session_key(self, key_id: str) -> bool:
        """Revoke a session key"""
        if key_id in self.session_keys:
            self.session_keys[key_id].status = SessionStatus.REVOKED
            logger.info(f"Revoked session key {key_id}")
            return True
        return False
    
    def revoke_peer_sessions(self, peer_id: str) -> int:
        """Revoke all session keys for a peer"""
        if peer_id not in self.peer_sessions:
            return 0
        
        revoked_count = 0
        for key_id in self.peer_sessions[peer_id]:
            if self.revoke_session_key(key_id):
                revoked_count += 1
        
        logger.info(f"Revoked {revoked_count} session keys for peer {peer_id}")
        return revoked_count
    
    def cleanup_expired_keys(self) -> int:
        """Clean up expired session keys"""
        current_time = datetime.utcnow()
        expired_keys = []
        
        for key_id, session_key in self.session_keys.items():
            expires_at = datetime.fromisoformat(session_key.expires_at)
            if current_time >= expires_at and session_key.status == SessionStatus.ACTIVE:
                session_key.status = SessionStatus.EXPIRED
                expired_keys.append(key_id)
        
        logger.info(f"Marked {len(expired_keys)} session keys as expired")
        return len(expired_keys)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session key statistics"""
        active_count = sum(1 for key in self.session_keys.values() if key.status == SessionStatus.ACTIVE)
        expired_count = sum(1 for key in self.session_keys.values() if key.status == SessionStatus.EXPIRED)
        revoked_count = sum(1 for key in self.session_keys.values() if key.status == SessionStatus.REVOKED)
        
        return {
            "total_keys": len(self.session_keys),
            "active_keys": active_count,
            "expired_keys": expired_count,
            "revoked_keys": revoked_count,
            "total_peers": len(self.peer_sessions)
        }


class HMACMessageProtector:
    """
    Protects P2P messages with HMAC-SHA256
    """
    
    def __init__(self, session_key_manager: SessionKeyManager):
        """
        Initialize HMAC message protector
        
        Args:
            session_key_manager: Session key manager instance
        """
        self.session_key_manager = session_key_manager
        self.message_cache: Dict[str, str] = {}  # message_id -> timestamp
        self.cache_ttl_seconds = 300  # 5 minutes
        
        logger.info("HMAC Message Protector initialized")
    
    def protect_message(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        sender_id: str,
        recipient_id: str,
        session_key_id: Optional[str] = None
    ) -> Optional[ProtectedMessage]:
        """
        Protect a message with HMAC
        
        Args:
            message_type: Type of message
            payload: Message payload
            sender_id: Sender node ID
            recipient_id: Recipient node ID
            session_key_id: Optional specific session key ID
            
        Returns:
            Protected message or None if failed
        """
        try:
            # Get session key
            if session_key_id:
                session_key = self.session_key_manager.get_session_key(session_key_id)
            else:
                session_key = self.session_key_manager.get_active_session_key(recipient_id)
            
            if not session_key:
                logger.error(f"No active session key found for recipient {recipient_id}")
                return None
            
            # Generate message ID
            message_id = hashlib.sha256(
                f"{sender_id}_{recipient_id}_{time.time()}_{secrets.token_hex(8)}".encode()
            ).hexdigest()[:16]
            
            # Generate nonce
            nonce = secrets.token_hex(16)
            
            # Create message data
            timestamp = datetime.utcnow().isoformat()
            message_data = {
                "message_id": message_id,
                "message_type": message_type.value,
                "payload": payload,
                "timestamp": timestamp,
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "nonce": nonce,
                "version": "1.0"
            }
            
            # Create HMAC signature
            hmac_signature = self._create_hmac_signature(message_data, session_key.key_value)
            
            # Create protected message
            protected_message = ProtectedMessage(
                message_id=message_id,
                message_type=message_type,
                payload=payload,
                timestamp=timestamp,
                sender_id=sender_id,
                recipient_id=recipient_id,
                hmac_signature=hmac_signature,
                session_key_id=session_key.key_id,
                nonce=nonce
            )
            
            # Update session key usage
            session_key.usage_count += 1
            session_key.last_used = timestamp
            
            # Cache message ID
            self.message_cache[message_id] = timestamp
            
            logger.info(f"Protected message {message_id} of type {message_type.value}")
            return protected_message
            
        except Exception as e:
            logger.error(f"Error protecting message: {e}")
            return None
    
    def _create_hmac_signature(self, message_data: Dict[str, Any], key: bytes) -> str:
        """Create HMAC signature for message data"""
        # Sort data for consistent hashing
        sorted_data = json.dumps(message_data, sort_keys=True)
        
        # Create HMAC-SHA256 signature
        signature = hmac.new(
            key,
            sorted_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def validate_message(self, protected_message: ProtectedMessage) -> MessageValidationResult:
        """
        Validate a protected message
        
        Args:
            protected_message: Protected message to validate
            
        Returns:
            Validation result
        """
        try:
            # Get session key
            session_key = self.session_key_manager.get_session_key(protected_message.session_key_id)
            if not session_key:
                return MessageValidationResult(
                    is_valid=False,
                    error_message=f"Session key {protected_message.session_key_id} not found"
                )
            
            # Check session key status
            if session_key.status != SessionStatus.ACTIVE:
                return MessageValidationResult(
                    is_valid=False,
                    error_message=f"Session key {protected_message.session_key_id} is not active"
                )
            
            # Check if key is expired
            expires_at = datetime.fromisoformat(session_key.expires_at)
            if datetime.utcnow() >= expires_at:
                session_key.status = SessionStatus.EXPIRED
                return MessageValidationResult(
                    is_valid=False,
                    error_message=f"Session key {protected_message.session_key_id} has expired"
                )
            
            # Check for replay attacks
            if protected_message.message_id in self.message_cache:
                cached_time = self.message_cache[protected_message.message_id]
                cached_timestamp = datetime.fromisoformat(cached_time)
                if datetime.utcnow() - cached_timestamp < timedelta(seconds=self.cache_ttl_seconds):
                    return MessageValidationResult(
                        is_valid=False,
                        error_message="Potential replay attack detected"
                    )
            
            # Recreate message data for validation
            message_data = {
                "message_id": protected_message.message_id,
                "message_type": protected_message.message_type.value,
                "payload": protected_message.payload,
                "timestamp": protected_message.timestamp,
                "sender_id": protected_message.sender_id,
                "recipient_id": protected_message.recipient_id,
                "nonce": protected_message.nonce,
                "version": protected_message.version
            }
            
            # Verify HMAC signature
            expected_signature = self._create_hmac_signature(message_data, session_key.key_value)
            if not hmac.compare_digest(protected_message.hmac_signature, expected_signature):
                return MessageValidationResult(
                    is_valid=False,
                    error_message="HMAC signature verification failed"
                )
            
            # Check timestamp (prevent old messages)
            message_time = datetime.fromisoformat(protected_message.timestamp)
            if datetime.utcnow() - message_time > timedelta(minutes=10):
                return MessageValidationResult(
                    is_valid=False,
                    error_message="Message timestamp is too old"
                )
            
            # Update session key usage
            session_key.usage_count += 1
            session_key.last_used = protected_message.timestamp
            
            # Cache message ID
            self.message_cache[protected_message.message_id] = protected_message.timestamp
            
            logger.info(f"Message {protected_message.message_id} validated successfully")
            return MessageValidationResult(
                is_valid=True,
                message=protected_message,
                session_key=session_key
            )
            
        except Exception as e:
            logger.error(f"Error validating message: {e}")
            return MessageValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )
    
    def cleanup_message_cache(self) -> int:
        """Clean up expired message cache entries"""
        current_time = datetime.utcnow()
        expired_entries = []
        
        for message_id, timestamp_str in self.message_cache.items():
            timestamp = datetime.fromisoformat(timestamp_str)
            if current_time - timestamp > timedelta(seconds=self.cache_ttl_seconds):
                expired_entries.append(message_id)
        
        for message_id in expired_entries:
            del self.message_cache[message_id]
        
        logger.info(f"Cleaned up {len(expired_entries)} expired cache entries")
        return len(expired_entries)


class P2PNetworkSecurity:
    """
    Main security manager for P2P network communications
    """
    
    def __init__(self, node_id: str):
        """
        Initialize P2P network security
        
        Args:
            node_id: Unique node identifier
        """
        self.node_id = node_id
        self.session_key_manager = SessionKeyManager()
        self.message_protector = HMACMessageProtector(self.session_key_manager)
        self.trusted_peers: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"P2P Network Security initialized for node {node_id}")
    
    def establish_secure_session(self, peer_id: str) -> Optional[SessionKey]:
        """
        Establish secure session with a peer
        
        Args:
            peer_id: Peer node ID
            
        Returns:
            Session key or None if failed
        """
        try:
            # Generate session key for peer
            session_key = self.session_key_manager.generate_session_key(peer_id)
            
            # Add to trusted peers
            self.trusted_peers[peer_id] = {
                "session_key_id": session_key.key_id,
                "established_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
            logger.info(f"Established secure session with peer {peer_id}")
            return session_key
            
        except Exception as e:
            logger.error(f"Error establishing secure session: {e}")
            return None
    
    def send_secure_message(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        recipient_id: str
    ) -> Optional[ProtectedMessage]:
        """
        Send a secure message to a peer
        
        Args:
            message_type: Type of message
            payload: Message payload
            recipient_id: Recipient node ID
            
        Returns:
            Protected message or None if failed
        """
        try:
            # Check if we have a session with the peer
            if recipient_id not in self.trusted_peers:
                logger.error(f"No secure session with peer {recipient_id}")
                return None
            
            # Protect message
            protected_message = self.message_protector.protect_message(
                message_type=message_type,
                payload=payload,
                sender_id=self.node_id,
                recipient_id=recipient_id
            )
            
            if protected_message:
                logger.info(f"Sent secure message {protected_message.message_id} to {recipient_id}")
            
            return protected_message
            
        except Exception as e:
            logger.error(f"Error sending secure message: {e}")
            return None
    
    def receive_secure_message(self, protected_message: ProtectedMessage) -> MessageValidationResult:
        """
        Receive and validate a secure message
        
        Args:
            protected_message: Protected message to validate
            
        Returns:
            Validation result
        """
        try:
            # Validate message
            result = self.message_protector.validate_message(protected_message)
            
            if result.is_valid:
                logger.info(f"Received valid secure message {protected_message.message_id}")
            else:
                logger.warning(f"Received invalid secure message: {result.error_message}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error receiving secure message: {e}")
            return MessageValidationResult(
                is_valid=False,
                error_message=f"Receive error: {str(e)}"
            )
    
    def revoke_peer_session(self, peer_id: str) -> bool:
        """Revoke secure session with a peer"""
        try:
            if peer_id in self.trusted_peers:
                del self.trusted_peers[peer_id]
            
            revoked_count = self.session_key_manager.revoke_peer_sessions(peer_id)
            
            logger.info(f"Revoked secure session with peer {peer_id}")
            return revoked_count > 0
            
        except Exception as e:
            logger.error(f"Error revoking peer session: {e}")
            return False
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        session_stats = self.session_key_manager.get_session_stats()
        
        return {
            "node_id": self.node_id,
            "trusted_peers": len(self.trusted_peers),
            "session_keys": session_stats,
            "message_cache_size": len(self.message_protector.message_cache)
        }


def main():
    """Command line interface for HMAC message protection"""
    parser = argparse.ArgumentParser(description="DRP HMAC Message Protection Demo")
    parser.add_argument("--demo", action="store_true", help="Run demonstration")
    parser.add_argument("--node-id", default="node_001", help="Node ID")
    
    args = parser.parse_args()
    
    try:
        # Initialize P2P network security
        network_security = P2PNetworkSecurity(args.node_id)
        
        print(f"🔐 P2P Network Security Initialized")
        print(f"   Node ID: {args.node_id}")
        
        if args.demo:
            print(f"\n🛡️ HMAC Message Protection Demo")
            print(f"=" * 50)
            
            # Establish secure sessions with peers
            print(f"Establishing secure sessions...")
            peer_ids = ["peer_001", "peer_002", "peer_003"]
            
            for peer_id in peer_ids:
                session_key = network_security.establish_secure_session(peer_id)
                if session_key:
                    print(f"   ✅ Session established with {peer_id}")
                    print(f"      Key ID: {session_key.key_id}")
                    print(f"      Expires: {session_key.expires_at}")
                else:
                    print(f"   ❌ Failed to establish session with {peer_id}")
            
            # Send secure messages
            print(f"\n📤 Sending secure messages...")
            
            # Block proposal message
            block_payload = {
                "block_number": 12345,
                "block_hash": "0xabcdef1234567890",
                "transactions": ["tx1", "tx2", "tx3"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            protected_message = network_security.send_secure_message(
                MessageType.BLOCK_PROPOSAL,
                block_payload,
                "peer_001"
            )
            
            if protected_message:
                print(f"   ✅ Sent block proposal message")
                print(f"      Message ID: {protected_message.message_id}")
                print(f"      HMAC: {protected_message.hmac_signature[:16]}...")
            
            # AI verification message
            ai_payload = {
                "verification_type": "face_verification",
                "user_id": "user_123",
                "verification_hash": "0xhash123456789",
                "confidence": 0.95,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            ai_message = network_security.send_secure_message(
                MessageType.AI_VERIFICATION,
                ai_payload,
                "peer_002"
            )
            
            if ai_message:
                print(f"   ✅ Sent AI verification message")
                print(f"      Message ID: {ai_message.message_id}")
            
            # Simulate receiving and validating messages
            print(f"\n📥 Validating received messages...")
            
            if protected_message:
                # Simulate receiving the message
                validation_result = network_security.receive_secure_message(protected_message)
                
                if validation_result.is_valid:
                    print(f"   ✅ Message {protected_message.message_id} validated successfully")
                    print(f"      Type: {protected_message.message_type.value}")
                    print(f"      Sender: {protected_message.sender_id}")
                else:
                    print(f"   ❌ Message validation failed: {validation_result.error_message}")
            
            # Test with tampered message
            print(f"\n🔍 Testing message tampering detection...")
            if protected_message:
                # Tamper with the message
                tampered_message = ProtectedMessage(
                    message_id=protected_message.message_id,
                    message_type=protected_message.message_type,
                    payload={"tampered": True},  # Tampered payload
                    timestamp=protected_message.timestamp,
                    sender_id=protected_message.sender_id,
                    recipient_id=protected_message.recipient_id,
                    hmac_signature=protected_message.hmac_signature,
                    session_key_id=protected_message.session_key_id,
                    nonce=protected_message.nonce
                )
                
                tamper_result = network_security.receive_secure_message(tampered_message)
                print(f"   Tampered message validation: {'❌ Failed (expected)' if not tamper_result.is_valid else '✅ Passed (unexpected)'}")
                if not tamper_result.is_valid:
                    print(f"      Error: {tamper_result.error_message}")
            
            # Show security statistics
            print(f"\n📊 Security Statistics:")
            stats = network_security.get_security_stats()
            for key, value in stats.items():
                if isinstance(value, dict):
                    print(f"   {key}:")
                    for sub_key, sub_value in value.items():
                        print(f"      {sub_key}: {sub_value}")
                else:
                    print(f"   {key}: {value}")
            
            # Cleanup
            print(f"\n🧹 Cleanup...")
            network_security.session_key_manager.cleanup_expired_keys()
            network_security.message_protector.cleanup_message_cache()
            print(f"   Cleanup completed")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())


