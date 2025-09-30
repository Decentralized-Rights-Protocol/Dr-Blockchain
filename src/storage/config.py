"""
DRP Storage Configuration
Centralized configuration for all storage layers
"""

import os
from typing import Dict, Any
from pathlib import Path

class StorageConfig:
    """Configuration for DRP storage layers"""
    
    def __init__(self):
        # Ledger Layer (RocksDB) Configuration
        self.ledger = {
            "db_path": os.getenv("DRP_LEDGER_DB_PATH", "./drp_ledger_db"),
            "max_open_files": int(os.getenv("DRP_LEDGER_MAX_OPEN_FILES", "300000")),
            "write_buffer_size": int(os.getenv("DRP_LEDGER_WRITE_BUFFER_SIZE", "67108864")),
            "max_write_buffer_number": int(os.getenv("DRP_LEDGER_MAX_WRITE_BUFFER_NUMBER", "3")),
            "target_file_size_base": int(os.getenv("DRP_LEDGER_TARGET_FILE_SIZE_BASE", "67108864")),
            "max_bytes_for_level_base": int(os.getenv("DRP_LEDGER_MAX_BYTES_FOR_LEVEL_BASE", "268435456")),
            "level0_file_num_compaction_trigger": int(os.getenv("DRP_LEDGER_LEVEL0_FILE_NUM_COMPACTION_TRIGGER", "2")),
            "level0_slowdown_writes_trigger": int(os.getenv("DRP_LEDGER_LEVEL0_SLOWDOWN_WRITES_TRIGGER", "2")),
            "level0_stop_writes_trigger": int(os.getenv("DRP_LEDGER_LEVEL0_STOP_WRITES_TRIGGER", "2")),
            "num_levels": int(os.getenv("DRP_LEDGER_NUM_LEVELS", "4")),
            "max_background_compactions": int(os.getenv("DRP_LEDGER_MAX_BACKGROUND_COMPACTIONS", "2")),
            "max_background_flushes": int(os.getenv("DRP_LEDGER_MAX_BACKGROUND_FLUSHES", "1")),
            "disable_auto_compactions": os.getenv("DRP_LEDGER_DISABLE_AUTO_COMPACTIONS", "false").lower() == "true"
        }
        
        # Indexer Layer (Neo4j) Configuration
        self.indexer = {
            "uri": os.getenv("DRP_NEO4J_URI", "bolt://localhost:7687"),
            "username": os.getenv("DRP_NEO4J_USERNAME", "neo4j"),
            "password": os.getenv("DRP_NEO4J_PASSWORD", "password"),
            "database": os.getenv("DRP_NEO4J_DATABASE", "neo4j"),
            "max_connection_lifetime": int(os.getenv("DRP_NEO4J_MAX_CONNECTION_LIFETIME", "3600")),
            "max_connection_pool_size": int(os.getenv("DRP_NEO4J_MAX_CONNECTION_POOL_SIZE", "50")),
            "connection_acquisition_timeout": int(os.getenv("DRP_NEO4J_CONNECTION_ACQUISITION_TIMEOUT", "60")),
            "encrypted": os.getenv("DRP_NEO4J_ENCRYPTED", "false").lower() == "true"
        }
        
        # Proof Storage (OrbitDB/IPFS) Configuration
        self.proof_storage = {
            "ipfs_host": os.getenv("DRP_IPFS_HOST", "localhost"),
            "ipfs_port": int(os.getenv("DRP_IPFS_PORT", "5001")),
            "ipfs_protocol": os.getenv("DRP_IPFS_PROTOCOL", "http"),
            "orbitdb_path": os.getenv("DRP_ORBITDB_PATH", "./orbitdb"),
            "iot_logs_db_name": os.getenv("DRP_IOT_LOGS_DB_NAME", "drp-iot-logs"),
            "proof_submissions_db_name": os.getenv("DRP_PROOF_SUBMISSIONS_DB_NAME", "drp-proof-submissions"),
            "max_file_size": int(os.getenv("DRP_IPFS_MAX_FILE_SIZE", "104857600")),  # 100MB
            "timeout": int(os.getenv("DRP_IPFS_TIMEOUT", "30")),
            "retry_attempts": int(os.getenv("DRP_IPFS_RETRY_ATTEMPTS", "3"))
        }
        
        # Explorer API Configuration
        self.explorer_api = {
            "host": os.getenv("DRP_EXPLORER_API_HOST", "0.0.0.0"),
            "port": int(os.getenv("DRP_EXPLORER_API_PORT", "8000")),
            "reload": os.getenv("DRP_EXPLORER_API_RELOAD", "true").lower() == "true",
            "log_level": os.getenv("DRP_EXPLORER_API_LOG_LEVEL", "info"),
            "cors_origins": os.getenv("DRP_EXPLORER_API_CORS_ORIGINS", "*").split(","),
            "max_request_size": int(os.getenv("DRP_EXPLORER_API_MAX_REQUEST_SIZE", "10485760")),  # 10MB
            "request_timeout": int(os.getenv("DRP_EXPLORER_API_REQUEST_TIMEOUT", "30"))
        }
        
        # General Configuration
        self.general = {
            "log_level": os.getenv("DRP_LOG_LEVEL", "INFO"),
            "log_format": os.getenv("DRP_LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            "data_dir": Path(os.getenv("DRP_DATA_DIR", "./drp_data")),
            "backup_enabled": os.getenv("DRP_BACKUP_ENABLED", "true").lower() == "true",
            "backup_interval": int(os.getenv("DRP_BACKUP_INTERVAL", "3600")),  # 1 hour
            "backup_retention_days": int(os.getenv("DRP_BACKUP_RETENTION_DAYS", "30"))
        }
    
    def get_ledger_config(self) -> Dict[str, Any]:
        """Get ledger configuration"""
        return self.ledger.copy()
    
    def get_indexer_config(self) -> Dict[str, Any]:
        """Get indexer configuration"""
        return self.indexer.copy()
    
    def get_proof_storage_config(self) -> Dict[str, Any]:
        """Get proof storage configuration"""
        return self.proof_storage.copy()
    
    def get_explorer_api_config(self) -> Dict[str, Any]:
        """Get explorer API configuration"""
        return self.explorer_api.copy()
    
    def get_general_config(self) -> Dict[str, Any]:
        """Get general configuration"""
        return self.general.copy()
    
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            self.ledger["db_path"],
            self.proof_storage["orbitdb_path"],
            self.general["data_dir"],
            self.general["data_dir"] / "backups"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        try:
            # Validate paths
            self.create_directories()
            
            # Validate numeric values
            assert self.ledger["max_open_files"] > 0
            assert self.ledger["write_buffer_size"] > 0
            assert self.indexer["max_connection_pool_size"] > 0
            assert self.proof_storage["ipfs_port"] > 0
            assert self.explorer_api["port"] > 0
            
            # Validate Neo4j URI format
            assert self.indexer["uri"].startswith(("bolt://", "neo4j://"))
            
            return True
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False

# Global configuration instance
config = StorageConfig()

def get_config() -> StorageConfig:
    """Get the global configuration instance"""
    return config
