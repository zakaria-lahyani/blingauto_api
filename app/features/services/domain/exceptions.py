"""
Pure Python domain exceptions for services feature.
No framework dependencies as per TO_REFACTORE_ARCHITECTURE.md line 116.
"""


class ServicesDomainError(Exception):
    """Base exception for services domain errors."""
    pass


class ValidationError(ServicesDomainError):
    """Validation error in services domain."""
    pass


class BusinessRuleViolationError(ServicesDomainError):
    """Business rule violation in services domain."""
    pass