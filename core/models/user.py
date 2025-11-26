"""User and wallet models."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class Wallet(BaseModel):
    """Cryptographic wallet."""
    
    address: str = Field(..., description="Wallet address")
    public_key: str = Field(..., description="Public key")
    encrypted_private_key: Optional[str] = Field(None, description="Encrypted private key")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(BaseModel):
    """User profile information."""
    
    user_id: str = Field(..., description="Unique user identifier")
    username: Optional[str] = Field(None, description="Username")
    email: Optional[str] = Field(None, description="Email address")
    wallet: Wallet = Field(..., description="Associated wallet")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class User(BaseModel):
    """User model with authentication."""
    
    user_id: str = Field(..., description="Unique user identifier")
    profile: UserProfile = Field(..., description="User profile")
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    last_login: Optional[datetime] = Field(None)
    session_token: Optional[str] = Field(None, description="Current session token")

