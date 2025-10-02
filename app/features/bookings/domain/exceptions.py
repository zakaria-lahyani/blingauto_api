"""
Pure Python domain exceptions for bookings feature.
No framework dependencies as per TO_REFACTORE_ARCHITECTURE.md line 116.
"""


class BookingsDomainError(Exception):
    """Base exception for bookings domain errors."""
    pass


class ValidationError(BookingsDomainError):
    """Validation error in bookings domain."""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


class BusinessRuleViolationError(BookingsDomainError):
    """Business rule violation in bookings domain."""

    def __init__(self, message: str, rule: str = None):
        self.message = message
        self.rule = rule
        super().__init__(message)