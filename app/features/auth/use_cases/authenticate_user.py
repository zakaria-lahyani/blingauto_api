"""Authenticate user use case."""

from typing import Optional
from dataclasses import dataclass

from ..domain import User
from ..ports import IUserRepository, ITokenService
from ..domain.exceptions import AuthenticationError, UserInactiveError


@dataclass
class AuthenticateUserRequest:
    """Request to authenticate user from token."""
    token: str


class AuthenticateUserUseCase:
    """Use case for authenticating a user from JWT token."""
    
    def __init__(
        self,
        user_repository: IUserRepository,
        token_service: ITokenService
    ):
        self._user_repository = user_repository
        self._token_service = token_service
    
    async def execute(self, request: AuthenticateUserRequest) -> User:
        """Authenticate user from token.
        
        Returns:
            User entity if authentication successful
            
        Raises:
            AuthenticationError: If token is invalid or user not found
            UserInactiveError: If user account is inactive
        """
        # Validate token and extract user ID
        payload = self._token_service.validate_access_token(request.token)
        if not payload:
            raise AuthenticationError("Invalid token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        
        # Get user from repository
        user = await self._user_repository.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")
        
        # Check user status - this is business logic!
        if not user.is_active:
            raise UserInactiveError("User account is inactive")
        
        return user