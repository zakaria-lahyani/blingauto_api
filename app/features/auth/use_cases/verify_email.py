from dataclasses import dataclass

from app.features.auth.ports import (
    IUserRepository,
    IEmailVerificationTokenRepository,
    IEmailService,
)
from app.core.errors import NotFoundError, BusinessRuleViolationError


@dataclass
class VerifyEmailRequest:
    """Request for email verification."""
    token: str


@dataclass
class VerifyEmailResponse:
    """Response after email verification."""
    user_id: str
    email: str
    message: str


class VerifyEmailUseCase:
    """Use case for email verification."""
    
    def __init__(
        self,
        user_repository: IUserRepository,
        token_repository: IEmailVerificationTokenRepository,
        email_service: IEmailService,
    ):
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.email_service = email_service
    
    async def execute(self, request: VerifyEmailRequest) -> VerifyEmailResponse:
        """
        Verify user email address.
        
        Business rules:
        - RG-AUTH-007: Email verification required for activation
        """
        
        # Get verification token
        token = await self.token_repository.get_by_token(request.token)
        if not token:
            raise NotFoundError("Verification token", request.token)
        
        # Validate token
        if not token.is_valid:
            raise BusinessRuleViolationError(
                "Verification token is expired or already used",
                rule="RG-AUTH-007"
            )
        
        # Get user
        user = await self.user_repository.get_by_id(token.user_id)
        if not user:
            raise NotFoundError("User", token.user_id)
        
        # Verify email
        user.verify_email()
        await self.user_repository.update(user)
        
        # Mark token as used
        token.use()
        await self.token_repository.mark_as_used(request.token)
        
        # Send welcome email
        await self.email_service.send_welcome_email(
            email=user.email,
            first_name=user.first_name,
        )
        
        return VerifyEmailResponse(
            user_id=user.id,
            email=user.email,
            message="Email verified successfully. Your account is now active.",
        )