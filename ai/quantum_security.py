"""Quantum-secure hashing for DRP."""

from typing import Optional
from core.utils.quantum import generate_quantum_hash, verify_quantum_hash


class QuantumSecurity:
    """Quantum-secure cryptographic operations."""
    
    @staticmethod
    def generate_proof_hash(data: str, salt: Optional[str] = None) -> Dict[str, str]:
        """
        Generate a quantum-secure proof hash.
        
        Args:
            data: Data to hash
            salt: Optional salt
            
        Returns:
            Dictionary with hash and salt
        """
        import secrets
        
        if salt is None:
            salt = secrets.token_hex(32)
        
        quantum_hash = generate_quantum_hash(data, salt)
        
        return {
            "quantum_hash": quantum_hash,
            "salt": salt,
            "algorithm": "SHA3-512+BLAKE2b+LatticePadding"
        }
    
    @staticmethod
    def verify_proof(original_data: str, quantum_hash: str, salt: Optional[str] = None) -> bool:
        """
        Verify a quantum-secure proof.
        
        Args:
            original_data: Original data
            quantum_hash: Expected quantum hash
            salt: Salt used during generation
            
        Returns:
            True if proof is valid
        """
        return verify_quantum_hash(original_data, quantum_hash, salt)
    
    @staticmethod
    def generate_activity_proof(activity_id: str, user_id: str, orbitdb_cid: str,
                               verification_score: float) -> Dict[str, Any]:
        """
        Generate quantum-secure proof for activity.
        
        Args:
            activity_id: Activity identifier
            user_id: User identifier
            orbitdb_cid: OrbitDB CID
            verification_score: AI verification score
            
        Returns:
            Proof dictionary
        """
        proof_data = f"{activity_id}:{user_id}:{orbitdb_cid}:{verification_score}"
        proof = QuantumSecurity.generate_proof_hash(proof_data)
        
        return {
            "activity_id": activity_id,
            "user_id": user_id,
            "orbitdb_cid": orbitdb_cid,
            "verification_score": verification_score,
            **proof
        }
    
    @staticmethod
    def generate_status_proof(user_id: str, status_score: Dict[str, Any],
                              orbitdb_cid: str) -> Dict[str, Any]:
        """
        Generate quantum-secure proof for status.
        
        Args:
            user_id: User identifier
            status_score: Status score dictionary
            orbitdb_cid: OrbitDB CID
            
        Returns:
            Proof dictionary
        """
        import json
        score_string = json.dumps(status_score, sort_keys=True)
        proof_data = f"{user_id}:{orbitdb_cid}:{score_string}"
        proof = QuantumSecurity.generate_proof_hash(proof_data)
        
        return {
            "user_id": user_id,
            "status_score": status_score,
            "orbitdb_cid": orbitdb_cid,
            **proof
        }

