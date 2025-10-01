"""
Pure Python domain exceptions for vehicles feature.
No framework dependencies as per TO_REFACTORE_ARCHITECTURE.md line 116.
"""


class VehiclesDomainError(Exception):
    """Base exception for vehicles domain errors."""
    pass


class ValidationError(VehiclesDomainError):
    """Validation error in vehicles domain."""
    pass


class BusinessRuleViolationError(VehiclesDomainError):
    """Business rule violation in vehicles domain."""
    pass