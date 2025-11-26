"""Block builder for creating new blocks."""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import hashlib
from pathlib import Path
from core.models.transaction import Transaction, Block
from core.models.transaction import TransactionType


class BlockBuilder:
    """Builds and manages blockchain blocks."""
    
    def __init__(self, state_file: Optional[str] = None):
        self.state_file = state_file or Path(__file__).parent / "node_state.json"
        self.blocks: List[Block] = []
        self.chain_id = "drp-testnet"
        self.load_state()
    
    def load_state(self):
        """Load blockchain state from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.blocks = [Block(**block) for block in state.get('blocks', [])]
                    self.chain_id = state.get('chain_id', 'drp-testnet')
        except Exception as e:
            print(f"Error loading blockchain state: {e}")
            self.blocks = []
    
    def save_state(self):
        """Save blockchain state to file."""
        try:
            # Load existing state
            state = {}
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
            
            # Update blocks
            state['blocks'] = [block.dict() for block in self.blocks]
            state['chain_id'] = self.chain_id
            state['block_number'] = len(self.blocks)
            if self.blocks:
                state['last_block_hash'] = self.blocks[-1].hash
            else:
                state['last_block_hash'] = "0x0000000000000000000000000000000000000000000000000000000000000000"
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving blockchain state: {e}")
    
    def calculate_block_hash(self, block: Block) -> str:
        """Calculate block hash."""
        block_data = {
            'number': block.number,
            'parent_hash': block.parent_hash,
            'timestamp': block.timestamp.isoformat(),
            'transactions': [tx.hash for tx in block.transactions],
            'miner': block.miner,
            'difficulty': block.difficulty,
            'gas_used': block.gas_used,
            'gas_limit': block.gas_limit
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return "0x" + hashlib.sha256(block_string.encode()).hexdigest()
    
    def build_block(self, transactions: List[Transaction], miner: str) -> Block:
        """
        Build a new block from transactions.
        
        Args:
            transactions: List of transactions to include
            miner: Miner address
            
        Returns:
            New block
        """
        # Get parent hash
        parent_hash = "0x0000000000000000000000000000000000000000000000000000000000000000"
        if self.blocks:
            parent_hash = self.blocks[-1].hash
        
        # Create block
        block = Block(
            number=len(self.blocks),
            hash="",  # Will be calculated
            parent_hash=parent_hash,
            timestamp=datetime.utcnow(),
            transactions=transactions,
            transaction_count=len(transactions),
            miner=miner,
            difficulty=1,
            gas_used=sum(tx.gas_limit for tx in transactions),
            gas_limit=8000000
        )
        
        # Calculate hash
        block.hash = self.calculate_block_hash(block)
        
        # Update transaction block info
        for tx in transactions:
            tx.block_number = block.number
            tx.block_hash = block.hash
            tx.status = "mined"
        
        return block
    
    def add_block(self, block: Block) -> bool:
        """
        Add a block to the chain.
        
        Args:
            block: Block to add
            
        Returns:
            True if added successfully
        """
        # Validate block
        if not self.validate_block(block):
            return False
        
        self.blocks.append(block)
        self.save_state()
        return True
    
    def validate_block(self, block: Block) -> bool:
        """
        Validate a block.
        
        Args:
            block: Block to validate
            
        Returns:
            True if valid
        """
        # Check block number
        if block.number != len(self.blocks):
            return False
        
        # Check parent hash
        if self.blocks:
            if block.parent_hash != self.blocks[-1].hash:
                return False
        else:
            if block.parent_hash != "0x0000000000000000000000000000000000000000000000000000000000000000":
                return False
        
        # Check hash
        calculated_hash = self.calculate_block_hash(block)
        if block.hash != calculated_hash:
            return False
        
        return True
    
    def get_block(self, block_number: int) -> Optional[Block]:
        """Get a block by number."""
        if 0 <= block_number < len(self.blocks):
            return self.blocks[block_number]
        return None
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """Get a block by hash."""
        for block in self.blocks:
            if block.hash == block_hash:
                return block
        return None
    
    def get_latest_block(self) -> Optional[Block]:
        """Get the latest block."""
        if self.blocks:
            return self.blocks[-1]
        return None
    
    def get_block_count(self) -> int:
        """Get total number of blocks."""
        return len(self.blocks)

