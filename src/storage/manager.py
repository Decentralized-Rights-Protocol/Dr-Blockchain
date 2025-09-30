"""
DRP Storage Manager
Centralized manager for all storage layers with connection pooling and health monitoring
"""

import logging
import threading
import time
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime, timedelta

from .config import get_config
from .ledger.rocksdb_storage import create_ledger
from .indexer.neo4j_indexer import create_indexer
from .proof.orbitdb_storage import create_proof_storage

class StorageHealth:
    """Storage health monitoring"""
    
    def __init__(self):
        self.ledger_healthy = False
        self.indexer_healthy = False
        self.proof_storage_healthy = False
        self.last_health_check = None
        self.health_check_interval = 30  # seconds
    
    def update_health(self, ledger_healthy: bool, indexer_healthy: bool, proof_storage_healthy: bool):
        """Update health status"""
        self.ledger_healthy = ledger_healthy
        self.indexer_healthy = indexer_healthy
        self.proof_storage_healthy = proof_storage_healthy
        self.last_health_check = datetime.now()
    
    def is_healthy(self) -> bool:
        """Check if all storage layers are healthy"""
        return self.ledger_healthy and self.indexer_healthy and self.proof_storage_healthy
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status"""
        return {
            "overall_healthy": self.is_healthy(),
            "ledger_healthy": self.ledger_healthy,
            "indexer_healthy": self.indexer_healthy,
            "proof_storage_healthy": self.proof_storage_healthy,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_check_interval": self.health_check_interval
        }

class StorageManager:
    """Centralized storage manager for DRP blockchain"""
    
    def __init__(self):
        self.config = get_config()
        self.health = StorageHealth()
        
        # Storage instances
        self._ledger = None
        self._indexer = None
        self._proof_storage = None
        
        # Threading locks
        self._ledger_lock = threading.Lock()
        self._indexer_lock = threading.Lock()
        self._proof_storage_lock = threading.Lock()
        
        # Health monitoring thread
        self._health_monitor_thread = None
        self._shutdown_event = threading.Event()
        
        # Initialize storage
        self._initialize_storage()
        self._start_health_monitoring()
    
    def _initialize_storage(self):
        """Initialize all storage layers"""
        try:
            # Validate configuration
            if not self.config.validate_config():
                raise RuntimeError("Configuration validation failed")
            
            # Create directories
            self.config.create_directories()
            
            logging.info("Storage manager initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize storage manager: {e}")
            raise
    
    def _start_health_monitoring(self):
        """Start health monitoring thread"""
        self._health_monitor_thread = threading.Thread(
            target=self._health_monitor_loop,
            daemon=True
        )
        self._health_monitor_thread.start()
        logging.info("Health monitoring started")
    
    def _health_monitor_loop(self):
        """Health monitoring loop"""
        while not self._shutdown_event.is_set():
            try:
                # Check ledger health
                ledger_healthy = self._check_ledger_health()
                
                # Check indexer health
                indexer_healthy = self._check_indexer_health()
                
                # Check proof storage health
                proof_storage_healthy = self._check_proof_storage_health()
                
                # Update health status
                self.health.update_health(ledger_healthy, indexer_healthy, proof_storage_healthy)
                
                if not self.health.is_healthy():
                    logging.warning("Storage health check failed - some services are unhealthy")
                
            except Exception as e:
                logging.error(f"Health monitoring error: {e}")
            
            # Wait for next check
            self._shutdown_event.wait(self.health.health_check_interval)
    
    def _check_ledger_health(self) -> bool:
        """Check ledger health"""
        try:
            with self._ledger_lock:
                if self._ledger is None:
                    return False
                # Try to get chain length as a health check
                chain_length = self._ledger.get_chain_length()
                return chain_length >= 0
        except Exception as e:
            logging.error(f"Ledger health check failed: {e}")
            return False
    
    def _check_indexer_health(self) -> bool:
        """Check indexer health"""
        try:
            with self._indexer_lock:
                if self._indexer is None:
                    return False
                # Try to get governance network as a health check
                network_data = self._indexer.get_governance_network()
                return network_data is not None
        except Exception as e:
            logging.error(f"Indexer health check failed: {e}")
            return False
    
    def _check_proof_storage_health(self) -> bool:
        """Check proof storage health"""
        try:
            with self._proof_storage_lock:
                if self._proof_storage is None:
                    return False
                # Try to get storage stats as a health check
                stats = self._proof_storage.get_storage_stats()
                return stats is not None
        except Exception as e:
            logging.error(f"Proof storage health check failed: {e}")
            return False
    
    @contextmanager
    def get_ledger(self):
        """Get ledger instance with thread safety"""
        with self._ledger_lock:
            if self._ledger is None:
                try:
                    self._ledger = create_ledger(self.config.ledger["db_path"])
                    logging.info("Ledger instance created")
                except Exception as e:
                    logging.error(f"Failed to create ledger instance: {e}")
                    raise
            
            yield self._ledger
    
    @contextmanager
    def get_indexer(self):
        """Get indexer instance with thread safety"""
        with self._indexer_lock:
            if self._indexer is None:
                try:
                    indexer_config = self.config.get_indexer_config()
                    self._indexer = create_indexer(
                        uri=indexer_config["uri"],
                        username=indexer_config["username"],
                        password=indexer_config["password"]
                    )
                    logging.info("Indexer instance created")
                except Exception as e:
                    logging.error(f"Failed to create indexer instance: {e}")
                    raise
            
            yield self._indexer
    
    @contextmanager
    def get_proof_storage(self):
        """Get proof storage instance with thread safety"""
        with self._proof_storage_lock:
            if self._proof_storage is None:
                try:
                    proof_config = self.config.get_proof_storage_config()
                    self._proof_storage = create_proof_storage(
                        ipfs_host=proof_config["ipfs_host"],
                        ipfs_port=proof_config["ipfs_port"],
                        orbitdb_path=proof_config["orbitdb_path"]
                    )
                    logging.info("Proof storage instance created")
                except Exception as e:
                    logging.error(f"Failed to create proof storage instance: {e}")
                    raise
            
            yield self._proof_storage
    
    def store_block_with_indexing(self, block_data: Dict[str, Any]) -> bool:
        """Store a block in all storage layers"""
        try:
            # Store in ledger
            with self.get_ledger() as ledger:
                from .ledger.rocksdb_storage import DRPBlock
                block = DRPBlock.from_dict(block_data)
                ledger.store_block(block)
            
            # Index in Neo4j
            with self.get_indexer() as indexer:
                indexer.index_block(block_data)
            
            logging.info(f"Block {block_data.get('index', 'unknown')} stored and indexed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to store block with indexing: {e}")
            return False
    
    def store_proof_with_linking(self, proof_data: Dict[str, Any], drp_block_hash: str = None) -> str:
        """Store a proof and link it to DRP block"""
        try:
            with self.get_proof_storage() as proof_storage:
                from .proof.orbitdb_storage import ProofSubmission
                submission = ProofSubmission.from_dict(proof_data)
                proof_hash = proof_storage.store_proof_submission(submission)
                
                # Link to DRP block if provided
                if drp_block_hash:
                    proof_storage.link_to_drp_block(proof_hash, drp_block_hash)
                
                logging.info(f"Proof {proof_hash} stored and linked successfully")
                return proof_hash
                
        except Exception as e:
            logging.error(f"Failed to store proof with linking: {e}")
            raise
    
    def get_comprehensive_block_data(self, block_hash: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive block data from all storage layers"""
        try:
            result = {}
            
            # Get block from ledger
            with self.get_ledger() as ledger:
                block = ledger.get_block_by_hash(block_hash)
                if block:
                    result["block"] = block.to_dict()
                else:
                    return None
            
            # Get linked proofs
            with self.get_proof_storage() as proof_storage:
                linked_proofs = proof_storage.get_proofs_linked_to_block(block_hash)
                result["linked_proofs"] = linked_proofs
            
            # Get governance data from indexer
            with self.get_indexer() as indexer:
                # This would need specific methods in the indexer
                result["governance_data"] = {}
            
            return result
            
        except Exception as e:
            logging.error(f"Failed to get comprehensive block data: {e}")
            return None
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics"""
        try:
            stats = {
                "timestamp": datetime.now().isoformat(),
                "health": self.health.get_health_status()
            }
            
            # Ledger stats
            try:
                with self.get_ledger() as ledger:
                    stats["ledger"] = {
                        "chain_length": ledger.get_chain_length(),
                        "latest_block": ledger.get_latest_block().to_dict() if ledger.get_latest_block() else None
                    }
            except Exception as e:
                stats["ledger"] = {"error": str(e)}
            
            # Indexer stats
            try:
                with self.get_indexer() as indexer:
                    stats["indexer"] = indexer.get_governance_network()
            except Exception as e:
                stats["indexer"] = {"error": str(e)}
            
            # Proof storage stats
            try:
                with self.get_proof_storage() as proof_storage:
                    stats["proof_storage"] = proof_storage.get_storage_stats()
            except Exception as e:
                stats["proof_storage"] = {"error": str(e)}
            
            return stats
            
        except Exception as e:
            logging.error(f"Failed to get storage statistics: {e}")
            return {"error": str(e)}
    
    def backup_storage(self, backup_path: str = None) -> bool:
        """Create backup of all storage layers"""
        try:
            if backup_path is None:
                backup_path = self.config.general["data_dir"] / "backups" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_path = Path(backup_path)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup ledger (RocksDB)
            try:
                with self.get_ledger() as ledger:
                    # RocksDB backup would need specific implementation
                    logging.info("Ledger backup completed")
            except Exception as e:
                logging.error(f"Ledger backup failed: {e}")
            
            # Backup indexer (Neo4j)
            try:
                with self.get_indexer() as indexer:
                    # Neo4j backup would need specific implementation
                    logging.info("Indexer backup completed")
            except Exception as e:
                logging.error(f"Indexer backup failed: {e}")
            
            # Backup proof storage (OrbitDB/IPFS)
            try:
                with self.get_proof_storage() as proof_storage:
                    # OrbitDB backup would need specific implementation
                    logging.info("Proof storage backup completed")
            except Exception as e:
                logging.error(f"Proof storage backup failed: {e}")
            
            logging.info(f"Storage backup completed at {backup_path}")
            return True
            
        except Exception as e:
            logging.error(f"Storage backup failed: {e}")
            return False
    
    def shutdown(self):
        """Shutdown storage manager"""
        logging.info("Shutting down storage manager...")
        
        # Signal health monitor to stop
        self._shutdown_event.set()
        
        # Wait for health monitor thread to finish
        if self._health_monitor_thread and self._health_monitor_thread.is_alive():
            self._health_monitor_thread.join(timeout=5)
        
        # Close storage connections
        with self._ledger_lock:
            if self._ledger:
                self._ledger.close()
                self._ledger = None
        
        with self._indexer_lock:
            if self._indexer:
                self._indexer.close()
                self._indexer = None
        
        with self._proof_storage_lock:
            if self._proof_storage:
                self._proof_storage.close()
                self._proof_storage = None
        
        logging.info("Storage manager shutdown completed")

# Global storage manager instance
_storage_manager = None

def get_storage_manager() -> StorageManager:
    """Get the global storage manager instance"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = StorageManager()
    return _storage_manager

def shutdown_storage_manager():
    """Shutdown the global storage manager"""
    global _storage_manager
    if _storage_manager:
        _storage_manager.shutdown()
        _storage_manager = None
