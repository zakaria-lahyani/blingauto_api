from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class IPasswordHasher(ABC):
    """Password hashing service interface."""
    
    @abstractmethod
    def hash(self, password: str) -> str:
        """Hash a password."""
        pass
    
    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        pass


class ITokenService(ABC):
    """Token generation and validation service interface."""
    
    @abstractmethod
    def create_access_token(self, user_id: str, role: str) -> str:
        """Create an access token."""
        pass
    
    @abstractmethod
    def create_refresh_token(self, user_id: str) -> str:
        """Create a refresh token."""
        pass
    
    @abstractmethod
    def validate_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate an access token."""
        pass
    
    @abstractmethod
    def validate_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a refresh token."""
        pass


class IEmailService(ABC):
    """Email service interface."""
    
    @abstractmethod
    async def send_verification_email(self, email: str, token: str) -> bool:
        """Send email verification."""
        pass
    
    @abstractmethod
    async def send_password_reset_email(self, email: str, token: str) -> bool:
        """Send password reset email."""
        pass
    
    @abstractmethod
    async def send_welcome_email(self, email: str, first_name: str) -> bool:
        """Send welcome email."""
        pass
    
    @abstractmethod
    async def send_account_locked_email(self, email: str, locked_until: str) -> bool:
        """Send account locked notification."""
        pass


class ICacheService(ABC):
    """Cache service interface for auth-related caching."""
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user data."""
        pass
    
    @abstractmethod
    async def set_user(self, user_id: str, user_data: Dict[str, Any], ttl: int = 300) -> bool:
        """Cache user data."""
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Delete cached user data."""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached session data."""
        pass
    
    @abstractmethod
    async def set_session(self, session_id: str, session_data: Dict[str, Any], ttl: int = 900) -> bool:
        """Cache session data."""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete cached session data."""
        pass