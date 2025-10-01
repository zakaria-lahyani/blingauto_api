"""
Pure Python domain exceptions for pricing feature.
No framework dependencies as per TO_REFACTORE_ARCHITECTURE.md line 116.
"""


class PricingDomainError(Exception):
    """Base exception for pricing domain errors."""
    pass


class ValidationError(PricingDomainError):
    """Validation error in pricing domain."""
    pass


class BusinessRuleViolationError(PricingDomainError):
    """Business rule violation in pricing domain."""
    pass