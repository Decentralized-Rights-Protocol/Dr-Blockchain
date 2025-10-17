"""
DRP Decentralized Storage Gateway
FastAPI backend for proof submission, encryption, and blockchain anchoring
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import our custom modules
try:
    from storage.ipfs_handler import IPFSHandler
    from db.indexer import ScyllaIndexer
    from ledger.anchor import BlockchainAnchor
    from ledger.elders import ElderVerification
    from security.encryption import EncryptionManager
    from privacy.consent import ConsentManager
    from audit.logger import AuditLogger
except ImportError as e:
    print(f"Warning: Some modules not available: {e}")
    # Create mock classes for missing modules
    class IPFSHandler:
        def __init__(self): pass
        async def initialize(self): pass
        def is_connected(self): return False
    class ScyllaIndexer:
        def __init__(self): pass
        async def initialize(self): pass
        def is_connected(self): return False
    class BlockchainAnchor:
        def __init__(self): pass
        async def initialize(self): pass
        def is_connected(self): return False
    class ElderVerification:
        def __init__(self): pass
        async def initialize(self): pass
        def is_ready(self): return False
    class EncryptionManager:
        def __init__(self): pass
        async def initialize(self): pass
    class ConsentManager:
        def __init__(self): pass
        async def initialize(self): pass
    class AuditLogger:
        def __init__(self): pass
        async def initialize(self): pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class ProofSubmission(BaseModel):
    """Proof submission from client"""
    proof_type: str = Field(..., description="Type of proof (PoST, PoAT, etc.)")
    user_id: str = Field(..., description="User identifier (will be hashed)")
    activity_data: Dict[str, Any] = Field(..., description="Activity/proof data")
    consent_token: str = Field(..., description="Signed user consent token")
    timestamp: float = Field(default_factory=time.time, description="Submission timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class ProofResponse(BaseModel):
    """Response after proof submission"""
    proof_id: str
    cid: str
    block_hash: Optional[str] = None
    status: str
    message: str
    timestamp: float

class ExplorerResponse(BaseModel):
    """Response for explorer queries"""
    cid: str
    proof_type: str
    user_hash: str
    block_height: int
    timestamp: float
    metadata_hash: str
    is_verified: bool

# Initialize FastAPI app
app = FastAPI(
    title="DRP Decentralized Storage Gateway",
    description="Decentralized storage and ledger integration for DRP proofs",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instances
ipfs_handler: Optional[IPFSHandler] = None
scylla_indexer: Optional[ScyllaIndexer] = None
blockchain_anchor: Optional[BlockchainAnchor] = None
elder_verification: Optional[ElderVerification] = None
encryption_manager: Optional[EncryptionManager] = None
consent_manager: Optional[ConsentManager] = None
audit_logger: Optional[AuditLogger] = None

async def get_services():
    """Dependency to get service instances"""
    global ipfs_handler, scylla_indexer, blockchain_anchor, elder_verification
    global encryption_manager, consent_manager, audit_logger
    
    if not ipfs_handler:
        ipfs_handler = IPFSHandler()
        await ipfs_handler.initialize()
    
    if not scylla_indexer:
        scylla_indexer = ScyllaIndexer()
        await scylla_indexer.initialize()
    
    if not blockchain_anchor:
        blockchain_anchor = BlockchainAnchor()
        await blockchain_anchor.initialize()
    
    if not elder_verification:
        elder_verification = ElderVerification()
        await elder_verification.initialize()
    
    if not encryption_manager:
        encryption_manager = EncryptionManager()
        await encryption_manager.initialize()
    
    if not consent_manager:
        consent_manager = ConsentManager()
        await consent_manager.initialize()
    
    if not audit_logger:
        audit_logger = AuditLogger()
        await audit_logger.initialize()
    
    return {
        "ipfs": ipfs_handler,
        "scylla": scylla_indexer,
        "blockchain": blockchain_anchor,
        "elders": elder_verification,
        "encryption": encryption_manager,
        "consent": consent_manager,
        "audit": audit_logger
    }

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting DRP Decentralized Storage Gateway...")
    services = await get_services()
    logger.info("All services initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services on shutdown"""
    logger.info("Shutting down DRP Gateway...")
    # Cleanup will be handled by individual service classes

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "ipfs": ipfs_handler.is_connected() if ipfs_handler else False,
            "scylla": scylla_indexer.is_connected() if scylla_indexer else False,
            "blockchain": blockchain_anchor.is_connected() if blockchain_anchor else False,
            "elders": elder_verification.is_ready() if elder_verification else False
        }
    }

@app.post("/submit-proof", response_model=ProofResponse)
async def submit_proof(
    proof: ProofSubmission,
    background_tasks: BackgroundTasks,
    services: Dict[str, Any] = Depends(get_services)
):
    """
    Submit a proof for storage and blockchain anchoring
    
    Process:
    1. Validate consent token
    2. Encrypt sensitive fields
    3. Upload to IPFS
    4. Store metadata in ScyllaDB
    5. Submit to blockchain with Elder verification
    """
    try:
        proof_id = str(uuid4())
        start_time = time.time()
        
        # Log proof submission
        await services["audit"].log_proof_submission(proof_id, proof.dict())
        
        # 1. Validate consent token
        consent_valid = await services["consent"].validate_consent_token(
            proof.consent_token, proof.user_id
        )
        if not consent_valid:
            raise HTTPException(status_code=403, detail="Invalid consent token")
        
        # 2. Encrypt sensitive fields
        user_hash = hashlib.sha256(proof.user_id.encode()).hexdigest()
        encrypted_data = await services["encryption"].encrypt_proof_data(
            proof.activity_data, user_hash
        )
        
        # 3. Create proof document
        proof_document = {
            "proof_id": proof_id,
            "proof_type": proof.proof_type,
            "user_hash": user_hash,
            "encrypted_data": encrypted_data,
            "metadata": proof.metadata,
            "timestamp": proof.timestamp,
            "consent_token": proof.consent_token
        }
        
        # 4. Upload to IPFS
        cid = await services["ipfs"].upload_proof(proof_document)
        logger.info(f"Proof {proof_id} uploaded to IPFS with CID: {cid}")
        
        # 5. Compute metadata hash
        metadata_hash = hashlib.sha256(
            json.dumps(proof.metadata, sort_keys=True).encode()
        ).hexdigest()
        
        # 6. Store in ScyllaDB
        await services["scylla"].store_proof_metadata(
            proof_id=proof_id,
            user_hash=user_hash,
            cid=cid,
            proof_type=proof.proof_type,
            metadata_hash=metadata_hash,
            timestamp=proof.timestamp
        )
        
        # 7. Submit to blockchain (background task)
        background_tasks.add_task(
            submit_to_blockchain,
            proof_id, cid, metadata_hash, proof.timestamp, services
        )
        
        # Log successful submission
        await services["audit"].log_proof_upload(proof_id, cid, time.time() - start_time)
        
        return ProofResponse(
            proof_id=proof_id,
            cid=cid,
            status="submitted",
            message="Proof submitted successfully, blockchain anchoring in progress",
            timestamp=time.time()
        )
        
    except Exception as e:
        logger.error(f"Error submitting proof: {e}")
        await services["audit"].log_proof_error(proof_id if 'proof_id' in locals() else None, str(e))
        raise HTTPException(status_code=500, detail=f"Proof submission failed: {str(e)}")

async def submit_to_blockchain(
    proof_id: str,
    cid: str,
    metadata_hash: str,
    timestamp: float,
    services: Dict[str, Any]
):
    """Background task to submit proof to blockchain"""
    try:
        # Create anchor payload
        anchor_payload = {
            "proof_id": proof_id,
            "cid": cid,
            "metadata_hash": metadata_hash,
            "timestamp": timestamp
        }
        
        # Get Elder signatures
        elder_signatures = await services["elders"].get_quorum_signatures(anchor_payload)
        
        # Submit to blockchain
        block_hash = await services["blockchain"].anchor_proof(
            anchor_payload, elder_signatures
        )
        
        # Update ScyllaDB with block info
        await services["scylla"].update_proof_block_info(proof_id, block_hash)
        
        # Log successful anchoring
        await services["audit"].log_blockchain_anchor(proof_id, block_hash)
        
        logger.info(f"Proof {proof_id} anchored to blockchain: {block_hash}")
        
    except Exception as e:
        logger.error(f"Error anchoring proof {proof_id} to blockchain: {e}")
        await services["audit"].log_anchor_error(proof_id, str(e))

@app.get("/explorer/{cid}", response_model=ExplorerResponse)
async def get_proof_by_cid(
    cid: str,
    services: Dict[str, Any] = Depends(get_services)
):
    """Get proof information by IPFS CID"""
    try:
        # Get metadata from ScyllaDB
        metadata = await services["scylla"].get_proof_by_cid(cid)
        if not metadata:
            raise HTTPException(status_code=404, detail="Proof not found")
        
        # Verify CID matches blockchain anchor
        is_verified = await services["blockchain"].verify_cid_anchor(cid)
        
        return ExplorerResponse(
            cid=cid,
            proof_type=metadata["proof_type"],
            user_hash=metadata["user_hash"],
            block_height=metadata.get("block_height", 0),
            timestamp=metadata["timestamp"],
            metadata_hash=metadata["metadata_hash"],
            is_verified=is_verified
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving proof {cid}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve proof: {str(e)}")

@app.get("/explorer/user/{user_hash}")
async def get_proofs_by_user(
    user_hash: str,
    limit: int = 100,
    services: Dict[str, Any] = Depends(get_services)
):
    """Get all proofs for a user (by hash)"""
    try:
        proofs = await services["scylla"].get_proofs_by_user(user_hash, limit)
        return {
            "user_hash": user_hash,
            "proofs": proofs,
            "count": len(proofs)
        }
    except Exception as e:
        logger.error(f"Error retrieving proofs for user {user_hash}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user proofs: {str(e)}")

@app.get("/explorer/block/{block_height}")
async def get_proofs_by_block(
    block_height: int,
    services: Dict[str, Any] = Depends(get_services)
):
    """Get all proofs anchored in a specific block"""
    try:
        proofs = await services["scylla"].get_proofs_by_block(block_height)
        return {
            "block_height": block_height,
            "proofs": proofs,
            "count": len(proofs)
        }
    except Exception as e:
        logger.error(f"Error retrieving proofs for block {block_height}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve block proofs: {str(e)}")

@app.get("/stats")
async def get_system_stats(services: Dict[str, Any] = Depends(get_services)):
    """Get system statistics"""
    try:
        stats = await services["scylla"].get_system_stats()
        return {
            "total_proofs": stats.get("total_proofs", 0),
            "total_users": stats.get("total_users", 0),
            "latest_block": stats.get("latest_block", 0),
            "system_health": {
                "ipfs": services["ipfs"].is_connected(),
                "scylla": services["scylla"].is_connected(),
                "blockchain": services["blockchain"].is_connected(),
                "elders": services["elders"].is_ready()
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving system stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "gateway:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )



