"""
Pure Python domain exceptions for auth feature.
No framework dependencies as per TO_REFACTORE_ARCHITECTURE.md line 116.
"""


class AuthDomainError(Exception):
    """Base exception for auth domain errors."""
    pass


class ValidationError(AuthDomainError):
    """Validation error in auth domain."""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


class BusinessRuleViolationError(AuthDomainError):
    """Business rule violation in auth domain."""

    def __init__(self, message: str, rule: str = None):
        self.message = message
        self.rule = rule
        super().__init__(message)


class AuthenticationError(AuthDomainError):
    """Authentication failed."""
    pass


class UserInactiveError(AuthDomainError):
    """User account is inactive."""
    pass


class InsufficientPermissionError(AuthDomainError):
    """User lacks required permissions."""
    pass