"""
Pure Python domain exceptions for vehicles feature.
No framework dependencies as per TO_REFACTORE_ARCHITECTURE.md line 116.
"""


class VehiclesDomainError(Exception):
    """Base exception for vehicles domain errors."""
    pass


class ValidationError(VehiclesDomainError):
    """Validation error in vehicles domain."""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


class BusinessRuleViolationError(VehiclesDomainError):
    """Business rule violation in vehicles domain."""

    def __init__(self, message: str, rule: str = None):
        self.message = message
        self.rule = rule
        super().__init__(message)