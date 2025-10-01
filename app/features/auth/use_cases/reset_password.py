from dataclasses import dataclass
from typing import Optional

from app.features.auth.domain import PasswordResetToken, PasswordPolicy
from app.features.auth.ports import (
    IUserRepository,
    IPasswordResetTokenRepository,
    IPasswordHasher,
    IEmailService,
)
from app.core.errors import NotFoundError, BusinessRuleViolationError


@dataclass
class RequestPasswordResetRequest:
    """Request for password reset."""
    email: str


@dataclass
class RequestPasswordResetResponse:
    """Response after password reset request."""
    message: str


@dataclass
class ResetPasswordRequest:
    """Request to reset password with token."""
    token: str
    new_password: str


@dataclass
class ResetPasswordResponse:
    """Response after password reset."""
    message: str


class RequestPasswordResetUseCase:
    """Use case for requesting password reset."""
    
    def __init__(
        self,
        user_repository: IUserRepository,
        token_repository: IPasswordResetTokenRepository,
        email_service: IEmailService,
    ):
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.email_service = email_service
    
    async def execute(self, request: RequestPasswordResetRequest) -> RequestPasswordResetResponse:
        """
        Request password reset.
        
        Business rules:
        - RG-AUTH-008: Password reset token expires after 1 hour
        """
        
        # Find user by email
        user = await self.user_repository.get_by_email(request.email.lower())
        if not user:
            # Don't reveal if email exists or not for security
            return RequestPasswordResetResponse(
                message="If the email exists, a password reset link has been sent."
            )
        
        # Create password reset token
        reset_token = PasswordResetToken.create(user_id=user.id)
        await self.token_repository.create(reset_token)
        
        # Send password reset email
        await self.email_service.send_password_reset_email(
            email=user.email,
            token=reset_token.token,
        )
        
        return RequestPasswordResetResponse(
            message="If the email exists, a password reset link has been sent."
        )


class ResetPasswordUseCase:
    """Use case for resetting password."""
    
    def __init__(
        self,
        user_repository: IUserRepository,
        token_repository: IPasswordResetTokenRepository,
        password_hasher: IPasswordHasher,
    ):
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.password_hasher = password_hasher
    
    async def execute(self, request: ResetPasswordRequest) -> ResetPasswordResponse:
        """
        Reset password using token.
        
        Business rules:
        - RG-AUTH-008: Token can only be used once
        - RG-AUTH-002: New password must meet policy requirements
        """
        
        # Get reset token
        token = await self.token_repository.get_by_token(request.token)
        if not token:
            raise NotFoundError("Password reset token", request.token)
        
        # Validate token
        if not token.is_valid:
            raise BusinessRuleViolationError(
                "Password reset token is expired or already used",
                rule="RG-AUTH-008"
            )
        
        # Validate new password
        PasswordPolicy.validate(request.new_password)
        
        # Get user
        user = await self.user_repository.get_by_id(token.user_id)
        if not user:
            raise NotFoundError("User", token.user_id)
        
        # Hash new password
        hashed_password = self.password_hasher.hash(request.new_password)
        
        # Update user password
        user.change_password(hashed_password)
        await self.user_repository.update(user)
        
        # Mark token as used
        token.use()
        await self.token_repository.mark_as_used(request.token)
        
        return ResetPasswordResponse(
            message="Password reset successfully. You can now login with your new password."
        )