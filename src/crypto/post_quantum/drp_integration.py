"""
DRP Post-Quantum Integration Example

This module demonstrates how to integrate post-quantum cryptographic primitives
with DRP's elder quorum system and block header signing. It provides:

- Integration with DRP's existing elder quorum system
- Post-quantum block header signing
- FastAPI microservice examples
- Migration path from classical to post-quantum cryptography
- Hybrid classical/post-quantum signature support

This integration ensures DRP remains secure against quantum attacks while
maintaining compatibility with existing infrastructure.
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, Depends
    from pydantic import BaseModel, Field
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from .pq_keys import (
        PostQuantumKeyManager, 
        DilithiumKeyPair, 
        KyberKeyPair,
        KeyRotationManager,
        KeyRevocationManager,
        PostQuantumCryptoError
    )
    from .pq_sign import (
        PostQuantumSigner,
        PostQuantumVerifier,
        PostQuantumSignature,
        QuorumSignature,
        DRPPostQuantumSigner
    )
except ImportError:
    # Handle direct execution
    from pq_keys import (
        PostQuantumKeyManager, 
        DilithiumKeyPair, 
        KyberKeyPair,
        KeyRotationManager,
        KeyRevocationManager,
        PostQuantumCryptoError
    )
    from pq_sign import (
        PostQuantumSigner,
        PostQuantumVerifier,
        PostQuantumSignature,
        QuorumSignature,
        DRPPostQuantumSigner
    )


@dataclass
class DRPElder:
    """DRP Elder with post-quantum cryptographic capabilities"""
    elder_id: str
    dilithium_keypair: DilithiumKeyPair
    kyber_keypair: Optional[KyberKeyPair]
    is_active: bool = True
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class DRPPostQuantumElderQuorum:
    """
    Post-quantum enhanced DRP Elder Quorum system
    
    This class integrates post-quantum cryptography with DRP's elder quorum:
    - Uses CRYSTALS-Dilithium for block header signatures
    - Uses CRYSTALS-Kyber for secure key exchange
    - Maintains compatibility with existing DRP consensus
    - Supports hybrid classical/post-quantum signatures
    """
    
    def __init__(self, 
                 keystore_path: str = ".keystore/drp_elders",
                 total_elders: int = 5,
                 required_signatures: int = 3):
        """
        Initialize the post-quantum elder quorum
        
        Args:
            keystore_path: Path to store elder keys
            total_elders: Total number of elders in the quorum
            required_signatures: Minimum signatures required for consensus
        """
        self.total_elders = total_elders
        self.required_signatures = required_signatures
        
        # Initialize key management
        self.key_manager = PostQuantumKeyManager(keystore_path)
        self.rotation_manager = KeyRotationManager(self.key_manager)
        self.revocation_manager = KeyRevocationManager(self.key_manager)
        
        # Initialize signer/verifier
        self.pq_signer = DRPPostQuantumSigner(self.key_manager)
        self.verifier = PostQuantumVerifier()
        
        # Load or create elders
        self.elders: Dict[str, DRPElder] = {}
        self._initialize_elders()
    
    def _initialize_elders(self):
        """Initialize or load elder key pairs"""
        for i in range(self.total_elders):
            elder_id = f"elder_{i}"
            
            # Check if elder already exists
            dilithium_key = self.key_manager.get_dilithium_keypair(f"{elder_id}_dilithium")
            kyber_key = self.key_manager.get_kyber_keypair(f"{elder_id}_kyber")
            
            if not dilithium_key:
                # Generate new Dilithium key pair
                dilithium_key = self.key_manager.generate_dilithium_keypair(
                    algorithm="Dilithium3",
                    expires_in_days=365
                )
                # Update key ID for consistency
                dilithium_key.key_id = f"{elder_id}_dilithium"
            
            if not kyber_key:
                # Generate new Kyber key pair
                kyber_key = self.key_manager.generate_kyber_keypair(
                    algorithm="Kyber-768",
                    expires_in_days=365
                )
                # Update key ID for consistency
                kyber_key.key_id = f"{elder_id}_kyber"
            
            # Create elder
            elder = DRPElder(
                elder_id=elder_id,
                dilithium_keypair=dilithium_key,
                kyber_keypair=kyber_key
            )
            
            self.elders[elder_id] = elder
            
            # Schedule key rotation
            self.rotation_manager.schedule_rotation(
                dilithium_key.key_id,
                rotation_interval_days=90,
                advance_notice_days=7
            )
    
    def sign_block_header(self, 
                         block_data: Dict[str, Any],
                         elder_ids: Optional[List[str]] = None) -> QuorumSignature:
        """
        Sign a block header with the elder quorum
        
        Args:
            block_data: Block header data
            elder_ids: Specific elders to sign (None for all active elders)
        
        Returns:
            QuorumSignature with elder signatures
        """
        if elder_ids is None:
            elder_ids = [e.elder_id for e in self.elders.values() if e.is_active]
        
        signatures = []
        
        for elder_id in elder_ids:
            if elder_id not in self.elders:
                continue
            
            elder = self.elders[elder_id]
            if not elder.is_active:
                continue
            
            try:
                # Create signer for this elder
                signer = PostQuantumSigner(elder.dilithium_keypair, elder_id)
                
                # Sign the block header
                signature = signer.sign_drp_block_header(
                    block_index=block_data["index"],
                    previous_hash=block_data["previous_hash"],
                    merkle_root=block_data.get("merkle_root", ""),
                    timestamp=block_data["timestamp"],
                    miner_id=block_data.get("miner_id", ""),
                    nonce=block_data.get("nonce", 0),
                    difficulty=block_data.get("difficulty", 0)
                )
                
                signatures.append(signature)
                
            except Exception as e:
                print(f"Error signing with elder {elder_id}: {e}")
                continue
        
        # Create block hash
        canonical_string = json.dumps(block_data, separators=(",", ":"), sort_keys=True)
        block_hash = hashlib.sha256(canonical_string.encode()).hexdigest()
        
        # Create quorum signature
        quorum_sig = QuorumSignature(
            signatures=signatures,
            required_signatures=self.required_signatures,
            total_elders=len(self.elders),
            block_header_hash=block_hash,
            created_at=time.time(),
            quorum_id=f"drp_quorum_{block_hash[:16]}"
        )
        
        return quorum_sig
    
    def verify_block_signature(self, 
                              quorum_sig: QuorumSignature,
                              block_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Verify a quorum signature for a block
        
        Args:
            quorum_sig: QuorumSignature to verify
            block_data: Block header data
        
        Returns:
            Tuple of (is_valid, list_of_valid_elder_ids)
        """
        return self.verifier.verify_quorum_signature(quorum_sig, block_data)
    
    def rotate_elder_keys(self, elder_id: str) -> bool:
        """
        Rotate keys for a specific elder
        
        Args:
            elder_id: ID of the elder to rotate keys for
        
        Returns:
            True if rotation successful
        """
        if elder_id not in self.elders:
            return False
        
        elder = self.elders[elder_id]
        
        try:
            # Rotate Dilithium key
            new_dilithium = self.rotation_manager.rotate_key(elder.dilithium_keypair.key_id)
            if new_dilithium:
                elder.dilithium_keypair = new_dilithium
            
            # Rotate Kyber key
            new_kyber = self.rotation_manager.rotate_key(elder.kyber_keypair.key_id)
            if new_kyber:
                elder.kyber_keypair = new_kyber
            
            return True
            
        except Exception as e:
            print(f"Error rotating keys for elder {elder_id}: {e}")
            return False
    
    def revoke_elder(self, elder_id: str, reason: str = "unspecified") -> bool:
        """
        Revoke an elder from the quorum
        
        Args:
            elder_id: ID of the elder to revoke
            reason: Reason for revocation
        
        Returns:
            True if revocation successful
        """
        if elder_id not in self.elders:
            return False
        
        elder = self.elders[elder_id]
        
        try:
            # Revoke Dilithium key
            self.revocation_manager.revoke_key_with_reason(
                elder.dilithium_keypair.key_id,
                reason=reason,
                revoked_by="quorum_manager"
            )
            
            # Revoke Kyber key
            self.revocation_manager.revoke_key_with_reason(
                elder.kyber_keypair.key_id,
                reason=reason,
                revoked_by="quorum_manager"
            )
            
            # Mark elder as inactive
            elder.is_active = False
            
            return True
            
        except Exception as e:
            print(f"Error revoking elder {elder_id}: {e}")
            return False
    
    def get_elder_info(self, elder_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific elder"""
        if elder_id not in self.elders:
            return None
        
        elder = self.elders[elder_id]
        
        return {
            "elder_id": elder.elder_id,
            "is_active": elder.is_active,
            "created_at": elder.created_at,
            "dilithium_key": {
                "algorithm": elder.dilithium_keypair.algorithm,
                "key_id": elder.dilithium_keypair.key_id,
                "created_at": elder.dilithium_keypair.created_at,
                "expires_at": elder.dilithium_keypair.expires_at,
                "is_expired": elder.dilithium_keypair.is_expired()
            },
            "kyber_key": {
                "algorithm": elder.kyber_keypair.algorithm,
                "key_id": elder.kyber_keypair.key_id,
                "created_at": elder.kyber_keypair.created_at,
                "expires_at": elder.kyber_keypair.expires_at,
                "is_expired": elder.kyber_keypair.is_expired()
            } if elder.kyber_keypair else None
        }
    
    def get_quorum_status(self) -> Dict[str, Any]:
        """Get status of the entire quorum"""
        active_elders = [e for e in self.elders.values() if e.is_active]
        
        return {
            "total_elders": self.total_elders,
            "active_elders": len(active_elders),
            "required_signatures": self.required_signatures,
            "quorum_healthy": len(active_elders) >= self.required_signatures,
            "elders": {
                elder_id: self.get_elder_info(elder_id) 
                for elder_id in self.elders.keys()
            }
        }


# FastAPI Integration Models
if FASTAPI_AVAILABLE:
    class BlockHeaderRequest(BaseModel):
        """Request model for block header signing"""
        index: int = Field(..., ge=0, description="Block index")
        previous_hash: str = Field(..., description="Previous block hash")
        timestamp: int = Field(..., description="Block timestamp")
        merkle_root: str = Field(default="", description="Merkle root of transactions")
        miner_id: str = Field(default="", description="Miner ID")
        nonce: int = Field(default=0, description="Proof of work nonce")
        difficulty: int = Field(default=0, description="Mining difficulty")
        elder_ids: Optional[List[str]] = Field(default=None, description="Specific elders to sign")
    
    class BlockSignatureResponse(BaseModel):
        """Response model for block signature"""
        quorum_signature: Dict[str, Any] = Field(..., description="Quorum signature data")
        valid_signatures: int = Field(..., description="Number of valid signatures")
        required_signatures: int = Field(..., description="Required signatures for consensus")
        quorum_healthy: bool = Field(..., description="Whether quorum is healthy")
    
    class ElderInfoResponse(BaseModel):
        """Response model for elder information"""
        elder_id: str = Field(..., description="Elder ID")
        is_active: bool = Field(..., description="Whether elder is active")
        created_at: float = Field(..., description="Elder creation timestamp")
        dilithium_key: Dict[str, Any] = Field(..., description="Dilithium key information")
        kyber_key: Optional[Dict[str, Any]] = Field(default=None, description="Kyber key information")
    
    class QuorumStatusResponse(BaseModel):
        """Response model for quorum status"""
        total_elders: int = Field(..., description="Total number of elders")
        active_elders: int = Field(..., description="Number of active elders")
        required_signatures: int = Field(..., description="Required signatures for consensus")
        quorum_healthy: bool = Field(..., description="Whether quorum is healthy")
        elders: Dict[str, ElderInfoResponse] = Field(..., description="Information about each elder")


class DRPPostQuantumAPI:
    """
    FastAPI application for DRP Post-Quantum Elder Quorum
    
    This class provides a complete FastAPI application that integrates
    post-quantum cryptography with DRP's elder quorum system.
    """
    
    def __init__(self, 
                 keystore_path: str = ".keystore/drp_api",
                 total_elders: int = 5,
                 required_signatures: int = 3):
        """
        Initialize the FastAPI application
        
        Args:
            keystore_path: Path to store elder keys
            total_elders: Total number of elders
            required_signatures: Required signatures for consensus
        """
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI not available. Install with: pip install fastapi uvicorn")
        
        self.app = FastAPI(
            title="DRP Post-Quantum Elder Quorum API",
            description="Post-quantum cryptographic elder quorum for DRP blockchain",
            version="1.0.0"
        )
        
        # Initialize quorum
        self.quorum = DRPPostQuantumElderQuorum(
            keystore_path=keystore_path,
            total_elders=total_elders,
            required_signatures=required_signatures
        )
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/v1/quorum/status", response_model=QuorumStatusResponse)
        async def get_quorum_status():
            """Get status of the elder quorum"""
            status = self.quorum.get_quorum_status()
            return QuorumStatusResponse(**status)
        
        @self.app.get("/v1/elders/{elder_id}", response_model=ElderInfoResponse)
        async def get_elder_info(elder_id: str):
            """Get information about a specific elder"""
            info = self.quorum.get_elder_info(elder_id)
            if not info:
                raise HTTPException(status_code=404, detail="Elder not found")
            return ElderInfoResponse(**info)
        
        @self.app.post("/v1/consensus/sign-block", response_model=BlockSignatureResponse)
        async def sign_block(request: BlockHeaderRequest):
            """Sign a block header with the elder quorum"""
            try:
                block_data = request.dict()
                elder_ids = block_data.pop("elder_ids", None)
                
                quorum_sig = self.quorum.sign_block_header(block_data, elder_ids)
                
                return BlockSignatureResponse(
                    quorum_signature=quorum_sig.to_dict(),
                    valid_signatures=len(quorum_sig.signatures),
                    required_signatures=quorum_sig.required_signatures,
                    quorum_healthy=quorum_sig.is_valid_quorum()
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Signing failed: {str(e)}")
        
        @self.app.post("/v1/consensus/verify-block")
        async def verify_block_signature(
            quorum_signature: Dict[str, Any],
            block_data: Dict[str, Any]
        ):
            """Verify a quorum signature for a block"""
            try:
                quorum_sig = QuorumSignature.from_dict(quorum_signature)
                is_valid, valid_signers = self.quorum.verify_block_signature(quorum_sig, block_data)
                
                return {
                    "valid": is_valid,
                    "valid_signers": valid_signers,
                    "required_signatures": quorum_sig.required_signatures,
                    "actual_signatures": len(quorum_sig.signatures)
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")
        
        @self.app.post("/v1/elders/{elder_id}/rotate-keys")
        async def rotate_elder_keys(elder_id: str):
            """Rotate keys for a specific elder"""
            success = self.quorum.rotate_elder_keys(elder_id)
            if not success:
                raise HTTPException(status_code=404, detail="Elder not found or rotation failed")
            
            return {"message": f"Keys rotated for elder {elder_id}"}
        
        @self.app.post("/v1/elders/{elder_id}/revoke")
        async def revoke_elder(elder_id: str, reason: str = "unspecified"):
            """Revoke an elder from the quorum"""
            success = self.quorum.revoke_elder(elder_id, reason)
            if not success:
                raise HTTPException(status_code=404, detail="Elder not found or revocation failed")
            
            return {"message": f"Elder {elder_id} revoked with reason: {reason}"}
        
        @self.app.get("/v1/health")
        async def health_check():
            """Health check endpoint"""
            status = self.quorum.get_quorum_status()
            return {
                "status": "healthy" if status["quorum_healthy"] else "degraded",
                "quorum_status": status
            }


# Example usage and testing
def create_demo_quorum():
    """Create a demo quorum for testing"""
    print("Creating DRP Post-Quantum Elder Quorum Demo")
    print("=" * 50)
    
    try:
        # Create quorum
        quorum = DRPPostQuantumElderQuorum(
            keystore_path=".demo_keystore",
            total_elders=5,
            required_signatures=3
        )
        
        print(f"✅ Quorum created with {quorum.total_elders} elders")
        print(f"   Required signatures: {quorum.required_signatures}")
        
        # Get quorum status
        status = quorum.get_quorum_status()
        print(f"   Active elders: {status['active_elders']}")
        print(f"   Quorum healthy: {status['quorum_healthy']}")
        
        # Test block signing
        print("\n📝 Testing block header signing...")
        block_data = {
            "index": 12345,
            "previous_hash": "0xabcdef1234567890",
            "timestamp": int(time.time()),
            "merkle_root": "0x1234567890abcdef",
            "miner_id": "test_miner_001",
            "nonce": 42,
            "difficulty": 4
        }
        
        quorum_sig = quorum.sign_block_header(block_data)
        print(f"   Signatures created: {len(quorum_sig.signatures)}")
        print(f"   Quorum valid: {quorum_sig.is_valid_quorum()}")
        print(f"   Quorum ID: {quorum_sig.quorum_id}")
        
        # Test signature verification
        print("\n🔍 Testing signature verification...")
        is_valid, valid_signers = quorum.verify_block_signature(quorum_sig, block_data)
        print(f"   Verification result: {is_valid}")
        print(f"   Valid signers: {valid_signers}")
        
        # Test elder info
        print("\n👥 Elder information:")
        for elder_id in quorum.elders.keys():
            info = quorum.get_elder_info(elder_id)
            print(f"   {elder_id}: {info['dilithium_key']['algorithm']} (Active: {info['is_active']})")
        
        print("\n✅ Demo completed successfully!")
        return quorum
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return None


if __name__ == "__main__":
    # Run demo
    demo_quorum = create_demo_quorum()
    
    if FASTAPI_AVAILABLE and demo_quorum:
        print("\n🚀 Starting FastAPI server...")
        print("   Visit http://localhost:8080/docs for API documentation")
        print("   Press Ctrl+C to stop")
        
        import uvicorn
        api = DRPPostQuantumAPI(
            keystore_path=".demo_keystore",
            total_elders=5,
            required_signatures=3
        )
        
        try:
            uvicorn.run(api.app, host="0.0.0.0", port=8080)
        except KeyboardInterrupt:
            print("\n👋 Server stopped")



