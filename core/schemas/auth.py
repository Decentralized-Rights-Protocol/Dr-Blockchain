"""Authentication API schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request."""
    
    username: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    password: str = Field(..., min_length=8)
    wallet_address: Optional[str] = Field(None, description="Wallet address for wallet-based auth")


class LoginResponse(BaseModel):
    """Login response with JWT token."""
    
    access_token: str
    token_type: str = Field(default="bearer")
    user_id: str
    expires_in: int = Field(default=3600, description="Token expiration in seconds")


class WalletLinkRequest(BaseModel):
    """Request to link a wallet."""
    
    user_id: str
    wallet_address: str = Field(..., description="Wallet address")
    signature: str = Field(..., description="Signature proving wallet ownership")


class WalletLinkResponse(BaseModel):
    """Wallet link response."""
    
    success: bool
    wallet_address: str
    message: str

