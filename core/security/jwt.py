"""JWT token utilities."""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from config import get_settings


def create_jwt_token(user_id: str, additional_claims: Optional[Dict[str, Any]] = None, 
                     expires_in: int = 3600) -> str:
    """
    Create a JWT token for a user.
    
    Args:
        user_id: User identifier
        additional_claims: Additional claims to include
        expires_in: Token expiration in seconds
        
    Returns:
        JWT token string
    """
    settings = get_settings()
    
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in),
        'iat': datetime.utcnow(),
    }
    
    if additional_claims:
        payload.update(additional_claims)
    
    token = jwt.encode(payload, settings.jwt_secret, algorithm='HS256')
    return token


def verify_jwt_token(token: str) -> bool:
    """
    Verify a JWT token is valid.
    
    Args:
        token: JWT token string
        
    Returns:
        True if token is valid
    """
    try:
        settings = get_settings()
        jwt.decode(token, settings.jwt_secret, algorithms=['HS256'])
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a JWT token and return payload.
    
    Args:
        token: JWT token string
        
    Returns:
        Token payload or None if invalid
    """
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.jwt_secret, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

