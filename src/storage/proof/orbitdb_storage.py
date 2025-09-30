"""
DRP Proof Storage - OrbitDB/IPFS
Stores IoT/app logs and proofs with hash-linking and DRP ledger references
"""

import json
import logging
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path

try:
    from orbitdb import OrbitDB
    from ipfshttpclient import connect
except ImportError:
    OrbitDB = None
    connect = None
    logging.warning("OrbitDB/IPFS not available. Install with: pip install orbitdb ipfshttpclient")

class IoTLogEntry:
    """IoT log entry structure"""
    def __init__(self, device_id: str, timestamp: float, log_type: str, 
                 data: Dict[str, Any], metadata: Dict[str, Any] = None):
        self.device_id = device_id
        self.timestamp = timestamp
        self.log_type = log_type
        self.data = data
        self.metadata = metadata or {}
        self.hash = self.calculate_hash()
        self.drp_references = []  # References to DRP blocks
    
    def calculate_hash(self) -> str:
        """Calculate hash of the log entry"""
        content = json.dumps({
            "device_id": self.device_id,
            "timestamp": self.timestamp,
            "log_type": self.log_type,
            "data": self.data,
            "metadata": self.metadata
        }, sort_keys=True).encode()
        return hashlib.sha256(content).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "device_id": self.device_id,
            "timestamp": self.timestamp,
            "log_type": self.log_type,
            "data": self.data,
            "metadata": self.metadata,
            "hash": self.hash,
            "drp_references": self.drp_references
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IoTLogEntry':
        """Create from dictionary"""
        entry = cls(
            device_id=data["device_id"],
            timestamp=data["timestamp"],
            log_type=data["log_type"],
            data=data["data"],
            metadata=data.get("metadata", {})
        )
        entry.drp_references = data.get("drp_references", [])
        return entry

class ProofSubmission:
    """Proof submission structure"""
    def __init__(self, submission_id: str, proof_type: str, proof_data: Dict[str, Any],
                 submitter_id: str, timestamp: float, drp_block_hash: str = None):
        self.submission_id = submission_id
        self.proof_type = proof_type
        self.proof_data = proof_data
        self.submitter_id = submitter_id
        self.timestamp = timestamp
        self.drp_block_hash = drp_block_hash
        self.hash = self.calculate_hash()
        self.validation_status = "pending"
        self.validators = []
    
    def calculate_hash(self) -> str:
        """Calculate hash of the proof submission"""
        content = json.dumps({
            "submission_id": self.submission_id,
            "proof_type": self.proof_type,
            "proof_data": self.proof_data,
            "submitter_id": self.submitter_id,
            "timestamp": self.timestamp,
            "drp_block_hash": self.drp_block_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(content).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "submission_id": self.submission_id,
            "proof_type": self.proof_type,
            "proof_data": self.proof_data,
            "submitter_id": self.submitter_id,
            "timestamp": self.timestamp,
            "drp_block_hash": self.drp_block_hash,
            "hash": self.hash,
            "validation_status": self.validation_status,
            "validators": self.validators
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProofSubmission':
        """Create from dictionary"""
        submission = cls(
            submission_id=data["submission_id"],
            proof_type=data["proof_type"],
            proof_data=data["proof_data"],
            submitter_id=data["submitter_id"],
            timestamp=data["timestamp"],
            drp_block_hash=data.get("drp_block_hash")
        )
        submission.validation_status = data.get("validation_status", "pending")
        submission.validators = data.get("validators", [])
        return submission

class OrbitDBProofStorage:
    """OrbitDB-based proof storage for IoT logs and proofs"""
    
    def __init__(self, ipfs_host: str = "localhost", ipfs_port: int = 5001,
                 orbitdb_path: str = "./orbitdb"):
        self.ipfs_host = ipfs_host
        self.ipfs_port = ipfs_port
        self.orbitdb_path = Path(orbitdb_path)
        self.orbitdb_path.mkdir(parents=True, exist_ok=True)
        
        self.ipfs_client = None
        self.orbitdb = None
        self.iot_logs_db = None
        self.proof_submissions_db = None
        
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize IPFS and OrbitDB connections"""
        if connect is None or OrbitDB is None:
            raise ImportError("OrbitDB/IPFS not available. Install with: pip install orbitdb ipfshttpclient")
        
        try:
            # Connect to IPFS
            self.ipfs_client = connect(f"/ip4/{self.ipfs_host}/tcp/{self.ipfs_port}/http")
            logging.info(f"Connected to IPFS at {self.ipfs_host}:{self.ipfs_port}")
            
            # Initialize OrbitDB
            self.orbitdb = OrbitDB(self.ipfs_client)
            logging.info("OrbitDB initialized")
            
            # Create or open databases
            self._initialize_databases()
            
        except Exception as e:
            logging.error(f"Failed to initialize OrbitDB/IPFS: {e}")
            raise
    
    def _initialize_databases(self):
        """Initialize the required databases"""
        try:
            # IoT Logs database
            self.iot_logs_db = self.orbitdb.open("drp-iot-logs", create=True)
            logging.info("IoT logs database opened")
            
            # Proof submissions database
            self.proof_submissions_db = self.orbitdb.open("drp-proof-submissions", create=True)
            logging.info("Proof submissions database opened")
            
        except Exception as e:
            logging.error(f"Failed to initialize databases: {e}")
            raise
    
    def store_iot_log(self, log_entry: IoTLogEntry) -> str:
        """Store an IoT log entry"""
        try:
            log_data = log_entry.to_dict()
            log_data["_id"] = log_entry.hash
            
            # Store in OrbitDB
            result = self.iot_logs_db.put(log_data)
            
            # Also store raw data in IPFS
            ipfs_hash = self._store_in_ipfs(log_data)
            log_data["ipfs_hash"] = ipfs_hash
            
            # Update with IPFS hash
            self.iot_logs_db.put(log_data)
            
            logging.info(f"Stored IoT log {log_entry.hash} with IPFS hash {ipfs_hash}")
            return log_entry.hash
            
        except Exception as e:
            logging.error(f"Failed to store IoT log: {e}")
            raise
    
    def store_proof_submission(self, submission: ProofSubmission) -> str:
        """Store a proof submission"""
        try:
            submission_data = submission.to_dict()
            submission_data["_id"] = submission.hash
            
            # Store in OrbitDB
            result = self.proof_submissions_db.put(submission_data)
            
            # Also store raw data in IPFS
            ipfs_hash = self._store_in_ipfs(submission_data)
            submission_data["ipfs_hash"] = ipfs_hash
            
            # Update with IPFS hash
            self.proof_submissions_db.put(submission_data)
            
            logging.info(f"Stored proof submission {submission.hash} with IPFS hash {ipfs_hash}")
            return submission.hash
            
        except Exception as e:
            logging.error(f"Failed to store proof submission: {e}")
            raise
    
    def _store_in_ipfs(self, data: Dict[str, Any]) -> str:
        """Store data in IPFS and return hash"""
        try:
            # Convert to JSON bytes
            json_data = json.dumps(data, indent=2).encode('utf-8')
            
            # Add to IPFS
            result = self.ipfs_client.add(json_data)
            return result['Hash']
            
        except Exception as e:
            logging.error(f"Failed to store in IPFS: {e}")
            raise
    
    def get_iot_log(self, log_hash: str) -> Optional[IoTLogEntry]:
        """Retrieve an IoT log entry"""
        try:
            log_data = self.iot_logs_db.get(log_hash)
            if log_data:
                return IoTLogEntry.from_dict(log_data)
            return None
        except Exception as e:
            logging.error(f"Failed to get IoT log {log_hash}: {e}")
            return None
    
    def get_proof_submission(self, submission_hash: str) -> Optional[ProofSubmission]:
        """Retrieve a proof submission"""
        try:
            submission_data = self.proof_submissions_db.get(submission_hash)
            if submission_data:
                return ProofSubmission.from_dict(submission_data)
            return None
        except Exception as e:
            logging.error(f"Failed to get proof submission {submission_hash}: {e}")
            return None
    
    def get_iot_logs_by_device(self, device_id: str, limit: int = 100) -> List[IoTLogEntry]:
        """Get IoT logs for a specific device"""
        try:
            logs = []
            for log_data in self.iot_logs_db.query(lambda doc: doc.get("device_id") == device_id):
                logs.append(IoTLogEntry.from_dict(log_data))
            
            # Sort by timestamp descending and limit
            logs.sort(key=lambda x: x.timestamp, reverse=True)
            return logs[:limit]
            
        except Exception as e:
            logging.error(f"Failed to get IoT logs for device {device_id}: {e}")
            return []
    
    def get_proof_submissions_by_type(self, proof_type: str, limit: int = 100) -> List[ProofSubmission]:
        """Get proof submissions by type"""
        try:
            submissions = []
            for submission_data in self.proof_submissions_db.query(
                lambda doc: doc.get("proof_type") == proof_type):
                submissions.append(ProofSubmission.from_dict(submission_data))
            
            # Sort by timestamp descending and limit
            submissions.sort(key=lambda x: x.timestamp, reverse=True)
            return submissions[:limit]
            
        except Exception as e:
            logging.error(f"Failed to get proof submissions by type {proof_type}: {e}")
            return []
    
    def link_to_drp_block(self, proof_hash: str, drp_block_hash: str) -> bool:
        """Link a proof to a DRP block"""
        try:
            # Update IoT log if it exists
            log_data = self.iot_logs_db.get(proof_hash)
            if log_data:
                if "drp_references" not in log_data:
                    log_data["drp_references"] = []
                if drp_block_hash not in log_data["drp_references"]:
                    log_data["drp_references"].append(drp_block_hash)
                self.iot_logs_db.put(log_data)
            
            # Update proof submission if it exists
            submission_data = self.proof_submissions_db.get(proof_hash)
            if submission_data:
                submission_data["drp_block_hash"] = drp_block_hash
                self.proof_submissions_db.put(submission_data)
            
            logging.info(f"Linked proof {proof_hash} to DRP block {drp_block_hash}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to link proof to DRP block: {e}")
            return False
    
    def get_proofs_linked_to_block(self, drp_block_hash: str) -> List[Dict[str, Any]]:
        """Get all proofs linked to a specific DRP block"""
        try:
            linked_proofs = []
            
            # Search IoT logs
            for log_data in self.iot_logs_db.query(
                lambda doc: drp_block_hash in doc.get("drp_references", [])):
                linked_proofs.append({
                    "type": "iot_log",
                    "hash": log_data["hash"],
                    "device_id": log_data["device_id"],
                    "timestamp": log_data["timestamp"]
                })
            
            # Search proof submissions
            for submission_data in self.proof_submissions_db.query(
                lambda doc: doc.get("drp_block_hash") == drp_block_hash):
                linked_proofs.append({
                    "type": "proof_submission",
                    "hash": submission_data["hash"],
                    "proof_type": submission_data["proof_type"],
                    "submitter_id": submission_data["submitter_id"],
                    "timestamp": submission_data["timestamp"]
                })
            
            return linked_proofs
            
        except Exception as e:
            logging.error(f"Failed to get proofs linked to block {drp_block_hash}: {e}")
            return []
    
    def validate_proof(self, submission_hash: str, validator_id: str, is_valid: bool) -> bool:
        """Validate a proof submission"""
        try:
            submission_data = self.proof_submissions_db.get(submission_hash)
            if not submission_data:
                return False
            
            # Add validator
            validator_entry = {
                "validator_id": validator_id,
                "is_valid": is_valid,
                "timestamp": datetime.now().timestamp()
            }
            
            if "validators" not in submission_data:
                submission_data["validators"] = []
            
            submission_data["validators"].append(validator_entry)
            
            # Update validation status based on consensus
            valid_count = sum(1 for v in submission_data["validators"] if v["is_valid"])
            total_count = len(submission_data["validators"])
            
            if total_count >= 3:  # Require 3 validators for consensus
                submission_data["validation_status"] = "valid" if valid_count >= 2 else "invalid"
            
            self.proof_submissions_db.put(submission_data)
            
            logging.info(f"Validated proof {submission_hash} by {validator_id}: {is_valid}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to validate proof: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            iot_logs_count = len(list(self.iot_logs_db.query()))
            proof_submissions_count = len(list(self.proof_submissions_db.query()))
            
            return {
                "iot_logs_count": iot_logs_count,
                "proof_submissions_count": proof_submissions_count,
                "total_entries": iot_logs_count + proof_submissions_count,
                "ipfs_connected": self.ipfs_client is not None,
                "orbitdb_connected": self.orbitdb is not None
            }
            
        except Exception as e:
            logging.error(f"Failed to get storage stats: {e}")
            return {"error": str(e)}
    
    def close(self):
        """Close connections"""
        try:
            if self.iot_logs_db:
                self.iot_logs_db.close()
            if self.proof_submissions_db:
                self.proof_submissions_db.close()
            if self.orbitdb:
                self.orbitdb.close()
            if self.ipfs_client:
                self.ipfs_client.close()
            logging.info("OrbitDB/IPFS connections closed")
        except Exception as e:
            logging.error(f"Error closing connections: {e}")

# Mock implementation for testing when OrbitDB/IPFS is not available
class MockOrbitDBProofStorage:
    """Mock OrbitDB proof storage for testing"""
    
    def __init__(self, ipfs_host: str = "localhost", ipfs_port: int = 5001,
                 orbitdb_path: str = "./orbitdb"):
        self.iot_logs = {}
        self.proof_submissions = {}
        logging.info("Mock OrbitDB proof storage initialized")
    
    def store_iot_log(self, log_entry: IoTLogEntry) -> str:
        """Mock store IoT log"""
        self.iot_logs[log_entry.hash] = log_entry.to_dict()
        logging.info(f"Mock stored IoT log {log_entry.hash}")
        return log_entry.hash
    
    def store_proof_submission(self, submission: ProofSubmission) -> str:
        """Mock store proof submission"""
        self.proof_submissions[submission.hash] = submission.to_dict()
        logging.info(f"Mock stored proof submission {submission.hash}")
        return submission.hash
    
    def get_iot_log(self, log_hash: str) -> Optional[IoTLogEntry]:
        """Mock get IoT log"""
        log_data = self.iot_logs.get(log_hash)
        return IoTLogEntry.from_dict(log_data) if log_data else None
    
    def get_proof_submission(self, submission_hash: str) -> Optional[ProofSubmission]:
        """Mock get proof submission"""
        submission_data = self.proof_submissions.get(submission_hash)
        return ProofSubmission.from_dict(submission_data) if submission_data else None
    
    def get_iot_logs_by_device(self, device_id: str, limit: int = 100) -> List[IoTLogEntry]:
        """Mock get IoT logs by device"""
        logs = []
        for log_data in self.iot_logs.values():
            if log_data.get("device_id") == device_id:
                logs.append(IoTLogEntry.from_dict(log_data))
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        return logs[:limit]
    
    def get_proof_submissions_by_type(self, proof_type: str, limit: int = 100) -> List[ProofSubmission]:
        """Mock get proof submissions by type"""
        submissions = []
        for submission_data in self.proof_submissions.values():
            if submission_data.get("proof_type") == proof_type:
                submissions.append(ProofSubmission.from_dict(submission_data))
        submissions.sort(key=lambda x: x.timestamp, reverse=True)
        return submissions[:limit]
    
    def link_to_drp_block(self, proof_hash: str, drp_block_hash: str) -> bool:
        """Mock link to DRP block"""
        if proof_hash in self.iot_logs:
            if "drp_references" not in self.iot_logs[proof_hash]:
                self.iot_logs[proof_hash]["drp_references"] = []
            if drp_block_hash not in self.iot_logs[proof_hash]["drp_references"]:
                self.iot_logs[proof_hash]["drp_references"].append(drp_block_hash)
        
        if proof_hash in self.proof_submissions:
            self.proof_submissions[proof_hash]["drp_block_hash"] = drp_block_hash
        
        logging.info(f"Mock linked proof {proof_hash} to DRP block {drp_block_hash}")
        return True
    
    def get_proofs_linked_to_block(self, drp_block_hash: str) -> List[Dict[str, Any]]:
        """Mock get proofs linked to block"""
        linked_proofs = []
        
        for log_data in self.iot_logs.values():
            if drp_block_hash in log_data.get("drp_references", []):
                linked_proofs.append({
                    "type": "iot_log",
                    "hash": log_data["hash"],
                    "device_id": log_data["device_id"],
                    "timestamp": log_data["timestamp"]
                })
        
        for submission_data in self.proof_submissions.values():
            if submission_data.get("drp_block_hash") == drp_block_hash:
                linked_proofs.append({
                    "type": "proof_submission",
                    "hash": submission_data["hash"],
                    "proof_type": submission_data["proof_type"],
                    "submitter_id": submission_data["submitter_id"],
                    "timestamp": submission_data["timestamp"]
                })
        
        return linked_proofs
    
    def validate_proof(self, submission_hash: str, validator_id: str, is_valid: bool) -> bool:
        """Mock validate proof"""
        if submission_hash in self.proof_submissions:
            submission_data = self.proof_submissions[submission_hash]
            if "validators" not in submission_data:
                submission_data["validators"] = []
            
            submission_data["validators"].append({
                "validator_id": validator_id,
                "is_valid": is_valid,
                "timestamp": datetime.now().timestamp()
            })
            
            valid_count = sum(1 for v in submission_data["validators"] if v["is_valid"])
            total_count = len(submission_data["validators"])
            
            if total_count >= 3:
                submission_data["validation_status"] = "valid" if valid_count >= 2 else "invalid"
            
            logging.info(f"Mock validated proof {submission_hash} by {validator_id}: {is_valid}")
            return True
        return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Mock get storage stats"""
        return {
            "iot_logs_count": len(self.iot_logs),
            "proof_submissions_count": len(self.proof_submissions),
            "total_entries": len(self.iot_logs) + len(self.proof_submissions),
            "ipfs_connected": False,
            "orbitdb_connected": False
        }
    
    def close(self):
        """Mock close"""
        logging.info("Mock OrbitDB proof storage closed")

# Factory function to create appropriate storage instance
def create_proof_storage(ipfs_host: str = "localhost", ipfs_port: int = 5001,
                        orbitdb_path: str = "./orbitdb") -> OrbitDBProofStorage:
    """Create a proof storage instance, falling back to mock if OrbitDB/IPFS unavailable"""
    if connect is not None and OrbitDB is not None:
        return OrbitDBProofStorage(ipfs_host, ipfs_port, orbitdb_path)
    else:
        logging.warning("Using mock proof storage - OrbitDB/IPFS not available")
        return MockOrbitDBProofStorage(ipfs_host, ipfs_port, orbitdb_path)
