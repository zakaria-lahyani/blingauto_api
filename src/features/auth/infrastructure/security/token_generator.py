"""
Secure token generation utilities
"""
import secrets
import hashlib


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)


def hash_token(token: str, salt: str = "") -> str:
    """Hash a token for secure storage"""
    return hashlib.sha256((token + salt).encode()).hexdigest()


def generate_verification_token() -> str:
    """Generate email verification token"""
    return generate_secure_token(32)


def generate_reset_token() -> str:
    """Generate password reset token"""
    return generate_secure_token(32)