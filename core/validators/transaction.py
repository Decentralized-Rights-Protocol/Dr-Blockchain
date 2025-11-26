"""Transaction validation utilities."""

from typing import Optional
from ..models.transaction import Transaction
import re


def validate_address(address: str) -> bool:
    """
    Validate an Ethereum-style address.
    
    Args:
        address: Address string
        
    Returns:
        True if valid
    """
    if not address:
        return False
    
    # Basic Ethereum address format
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return bool(re.match(pattern, address))


def validate_transaction(transaction: Transaction) -> tuple[bool, Optional[str]]:
    """
    Validate a transaction.
    
    Args:
        transaction: Transaction object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not validate_address(transaction.from_address):
        return False, "Invalid from_address"
    
    if transaction.to_address and not validate_address(transaction.to_address):
        return False, "Invalid to_address"
    
    if transaction.value < 0:
        return False, "Transaction value cannot be negative"
    
    if transaction.gas_price < 0:
        return False, "Gas price cannot be negative"
    
    if transaction.gas_limit < 21000:
        return False, "Gas limit too low"
    
    if transaction.nonce < 0:
        return False, "Nonce cannot be negative"
    
    return True, None

