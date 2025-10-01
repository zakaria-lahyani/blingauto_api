# Re-export domain entities through ports so adapters don't import domain directly
from ..domain.entities import (
    User,
    UserRole,
    UserStatus,
    PasswordResetToken,
    EmailVerificationToken,
    RefreshToken,
)

from .repositories import (
    IUserRepository,
    IPasswordResetTokenRepository,
    IEmailVerificationTokenRepository,
    IRefreshTokenRepository,
)
from .services import (
    IPasswordHasher,
    ITokenService,
    IEmailService,
    ICacheService,
)

# Alias for backward compatibility
ITokenRepository = IRefreshTokenRepository

__all__ = [
    # Domain entities (re-exported)
    "User",
    "UserRole",
    "UserStatus",
    "PasswordResetToken",
    "EmailVerificationToken",
    "RefreshToken",
    # Repository interfaces
    "IUserRepository",
    "IPasswordResetTokenRepository",
    "IEmailVerificationTokenRepository",
    "IRefreshTokenRepository",
    "ITokenRepository",
    # Service interfaces
    "IPasswordHasher",
    "ITokenService",
    "IEmailService",
    "ICacheService",
]
