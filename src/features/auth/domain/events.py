"""
Auth domain events
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.shared.events import DomainEvent


@dataclass
class UserRegistered(DomainEvent):
    """User registered event"""
    user_id: UUID
    email: str
    first_name: str
    last_name: str
    role: str
    requires_verification: bool = True


@dataclass 
class UserLoggedIn(DomainEvent):
    """User logged in event"""
    user_id: UUID
    email: str
    login_time: datetime
    ip_address: str = None


@dataclass
class UserPasswordChanged(DomainEvent):
    """User password changed event"""
    user_id: UUID
    email: str
    changed_at: datetime
    via_reset: bool = False


@dataclass
class UserEmailVerified(DomainEvent):
    """User email verified event"""
    user_id: UUID
    email: str
    verified_at: datetime


@dataclass
class UserAccountLocked(DomainEvent):
    """User account locked event"""
    user_id: UUID
    email: str
    locked_until: datetime
    attempt_count: int
    lockout_count: int


@dataclass
class UserRoleChanged(DomainEvent):
    """User role changed event"""
    user_id: UUID
    email: str
    old_role: str
    new_role: str
    changed_by: UUID = None