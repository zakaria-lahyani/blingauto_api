from dataclasses import dataclass

from app.features.auth.domain import RefreshToken, SessionPolicy
from app.features.auth.ports import (
    IUserRepository,
    IRefreshTokenRepository,
    ITokenService,
)
from app.core.errors import AuthenticationError


@dataclass
class RefreshTokenRequest:
    """Request for token refresh."""
    refresh_token: str


@dataclass
class RefreshTokenResponse:
    """Response after token refresh."""
    access_token: str
    refresh_token: str


class RefreshTokenUseCase:
    """Use case for refreshing access token."""
    
    def __init__(
        self,
        user_repository: IUserRepository,
        refresh_token_repository: IRefreshTokenRepository,
        token_service: ITokenService,
    ):
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository
        self.token_service = token_service
    
    async def execute(self, request: RefreshTokenRequest) -> RefreshTokenResponse:
        """
        Refresh access token using refresh token.
        
        Business rules:
        - RG-AUTH-005: Token rotation for security
        """
        
        # Get refresh token from repository
        token = await self.refresh_token_repository.get_by_token(request.refresh_token)
        if not token:
            raise AuthenticationError("Invalid refresh token")
        
        # Validate token
        if not token.is_valid:
            raise AuthenticationError("Refresh token expired or revoked")
        
        # Get user
        user = await self.user_repository.get_by_id(token.user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        
        # Create new access token
        access_token = self.token_service.create_access_token(
            user_id=user.id,
            role=user.role.value,
        )
        
        # Rotate refresh token if policy requires
        new_refresh_token = request.refresh_token
        if SessionPolicy.should_rotate_refresh_token(1):  # Always rotate for security
            # Revoke old token
            await self.refresh_token_repository.revoke(request.refresh_token)
            
            # Create new refresh token
            new_token = RefreshToken.create(user_id=user.id)
            await self.refresh_token_repository.create(new_token)
            new_refresh_token = new_token.token
        
        return RefreshTokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )