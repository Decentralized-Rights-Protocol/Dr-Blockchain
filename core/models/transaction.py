"""Transaction and block models."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """Types of blockchain transactions."""
    
    ACTIVITY_PROOF = "activity_proof"
    STATUS_PROOF = "status_proof"
    REWARD_CLAIM = "reward_claim"
    TRANSFER = "transfer"
    CONTRACT_CALL = "contract_call"


class Transaction(BaseModel):
    """Blockchain transaction."""
    
    hash: str = Field(..., description="Transaction hash")
    from_address: str = Field(..., description="Sender address")
    to_address: Optional[str] = Field(None, description="Recipient address")
    transaction_type: TransactionType
    value: float = Field(default=0.0, description="Transaction value in DeRi")
    gas_price: float = Field(default=0.0)
    gas_limit: int = Field(default=21000)
    nonce: int = Field(..., description="Transaction nonce")
    data: Dict[str, Any] = Field(default_factory=dict, description="Transaction data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    block_number: Optional[int] = Field(None, description="Block number if mined")
    block_hash: Optional[str] = Field(None, description="Block hash if mined")
    status: str = Field(default="pending", description="Transaction status")
    signature: Optional[str] = Field(None, description="Transaction signature")
    
    class Config:
        use_enum_values = True


class Block(BaseModel):
    """Blockchain block."""
    
    number: int = Field(..., description="Block number")
    hash: str = Field(..., description="Block hash")
    parent_hash: str = Field(..., description="Parent block hash")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    transactions: List[Transaction] = Field(default_factory=list)
    transaction_count: int = Field(default=0)
    miner: str = Field(..., description="Miner address")
    difficulty: int = Field(default=1)
    gas_used: int = Field(default=0)
    gas_limit: int = Field(default=8000000)
    extra_data: Dict[str, Any] = Field(default_factory=dict)

