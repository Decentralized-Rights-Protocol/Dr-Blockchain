"""API request/response schemas."""

from .activity import (
    ActivityFeedResponse,
    ActivitySubmitRequest,
    ActivitySubmitResponse,
    ActivityVerificationRequest,
)
from .auth import (
    LoginRequest,
    LoginResponse,
    WalletLinkRequest,
    WalletLinkResponse,
)
from .rewards import (
    RewardClaimRequest,
    RewardClaimResponse,
    RewardSummaryResponse,
)
from .status import (
    StatusProfileRequest,
    StatusProfileResponse,
    StatusUpdateRequest,
)

__all__ = [
    "ActivitySubmitRequest",
    "ActivitySubmitResponse",
    "ActivityFeedResponse",
    "ActivityVerificationRequest",
    "StatusProfileRequest",
    "StatusProfileResponse",
    "StatusUpdateRequest",
    "LoginRequest",
    "LoginResponse",
    "WalletLinkRequest",
    "WalletLinkResponse",
    "RewardClaimRequest",
    "RewardClaimResponse",
    "RewardSummaryResponse",
]
