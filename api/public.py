"""
Public API endpoints for DRP backend.
Exposes blockchain, explorer, and app portal routes.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from blockchain.node import DRPBlockchainNode
from ai.elder_core import AIElderCore
from storage.orbitdb_manager import OrbitDBManager
from storage.ipfs_manager import IPFSManager

router = APIRouter()

# Initialize components
blockchain_node = DRPBlockchainNode()
ai_elder = AIElderCore()
orbitdb = OrbitDBManager()
ipfs = IPFSManager()


# --- Blockchain Endpoints ---

@router.get("/chain/latest")
async def get_latest_block():
    """Get the latest block."""
    latest = blockchain_node.get_latest_block()
    if not latest:
        return {"block": None, "height": 0}
    return {
        "block": latest.dict(),
        "height": blockchain_node.get_block_height()
    }


@router.get("/chain/block/{height}")
async def get_block_by_height(height: int):
    """Get block by height."""
    if height < 0 or height >= len(blockchain_node.blocks):
        raise HTTPException(status_code=404, detail="Block not found")
    
    block = blockchain_node.blocks[height]
    return {"block": block.dict()}


@router.post("/chain/submit-tx")
async def submit_transaction(tx_data: Dict[str, Any]):
    """Submit a transaction."""
    from core.models.transaction import Transaction, TransactionType
    
    try:
        tx = Transaction(
            hash=tx_data.get("hash", ""),
            from_address=tx_data["from"],
            to_address=tx_data.get("to"),
            transaction_type=TransactionType.TRANSFER,
            value=float(tx_data.get("value", 0)),
            gas_price=float(tx_data.get("gasPrice", 0)),
            gas_limit=int(tx_data.get("gasLimit", 21000)),
            nonce=int(tx_data.get("nonce", 0)),
            data=tx_data.get("data", {}),
            signature=tx_data.get("signature")
        )
        
        success = blockchain_node.submit_transaction(tx)
        
        if success:
            return {
                "success": True,
                "tx_hash": tx.hash,
                "status": "pending"
            }
        else:
            raise HTTPException(status_code=400, detail="Transaction validation failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chain/submit-poat")
async def submit_poat(poat_data: Dict[str, Any]):
    """Submit Proof of Activity."""
    try:
        # Verify with AI first
        activity = {
            'activity_id': poat_data.get('activity_id'),
            'user_id': poat_data.get('user_id'),
            'activity_type': poat_data.get('activity_type'),
            'title': poat_data.get('title', ''),
            'description': poat_data.get('description', ''),
            'metadata': poat_data.get('metadata', {})
        }
        
        ai_result = ai_elder.verify_activity(activity)
        
        # Store in OrbitDB
        orbitdb_result = orbitdb.add_entry('poat', {
            **poat_data,
            'ai_verification': ai_result
        })
        
        # Pin to IPFS if IPFS CID provided
        ipfs_cid = poat_data.get('ipfs_cid')
        if not ipfs_cid and poat_data.get('pin_to_ipfs'):
            ipfs_result = ipfs.add_data(poat_data)
            ipfs_cid = ipfs_result.get('cid')
        
        # Submit to blockchain
        blockchain_result = blockchain_node.submit_poat({
            **poat_data,
            'verification_score': ai_result['verification_score'],
            'quantum_hash': ai_result['quantum_hash'],
            'orbitdb_cid': orbitdb_result.get('cid'),
            'ipfs_cid': ipfs_cid
        })
        
        return {
            "success": True,
            "poat_id": blockchain_result.get('poat_id'),
            "ai_verification": ai_result,
            "orbitdb_cid": orbitdb_result.get('cid'),
            "ipfs_cid": ipfs_cid,
            "status_score": blockchain_result.get('status_score')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chain/submit-post")
async def submit_post(post_data: Dict[str, Any]):
    """Submit Proof of Status."""
    try:
        # Verify with AI
        status_result = ai_elder.verify_status(post_data)
        
        # Store in OrbitDB
        orbitdb_result = orbitdb.add_entry('post', {
            **post_data,
            'ai_verification': status_result
        })
        
        # Submit to blockchain
        blockchain_result = blockchain_node.submit_post({
            **post_data,
            'status_score': status_result['calculated_score'],
            'quantum_hash': status_result['quantum_hash'],
            'orbitdb_cid': orbitdb_result.get('cid')
        })
        
        return {
            "success": True,
            "user_id": blockchain_result.get('user_id'),
            "status_score": blockchain_result.get('status_score'),
            "ai_verification": status_result,
            "orbitdb_cid": orbitdb_result.get('cid')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Explorer Endpoints ---

@router.get("/explorer/transactions")
async def get_transactions(limit: int = 50, offset: int = 0):
    """Get recent transactions."""
    all_txs = []
    for block in blockchain_node.blocks[-10:]:  # Last 10 blocks
        all_txs.extend([tx.dict() for tx in block.transactions])
    
    return {
        "transactions": all_txs[offset:offset+limit],
        "total": len(all_txs)
    }


@router.get("/explorer/blocks")
async def get_blocks(limit: int = 20, offset: int = 0):
    """Get recent blocks."""
    blocks = blockchain_node.blocks[-limit-offset:][:limit]
    return {
        "blocks": [b.dict() for b in blocks],
        "total": len(blockchain_node.blocks)
    }


@router.get("/explorer/ai-summary/{cid}")
async def get_ai_summary(cid: str):
    """Get AI verification summary for a CID."""
    # Get from OrbitDB
    entries = orbitdb.get_entries('poat', limit=1000)
    
    for entry in entries:
        if entry.get('data', {}).get('orbitdb_cid') == cid or entry.get('data', {}).get('ipfs_cid') == cid:
            ai_verification = entry.get('data', {}).get('ai_verification', {})
            return {
                "cid": cid,
                "verification": ai_verification,
                "timestamp": entry.get('timestamp')
            }
    
    raise HTTPException(status_code=404, detail="CID not found")


# --- App Portal Endpoints ---

@router.post("/user/register")
async def register_user(user_data: Dict[str, Any]):
    """Register a new user."""
    wallet = blockchain_node.create_wallet()
    
    return {
        "success": True,
        "user_id": user_data.get("user_id", wallet['address']),
        "wallet": {
            "address": wallet['address'],
            "public_key": wallet['public_key']
        }
    }


@router.post("/user/wallet-create")
async def create_wallet():
    """Create a new wallet."""
    wallet = blockchain_node.create_wallet()
    
    return {
        "success": True,
        "wallet": {
            "address": wallet['address'],
            "public_key": wallet['public_key']
        }
    }


@router.get("/user/sync/activities")
async def sync_user_activities(user_id: str):
    """Sync user activities from OrbitDB."""
    entries = orbitdb.get_entries('poat', limit=1000)
    
    user_activities = [
        entry['data'] for entry in entries
        if entry.get('data', {}).get('user_id') == user_id
    ]
    
    return {
        "user_id": user_id,
        "activities": user_activities,
        "count": len(user_activities)
    }


# --- IPFS Endpoints ---

@router.post("/ipfs/add")
async def ipfs_add(file: UploadFile = File(...)):
    """Add file to IPFS."""
    # Save temporarily
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        result = ipfs.add_file(tmp_path)
        return result
    finally:
        import os
        os.unlink(tmp_path)


@router.get("/ipfs/get/{cid}")
async def ipfs_get(cid: str):
    """Get file from IPFS."""
    data = ipfs.get_file(cid)
    if data:
        return JSONResponse(content={"cid": cid, "data": data.hex()})
    else:
        raise HTTPException(status_code=404, detail="CID not found")

