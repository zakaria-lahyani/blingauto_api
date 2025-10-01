from dataclasses import dataclass
from typing import Optional

from app.features.auth.domain import (
    User,
    UserRole,
    EmailVerificationToken,
    PasswordPolicy,
    EmailPolicy,
)
from app.features.auth.ports import (
    IUserRepository,
    IEmailVerificationTokenRepository,
    IPasswordHasher,
    IEmailService,
)
from app.core.errors import ConflictError, ValidationError


@dataclass
class RegisterUserRequest:
    """Request for user registration."""
    email: str
    password: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    role: UserRole = UserRole.CLIENT


@dataclass
class RegisterUserResponse:
    """Response after user registration."""
    user_id: str
    email: str
    full_name: str
    verification_token: str
    message: str


class RegisterUserUseCase:
    """Use case for user registration."""
    
    def __init__(
        self,
        user_repository: IUserRepository,
        token_repository: IEmailVerificationTokenRepository,
        password_hasher: IPasswordHasher,
        email_service: IEmailService,
    ):
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.password_hasher = password_hasher
        self.email_service = email_service
    
    async def execute(self, request: RegisterUserRequest) -> RegisterUserResponse:
        """
        Register a new user.
        
        Business rules:
        - RG-AUTH-001: Email validation and uniqueness
        - RG-AUTH-002: Password validation
        - RG-AUTH-003: Name validation
        - RG-AUTH-004: Phone validation
        - RG-AUTH-007: Email verification required
        """
        
        # Validate email format and normalize
        email = EmailPolicy.validate_email(request.email)
        
        # Check if email already exists
        if await self.user_repository.email_exists(email):
            raise ConflictError(
                "Email address already registered",
                field="email"
            )
        
        # Validate password
        PasswordPolicy.validate(request.password)
        
        # Hash password
        hashed_password = self.password_hasher.hash(request.password)
        
        # Create user entity
        user = User.create(
            email=email,
            first_name=request.first_name,
            last_name=request.last_name,
            hashed_password=hashed_password,
            role=request.role,
            phone_number=request.phone_number,
        )
        
        # Save user to repository
        saved_user = await self.user_repository.create(user)
        
        # Create email verification token
        verification_token = EmailVerificationToken.create(
            user_id=saved_user.id,
            email=saved_user.email,
        )
        
        # Save verification token
        await self.token_repository.create(verification_token)
        
        # Send verification email (async, don't wait)
        await self.email_service.send_verification_email(
            email=saved_user.email,
            token=verification_token.token,
        )
        
        return RegisterUserResponse(
            user_id=saved_user.id,
            email=saved_user.email,
            full_name=saved_user.full_name,
            verification_token=verification_token.token,
            message="Registration successful. Please check your email to verify your account.",
        )