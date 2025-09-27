"""
Auth API schemas
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from src.features.auth.domain.enums import AuthRole
from src.shared.utils.validation import InputValidator


class UserRegister(BaseModel):
    """User registration schema"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    
    @validator('email')
    def validate_email_security(cls, v):
        return InputValidator.validate_email(v)
    
    @validator('password')
    def validate_password_strength(cls, v):
        return InputValidator.validate_password(v)
    
    @validator('first_name')
    def validate_first_name_security(cls, v):
        return InputValidator.validate_name(v, "First name")
    
    @validator('last_name')
    def validate_last_name_security(cls, v):
        return InputValidator.validate_name(v, "Last name")
    
    @validator('phone')
    def validate_phone_security(cls, v):
        return InputValidator.validate_phone(v)


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str
    
    @validator('email')
    def validate_email_security(cls, v):
        return InputValidator.validate_email(v)


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


class EmailVerificationRequest(BaseModel):
    """Email verification request schema"""
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    """Email verification confirmation schema"""
    token: str


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request schema"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    """User response schema"""
    id: UUID
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    role: AuthRole
    is_active: bool
    email_verified: bool
    email_verified_at: Optional[datetime]
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_entity(cls, user) -> "UserResponse":
        """Create response from user entity"""
        return cls(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            role=user.role,
            is_active=user.is_active,
            email_verified=user.email_verified,
            email_verified_at=user.email_verified_at,
            last_login=user.last_login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    class Config:
        from_attributes = True


class UserUpdateProfile(BaseModel):
    """User profile update schema"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)


class UserRoleUpdate(BaseModel):
    """User role update schema"""
    role: AuthRole


class UserListResponse(BaseModel):
    """User list response schema"""
    users: List[UserResponse]
    total: int
    limit: int
    offset: int


class MessageResponse(BaseModel):
    """Generic message response schema"""
    message: str


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None


class AccountLockoutInfo(BaseModel):
    """Account lockout information schema"""
    is_locked: bool
    failed_attempts: int
    max_attempts: int
    locked_until: Optional[datetime]
    lockout_count: int
    last_failed_login: Optional[datetime]
    last_successful_login: Optional[datetime]


class AuthFeatureStatus(BaseModel):
    """Auth feature status schema"""
    email_verification: bool
    password_reset: bool
    account_lockout: bool
    token_rotation: bool
    rate_limiting: bool
    admin_setup: bool