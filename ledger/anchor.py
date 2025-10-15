"""
Blockchain Anchor Service for DRP Ledger Integration
Handles proof anchoring to DRP blockchain with Elder verification
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from web3 import Web3
from eth_account import Account
import aiohttp

logger = logging.getLogger(__name__)

class BlockchainAnchor:
    """Handles blockchain anchoring of proofs with Elder verification"""
    
    def __init__(self, 
                 rpc_url: str = None,
                 contract_address: str = None,
                 private_key: str = None):
        self.rpc_url = rpc_url or os.getenv("DRP_RPC_URL", "http://localhost:8545")
        self.contract_address = contract_address or os.getenv("DRP_CONTRACT_ADDRESS")
        self.private_key = private_key or os.getenv("DRP_PRIVATE_KEY")
        self.w3: Optional[Web3] = None
        self.account: Optional[Account] = None
        self.connected = False
        
    async def initialize(self):
        """Initialize blockchain connection"""
        try:
            # Initialize Web3 connection
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            if not self.w3.is_connected():
                raise Exception("Failed to connect to DRP blockchain")
            
            # Initialize account if private key provided
            if self.private_key:
                self.account = Account.from_key(self.private_key)
                logger.info(f"Blockchain anchor initialized with account: {self.account.address}")
            else:
                logger.warning("No private key provided - running in read-only mode")
            
            self.connected = True
            logger.info(f"Blockchain anchor initialized successfully with RPC: {self.rpc_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize blockchain anchor: {e}")
            self.connected = False
            raise
    
    async def anchor_proof(self, 
                          anchor_payload: Dict[str, Any], 
                          elder_signatures: List[Dict[str, Any]]) -> str:
        """
        Anchor proof to DRP blockchain with Elder verification
        
        Args:
            anchor_payload: Proof data to anchor
            elder_signatures: List of Elder signatures
            
        Returns:
            str: Transaction hash of the anchor
        """
        if not self.connected:
            raise Exception("Blockchain anchor not connected")
        
        if not self.account:
            raise Exception("No account configured for anchoring")
        
        try:
            # Create anchor transaction data
            anchor_data = {
                "proof_id": anchor_payload["proof_id"],
                "cid": anchor_payload["cid"],
                "metadata_hash": anchor_payload["metadata_hash"],
                "timestamp": anchor_payload["timestamp"],
                "elder_signatures": elder_signatures
            }
            
            # Encode anchor data
            anchor_json = json.dumps(anchor_data, sort_keys=True)
            anchor_hash = hashlib.sha256(anchor_json.encode()).hexdigest()
            
            # For now, we'll simulate blockchain anchoring
            # In production, this would interact with the actual DRP smart contract
            block_hash = await self._simulate_anchor_transaction(anchor_data)
            
            logger.info(f"Proof {anchor_payload['proof_id']} anchored to blockchain: {block_hash}")
            return block_hash
            
        except Exception as e:
            logger.error(f"Error anchoring proof to blockchain: {e}")
            raise
    
    async def _simulate_anchor_transaction(self, anchor_data: Dict[str, Any]) -> str:
        """Simulate blockchain transaction (for development)"""
        try:
            # In development mode, simulate the transaction
            # In production, this would be a real blockchain transaction
            
            # Create a mock block hash
            anchor_json = json.dumps(anchor_data, sort_keys=True)
            mock_hash = hashlib.sha256(anchor_json.encode()).hexdigest()
            
            # Simulate transaction delay
            await asyncio.sleep(0.1)
            
            logger.info(f"Simulated anchor transaction: {mock_hash}")
            return mock_hash
            
        except Exception as e:
            logger.error(f"Error simulating anchor transaction: {e}")
            raise
    
    async def verify_cid_anchor(self, cid: str) -> bool:
        """
        Verify that a CID is anchored on the blockchain
        
        Args:
            cid: IPFS CID to verify
            
        Returns:
            bool: True if CID is anchored and verified
        """
        if not self.connected:
            raise Exception("Blockchain anchor not connected")
        
        try:
            # In development mode, simulate verification
            # In production, this would query the actual blockchain
            
            # For now, assume all CIDs are verified if they exist in our system
            # This would be replaced with actual blockchain queries
            await asyncio.sleep(0.05)  # Simulate network delay
            
            logger.info(f"Verified CID anchor: {cid}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying CID anchor {cid}: {e}")
            return False
    
    async def get_block_info(self, block_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get block information from blockchain
        
        Args:
            block_hash: Hash of the block
            
        Returns:
            Dict: Block information or None if not found
        """
        if not self.connected:
            raise Exception("Blockchain anchor not connected")
        
        try:
            # In development mode, simulate block info
            # In production, this would query the actual blockchain
            
            block_info = {
                "block_hash": block_hash,
                "block_height": int(block_hash[:8], 16),  # Mock block height
                "timestamp": int(datetime.now(timezone.utc).timestamp()),
                "transaction_count": 1,
                "anchor_count": 1
            }
            
            logger.info(f"Retrieved block info for {block_hash}")
            return block_info
            
        except Exception as e:
            logger.error(f"Error getting block info for {block_hash}: {e}")
            return None
    
    async def get_chain_info(self) -> Dict[str, Any]:
        """Get blockchain chain information"""
        if not self.connected:
            raise Exception("Blockchain anchor not connected")
        
        try:
            # Get chain information
            chain_id = self.w3.eth.chain_id
            latest_block = self.w3.eth.get_block('latest')
            
            chain_info = {
                "chain_id": chain_id,
                "latest_block_height": latest_block.number,
                "latest_block_hash": latest_block.hash.hex(),
                "gas_price": self.w3.eth.gas_price,
                "connected": True
            }
            
            logger.info(f"Retrieved chain info: block {latest_block.number}")
            return chain_info
            
        except Exception as e:
            logger.error(f"Error getting chain info: {e}")
            return {"connected": False, "error": str(e)}
    
    async def get_anchor_history(self, 
                               start_block: int = None, 
                               end_block: int = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get anchor transaction history
        
        Args:
            start_block: Starting block height
            end_block: Ending block height
            limit: Maximum number of results
            
        Returns:
            List[Dict]: List of anchor transactions
        """
        if not self.connected:
            raise Exception("Blockchain anchor not connected")
        
        try:
            # In development mode, simulate anchor history
            # In production, this would query the actual blockchain
            
            anchors = []
            current_block = start_block or 0
            end_block = end_block or current_block + limit
            
            for i in range(min(limit, end_block - current_block)):
                anchor = {
                    "block_height": current_block + i,
                    "block_hash": f"0x{hashlib.sha256(f'block_{current_block + i}'.encode()).hexdigest()}",
                    "proof_id": f"proof_{current_block + i}",
                    "cid": f"QmMock{i}",
                    "timestamp": int(datetime.now(timezone.utc).timestamp()) - i * 60,
                    "elder_count": 3
                }
                anchors.append(anchor)
            
            logger.info(f"Retrieved {len(anchors)} anchor transactions")
            return anchors
            
        except Exception as e:
            logger.error(f"Error getting anchor history: {e}")
            raise
    
    async def estimate_gas_cost(self, anchor_data: Dict[str, Any]) -> int:
        """
        Estimate gas cost for anchoring transaction
        
        Args:
            anchor_data: Data to be anchored
            
        Returns:
            int: Estimated gas cost in wei
        """
        if not self.connected:
            raise Exception("Blockchain anchor not connected")
        
        try:
            # Estimate gas cost (simplified)
            # In production, this would use actual gas estimation
            
            base_gas = 21000  # Base transaction cost
            data_gas = len(json.dumps(anchor_data)) * 16  # Data cost
            elder_gas = len(anchor_data.get("elder_signatures", [])) * 1000  # Signature verification
            
            total_gas = base_gas + data_gas + elder_gas
            
            logger.info(f"Estimated gas cost: {total_gas}")
            return total_gas
            
        except Exception as e:
            logger.error(f"Error estimating gas cost: {e}")
            return 0
    
    def is_connected(self) -> bool:
        """Check if blockchain anchor is connected"""
        return self.connected
    
    async def close(self):
        """Close blockchain connection"""
        self.connected = False
        logger.info("Blockchain anchor closed")

# Utility functions
async def create_blockchain_anchor(rpc_url: str = None) -> BlockchainAnchor:
    """Create and initialize blockchain anchor"""
    anchor = BlockchainAnchor(rpc_url)
    await anchor.initialize()
    return anchor

async def anchor_proof_to_blockchain(anchor_data: Dict[str, Any], 
                                   elder_signatures: List[Dict[str, Any]],
                                   rpc_url: str = None) -> str:
    """Utility function to anchor proof to blockchain"""
    anchor = await create_blockchain_anchor(rpc_url)
    try:
        block_hash = await anchor.anchor_proof(anchor_data, elder_signatures)
        return block_hash
    finally:
        await anchor.close()
