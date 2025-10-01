"""
Logout Use Case
Implements RG-AUTH-018: Secure logout with token revocation
"""

from dataclasses import dataclass

from app.core.errors import NotFoundError
from app.features.auth.ports import IUserRepository, ITokenRepository, ICacheService


@dataclass
class LogoutRequest:
    """Request to logout user."""
    user_id: str
    token: str  # Current access token


@dataclass
class LogoutResponse:
    """Response after logout."""
    success: bool
    message: str


class LogoutUseCase:
    """
    Use case for logging out a user.

    Business Rules:
    - RG-AUTH-018: Revoke all refresh tokens for the user
    - RG-AUTH-019: Invalidate current session cache
    - RG-AUTH-020: Blacklist current access token until expiry
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        token_repository: ITokenRepository,
        cache_service: ICacheService,
    ):
        self._user_repository = user_repository
        self._token_repository = token_repository
        self._cache_service = cache_service

    def execute(self, request: LogoutRequest) -> LogoutResponse:
        """Execute the logout use case."""

        # Step 1: Verify user exists
        user = self._user_repository.get_by_id(request.user_id)
        if not user:
            raise NotFoundError(f"User {request.user_id} not found")

        # Step 2: Revoke all refresh tokens for this user
        # This ensures user must re-authenticate on all devices
        self._token_repository.revoke_all_user_tokens(request.user_id)

        # Step 3: Blacklist current access token
        # Token remains blacklisted until its natural expiry
        self._cache_service.blacklist_token(request.token)

        # Step 4: Invalidate all user sessions from cache
        self._cache_service.invalidate_user_sessions(request.user_id)

        # Step 5: Clear user-specific cache
        self._cache_service.invalidate_user_cache(request.user_id)

        return LogoutResponse(
            success=True,
            message="Successfully logged out from all devices"
        )
