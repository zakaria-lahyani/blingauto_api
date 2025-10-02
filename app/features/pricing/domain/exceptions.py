"""
Pure Python domain exceptions for pricing feature.
No framework dependencies as per TO_REFACTORE_ARCHITECTURE.md line 116.
"""


class PricingDomainError(Exception):
    """Base exception for pricing domain errors."""
    pass


class ValidationError(PricingDomainError):
    """Validation error in pricing domain."""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


class BusinessRuleViolationError(PricingDomainError):
    """Business rule violation in pricing domain."""

    def __init__(self, message: str, rule: str = None):
        self.message = message
        self.rule = rule
        super().__init__(message)