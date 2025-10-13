"""
DRP Explorer API - FastAPI endpoints
Provides REST API access to blockchain data from Ledger, Indexer, and Proof Storage
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import our storage layers
from ..storage.ledger.rocksdb_storage import create_ledger, DRPBlock
from ..storage.indexer.neo4j_indexer import create_indexer
from ..storage.proof.orbitdb_storage import create_proof_storage, IoTLogEntry, ProofSubmission

# Pydantic models for API responses
class BlockResponse(BaseModel):
    index: int
    hash: str
    previous_hash: str
    timestamp: float
    miner_id: str
    activity: Dict[str, Any]
    proof: Dict[str, Any]
    elder_signatures: List[Dict[str, Any]] = []
    post_proofs: List[Dict[str, Any]] = []
    poat_proofs: List[Dict[str, Any]] = []

class ActorActivityResponse(BaseModel):
    activity_id: str
    type: str
    timestamp: float
    data: Dict[str, Any]
    block_hash: str

class ElderSignatureResponse(BaseModel):
    block_index: int
    block_hash: str
    signature_timestamp: float
    signature: str
    miner_id: str

class IoTLogResponse(BaseModel):
    hash: str
    device_id: str
    timestamp: float
    log_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    drp_references: List[str] = []

class ProofSubmissionResponse(BaseModel):
    hash: str
    submission_id: str
    proof_type: str
    submitter_id: str
    timestamp: float
    validation_status: str
    drp_block_hash: Optional[str] = None

class GovernanceNetworkResponse(BaseModel):
    node_counts: List[Dict[str, Any]]
    relationship_counts: List[Dict[str, Any]]

class StorageStatsResponse(BaseModel):
    iot_logs_count: int
    proof_submissions_count: int
    total_entries: int
    ipfs_connected: bool
    orbitdb_connected: bool

# Global storage instances
ledger = None
indexer = None
proof_storage = None

def get_ledger():
    """Dependency to get ledger instance"""
    if ledger is None:
        ledger = create_ledger()
    return ledger

def get_indexer():
    """Dependency to get indexer instance"""
    global indexer
    if indexer is None:
        indexer = create_indexer()
    return indexer

def get_proof_storage():
    """Dependency to get proof storage instance"""
    global proof_storage
    if proof_storage is None:
        proof_storage = create_proof_storage()
    return proof_storage

# FastAPI app
app = FastAPI(
    title="DRP Blockchain Explorer API",
    description="API for exploring DRP blockchain data, governance, and proofs",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Block endpoints
@app.get("/block/{block_hash}", response_model=BlockResponse)
async def get_block_by_hash(
    block_hash: str = Path(..., description="Block hash"),
    ledger_instance = Depends(get_ledger)
):
    """Get block by hash"""
    try:
        block = ledger_instance.get_block_by_hash(block_hash)
        if not block:
            raise HTTPException(status_code=404, detail="Block not found")
        
        return BlockResponse(**block.to_dict())
    except Exception as e:
        logging.error(f"Error getting block {block_hash}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/block/index/{block_index}", response_model=BlockResponse)
async def get_block_by_index(
    block_index: int = Path(..., description="Block index"),
    ledger_instance = Depends(get_ledger)
):
    """Get block by index"""
    try:
        block = ledger_instance.get_block_by_index(block_index)
        if not block:
            raise HTTPException(status_code=404, detail="Block not found")
        
        return BlockResponse(**block.to_dict())
    except Exception as e:
        logging.error(f"Error getting block {block_index}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/blocks/latest", response_model=BlockResponse)
async def get_latest_block(ledger_instance = Depends(get_ledger)):
    """Get the latest block"""
    try:
        block = ledger_instance.get_latest_block()
        if not block:
            raise HTTPException(status_code=404, detail="No blocks found")
        
        return BlockResponse(**block.to_dict())
    except Exception as e:
        logging.error(f"Error getting latest block: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/blocks/range/{start_index}/{end_index}", response_model=List[BlockResponse])
async def get_blocks_range(
    start_index: int = Path(..., description="Start block index"),
    end_index: int = Path(..., description="End block index"),
    ledger_instance = Depends(get_ledger)
):
    """Get blocks in a range"""
    try:
        blocks = ledger_instance.get_blocks_range(start_index, end_index)
        return [BlockResponse(**block.to_dict()) for block in blocks]
    except Exception as e:
        logging.error(f"Error getting blocks range {start_index}-{end_index}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/blocks/miner/{miner_id}", response_model=List[BlockResponse])
async def get_blocks_by_miner(
    miner_id: str = Path(..., description="Miner ID"),
    ledger_instance = Depends(get_ledger)
):
    """Get blocks by miner ID"""
    try:
        blocks = ledger_instance.search_blocks_by_miner(miner_id)
        return [BlockResponse(**block.to_dict()) for block in blocks]
    except Exception as e:
        logging.error(f"Error getting blocks by miner {miner_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Actor endpoints
@app.get("/actor/{actor_id}/activities", response_model=List[ActorActivityResponse])
async def get_actor_activities(
    actor_id: str = Path(..., description="Actor ID"),
    indexer_instance = Depends(get_indexer)
):
    """Get activities for a specific actor"""
    try:
        # This would need to be implemented in the indexer
        # For now, return empty list
        return []
    except Exception as e:
        logging.error(f"Error getting activities for actor {actor_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/actor/{actor_id}/post-attestations", response_model=List[Dict[str, Any]])
async def get_actor_post_attestations(
    actor_id: str = Path(..., description="Actor ID"),
    indexer_instance = Depends(get_indexer)
):
    """Get PoST attestations for a specific actor"""
    try:
        attestations = indexer_instance.get_actor_post_attestations(actor_id)
        return attestations
    except Exception as e:
        logging.error(f"Error getting PoST attestations for actor {actor_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Elder endpoints
@app.get("/elder/{elder_id}/signatures", response_model=List[ElderSignatureResponse])
async def get_elder_signatures(
    elder_id: str = Path(..., description="Elder ID"),
    indexer_instance = Depends(get_indexer)
):
    """Get signature history for an elder"""
    try:
        signatures = indexer_instance.get_elder_signature_history(elder_id)
        return [ElderSignatureResponse(**sig) for sig in signatures]
    except Exception as e:
        logging.error(f"Error getting signatures for elder {elder_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/elder/{elder_id}/activities/epoch/{epoch}", response_model=List[Dict[str, Any]])
async def get_elder_activities_in_epoch(
    elder_id: str = Path(..., description="Elder ID"),
    epoch: int = Path(..., description="Epoch number"),
    indexer_instance = Depends(get_indexer)
):
    """Get all activities signed by Elder-X in epoch Y"""
    try:
        activities = indexer_instance.get_elder_activities_in_epoch(elder_id, epoch)
        return activities
    except Exception as e:
        logging.error(f"Error getting elder activities for {elder_id} in epoch {epoch}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Proof storage endpoints
@app.get("/proofs/iot-logs/{log_hash}", response_model=IoTLogResponse)
async def get_iot_log(
    log_hash: str = Path(..., description="IoT log hash"),
    proof_storage_instance = Depends(get_proof_storage)
):
    """Get IoT log by hash"""
    try:
        log_entry = proof_storage_instance.get_iot_log(log_hash)
        if not log_entry:
            raise HTTPException(status_code=404, detail="IoT log not found")
        
        return IoTLogResponse(**log_entry.to_dict())
    except Exception as e:
        logging.error(f"Error getting IoT log {log_hash}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/proofs/submissions/{submission_hash}", response_model=ProofSubmissionResponse)
async def get_proof_submission(
    submission_hash: str = Path(..., description="Proof submission hash"),
    proof_storage_instance = Depends(get_proof_storage)
):
    """Get proof submission by hash"""
    try:
        submission = proof_storage_instance.get_proof_submission(submission_hash)
        if not submission:
            raise HTTPException(status_code=404, detail="Proof submission not found")
        
        return ProofSubmissionResponse(**submission.to_dict())
    except Exception as e:
        logging.error(f"Error getting proof submission {submission_hash}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/proofs/device/{device_id}/logs", response_model=List[IoTLogResponse])
async def get_iot_logs_by_device(
    device_id: str = Path(..., description="Device ID"),
    limit: int = Query(100, description="Maximum number of logs to return"),
    proof_storage_instance = Depends(get_proof_storage)
):
    """Get IoT logs for a specific device"""
    try:
        logs = proof_storage_instance.get_iot_logs_by_device(device_id, limit)
        return [IoTLogResponse(**log.to_dict()) for log in logs]
    except Exception as e:
        logging.error(f"Error getting IoT logs for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/proofs/type/{proof_type}/submissions", response_model=List[ProofSubmissionResponse])
async def get_proof_submissions_by_type(
    proof_type: str = Path(..., description="Proof type"),
    limit: int = Query(100, description="Maximum number of submissions to return"),
    proof_storage_instance = Depends(get_proof_storage)
):
    """Get proof submissions by type"""
    try:
        submissions = proof_storage_instance.get_proof_submissions_by_type(proof_type, limit)
        return [ProofSubmissionResponse(**submission.to_dict()) for submission in submissions]
    except Exception as e:
        logging.error(f"Error getting proof submissions by type {proof_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/proofs/block/{block_hash}/linked", response_model=List[Dict[str, Any]])
async def get_proofs_linked_to_block(
    block_hash: str = Path(..., description="DRP block hash"),
    proof_storage_instance = Depends(get_proof_storage)
):
    """Get all proofs linked to a specific DRP block"""
    try:
        linked_proofs = proof_storage_instance.get_proofs_linked_to_block(block_hash)
        return linked_proofs
    except Exception as e:
        logging.error(f"Error getting proofs linked to block {block_hash}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Governance endpoints
@app.get("/governance/network", response_model=GovernanceNetworkResponse)
async def get_governance_network(indexer_instance = Depends(get_indexer)):
    """Get governance network structure"""
    try:
        network_data = indexer_instance.get_governance_network()
        return GovernanceNetworkResponse(**network_data)
    except Exception as e:
        logging.error(f"Error getting governance network: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/governance/actors/activity-type/{activity_type}", response_model=List[Dict[str, Any]])
async def search_actors_by_activity_type(
    activity_type: str = Path(..., description="Activity type"),
    indexer_instance = Depends(get_indexer)
):
    """Find actors who performed specific activity types"""
    try:
        actors = indexer_instance.search_actors_by_activity_type(activity_type)
        return actors
    except Exception as e:
        logging.error(f"Error searching actors by activity type {activity_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Statistics endpoints
@app.get("/stats/chain", response_model=Dict[str, Any])
async def get_chain_stats(ledger_instance = Depends(get_ledger)):
    """Get blockchain statistics"""
    try:
        chain_length = ledger_instance.get_chain_length()
        latest_block = ledger_instance.get_latest_block()
        
        return {
            "chain_length": chain_length,
            "latest_block_index": latest_block.index if latest_block else -1,
            "latest_block_hash": latest_block.hash if latest_block else None,
            "latest_block_timestamp": latest_block.timestamp if latest_block else None
        }
    except Exception as e:
        logging.error(f"Error getting chain stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats/storage", response_model=StorageStatsResponse)
async def get_storage_stats(proof_storage_instance = Depends(get_proof_storage)):
    """Get proof storage statistics"""
    try:
        stats = proof_storage_instance.get_storage_stats()
        return StorageStatsResponse(**stats)
    except Exception as e:
        logging.error(f"Error getting storage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Search endpoints
@app.get("/search/blocks", response_model=List[BlockResponse])
async def search_blocks(
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    miner_id: Optional[str] = Query(None, description="Filter by miner ID"),
    ledger_instance = Depends(get_ledger)
):
    """Search blocks with optional filters"""
    try:
        if miner_id:
            blocks = ledger_instance.search_blocks_by_miner(miner_id)
        elif activity_type:
            blocks = ledger_instance.search_blocks_by_activity_type(activity_type)
        else:
            # Return recent blocks
            chain_length = ledger_instance.get_chain_length()
            start_index = max(0, chain_length - 50)  # Last 50 blocks
            blocks = ledger_instance.get_blocks_range(start_index, chain_length - 1)
        
        return [BlockResponse(**block.to_dict()) for block in blocks]
    except Exception as e:
        logging.error(f"Error searching blocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize storage connections on startup"""
    logging.info("Starting DRP Explorer API...")
    # Storage instances will be created lazily via dependencies

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up storage connections on shutdown"""
    logging.info("Shutting down DRP Explorer API...")
    global ledger, indexer, proof_storage
    
    if ledger:
        ledger.close()
    if indexer:
        indexer.close()
    if proof_storage:
        proof_storage.close()

# Main entry point
if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
