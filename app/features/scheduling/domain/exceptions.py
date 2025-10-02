"""
Pure Python domain exceptions for scheduling feature.
No framework dependencies as per TO_REFACTORE_ARCHITECTURE.md line 116.
"""


class SchedulingDomainError(Exception):
    """Base exception for scheduling domain errors."""
    pass


class ValidationError(SchedulingDomainError):
    """Validation error in scheduling domain."""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


class BusinessRuleViolationError(SchedulingDomainError):
    """Business rule violation in scheduling domain."""

    def __init__(self, message: str, rule: str = None):
        self.message = message
        self.rule = rule
        super().__init__(message)