"""
Update Profile Use Case
Implements RG-AUTH-017: User profile updates
"""

from dataclasses import dataclass
from typing import Optional

from app.core.errors import ValidationError, NotFoundError
from app.features.auth.ports import IUserRepository, ICacheService


@dataclass
class UpdateProfileRequest:
    """Request to update user profile."""
    user_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None


@dataclass
class UpdateProfileResponse:
    """Response after updating profile."""
    user_id: str
    email: str
    first_name: str
    last_name: str
    phone_number: Optional[str]
    updated_at: str


class UpdateProfileUseCase:
    """
    Use case for updating user profile information.

    Business Rules:
    - RG-AUTH-017: Users can update their profile information
    - Email cannot be changed (requires separate email change flow)
    - At least one field must be provided for update
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        cache_service: ICacheService,
    ):
        self._user_repository = user_repository
        self._cache_service = cache_service

    def execute(self, request: UpdateProfileRequest) -> UpdateProfileResponse:
        """Execute the update profile use case."""

        # Step 1: Validate at least one field is being updated
        if not any([request.first_name, request.last_name, request.phone_number]):
            raise ValidationError("At least one field must be provided for update")

        # Step 2: Retrieve user
        user = self._user_repository.get_by_id(request.user_id)
        if not user:
            raise NotFoundError(f"User {request.user_id} not found")

        # Step 3: Validate and update fields
        if request.first_name is not None:
            if len(request.first_name.strip()) < 2:
                raise ValidationError("First name must be at least 2 characters long")
            user.first_name = request.first_name.strip()

        if request.last_name is not None:
            if len(request.last_name.strip()) < 2:
                raise ValidationError("Last name must be at least 2 characters long")
            user.last_name = request.last_name.strip()

        if request.phone_number is not None:
            # Simple phone validation - can be enhanced
            phone = request.phone_number.strip()
            if phone and len(phone) < 10:
                raise ValidationError("Phone number must be at least 10 digits")
            user.phone_number = phone if phone else None

        # Step 4: Save updated user
        updated_user = self._user_repository.update(user)

        # Step 5: Invalidate user cache
        self._cache_service.invalidate_user_cache(request.user_id)

        return UpdateProfileResponse(
            user_id=updated_user.id,
            email=updated_user.email,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            phone_number=updated_user.phone_number,
            updated_at=updated_user.updated_at.isoformat() if updated_user.updated_at else ""
        )
