"""Authentication API routes."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import secrets

from core.schemas.auth import LoginRequest, LoginResponse, WalletLinkRequest, WalletLinkResponse
from core.security.jwt import create_jwt_token, verify_jwt_token, decode_jwt_token
from core.security.auth import authenticate_user, verify_wallet_signature
from core.validators.user import validate_user_id, validate_wallet_address

router = APIRouter()
security = HTTPBearer()

# In-memory user store (in production, use database)
users_db = {}
sessions_db = {}


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    payload = decode_jwt_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {"user_id": user_id}


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login endpoint.
    
    Supports both password-based and wallet-based authentication.
    """
    user_id = None
    
    # Find user
    if request.username:
        user_id = request.username
    elif request.email:
        # In production, lookup by email
        user_id = request.email.split("@")[0]
    elif request.wallet_address:
        # Wallet-based auth
        if validate_wallet_address(request.wallet_address):
            user_id = request.wallet_address
        else:
            raise HTTPException(status_code=400, detail="Invalid wallet address")
    else:
        raise HTTPException(status_code=400, detail="Username, email, or wallet address required")
    
    # Authenticate
    if request.password:
        # Password-based auth
        authenticated = authenticate_user(user_id, password=request.password)
    elif request.wallet_address:
        # Wallet-based auth (would need signature in production)
        authenticated = True  # Simplified
    else:
        raise HTTPException(status_code=400, detail="Password or wallet signature required")
    
    if not authenticated:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    token = create_jwt_token(user_id, expires_in=3600)
    
    # Store session
    sessions_db[user_id] = {
        "token": token,
        "user_id": user_id
    }
    
    return LoginResponse(
        access_token=token,
        user_id=user_id,
        expires_in=3600
    )


@router.post("/auth/wallet-link", response_model=WalletLinkResponse)
async def link_wallet(request: WalletLinkRequest, current_user: dict = Depends(get_current_user)):
    """
    Link a wallet to a user account.
    """
    if not validate_wallet_address(request.wallet_address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    
    if not validate_user_id(request.user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    # Verify signature
    message = f"Link wallet {request.wallet_address} to user {request.user_id}"
    if not verify_wallet_signature(message, request.signature, request.wallet_address):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Link wallet (in production, save to database)
    if request.user_id not in users_db:
        users_db[request.user_id] = {}
    
    users_db[request.user_id]["wallet_address"] = request.wallet_address
    
    return WalletLinkResponse(
        success=True,
        wallet_address=request.wallet_address,
        message="Wallet linked successfully"
    )


@router.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return {
        "user_id": current_user["user_id"],
        "authenticated": True
    }

