from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from enum import Enum
import re
from uuid import uuid4

from .exceptions import ValidationError, BusinessRuleViolationError


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    WASHER = "washer"
    CLIENT = "client"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


@dataclass
class User:
    """User domain entity with business rules."""
    
    id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    hashed_password: str = field(repr=False)
    phone_number: Optional[str] = None
    email_verified: bool = False
    email_verified_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    
    # Business rule constants
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=30)
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 128
    EMAIL_MAX_LENGTH = 255
    NAME_MAX_LENGTH = 100
    PHONE_MAX_LENGTH = 20
    
    def __post_init__(self):
        """Validate entity after initialization."""
        self._validate_email()
        self._validate_names()
        self._validate_phone()
    
    @classmethod
    def create(
        cls,
        email: str,
        first_name: str,
        last_name: str,
        hashed_password: str,
        role: UserRole = UserRole.CLIENT,
        phone_number: Optional[str] = None,
    ) -> "User":
        """Factory method to create a new user."""
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid4()),
            email=email.lower().strip(),
            first_name=first_name.strip().title(),
            last_name=last_name.strip().title(),
            hashed_password=hashed_password,
            role=role,
            status=UserStatus.INACTIVE,  # Inactive until email verification
            phone_number=phone_number.strip() if phone_number else None,
            created_at=now,
            updated_at=now,
            email_verified=False,
            failed_login_attempts=0,
        )
    
    def _validate_email(self):
        """Validate email format and length."""
        if not self.email or "@" not in self.email:
            raise ValidationError("Invalid email format", field="email")
        
        if len(self.email) > self.EMAIL_MAX_LENGTH:
            raise ValidationError(
                f"Email must be less than {self.EMAIL_MAX_LENGTH} characters",
                field="email"
            )
        
        # Basic email regex validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, self.email):
            raise ValidationError("Invalid email format", field="email")
    
    def _validate_names(self):
        """Validate first and last names."""
        if not self.first_name or not self.first_name.strip():
            raise ValidationError("First name is required", field="first_name")
        
        if len(self.first_name) > self.NAME_MAX_LENGTH:
            raise ValidationError(
                f"First name must be less than {self.NAME_MAX_LENGTH} characters",
                field="first_name"
            )
        
        if not self.last_name or not self.last_name.strip():
            raise ValidationError("Last name is required", field="last_name")
        
        if len(self.last_name) > self.NAME_MAX_LENGTH:
            raise ValidationError(
                f"Last name must be less than {self.NAME_MAX_LENGTH} characters",
                field="last_name"
            )
    
    def _validate_phone(self):
        """Validate phone number if provided."""
        if self.phone_number:
            # Remove common separators
            cleaned = re.sub(r"[\s\-\(\)\.]", "", self.phone_number)
            
            if len(cleaned) > self.PHONE_MAX_LENGTH:
                raise ValidationError(
                    f"Phone number must be less than {self.PHONE_MAX_LENGTH} characters",
                    field="phone_number"
                )
            
            # Basic phone validation (digits and optional +)
            if not re.match(r"^\+?\d+$", cleaned):
                raise ValidationError("Invalid phone number format", field="phone_number")
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE
    
    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until:
            return datetime.now(timezone.utc) < self.locked_until
        return False
    
    @property
    def is_staff(self) -> bool:
        """Check if user is staff (not a client)."""
        return self.role != UserRole.CLIENT
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN
    
    def can_login(self) -> bool:
        """Check if user can login."""
        if not self.is_active:
            raise BusinessRuleViolationError(
                "Account is not active",
                rule="RG-AUTH-007"
            )
        
        if self.is_locked:
            raise BusinessRuleViolationError(
                "Account is temporarily locked due to too many failed attempts",
                rule="RG-AUTH-006"
            )
        
        if not self.email_verified:
            raise BusinessRuleViolationError(
                "Email verification required",
                rule="RG-AUTH-007"
            )
        
        return True
    
    def record_failed_login(self):
        """Record a failed login attempt."""
        self.failed_login_attempts += 1

        if self.failed_login_attempts >= self.MAX_LOGIN_ATTEMPTS:
            # Calculate progressive lockout duration
            lockout_multiplier = min(self.failed_login_attempts // self.MAX_LOGIN_ATTEMPTS, 4)
            lockout_duration = self.LOCKOUT_DURATION * lockout_multiplier
            self.locked_until = datetime.now(timezone.utc) + lockout_duration

    def record_successful_login(self):
        """Record a successful login."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.now(timezone.utc)
    
    def verify_email(self):
        """Mark email as verified."""
        if self.email_verified:
            raise BusinessRuleViolationError(
                "Email already verified",
                rule="RG-AUTH-007"
            )

        self.email_verified = True
        self.email_verified_at = datetime.now(timezone.utc)
        self.status = UserStatus.ACTIVE

    def change_password(self, new_hashed_password: str):
        """Change user password."""
        self.hashed_password = new_hashed_password
        self.password_changed_at = datetime.now(timezone.utc)
    
    def update_profile(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone_number: Optional[str] = None,
    ):
        """Update user profile."""
        if first_name is not None:
            self.first_name = first_name.strip().title()
        
        if last_name is not None:
            self.last_name = last_name.strip().title()
        
        if phone_number is not None:
            self.phone_number = phone_number.strip() if phone_number else None
        
        self._validate_names()
        self._validate_phone()
        self.updated_at = datetime.now(timezone.utc)

    def suspend(self):
        """Suspend user account."""
        if self.status == UserStatus.SUSPENDED:
            raise BusinessRuleViolationError("Account already suspended")

        self.status = UserStatus.SUSPENDED
        self.updated_at = datetime.now(timezone.utc)

    def reactivate(self):
        """Reactivate user account."""
        if self.status == UserStatus.ACTIVE:
            raise BusinessRuleViolationError("Account already active")

        if self.status == UserStatus.DELETED:
            raise BusinessRuleViolationError("Cannot reactivate deleted account")

        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)

    def soft_delete(self):
        """Soft delete user account."""
        if self.status == UserStatus.DELETED:
            raise BusinessRuleViolationError("Account already deleted")

        self.status = UserStatus.DELETED
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class PasswordResetToken:
    """Password reset token value object."""
    
    token: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    used: bool = False
    
    EXPIRY_HOURS = 1
    
    @classmethod
    def create(cls, user_id: str) -> "PasswordResetToken":
        """Create a new password reset token."""
        now = datetime.now(timezone.utc)
        return cls(
            token=str(uuid4()),
            user_id=user_id,
            created_at=now,
            expires_at=now + timedelta(hours=cls.EXPIRY_HOURS),
            used=False,
        )

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid."""
        return not self.used and not self.is_expired
    
    def use(self):
        """Mark token as used."""
        if self.used:
            raise BusinessRuleViolationError("Token already used", rule="RG-AUTH-008")
        
        if self.is_expired:
            raise BusinessRuleViolationError("Token expired", rule="RG-AUTH-008")
        
        self.used = True


@dataclass
class EmailVerificationToken:
    """Email verification token value object."""
    
    token: str
    user_id: str
    email: str
    created_at: datetime
    expires_at: datetime
    used: bool = False
    
    EXPIRY_HOURS = 24
    
    @classmethod
    def create(cls, user_id: str, email: str) -> "EmailVerificationToken":
        """Create a new email verification token."""
        now = datetime.now(timezone.utc)
        return cls(
            token=str(uuid4()),
            user_id=user_id,
            email=email,
            created_at=now,
            expires_at=now + timedelta(hours=cls.EXPIRY_HOURS),
            used=False,
        )

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid."""
        return not self.used and not self.is_expired
    
    def use(self):
        """Mark token as used."""
        if self.used:
            raise BusinessRuleViolationError("Token already used", rule="RG-AUTH-007")
        
        if self.is_expired:
            raise BusinessRuleViolationError("Token expired", rule="RG-AUTH-007")
        
        self.used = True


@dataclass
class RefreshToken:
    """Refresh token value object."""
    
    token: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    revoked: bool = False
    
    EXPIRY_DAYS = 7
    
    @classmethod
    def create(cls, user_id: str) -> "RefreshToken":
        """Create a new refresh token."""
        now = datetime.now(timezone.utc)
        return cls(
            token=str(uuid4()),
            user_id=user_id,
            created_at=now,
            expires_at=now + timedelta(days=cls.EXPIRY_DAYS),
            revoked=False,
        )

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid."""
        return not self.revoked and not self.is_expired
    
    def revoke(self):
        """Revoke the token."""
        self.revoked = True
    
    def rotate(self) -> "RefreshToken":
        """Rotate the token (revoke current and create new)."""
        self.revoke()
        return RefreshToken.create(self.user_id)