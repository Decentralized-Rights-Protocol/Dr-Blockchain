"""Authentication utilities."""

from typing import Optional
from eth_account.messages import encode_defunct
from eth_account import Account


def verify_wallet_signature(message: str, signature: str, wallet_address: str) -> bool:
    """
    Verify a wallet signature for authentication.
    
    Args:
        message: Original message
        signature: Signature hex string
        wallet_address: Wallet address
        
    Returns:
        True if signature is valid
    """
    try:
        message_encoded = encode_defunct(text=message)
        recovered_address = Account.recover_message(message_encoded, signature=signature)
        return recovered_address.lower() == wallet_address.lower()
    except Exception:
        return False


def authenticate_user(user_id: str, password: Optional[str] = None, 
                      wallet_address: Optional[str] = None,
                      signature: Optional[str] = None) -> bool:
    """
    Authenticate a user.
    
    Args:
        user_id: User identifier
        password: Password (if password-based auth)
        wallet_address: Wallet address (if wallet-based auth)
        signature: Signature (if wallet-based auth)
        
    Returns:
        True if authentication succeeds
    """
    # Placeholder implementation
    # In production, verify against database
    if password:
        # Verify password hash
        return True
    elif wallet_address and signature:
        # Verify wallet signature
        message = f"Authenticate {user_id}"
        return verify_wallet_signature(message, signature, wallet_address)
    return False

