"""
OrbitDB Manager - Python wrapper for OrbitDB operations.
"""

import subprocess
import json
import os
import hashlib
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OrbitDBManager:
    """
    Manages OrbitDB operations via Node.js bridge.
    Stores block metadata, PoAT results, and PoST claims.
    """
    
    def __init__(self, orbitdb_dir: Optional[Path] = None):
        self.orbitdb_dir = orbitdb_dir or Path(__file__).parent.parent / "orbitdb"
        self.orbitdb_dir.mkdir(parents=True, exist_ok=True)
        
        # Node.js script path
        self.node_script = self.orbitdb_dir / "orbit_manager.js"
        
    def add_entry(self, store_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add entry to OrbitDB store.
        
        Args:
            store_name: 'blocks', 'poat', 'post', etc.
            data: Data to store
        
        Returns:
            {'success': bool, 'cid': str, 'hash': str}
        """
        try:
            # For now, use file-based storage (can be replaced with actual OrbitDB)
            store_file = self.orbitdb_dir / f"{store_name}.jsonl"
            
            entry = {
                'data': data,
                'timestamp': str(datetime.utcnow()),
                'hash': self._hash_data(data)
            }
            
            with open(store_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
            
            cid = entry['hash']  # Simplified CID
            
            logger.info(f"Added entry to {store_name}, CID: {cid[:16]}...")
            
            return {
                'success': True,
                'cid': cid,
                'hash': entry['hash']
            }
        except Exception as e:
            logger.error(f"Error adding OrbitDB entry: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_entries(self, store_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get entries from OrbitDB store."""
        store_file = self.orbitdb_dir / f"{store_name}.jsonl"
        entries = []
        
        if store_file.exists():
            with open(store_file, 'r') as f:
                for line in f:
                    if line.strip():
                        entries.append(json.loads(line))
        
        return entries[-limit:] if limit else entries
    
    def get_peer_address(self) -> str:
        """Get OrbitDB peer address."""
        # In production, this would return the actual peer ID
        peer_id_file = self.orbitdb_dir / "peer_id.txt"
        if peer_id_file.exists():
            return peer_id_file.read_text().strip()
        
        # Generate a mock peer ID
        peer_id = f"/ip4/127.0.0.1/tcp/4001/p2p/{hashlib.sha256(str(self.orbitdb_dir).encode()).hexdigest()[:40]}"
        peer_id_file.write_text(peer_id)
        return peer_id
    
    def _hash_data(self, data: Dict[str, Any]) -> str:
        """Generate hash for data."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

