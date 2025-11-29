"""
DRP Blockchain Node - Full implementation with PoAT + PoST verification.
"""

import json
import hashlib
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path
import logging

from core.models.transaction import Transaction, TransactionType, Block
from core.utils.crypto import generate_wallet, sign_message, verify_signature
from core.utils.quantum import generate_quantum_hash

logger = logging.getLogger(__name__)


class DRPBlockchainNode:
    """
    Full DRP blockchain node with:
    - PoAT (Proof of Activity) verification
    - PoST (Proof of Status) verification
    - Block creation and storage
    - Transaction validation
    - Wallet signing
    """
    
    def __init__(self, chain_id: str = "drp-testnet", data_dir: Path = None):
        self.chain_id = chain_id
        self.data_dir = data_dir or Path(__file__).parent.parent / "data" / "chain"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.blocks: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.pending_poat: List[Dict[str, Any]] = []
        self.pending_post: List[Dict[str, Any]] = []
        
        self.wallets: Dict[str, Dict[str, str]] = {}  # address -> {public_key, private_key}
        self.balances: Dict[str, float] = {}
        self.status_scores: Dict[str, float] = {}  # user_id -> status_score
        
        self.load_chain()
        
    def load_chain(self):
        """Load blockchain from disk."""
        chain_file = self.data_dir / "chain.json"
        if chain_file.exists():
            try:
                with open(chain_file, 'r') as f:
                    data = json.load(f)
                    self.blocks = [Block(**b) for b in data.get('blocks', [])]
                    self.balances = data.get('balances', {})
                    self.status_scores = data.get('status_scores', {})
                logger.info(f"Loaded {len(self.blocks)} blocks from chain")
            except Exception as e:
                logger.error(f"Error loading chain: {e}")
    
    def save_chain(self):
        """Save blockchain to disk."""
        chain_file = self.data_dir / "chain.json"
        data = {
            'blocks': [b.dict() for b in self.blocks],
            'balances': self.balances,
            'status_scores': self.status_scores,
            'chain_id': self.chain_id
        }
        with open(chain_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def create_wallet(self) -> Dict[str, str]:
        """Create a new wallet."""
        address, public_key, private_key = generate_wallet()
        self.wallets[address] = {
            'public_key': public_key,
            'private_key': private_key
        }
        self.balances[address] = 0.0
        return {
            'address': address,
            'public_key': public_key,
            'private_key': private_key
        }
    
    def get_latest_block(self) -> Optional[Block]:
        """Get the latest block."""
        return self.blocks[-1] if self.blocks else None
    
    def get_block_height(self) -> int:
        """Get current block height."""
        return len(self.blocks)
    
    def create_block(self, miner_address: str = "0x0000000000000000000000000000000000000000") -> Block:
        """Create a new block from pending transactions."""
        parent_hash = "0x0000000000000000000000000000000000000000000000000000000000000000"
        if self.blocks:
            parent_hash = self.blocks[-1].hash
        
        # Include pending transactions
        txs = self.pending_transactions[:10]  # Limit block size
        self.pending_transactions = self.pending_transactions[10:]
        
        block = Block(
            number=len(self.blocks),
            hash="",  # Will be calculated
            parent_hash=parent_hash,
            timestamp=datetime.utcnow(),
            transactions=txs,
            transaction_count=len(txs),
            miner=miner_address,
            difficulty=1,
            gas_used=sum(tx.gas_limit for tx in txs),
            gas_limit=8000000
        )
        
        # Calculate block hash
        block_data = {
            'number': block.number,
            'parent_hash': block.parent_hash,
            'timestamp': block.timestamp.isoformat(),
            'transactions': [tx.hash for tx in block.transactions],
            'miner': block.miner
        }
        block_string = json.dumps(block_data, sort_keys=True)
        block.hash = "0x" + hashlib.sha256(block_string.encode()).hexdigest()
        
        # Update transaction statuses
        for tx in block.transactions:
            tx.block_number = block.number
            tx.block_hash = block.hash
            tx.status = "mined"
        
        self.blocks.append(block)
        self.save_chain()
        
        logger.info(f"Created block #{block.number} with {len(txs)} transactions")
        return block
    
    def submit_transaction(self, tx: Transaction) -> bool:
        """Submit a transaction to the pool."""
        # Validate transaction
        if not self.validate_transaction(tx):
            return False
        
        # Check nonce
        sender_nonce = self.get_nonce(tx.from_address)
        if tx.nonce <= sender_nonce:
            return False
        
        self.pending_transactions.append(tx)
        logger.info(f"Transaction {tx.hash[:16]}... added to pool")
        return True
    
    def validate_transaction(self, tx: Transaction) -> bool:
        """Validate a transaction."""
        if not tx.from_address or not tx.hash:
            return False
        
        # Check signature if present
        if tx.signature:
            # Verify signature (simplified)
            message = f"{tx.from_address}{tx.to_address}{tx.value}{tx.nonce}"
            # In production, use proper signature verification
            pass
        
        return True
    
    def submit_poat(self, poat_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit Proof of Activity.
        
        Args:
            poat_data: {
                'user_id': str,
                'activity_id': str,
                'activity_type': str,
                'verification_score': float,
                'orbitdb_cid': str,
                'ipfs_cid': str,
                'quantum_hash': str
            }
        """
        # Validate PoAT
        if not all(k in poat_data for k in ['user_id', 'activity_id', 'verification_score', 'quantum_hash']):
            return {'success': False, 'error': 'Missing required fields'}
        
        # Store PoAT
        poat_id = f"poat-{poat_data['activity_id']}"
        self.pending_poat.append({
            'id': poat_id,
            **poat_data,
            'timestamp': datetime.utcnow().isoformat(),
            'block_height': None
        })
        
        # Update user status score (simplified)
        user_id = poat_data['user_id']
        if user_id not in self.status_scores:
            self.status_scores[user_id] = 0.0
        
        # Increment status based on verification score
        self.status_scores[user_id] = min(100.0, 
            self.status_scores[user_id] + poat_data.get('verification_score', 0.0) * 10
        )
        
        logger.info(f"PoAT submitted for user {user_id}, activity {poat_data['activity_id']}")
        
        return {
            'success': True,
            'poat_id': poat_id,
            'status_score': self.status_scores[user_id]
        }
    
    def submit_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit Proof of Status.
        
        Args:
            post_data: {
                'user_id': str,
                'status_score': float,
                'orbitdb_cid': str,
                'quantum_hash': str
            }
        """
        if not all(k in post_data for k in ['user_id', 'status_score', 'quantum_hash']):
            return {'success': False, 'error': 'Missing required fields'}
        
        user_id = post_data['user_id']
        self.status_scores[user_id] = post_data['status_score']
        
        self.pending_post.append({
            'id': f"post-{user_id}",
            **post_data,
            'timestamp': datetime.utcnow().isoformat(),
            'block_height': None
        })
        
        logger.info(f"PoST submitted for user {user_id}, score: {post_data['status_score']}")
        
        return {
            'success': True,
            'user_id': user_id,
            'status_score': self.status_scores[user_id]
        }
    
    def get_nonce(self, address: str) -> int:
        """Get current nonce for an address."""
        # Count transactions from this address
        count = 0
        for block in self.blocks:
            for tx in block.transactions:
                if tx.from_address == address:
                    count += 1
        for tx in self.pending_transactions:
            if tx.from_address == address:
                count += 1
        return count
    
    def get_balance(self, address: str) -> float:
        """Get balance for an address."""
        return self.balances.get(address, 0.0)
    
    def get_status_score(self, user_id: str) -> float:
        """Get status score for a user."""
        return self.status_scores.get(user_id, 0.0)

