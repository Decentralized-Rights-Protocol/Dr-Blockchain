"""API request/response schemas."""

from .activity import (
    ActivitySubmitRequest,
    ActivitySubmitResponse,
    ActivityFeedResponse,
    ActivityVerificationRequest,
)
from .status import (
    StatusProfileRequest,
    StatusProfileResponse,
    StatusUpdateRequest,
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

