"""User validation utilities."""

from typing import Optional
import re


def validate_user_id(user_id: str) -> bool:
    """
    Validate user ID format.
    
    Args:
        user_id: User identifier
        
    Returns:
        True if valid
    """
    if not user_id:
        return False
    
    # User ID should be alphanumeric with dashes/underscores, 3-64 chars
    pattern = r'^[a-zA-Z0-9_-]{3,64}$'
    return bool(re.match(pattern, user_id))


def validate_wallet_address(address: str) -> bool:
    """
    Validate wallet address format.
    
    Args:
        address: Wallet address
        
    Returns:
        True if valid
    """
    if not address:
        return False
    
    # Ethereum address format
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return bool(re.match(pattern, address))

