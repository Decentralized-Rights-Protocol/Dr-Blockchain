"""
Merkle Proof Verifier

This module provides Merkle proof verification for cross-chain interoperability.
"""

import hashlib
from typing import List, Optional


class MerkleProofVerifier:
    """Merkle proof verification utility"""
    
    def __init__(self):
        self.hash_function = hashlib.sha256
    
    async def verify_proof(self, 
                          leaf_hash: str,
                          proof_path: List[str],
                          root_hash: str) -> bool:
        """Verify Merkle proof"""
        
        try:
            current_hash = leaf_hash
            
            for sibling_hash in proof_path:
                # Concatenate and hash (simplified Merkle tree logic)
                combined = current_hash + sibling_hash
                current_hash = self.hash_function(combined.encode()).hexdigest()
            
            return current_hash == root_hash
            
        except Exception:
            return False
    
    async def calculate_root(self, 
                           leaf_hash: str,
                           proof_path: List[str]) -> str:
        """Calculate Merkle root from proof path"""
        
        current_hash = leaf_hash
        
        for sibling_hash in proof_path:
            combined = current_hash + sibling_hash
            current_hash = self.hash_function(combined.encode()).hexdigest()
        
        return current_hash


