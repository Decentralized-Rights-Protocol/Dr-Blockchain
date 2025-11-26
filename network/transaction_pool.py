"""Transaction pool for managing pending transactions."""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from pathlib import Path
from core.models.transaction import Transaction, TransactionType


class TransactionPool:
    """Manages pending transactions before they are included in blocks."""
    
    def __init__(self, state_file: Optional[str] = None):
        self.state_file = state_file or Path(__file__).parent / "node_state.json"
        self.pending_transactions: List[Transaction] = []
        self.load_state()
    
    def load_state(self):
        """Load transaction pool state from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.pending_transactions = [
                        Transaction(**tx) for tx in state.get('pending_transactions', [])
                    ]
        except Exception as e:
            print(f"Error loading transaction pool state: {e}")
            self.pending_transactions = []
    
    def save_state(self):
        """Save transaction pool state to file."""
        try:
            state = {
                'pending_transactions': [
                    tx.dict() for tx in self.pending_transactions
                ]
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving transaction pool state: {e}")
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """
        Add a transaction to the pool.
        
        Args:
            transaction: Transaction to add
            
        Returns:
            True if added successfully
        """
        # Check for duplicates
        if any(tx.hash == transaction.hash for tx in self.pending_transactions):
            return False
        
        self.pending_transactions.append(transaction)
        self.save_state()
        return True
    
    def get_pending_transactions(self, limit: Optional[int] = None) -> List[Transaction]:
        """
        Get pending transactions.
        
        Args:
            limit: Maximum number of transactions to return
            
        Returns:
            List of pending transactions
        """
        transactions = self.pending_transactions.copy()
        if limit:
            transactions = transactions[:limit]
        return transactions
    
    def remove_transaction(self, tx_hash: str) -> bool:
        """
        Remove a transaction from the pool.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            True if removed
        """
        initial_count = len(self.pending_transactions)
        self.pending_transactions = [
            tx for tx in self.pending_transactions if tx.hash != tx_hash
        ]
        removed = len(self.pending_transactions) < initial_count
        if removed:
            self.save_state()
        return removed
    
    def clear(self):
        """Clear all pending transactions."""
        self.pending_transactions = []
        self.save_state()
    
    def get_transaction_by_hash(self, tx_hash: str) -> Optional[Transaction]:
        """Get a transaction by hash."""
        for tx in self.pending_transactions:
            if tx.hash == tx_hash:
                return tx
        return None

