"""
Auth domain enums
"""
from enum import Enum


class AuthRole(str, Enum):
    """User roles for the car wash system"""
    ADMIN = "admin"
    MANAGER = "manager" 
    WASHER = "washer"
    CLIENT = "client"


class TokenType(str, Enum):
    """Token types"""
    ACCESS = "access"
    REFRESH = "refresh"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"