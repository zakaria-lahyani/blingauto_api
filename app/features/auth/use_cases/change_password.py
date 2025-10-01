"""
Change Password Use Case
Implements RG-AUTH-015: Password change with current password validation
"""

from dataclasses import dataclass
from typing import Optional

from app.core.errors import ValidationError, UnauthorizedError
from app.features.auth.ports import IUserRepository, IPasswordHasher, ICacheService


@dataclass
class ChangePasswordRequest:
    """Request to change user password."""
    user_id: str
    current_password: str
    new_password: str


@dataclass
class ChangePasswordResponse:
    """Response after changing password."""
    success: bool
    message: str


class ChangePasswordUseCase:
    """
    Use case for changing user password.

    Business Rules:
    - RG-AUTH-015: User must provide current password for verification
    - RG-AUTH-002: New password must meet complexity requirements
    - RG-AUTH-016: Clear all user sessions after password change
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        password_hasher: IPasswordHasher,
        cache_service: ICacheService,
    ):
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._cache_service = cache_service

    def execute(self, request: ChangePasswordRequest) -> ChangePasswordResponse:
        """Execute the change password use case."""

        # Step 1: Retrieve user
        user = self._user_repository.get_by_id(request.user_id)
        if not user:
            raise UnauthorizedError("User not found")

        # Step 2: Verify current password
        if not self._password_hasher.verify(request.current_password, user.hashed_password):
            raise ValidationError("Current password is incorrect")

        # Step 3: Validate new password requirements
        if len(request.new_password) < 8:
            raise ValidationError("New password must be at least 8 characters long")

        if request.new_password == request.current_password:
            raise ValidationError("New password must be different from current password")

        # Step 4: Hash new password
        new_hashed_password = self._password_hasher.hash(request.new_password)

        # Step 5: Update user password
        user.hashed_password = new_hashed_password
        self._user_repository.update(user)

        # Step 6: Invalidate all user sessions (security best practice)
        self._cache_service.invalidate_user_sessions(request.user_id)

        return ChangePasswordResponse(
            success=True,
            message="Password changed successfully. Please login again with your new password."
        )
