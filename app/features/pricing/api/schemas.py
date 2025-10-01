"""
Pricing API schemas for request/response validation.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

from ..domain.entities import PriceQuote, ServiceItem


class ServiceItemSchema(BaseModel):
    """Schema for service item in quotes."""
    service_id: str = Field(..., description="Service ID")
    service_name: str = Field(..., description="Service name")
    price: Decimal = Field(..., ge=0, description="Service price")
    duration: int = Field(..., gt=0, description="Duration in minutes")
    category: str = Field(..., description="Service category")
    
    class Config:
        from_attributes = True


class QuoteRequestSchema(BaseModel):
    """Schema for quote calculation request."""
    service_ids: List[str] = Field(
        ..., 
        min_items=1, 
        max_items=10,
        description="List of service IDs to quote"
    )
    customer_location: Optional[str] = Field(
        None, 
        description="Customer location for tax calculation"
    )
    apply_tax: bool = Field(
        default=True, 
        description="Whether to apply tax calculation"
    )
    apply_discounts: bool = Field(
        default=True, 
        description="Whether to apply available discounts"
    )
    
    @validator('service_ids')
    def validate_service_ids(cls, v):
        """Validate service IDs are not empty and remove duplicates."""
        if not v:
            raise ValueError("At least one service ID is required")
        
        # Remove duplicates while preserving order
        unique_ids = list(dict.fromkeys(v))
        
        if len(unique_ids) > 10:
            raise ValueError("Cannot quote more than 10 services")
        
        return unique_ids


class PriceBreakdownSchema(BaseModel):
    """Schema for detailed price breakdown."""
    services: List[ServiceItemSchema] = Field(..., description="Service items")
    subtotal: Decimal = Field(..., description="Subtotal before tax and discount")
    discount_amount: Decimal = Field(..., description="Discount amount")
    taxable_amount: Decimal = Field(..., description="Amount subject to tax")
    tax_rate: Decimal = Field(..., description="Tax rate applied")
    tax_amount: Decimal = Field(..., description="Tax amount")
    total_price: Decimal = Field(..., description="Final total price")
    total_duration: int = Field(..., description="Total duration in minutes")
    service_count: int = Field(..., description="Number of services")


class QuoteResponseSchema(BaseModel):
    """Schema for quote calculation response."""
    quote_id: str = Field(..., description="Quote ID")
    total_price: Decimal = Field(..., description="Total price")
    total_duration: int = Field(..., description="Total duration in minutes")
    service_count: int = Field(..., description="Number of services")
    created_at: datetime = Field(..., description="Quote creation time")
    valid_until: Optional[datetime] = Field(None, description="Quote expiry time")
    breakdown: PriceBreakdownSchema = Field(..., description="Detailed breakdown")
    
    @classmethod
    def from_quote(cls, quote: PriceQuote) -> "QuoteResponseSchema":
        """Create response schema from quote entity."""
        breakdown_data = quote.get_price_breakdown()
        
        services = [
            ServiceItemSchema(
                service_id=service["service_id"],
                service_name=service["service_name"],
                price=Decimal(service["price"]),
                duration=service["duration"],
                category=service["category"]
            )
            for service in breakdown_data["services"]
        ]
        
        breakdown = PriceBreakdownSchema(
            services=services,
            subtotal=Decimal(breakdown_data["subtotal"]),
            discount_amount=Decimal(breakdown_data["discount_amount"]),
            taxable_amount=Decimal(breakdown_data["taxable_amount"]),
            tax_rate=Decimal(breakdown_data["tax_rate"]),
            tax_amount=Decimal(breakdown_data["tax_amount"]),
            total_price=Decimal(breakdown_data["total_price"]),
            total_duration=breakdown_data["total_duration"],
            service_count=breakdown_data["service_count"]
        )
        
        return cls(
            quote_id=quote.id,
            total_price=quote.total_price,
            total_duration=quote.total_duration,
            service_count=len(quote.services),
            created_at=quote.created_at,
            valid_until=quote.valid_until,
            breakdown=breakdown
        )


class QuoteValidationSchema(BaseModel):
    """Schema for quote validation response."""
    quote_id: str = Field(..., description="Quote ID")
    is_valid: bool = Field(..., description="Whether quote is valid")
    validation_errors: List[str] = Field(
        default_factory=list,
        description="List of validation errors if any"
    )
    updated_quote: Optional[QuoteResponseSchema] = Field(
        None,
        description="Updated quote if recalculation was needed"
    )