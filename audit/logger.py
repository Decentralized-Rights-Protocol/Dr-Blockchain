"""
Audit Logger for DRP
Handles comprehensive logging, auditing, and observability for the decentralized storage system
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
import aiofiles

logger = logging.getLogger(__name__)

class LogLevel(Enum):
    """Log levels for audit events"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class EventType(Enum):
    """Types of audit events"""
    PROOF_SUBMISSION = "proof_submission"
    PROOF_UPLOAD = "proof_upload"
    PROOF_ANCHOR = "proof_anchor"
    PROOF_ERROR = "proof_error"
    ANCHOR_ERROR = "anchor_error"
    ELDER_SIGNATURE = "elder_signature"
    CONSENT_CREATED = "consent_created"
    CONSENT_VALIDATED = "consent_validated"
    CONSENT_REVOKED = "consent_revoked"
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SECURITY_EVENT = "security_event"

class AuditEvent:
    """Represents an audit event"""
    
    def __init__(self,
                 event_type: EventType,
                 event_id: str,
                 timestamp: datetime,
                 level: LogLevel,
                 message: str,
                 data: Dict[str, Any] = None,
                 user_id: str = None,
                 ip_address: str = None,
                 user_agent: str = None):
        self.event_type = event_type
        self.event_id = event_id
        self.timestamp = timestamp
        self.level = level
        self.message = message
        self.data = data or {}
        self.user_id = user_id
        self.ip_address = ip_address
        self.user_agent = user_agent

class AuditLogger:
    """Comprehensive audit logging system"""
    
    def __init__(self,
                 log_directory: str = None,
                 max_log_size_mb: int = 100,
                 max_log_files: int = 10,
                 enable_console_logging: bool = True):
        self.log_directory = log_directory or os.getenv("AUDIT_LOG_DIR", "logs")
        self.max_log_size_mb = max_log_size_mb
        self.max_log_files = max_log_files
        self.enable_console_logging = enable_console_logging
        self.log_file_path = os.path.join(self.log_directory, "audit.log")
        self.error_log_path = os.path.join(self.log_directory, "errors.log")
        self.ready = False
        
    async def initialize(self):
        """Initialize audit logger"""
        try:
            # Create log directory
            os.makedirs(self.log_directory, exist_ok=True)
            
            # Setup logging configuration
            await self._setup_logging()
            
            self.ready = True
            logger.info("Audit logger initialized successfully")
            
            # Log system startup
            await self.log_system_startup()
            
        except Exception as e:
            logger.error(f"Failed to initialize audit logger: {e}")
            self.ready = False
            raise
    
    async def _setup_logging(self):
        """Setup logging configuration"""
        try:
            # Configure root logger
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(self.log_file_path),
                    logging.StreamHandler() if self.enable_console_logging else logging.NullHandler()
                ]
            )
            
            # Configure error logger
            error_handler = logging.FileHandler(self.error_log_path)
            error_handler.setLevel(logging.ERROR)
            error_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            error_handler.setFormatter(error_formatter)
            
            # Add error handler to root logger
            logging.getLogger().addHandler(error_handler)
            
        except Exception as e:
            logger.error(f"Error setting up logging: {e}")
            raise
    
    async def _create_audit_event(self,
                                event_type: EventType,
                                level: LogLevel,
                                message: str,
                                data: Dict[str, Any] = None,
                                user_id: str = None,
                                ip_address: str = None,
                                user_agent: str = None) -> AuditEvent:
        """Create an audit event"""
        event_id = f"{event_type.value}_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        
        return AuditEvent(
            event_type=event_type,
            event_id=event_id,
            timestamp=datetime.now(timezone.utc),
            level=level,
            message=message,
            data=data or {},
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def _write_audit_event(self, event: AuditEvent):
        """Write audit event to log file"""
        try:
            # Create log entry
            log_entry = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "level": event.level.value,
                "message": event.message,
                "data": event.data,
                "user_id": event.user_id,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent
            }
            
            # Write to log file
            log_line = json.dumps(log_entry) + "\n"
            async with aiofiles.open(self.log_file_path, 'a') as f:
                await f.write(log_line)
            
            # Also log to console if enabled
            if self.enable_console_logging:
                log_message = f"[{event.event_type.value}] {event.message}"
                if event.data:
                    log_message += f" | Data: {json.dumps(event.data)}"
                
                if event.level == LogLevel.ERROR:
                    logging.error(log_message)
                elif event.level == LogLevel.WARNING:
                    logging.warning(log_message)
                else:
                    logging.info(log_message)
            
        except Exception as e:
            logger.error(f"Error writing audit event: {e}")
    
    # Proof-related audit methods
    async def log_proof_submission(self, proof_id: str, proof_data: Dict[str, Any]):
        """Log proof submission"""
        event = await self._create_audit_event(
            event_type=EventType.PROOF_SUBMISSION,
            level=LogLevel.INFO,
            message=f"Proof submitted: {proof_id}",
            data={"proof_id": proof_id, "proof_type": proof_data.get("proof_type")},
            user_id=proof_data.get("user_id")
        )
        await self._write_audit_event(event)
    
    async def log_proof_upload(self, proof_id: str, cid: str, duration_ms: float):
        """Log proof upload to IPFS"""
        event = await self._create_audit_event(
            event_type=EventType.PROOF_UPLOAD,
            level=LogLevel.INFO,
            message=f"Proof uploaded to IPFS: {proof_id} -> {cid}",
            data={
                "proof_id": proof_id,
                "cid": cid,
                "duration_ms": duration_ms
            }
        )
        await self._write_audit_event(event)
    
    async def log_blockchain_anchor(self, proof_id: str, block_hash: str):
        """Log blockchain anchoring"""
        event = await self._create_audit_event(
            event_type=EventType.PROOF_ANCHOR,
            level=LogLevel.INFO,
            message=f"Proof anchored to blockchain: {proof_id} -> {block_hash}",
            data={
                "proof_id": proof_id,
                "block_hash": block_hash
            }
        )
        await self._write_audit_event(event)
    
    async def log_proof_error(self, proof_id: str, error_message: str):
        """Log proof processing error"""
        event = await self._create_audit_event(
            event_type=EventType.PROOF_ERROR,
            level=LogLevel.ERROR,
            message=f"Proof processing error: {proof_id}",
            data={
                "proof_id": proof_id,
                "error": error_message
            }
        )
        await self._write_audit_event(event)
    
    async def log_anchor_error(self, proof_id: str, error_message: str):
        """Log blockchain anchoring error"""
        event = await self._create_audit_event(
            event_type=EventType.ANCHOR_ERROR,
            level=LogLevel.ERROR,
            message=f"Blockchain anchoring error: {proof_id}",
            data={
                "proof_id": proof_id,
                "error": error_message
            }
        )
        await self._write_audit_event(event)
    
    # Elder-related audit methods
    async def log_elder_signature(self, elder_id: str, proof_id: str, signature_valid: bool):
        """Log Elder signature event"""
        event = await self._create_audit_event(
            event_type=EventType.ELDER_SIGNATURE,
            level=LogLevel.INFO,
            message=f"Elder signature: {elder_id} for proof {proof_id}",
            data={
                "elder_id": elder_id,
                "proof_id": proof_id,
                "signature_valid": signature_valid
            }
        )
        await self._write_audit_event(event)
    
    # Consent-related audit methods
    async def log_consent_created(self, token_id: str, user_id: str, consent_types: List[str]):
        """Log consent token creation"""
        event = await self._create_audit_event(
            event_type=EventType.CONSENT_CREATED,
            level=LogLevel.INFO,
            message=f"Consent token created: {token_id} for user {user_id}",
            data={
                "token_id": token_id,
                "user_id": user_id,
                "consent_types": consent_types
            },
            user_id=user_id
        )
        await self._write_audit_event(event)
    
    async def log_consent_validated(self, token_id: str, user_id: str, validation_result: bool):
        """Log consent token validation"""
        event = await self._create_audit_event(
            event_type=EventType.CONSENT_VALIDATED,
            level=LogLevel.INFO,
            message=f"Consent token validated: {token_id} for user {user_id}",
            data={
                "token_id": token_id,
                "user_id": user_id,
                "validation_result": validation_result
            },
            user_id=user_id
        )
        await self._write_audit_event(event)
    
    async def log_consent_revoked(self, token_id: str, user_id: str):
        """Log consent token revocation"""
        event = await self._create_audit_event(
            event_type=EventType.CONSENT_REVOKED,
            level=LogLevel.INFO,
            message=f"Consent token revoked: {token_id} for user {user_id}",
            data={
                "token_id": token_id,
                "user_id": user_id
            },
            user_id=user_id
        )
        await self._write_audit_event(event)
    
    # System-related audit methods
    async def log_system_startup(self):
        """Log system startup"""
        event = await self._create_audit_event(
            event_type=EventType.SYSTEM_STARTUP,
            level=LogLevel.INFO,
            message="DRP Decentralized Storage Gateway started",
            data={"version": "1.0.0", "startup_time": datetime.now(timezone.utc).isoformat()}
        )
        await self._write_audit_event(event)
    
    async def log_system_shutdown(self):
        """Log system shutdown"""
        event = await self._create_audit_event(
            event_type=EventType.SYSTEM_SHUTDOWN,
            level=LogLevel.INFO,
            message="DRP Decentralized Storage Gateway shutting down",
            data={"shutdown_time": datetime.now(timezone.utc).isoformat()}
        )
        await self._write_audit_event(event)
    
    async def log_security_event(self, event_description: str, severity: str, data: Dict[str, Any] = None):
        """Log security-related event"""
        level = LogLevel.ERROR if severity == "high" else LogLevel.WARNING
        
        event = await self._create_audit_event(
            event_type=EventType.SECURITY_EVENT,
            level=level,
            message=f"Security event: {event_description}",
            data=data or {}
        )
        await self._write_audit_event(event)
    
    # Query and analysis methods
    async def get_audit_logs(self, 
                           start_time: datetime = None,
                           end_time: datetime = None,
                           event_type: EventType = None,
                           user_id: str = None,
                           limit: int = 1000) -> List[Dict[str, Any]]:
        """Get audit logs with filters"""
        try:
            logs = []
            current_count = 0
            
            async with aiofiles.open(self.log_file_path, 'r') as f:
                async for line in f:
                    if current_count >= limit:
                        break
                    
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # Apply filters
                        if start_time and datetime.fromisoformat(log_entry["timestamp"]) < start_time:
                            continue
                        
                        if end_time and datetime.fromisoformat(log_entry["timestamp"]) > end_time:
                            continue
                        
                        if event_type and log_entry["event_type"] != event_type.value:
                            continue
                        
                        if user_id and log_entry.get("user_id") != user_id:
                            continue
                        
                        logs.append(log_entry)
                        current_count += 1
                        
                    except json.JSONDecodeError:
                        continue
            
            return logs
            
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return []
    
    async def get_audit_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get audit statistics for the last N hours"""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
            
            logs = await self.get_audit_logs(start_time, end_time)
            
            stats = {
                "total_events": len(logs),
                "event_types": {},
                "error_count": 0,
                "warning_count": 0,
                "unique_users": set(),
                "proofs_processed": 0,
                "consent_events": 0
            }
            
            for log in logs:
                # Count by event type
                event_type = log["event_type"]
                stats["event_types"][event_type] = stats["event_types"].get(event_type, 0) + 1
                
                # Count by level
                if log["level"] == "error":
                    stats["error_count"] += 1
                elif log["level"] == "warning":
                    stats["warning_count"] += 1
                
                # Count unique users
                if log.get("user_id"):
                    stats["unique_users"].add(log["user_id"])
                
                # Count specific events
                if event_type in ["proof_submission", "proof_upload", "proof_anchor"]:
                    stats["proofs_processed"] += 1
                elif event_type.startswith("consent_"):
                    stats["consent_events"] += 1
            
            stats["unique_users"] = len(stats["unique_users"])
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting audit statistics: {e}")
            return {}
    
    def is_ready(self) -> bool:
        """Check if audit logger is ready"""
        return self.ready
    
    async def close(self):
        """Close audit logger"""
        if self.ready:
            await self.log_system_shutdown()
        self.ready = False
        logger.info("Audit logger closed")

# Utility functions
async def create_audit_logger(log_directory: str = None) -> AuditLogger:
    """Create and initialize audit logger"""
    audit_logger = AuditLogger(log_directory)
    await audit_logger.initialize()
    return audit_logger
