from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    WASHER = "washer"
    CLIENT = "client"


class UserStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


# Request Schemas
class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    first_name: str = Field(..., min_length=1, max_length=100, description="User first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="User last name")
    phone_number: Optional[str] = Field(None, max_length=20, description="User phone number")
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip().title()
    
    @validator('phone_number')
    def validate_phone(cls, v):
        if v:
            # Basic phone validation
            import re
            cleaned = re.sub(r'[\s\-\(\)\.]', '', v)
            if not re.match(r'^\+?\d+$', cleaned):
                raise ValueError('Invalid phone number format')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890"
            }
        }


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "refresh_token_here"
            }
        }


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., description="Email verification token")

    class Config:
        json_schema_extra = {
            "example": {
                "token": "verification_token_here"
            }
        }


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")

    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset_token_here",
                "new_password": "newsecurepassword123"
            }
        }


class UpdateUserRoleRequest(BaseModel):
    role: UserRoleEnum = Field(..., description="New user role")

    class Config:
        json_schema_extra = {
            "example": {
                "role": "manager"
            }
        }


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")

    @validator('new_password')
    def validate_new_password(cls, v, values):
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('New password must be different from current password')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newsecurepassword123"
            }
        }


class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=2, max_length=100, description="User first name")
    last_name: Optional[str] = Field(None, min_length=2, max_length=100, description="User last name")
    phone_number: Optional[str] = Field(None, max_length=20, description="User phone number")

    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v is not None and v.strip():
            return v.strip().title()
        return v

    @validator('phone_number')
    def validate_phone(cls, v):
        if v:
            import re
            cleaned = re.sub(r'[\s\-\(\)\.]', '', v)
            if not re.match(r'^\+?\d{10,}$', cleaned):
                raise ValueError('Phone number must be at least 10 digits')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890"
            }
        }


# Response Schemas
class RegisterResponse(BaseModel):
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    full_name: str = Field(..., description="User full name")
    message: str = Field(..., description="Success message")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "12345",
                "email": "user@example.com",
                "full_name": "John Doe",
                "message": "Registration successful. Please check your email to verify your account."
            }
        }


class LoginResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    full_name: str = Field(..., description="User full name")
    role: str = Field(..., description="User role")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "refresh_token_here",
                "token_type": "bearer",
                "user_id": "12345",
                "email": "user@example.com",
                "full_name": "John Doe",
                "role": "client"
            }
        }


class RefreshTokenResponse(BaseModel):
    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New refresh token")
    token_type: str = Field(default="bearer", description="Token type")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "new_refresh_token_here",
                "token_type": "bearer"
            }
        }


class UserResponse(BaseModel):
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: str = Field(..., description="User first name")
    last_name: str = Field(..., description="User last name")
    full_name: str = Field(..., description="User full name")
    role: str = Field(..., description="User role")
    status: str = Field(..., description="User status")
    phone_number: Optional[str] = Field(None, description="User phone number")
    email_verified: bool = Field(..., description="Email verification status")
    created_at: str = Field(..., description="Creation timestamp")
    last_login_at: Optional[str] = Field(None, description="Last login timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "12345",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "role": "client",
                "status": "active",
                "phone_number": "+1234567890",
                "email_verified": True,
                "created_at": "2024-01-01T00:00:00Z",
                "last_login_at": "2024-01-01T12:00:00Z"
            }
        }


class UserListResponse(BaseModel):
    users: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    offset: int = Field(..., description="Offset for pagination")
    limit: int = Field(..., description="Limit for pagination")

    class Config:
        json_schema_extra = {
            "example": {
                "users": [
                    {
                        "id": "12345",
                        "email": "user@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "full_name": "John Doe",
                        "role": "client",
                        "status": "active",
                        "phone_number": "+1234567890",
                        "email_verified": True,
                        "created_at": "2024-01-01T00:00:00Z",
                        "last_login_at": "2024-01-01T12:00:00Z"
                    }
                ],
                "total": 1,
                "offset": 0,
                "limit": 20
            }
        }


class MessageResponse(BaseModel):
    message: str = Field(..., description="Response message")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully"
            }
        }


class ChangePasswordResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Success message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Password changed successfully. Please login again with your new password."
            }
        }


class UpdateProfileResponse(BaseModel):
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: str = Field(..., description="User first name")
    last_name: str = Field(..., description="User last name")
    phone_number: Optional[str] = Field(None, description="User phone number")
    updated_at: str = Field(..., description="Update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "12345",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890",
                "updated_at": "2024-01-01T12:00:00Z"
            }
        }


class LogoutResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Success message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully logged out from all devices"
            }
        }