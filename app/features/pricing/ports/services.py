"""
Pricing ports for external services.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any


class ITaxCalculationService(ABC):
    """Port for tax calculation service."""
    
    @abstractmethod
    async def calculate_tax(
        self, 
        amount: Decimal, 
        customer_location: str = None
    ) -> Decimal:
        """Calculate tax for given amount and location."""
        pass
    
    @abstractmethod
    async def get_tax_rate(self, location: str = None) -> Decimal:
        """Get tax rate for location."""
        pass


class IDiscountService(ABC):
    """Port for discount calculation service."""
    
    @abstractmethod
    async def calculate_discount(
        self,
        customer_id: str,
        service_ids: list[str],
        base_amount: Decimal
    ) -> Decimal:
        """Calculate available discount for customer and services."""
        pass
    
    @abstractmethod
    async def get_available_promotions(
        self,
        customer_id: str,
        service_ids: list[str]
    ) -> list[Dict[str, Any]]:
        """Get available promotions for customer."""
        pass