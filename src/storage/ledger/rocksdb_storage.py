"""
DRP Ledger Layer - RocksDB Storage
Stores DRP blocks, transactions, PoST proofs, PoAT proofs, and Elder quorum signatures
"""

import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    import rocksdb
except ImportError:
    rocksdb = None
    logging.warning("RocksDB not available. Install with: pip install python-rocksdb")

class DRPBlock:
    """Enhanced DRP Block structure for storage"""
    def __init__(self, index: int, previous_hash: str, timestamp: float, 
                 activity: Dict[str, Any], proof: Dict[str, Any], 
                 miner_id: str, elder_signatures: List[Dict[str, Any]] = None,
                 post_proofs: List[Dict[str, Any]] = None,
                 poat_proofs: List[Dict[str, Any]] = None):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.activity = activity
        self.proof = proof
        self.miner_id = miner_id
        self.elder_signatures = elder_signatures or []
        self.post_proofs = post_proofs or []
        self.poat_proofs = poat_proofs or []
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate block hash including all components"""
        import hashlib
        block_content = json.dumps({
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "activity": self.activity,
            "proof": self.proof,
            "miner_id": self.miner_id,
            "elder_signatures": self.elder_signatures,
            "post_proofs": self.post_proofs,
            "poat_proofs": self.poat_proofs
        }, sort_keys=True).encode()
        return hashlib.sha256(block_content).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary for JSON storage"""
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "activity": self.activity,
            "proof": self.proof,
            "miner_id": self.miner_id,
            "elder_signatures": self.elder_signatures,
            "post_proofs": self.post_proofs,
            "poat_proofs": self.poat_proofs,
            "hash": self.hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DRPBlock':
        """Create block from dictionary"""
        block = cls(
            index=data["index"],
            previous_hash=data["previous_hash"],
            timestamp=data["timestamp"],
            activity=data["activity"],
            proof=data["proof"],
            miner_id=data["miner_id"],
            elder_signatures=data.get("elder_signatures", []),
            post_proofs=data.get("post_proofs", []),
            poat_proofs=data.get("poat_proofs", [])
        )
        return block

class RocksDBLedger:
    """RocksDB-based ledger storage for DRP blockchain"""
    
    def __init__(self, db_path: str = "./drp_ledger_db"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.db = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize RocksDB with appropriate options"""
        if rocksdb is None:
            raise ImportError("RocksDB not available. Install with: pip install python-rocksdb")
        
        opts = rocksdb.Options()
        opts.create_if_missing = True
        opts.max_open_files = 300000
        opts.write_buffer_size = 67108864
        opts.max_write_buffer_number = 3
        opts.target_file_size_base = 67108864
        opts.max_bytes_for_level_base = 268435456
        opts.level0_file_num_compaction_trigger = 2
        opts.level0_slowdown_writes_trigger = 2
        opts.level0_stop_writes_trigger = 2
        opts.num_levels = 4
        opts.max_background_compactions = 2
        opts.max_background_flushes = 1
        opts.disable_auto_compactions = False
        
        self.db = rocksdb.DB(str(self.db_path), opts)
        logging.info(f"RocksDB ledger initialized at {self.db_path}")
    
    def store_block(self, block: DRPBlock) -> bool:
        """Store a block in RocksDB"""
        try:
            key = f"block:{block.hash}".encode()
            value = json.dumps(block.to_dict()).encode()
            self.db.put(key, value)
            
            # Also store by index for sequential access
            index_key = f"index:{block.index}".encode()
            self.db.put(index_key, block.hash.encode())
            
            # Store latest block reference
            self.db.put(b"latest_block", block.hash.encode())
            
            logging.info(f"Stored block {block.index} with hash {block.hash}")
            return True
        except Exception as e:
            logging.error(f"Failed to store block: {e}")
            return False
    
    def get_block_by_hash(self, block_hash: str) -> Optional[DRPBlock]:
        """Retrieve block by hash"""
        try:
            key = f"block:{block_hash}".encode()
            value = self.db.get(key)
            if value:
                data = json.loads(value.decode())
                return DRPBlock.from_dict(data)
            return None
        except Exception as e:
            logging.error(f"Failed to get block by hash {block_hash}: {e}")
            return None
    
    def get_block_by_index(self, index: int) -> Optional[DRPBlock]:
        """Retrieve block by index"""
        try:
            index_key = f"index:{index}".encode()
            block_hash = self.db.get(index_key)
            if block_hash:
                return self.get_block_by_hash(block_hash.decode())
            return None
        except Exception as e:
            logging.error(f"Failed to get block by index {index}: {e}")
            return None
    
    def get_latest_block(self) -> Optional[DRPBlock]:
        """Get the latest block"""
        try:
            latest_hash = self.db.get(b"latest_block")
            if latest_hash:
                return self.get_block_by_hash(latest_hash.decode())
            return None
        except Exception as e:
            logging.error(f"Failed to get latest block: {e}")
            return None
    
    def get_chain_length(self) -> int:
        """Get the current chain length"""
        try:
            latest = self.get_latest_block()
            return latest.index + 1 if latest else 0
        except Exception as e:
            logging.error(f"Failed to get chain length: {e}")
            return 0
    
    def get_blocks_range(self, start_index: int, end_index: int) -> List[DRPBlock]:
        """Get blocks in a range"""
        blocks = []
        for i in range(start_index, end_index + 1):
            block = self.get_block_by_index(i)
            if block:
                blocks.append(block)
        return blocks
    
    def search_blocks_by_miner(self, miner_id: str) -> List[DRPBlock]:
        """Search blocks by miner ID"""
        blocks = []
        chain_length = self.get_chain_length()
        
        for i in range(chain_length):
            block = self.get_block_by_index(i)
            if block and block.miner_id == miner_id:
                blocks.append(block)
        
        return blocks
    
    def search_blocks_by_activity_type(self, activity_type: str) -> List[DRPBlock]:
        """Search blocks by activity type"""
        blocks = []
        chain_length = self.get_chain_length()
        
        for i in range(chain_length):
            block = self.get_block_by_index(i)
            if block and activity_type in str(block.activity):
                blocks.append(block)
        
        return blocks
    
    def close(self):
        """Close the database connection"""
        if self.db:
            del self.db
            logging.info("RocksDB ledger closed")

# Mock implementation for testing when RocksDB is not available
class MockRocksDBLedger:
    """Mock RocksDB implementation for testing"""
    
    def __init__(self, db_path: str = "./mock_ledger_db"):
        self.blocks = {}
        self.index_to_hash = {}
        self.latest_hash = None
        logging.info(f"Mock RocksDB ledger initialized at {db_path}")
    
    def store_block(self, block: DRPBlock) -> bool:
        """Store a block in memory"""
        self.blocks[block.hash] = block
        self.index_to_hash[block.index] = block.hash
        self.latest_hash = block.hash
        logging.info(f"Mock stored block {block.index} with hash {block.hash}")
        return True
    
    def get_block_by_hash(self, block_hash: str) -> Optional[DRPBlock]:
        """Retrieve block by hash"""
        return self.blocks.get(block_hash)
    
    def get_block_by_index(self, index: int) -> Optional[DRPBlock]:
        """Retrieve block by index"""
        block_hash = self.index_to_hash.get(index)
        return self.blocks.get(block_hash) if block_hash else None
    
    def get_latest_block(self) -> Optional[DRPBlock]:
        """Get the latest block"""
        return self.blocks.get(self.latest_hash) if self.latest_hash else None
    
    def get_chain_length(self) -> int:
        """Get the current chain length"""
        latest = self.get_latest_block()
        return latest.index + 1 if latest else 0
    
    def get_blocks_range(self, start_index: int, end_index: int) -> List[DRPBlock]:
        """Get blocks in a range"""
        blocks = []
        for i in range(start_index, end_index + 1):
            block = self.get_block_by_index(i)
            if block:
                blocks.append(block)
        return blocks
    
    def search_blocks_by_miner(self, miner_id: str) -> List[DRPBlock]:
        """Search blocks by miner ID"""
        return [block for block in self.blocks.values() if block.miner_id == miner_id]
    
    def search_blocks_by_activity_type(self, activity_type: str) -> List[DRPBlock]:
        """Search blocks by activity type"""
        return [block for block in self.blocks.values() if activity_type in str(block.activity)]
    
    def close(self):
        """Close the mock database"""
        logging.info("Mock RocksDB ledger closed")

# Factory function to create appropriate ledger instance
def create_ledger(db_path: str = "./drp_ledger_db") -> RocksDBLedger:
    """Create a ledger instance, falling back to mock if RocksDB unavailable"""
    if rocksdb is not None:
        return RocksDBLedger(db_path)
    else:
        logging.warning("Using mock ledger - RocksDB not available")
        return MockRocksDBLedger(db_path)
