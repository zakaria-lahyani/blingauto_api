"""Shared authentication contracts."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class AuthenticatedUser:
    """Contract for authenticated user information across features."""

    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime
    phone_number: Optional[str] = None
    email_verified: bool = False
    last_login_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == "active"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == "admin"
    
    @property
    def is_client(self) -> bool:
        """Check if user has client role."""
        return self.role == "client"
    
    @property
    def is_washer(self) -> bool:
        """Check if user has washer role."""
        return self.role == "washer"


class AuthenticationPort:
    """Port for authentication services."""
    
    async def get_current_user(self, token: str) -> Optional[AuthenticatedUser]:
        """Get current authenticated user from token."""
        raise NotImplementedError
    
    async def verify_token(self, token: str) -> bool:
        """Verify if token is valid."""
        raise NotImplementedError
    
    async def has_permission(self, user: AuthenticatedUser, resource: str, action: str) -> bool:
        """Check if user has permission for resource action."""
        raise NotImplementedError