"""
Calculate Quote Use Case - RG-BOK-002, RG-BOK-003
Implements the core pricing calculation logic.
"""

from decimal import Decimal
from typing import List, Optional

from ..domain.entities import ServiceItem, PriceQuote
from ..domain.policies import PricingPolicy, QuotePolicy
from ..ports.repositories import IServiceCatalogRepository
from ..ports.services import ITaxCalculationService, IDiscountService
from app.core.errors import ValidationError, BusinessRuleViolationError


class CalculateQuoteUseCase:
    """Use case for calculating price quotes."""
    
    def __init__(
        self,
        service_catalog: IServiceCatalogRepository,
        tax_service: Optional[ITaxCalculationService] = None,
        discount_service: Optional[IDiscountService] = None
    ):
        self.service_catalog = service_catalog
        self.tax_service = tax_service
        self.discount_service = discount_service
    
    async def execute(
        self,
        service_ids: List[str],
        customer_id: Optional[str] = None,
        customer_location: Optional[str] = None,
        apply_tax: bool = True,
        apply_discounts: bool = True
    ) -> PriceQuote:
        """Calculate a price quote for the given services."""
        
        # Validate input
        if not service_ids:
            raise ValidationError("At least one service ID is required")
        
        if len(service_ids) > PriceQuote.MAX_SERVICES:
            raise ValidationError(f"Cannot quote more than {PriceQuote.MAX_SERVICES} services")
        
        # Remove duplicates while preserving order
        unique_service_ids = list(dict.fromkeys(service_ids))
        
        # Get service details from catalog
        services = await self.service_catalog.get_services_by_ids(unique_service_ids)
        
        # Check that all services were found
        found_service_ids = {service.service_id for service in services}
        missing_service_ids = set(unique_service_ids) - found_service_ids
        if missing_service_ids:
            raise ValidationError(f"Services not found: {', '.join(missing_service_ids)}")
        
        # Validate service combination
        if not PricingPolicy.validate_service_combination(services):
            raise BusinessRuleViolationError("Invalid service combination")
        
        # Calculate base totals
        subtotal = PricingPolicy.calculate_service_total(services)
        total_duration = PricingPolicy.calculate_duration_total(services)
        
        # Calculate discount if applicable
        discount_amount = Decimal('0')
        if apply_discounts and self.discount_service and customer_id:
            discount_amount = await self.discount_service.calculate_discount(
                customer_id=customer_id,
                service_ids=unique_service_ids,
                base_amount=subtotal
            )
        
        # Calculate tax if applicable
        tax_rate = Decimal('0')
        if apply_tax and self.tax_service:
            tax_rate = await self.tax_service.get_tax_rate(customer_location)
        
        # Create the quote
        quote = PriceQuote.create(
            services=services,
            tax_rate=tax_rate,
            discount_amount=discount_amount
        )
        
        return quote
    
    async def recalculate_quote(
        self,
        quote: PriceQuote,
        customer_id: Optional[str] = None,
        customer_location: Optional[str] = None
    ) -> PriceQuote:
        """Recalculate an existing quote with updated pricing."""
        
        if not QuotePolicy.can_modify_quote(quote):
            raise BusinessRuleViolationError("Quote cannot be modified")
        
        service_ids = [service.service_id for service in quote.services]
        
        return await self.execute(
            service_ids=service_ids,
            customer_id=customer_id,
            customer_location=customer_location
        )


class ValidateQuoteUseCase:
    """Use case for validating quotes."""
    
    def __init__(self, service_catalog: IServiceCatalogRepository):
        self.service_catalog = service_catalog
    
    async def execute(self, quote: PriceQuote) -> bool:
        """Validate that a quote is still valid."""
        
        try:
            # Check quote business rules
            if not QuotePolicy.is_quote_valid_for_booking(quote):
                return False
            
            # Verify all services are still active
            for service in quote.services:
                if not await self.service_catalog.is_service_active(service.service_id):
                    return False
            
            return True
            
        except Exception:
            return False