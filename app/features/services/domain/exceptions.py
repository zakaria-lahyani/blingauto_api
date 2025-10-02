"""
Pure Python domain exceptions for services feature.
No framework dependencies as per TO_REFACTORE_ARCHITECTURE.md line 116.
"""


class ServicesDomainError(Exception):
    """Base exception for services domain errors."""
    pass


class ValidationError(ServicesDomainError):
    """Validation error in services domain."""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


class BusinessRuleViolationError(ServicesDomainError):
    """Business rule violation in services domain."""

    def __init__(self, message: str, rule: str = None):
        self.message = message
        self.rule = rule
        super().__init__(message)