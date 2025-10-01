"""
Pure Python domain exceptions for bookings feature.
No framework dependencies as per TO_REFACTORE_ARCHITECTURE.md line 116.
"""


class BookingsDomainError(Exception):
    """Base exception for bookings domain errors."""
    pass


class ValidationError(BookingsDomainError):
    """Validation error in bookings domain."""
    pass


class BusinessRuleViolationError(BookingsDomainError):
    """Business rule violation in bookings domain."""
    pass