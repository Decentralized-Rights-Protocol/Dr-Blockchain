"""JSON-RPC server for DRP blockchain."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import json
import hashlib
from datetime import datetime
from pydantic import BaseModel

from config import get_settings
from network.transaction_pool import TransactionPool
from network.block_builder import BlockBuilder
from core.models.transaction import Transaction, TransactionType, Block
from core.utils.crypto import hash_data, generate_wallet
from core.utils.quantum import generate_quantum_hash


app = FastAPI(title="DRP RPC Server", version="1.0.0")

# Initialize components
settings = get_settings()
transaction_pool = TransactionPool()
block_builder = BlockBuilder()

# In-memory state
balances: Dict[str, float] = {}
nonces: Dict[str, int] = {}


class JSONRPCRequest(BaseModel):
    """JSON-RPC request model."""
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None


class JSONRPCResponse(BaseModel):
    """JSON-RPC response model."""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None


def create_transaction_hash(tx: Transaction) -> str:
    """Create transaction hash."""
    tx_data = {
        'from': tx.from_address,
        'to': tx.to_address,
        'value': tx.value,
        'nonce': tx.nonce,
        'gas_price': tx.gas_price,
        'gas_limit': tx.gas_limit,
        'data': tx.data
    }
    tx_string = json.dumps(tx_data, sort_keys=True)
    return "0x" + hashlib.sha256(tx_string.encode()).hexdigest()


@app.post("/")
async def rpc_endpoint(request: JSONRPCRequest):
    """Handle JSON-RPC requests."""
    try:
        method = request.method
        params = request.params or {}
        
        # Route to appropriate handler
        if method == "getBalance":
            result = await get_balance(params.get("address", ""))
        elif method == "sendTransaction":
            result = await send_transaction(params)
        elif method == "getTransaction":
            result = await get_transaction(params.get("hash", ""))
        elif method == "getBlock":
            result = await get_block(params)
        elif method == "submitActivityProof":
            result = await submit_activity_proof(params)
        elif method == "submitStatusProof":
            result = await submit_status_proof(params)
        elif method == "getBlockNumber":
            result = block_builder.get_block_count()
        elif method == "getTransactionCount":
            result = get_transaction_count(params.get("address", ""))
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
        
        return JSONRPCResponse(
            jsonrpc="2.0",
            result=result,
            id=request.id
        )
    except Exception as e:
        return JSONRPCResponse(
            jsonrpc="2.0",
            error={"code": -32000, "message": str(e)},
            id=request.id if 'request' in locals() else None
        )


async def get_balance(address: str) -> str:
    """Get balance for an address."""
    if not address:
        raise ValueError("Address is required")
    
    balance = balances.get(address, 0.0)
    return hex(int(balance * 1e18))  # Convert to wei equivalent


async def send_transaction(params: Dict[str, Any]) -> str:
    """Send a transaction."""
    from_address = params.get("from", "")
    to_address = params.get("to")
    value = float(params.get("value", 0))
    gas_price = float(params.get("gasPrice", 0))
    gas_limit = int(params.get("gasLimit", 21000))
    data = params.get("data", {})
    
    if not from_address:
        raise ValueError("from address is required")
    
    # Get nonce
    nonce = nonces.get(from_address, 0)
    nonces[from_address] = nonce + 1
    
    # Create transaction
    tx = Transaction(
        hash="",  # Will be calculated
        from_address=from_address,
        to_address=to_address,
        transaction_type=TransactionType.TRANSFER,
        value=value,
        gas_price=gas_price,
        gas_limit=gas_limit,
        nonce=nonce,
        data=data,
        status="pending"
    )
    
    # Calculate hash
    tx.hash = create_transaction_hash(tx)
    
    # Add to transaction pool
    transaction_pool.add_transaction(tx)
    
    # Update balances (simplified - in real blockchain, this happens after mining)
    if from_address in balances:
        balances[from_address] -= value
    if to_address and to_address in balances:
        balances[to_address] += value
    
    return tx.hash


async def get_transaction(tx_hash: str) -> Optional[Dict[str, Any]]:
    """Get transaction by hash."""
    # Check pending transactions
    tx = transaction_pool.get_transaction_by_hash(tx_hash)
    if tx:
        return tx.dict()
    
    # Check mined transactions
    for block in block_builder.blocks:
        for block_tx in block.transactions:
            if block_tx.hash == tx_hash:
                return block_tx.dict()
    
    return None


async def get_block(params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get block by number or hash."""
    if "blockNumber" in params:
        block_number = int(params["blockNumber"])
        block = block_builder.get_block(block_number)
    elif "blockHash" in params:
        block_hash = params["blockHash"]
        block = block_builder.get_block_by_hash(block_hash)
    else:
        # Get latest block
        block = block_builder.get_latest_block()
    
    if block:
        return block.dict()
    return None


async def submit_activity_proof(params: Dict[str, Any]) -> Dict[str, Any]:
    """Submit Proof of Activity to blockchain."""
    activity_id = params.get("activity_id")
    user_id = params.get("user_id")
    orbitdb_cid = params.get("orbitdb_cid")
    ipfs_cid = params.get("ipfs_cid")
    ai_verification_score = float(params.get("ai_verification_score", 0))
    
    if not all([activity_id, user_id, orbitdb_cid]):
        raise ValueError("Missing required parameters")
    
    # Generate quantum hash
    proof_data = f"{activity_id}:{user_id}:{orbitdb_cid}:{ai_verification_score}"
    quantum_hash = generate_quantum_hash(proof_data)
    
    # Create transaction
    from_address = params.get("from_address", "0x0000000000000000000000000000000000000000")
    nonce = nonces.get(from_address, 0)
    nonces[from_address] = nonce + 1
    
    tx = Transaction(
        hash="",
        from_address=from_address,
        to_address=None,
        transaction_type=TransactionType.ACTIVITY_PROOF,
        value=0.0,
        gas_price=0.0,
        gas_limit=100000,
        nonce=nonce,
        data={
            "activity_id": activity_id,
            "user_id": user_id,
            "orbitdb_cid": orbitdb_cid,
            "ipfs_cid": ipfs_cid,
            "quantum_hash": quantum_hash,
            "ai_verification_score": ai_verification_score
        },
        status="pending"
    )
    
    tx.hash = create_transaction_hash(tx)
    transaction_pool.add_transaction(tx)
    
    return {
        "transaction_hash": tx.hash,
        "quantum_hash": quantum_hash,
        "status": "submitted"
    }


async def submit_status_proof(params: Dict[str, Any]) -> Dict[str, Any]:
    """Submit Proof of Status to blockchain."""
    user_id = params.get("user_id")
    status_score = params.get("status_score")
    orbitdb_cid = params.get("orbitdb_cid")
    
    if not all([user_id, status_score, orbitdb_cid]):
        raise ValueError("Missing required parameters")
    
    # Generate quantum hash
    proof_data = f"{user_id}:{orbitdb_cid}:{status_score}"
    quantum_hash = generate_quantum_hash(proof_data)
    
    # Create transaction
    from_address = params.get("from_address", "0x0000000000000000000000000000000000000000")
    nonce = nonces.get(from_address, 0)
    nonces[from_address] = nonce + 1
    
    tx = Transaction(
        hash="",
        from_address=from_address,
        to_address=None,
        transaction_type=TransactionType.STATUS_PROOF,
        value=0.0,
        gas_price=0.0,
        gas_limit=100000,
        nonce=nonce,
        data={
            "user_id": user_id,
            "status_score": status_score,
            "orbitdb_cid": orbitdb_cid,
            "quantum_hash": quantum_hash
        },
        status="pending"
    )
    
    tx.hash = create_transaction_hash(tx)
    transaction_pool.add_transaction(tx)
    
    return {
        "transaction_hash": tx.hash,
        "quantum_hash": quantum_hash,
        "status": "submitted"
    }


def get_transaction_count(address: str) -> int:
    """Get transaction count (nonce) for an address."""
    return nonces.get(address, 0)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "chain_id": settings.blockchain_network,
        "block_number": block_builder.get_block_count(),
        "pending_transactions": len(transaction_pool.get_pending_transactions())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.rpc_host, port=settings.rpc_port)

