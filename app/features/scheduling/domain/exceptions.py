"""
Pure Python domain exceptions for scheduling feature.
No framework dependencies as per TO_REFACTORE_ARCHITECTURE.md line 116.
"""


class SchedulingDomainError(Exception):
    """Base exception for scheduling domain errors."""
    pass


class ValidationError(SchedulingDomainError):
    """Validation error in scheduling domain."""
    pass


class BusinessRuleViolationError(SchedulingDomainError):
    """Business rule violation in scheduling domain."""
    pass