from abc import ABC, abstractmethod
from typing import Optional, List

from app.features.auth.domain import (
    User,
    PasswordResetToken,
    EmailVerificationToken,
    RefreshToken,
)


class IUserRepository(ABC):
    """User repository interface."""
    
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user."""
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """Update an existing user."""
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete a user."""
        pass
    
    @abstractmethod
    async def list(
        self,
        offset: int = 0,
        limit: int = 20,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[User]:
        """List users with optional filters."""
        pass
    
    @abstractmethod
    async def count(
        self,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count users with optional filters."""
        pass
    
    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        pass


class IPasswordResetTokenRepository(ABC):
    """Password reset token repository interface."""
    
    @abstractmethod
    async def create(self, token: PasswordResetToken) -> PasswordResetToken:
        """Create a new password reset token."""
        pass
    
    @abstractmethod
    async def get_by_token(self, token: str) -> Optional[PasswordResetToken]:
        """Get password reset token by token string."""
        pass
    
    @abstractmethod
    async def mark_as_used(self, token: str) -> bool:
        """Mark token as used."""
        pass
    
    @abstractmethod
    async def delete_expired(self) -> int:
        """Delete expired tokens."""
        pass


class IEmailVerificationTokenRepository(ABC):
    """Email verification token repository interface."""
    
    @abstractmethod
    async def create(self, token: EmailVerificationToken) -> EmailVerificationToken:
        """Create a new email verification token."""
        pass
    
    @abstractmethod
    async def get_by_token(self, token: str) -> Optional[EmailVerificationToken]:
        """Get email verification token by token string."""
        pass
    
    @abstractmethod
    async def mark_as_used(self, token: str) -> bool:
        """Mark token as used."""
        pass
    
    @abstractmethod
    async def delete_expired(self) -> int:
        """Delete expired tokens."""
        pass


class IRefreshTokenRepository(ABC):
    """Refresh token repository interface."""
    
    @abstractmethod
    async def create(self, token: RefreshToken) -> RefreshToken:
        """Create a new refresh token."""
        pass
    
    @abstractmethod
    async def get_by_token(self, token: str) -> Optional[RefreshToken]:
        """Get refresh token by token string."""
        pass
    
    @abstractmethod
    async def revoke(self, token: str) -> bool:
        """Revoke a refresh token."""
        pass
    
    @abstractmethod
    async def revoke_all_for_user(self, user_id: str) -> int:
        """Revoke all refresh tokens for a user."""
        pass
    
    @abstractmethod
    async def delete_expired(self) -> int:
        """Delete expired tokens."""
        pass