"""
Pricing domain policies and business rules.
"""

from decimal import Decimal
from typing import List

from .entities import ServiceItem, PriceQuote


class PricingPolicy:
    """Pricing policy implementation."""
    
    @staticmethod
    def calculate_service_total(services: List[ServiceItem]) -> Decimal:
        """Calculate total price for a list of services."""
        return sum(service.price for service in services)
    
    @staticmethod
    def calculate_duration_total(services: List[ServiceItem]) -> int:
        """Calculate total duration for a list of services."""
        return sum(service.duration for service in services)
    
    @staticmethod
    def validate_service_combination(services: List[ServiceItem]) -> bool:
        """Validate that service combination is allowed."""
        # Check for duplicate services
        service_ids = [service.service_id for service in services]
        if len(service_ids) != len(set(service_ids)):
            return False
        
        # Check service count limits
        if len(services) < 1 or len(services) > PriceQuote.MAX_SERVICES:
            return False
        
        return True
    
    @staticmethod
    def calculate_tax(amount: Decimal, tax_rate: Decimal) -> Decimal:
        """Calculate tax amount."""
        if tax_rate < Decimal('0') or tax_rate > Decimal('1'):
            raise ValueError("Tax rate must be between 0 and 1")
        
        return amount * tax_rate
    
    @staticmethod
    def validate_discount(discount: Decimal, subtotal: Decimal) -> bool:
        """Validate discount amount."""
        return Decimal('0') <= discount <= subtotal


class QuotePolicy:
    """Quote-specific business policies."""
    
    @staticmethod
    def is_quote_valid_for_booking(quote: PriceQuote) -> bool:
        """Check if quote meets all requirements for booking creation."""
        try:
            # This will validate all constraints
            quote._validate()
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_quote_validity_period_hours() -> int:
        """Get how long quotes remain valid."""
        return 24  # Quotes valid for 24 hours
    
    @staticmethod
    def can_modify_quote(quote: PriceQuote) -> bool:
        """Check if quote can still be modified."""
        # For now, all quotes can be modified
        # In future, might add time-based restrictions
        return True