"""
Pure Python domain exceptions for auth feature.
No framework dependencies as per TO_REFACTORE_ARCHITECTURE.md line 116.
"""


class AuthDomainError(Exception):
    """Base exception for auth domain errors."""
    pass


class ValidationError(AuthDomainError):
    """Validation error in auth domain."""
    pass


class BusinessRuleViolationError(AuthDomainError):
    """Business rule violation in auth domain."""
    pass


class AuthenticationError(AuthDomainError):
    """Authentication failed."""
    pass


class UserInactiveError(AuthDomainError):
    """User account is inactive."""
    pass


class InsufficientPermissionError(AuthDomainError):
    """User lacks required permissions."""
    pass