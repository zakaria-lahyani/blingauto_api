from dataclasses import dataclass
from typing import Optional

from app.features.auth.domain import User, RefreshToken
from app.features.auth.ports import (
    IUserRepository,
    IRefreshTokenRepository,
    IPasswordHasher,
    ITokenService,
    ICacheService,
)
from app.core.errors import AuthenticationError, BusinessRuleViolationError


@dataclass
class LoginUserRequest:
    """Request for user login."""
    email: str
    password: str


@dataclass
class LoginUserResponse:
    """Response after successful login."""
    access_token: str
    refresh_token: str
    user_id: str
    email: str
    full_name: str
    role: str


class LoginUserUseCase:
    """Use case for user login."""
    
    def __init__(
        self,
        user_repository: IUserRepository,
        refresh_token_repository: IRefreshTokenRepository,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
        cache_service: ICacheService,
    ):
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.cache_service = cache_service
    
    async def execute(self, request: LoginUserRequest) -> LoginUserResponse:
        """
        Authenticate user and create session.
        
        Business rules:
        - RG-AUTH-005: JWT token management
        - RG-AUTH-006: Account lockout verification
        - RG-AUTH-007: Email verification check
        """
        
        # Find user by email
        user = await self.user_repository.get_by_email(request.email.lower())
        if not user:
            raise AuthenticationError("Invalid email or password")
        
        # Verify password
        if not self.password_hasher.verify(request.password, user.hashed_password):
            # Record failed attempt
            user.record_failed_login()
            await self.user_repository.update(user)
            raise AuthenticationError("Invalid email or password")
        
        # Check if user can login (active, not locked, verified)
        try:
            user.can_login()
        except BusinessRuleViolationError as e:
            raise AuthenticationError(str(e))
        
        # Record successful login
        user.record_successful_login()
        await self.user_repository.update(user)
        
        # Create tokens
        access_token = self.token_service.create_access_token(
            user_id=user.id,
            role=user.role.value,
        )
        
        # Create and save refresh token
        refresh_token = RefreshToken.create(user_id=user.id)
        await self.refresh_token_repository.create(refresh_token)
        
        # Cache user data for faster subsequent requests
        await self.cache_service.set_user(
            user_id=user.id,
            user_data={
                "id": user.id,
                "email": user.email,
                "role": user.role.value,
                "full_name": user.full_name,
            },
            ttl=900,  # 15 minutes
        )
        
        return LoginUserResponse(
            access_token=access_token,
            refresh_token=refresh_token.token,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
        )