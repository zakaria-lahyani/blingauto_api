"""
Pricing domain entities - RG-BOK-002, RG-BOK-003
Implements pricing calculation rules and quote generation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import uuid4

from .exceptions import ValidationError, BusinessRuleViolationError


@dataclass
class ServiceItem:
    """Individual service item in a quote - RG-BOK-001"""
    
    service_id: str
    service_name: str
    price: Decimal
    duration: int  # in minutes
    category: str
    
    def __post_init__(self):
        self._validate()
    
    def _validate(self):
        """Validate service item constraints."""
        if self.price < Decimal('0'):
            raise ValidationError("Service price cannot be negative")
        
        if self.duration <= 0:
            raise ValidationError("Service duration must be positive")
        
        if not self.service_name.strip():
            raise ValidationError("Service name cannot be empty")


@dataclass
class PriceQuote:
    """Price quote for a set of services - RG-BOK-002, RG-BOK-003"""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    services: List[ServiceItem] = field(default_factory=list)
    subtotal: Decimal = field(default=Decimal('0'))
    tax_amount: Decimal = field(default=Decimal('0'))
    tax_rate: Decimal = field(default=Decimal('0'))
    discount_amount: Decimal = field(default=Decimal('0'))
    total_price: Decimal = field(default=Decimal('0'))
    total_duration: int = field(default=0)  # in minutes
    created_at: datetime = field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None
    
    # Business rule constants from checklist
    MIN_TOTAL_DURATION = 30  # RG-BOK-002
    MAX_TOTAL_DURATION = 240  # RG-BOK-002
    MAX_TOTAL_PRICE = Decimal('10000.00')  # RG-BOK-003
    MAX_SERVICES = 10  # RG-BOK-001
    
    def __post_init__(self):
        self._calculate_totals()
        self._validate()
    
    @classmethod
    def create(
        cls,
        services: List[ServiceItem],
        tax_rate: Decimal = Decimal('0'),
        discount_amount: Decimal = Decimal('0')
    ) -> "PriceQuote":
        """Create a new price quote with validation."""
        quote = cls(
            services=services,
            tax_rate=tax_rate,
            discount_amount=discount_amount
        )
        return quote
    
    def add_service(self, service: ServiceItem) -> None:
        """Add a service to the quote - RG-BOK-013"""
        if len(self.services) >= self.MAX_SERVICES:
            raise BusinessRuleViolationError(f"Cannot add more than {self.MAX_SERVICES} services")
        
        # Check for duplicate services
        existing_service_ids = {s.service_id for s in self.services}
        if service.service_id in existing_service_ids:
            raise BusinessRuleViolationError("Duplicate services are not allowed")
        
        self.services.append(service)
        self._calculate_totals()
        self._validate()
    
    def remove_service(self, service_id: str) -> None:
        """Remove a service from the quote - RG-BOK-014"""
        if len(self.services) <= 1:
            raise BusinessRuleViolationError("At least one service must remain")
        
        self.services = [s for s in self.services if s.service_id != service_id]
        self._calculate_totals()
        self._validate()
    
    def apply_discount(self, discount_amount: Decimal) -> None:
        """Apply a discount to the quote."""
        if discount_amount < Decimal('0'):
            raise ValidationError("Discount amount cannot be negative")
        
        if discount_amount > self.subtotal:
            raise ValidationError("Discount cannot exceed subtotal")
        
        self.discount_amount = discount_amount
        self._calculate_totals()
    
    def _calculate_totals(self) -> None:
        """Calculate all totals for the quote."""
        # Calculate subtotal and duration
        self.subtotal = sum(service.price for service in self.services)
        self.total_duration = sum(service.duration for service in self.services)
        
        # Apply discount
        discounted_subtotal = self.subtotal - self.discount_amount
        
        # Calculate tax
        self.tax_amount = discounted_subtotal * self.tax_rate
        
        # Calculate final total
        self.total_price = discounted_subtotal + self.tax_amount
    
    def _validate(self) -> None:
        """Validate quote constraints."""
        # RG-BOK-001: Service count constraints
        if len(self.services) == 0:
            raise BusinessRuleViolationError("At least one service is required")
        
        if len(self.services) > self.MAX_SERVICES:
            raise BusinessRuleViolationError(f"Cannot have more than {self.MAX_SERVICES} services")
        
        # RG-BOK-002: Duration constraints
        if self.total_duration < self.MIN_TOTAL_DURATION:
            raise BusinessRuleViolationError(
                f"Total duration must be at least {self.MIN_TOTAL_DURATION} minutes"
            )
        
        if self.total_duration > self.MAX_TOTAL_DURATION:
            raise BusinessRuleViolationError(
                f"Total duration cannot exceed {self.MAX_TOTAL_DURATION} minutes"
            )
        
        # RG-BOK-003: Price constraints
        if self.total_price > self.MAX_TOTAL_PRICE:
            raise BusinessRuleViolationError(
                f"Total price cannot exceed {self.MAX_TOTAL_PRICE}"
            )
        
        if self.total_price < Decimal('0'):
            raise BusinessRuleViolationError("Total price cannot be negative")
    
    def get_price_breakdown(self) -> Dict[str, Any]:
        """Get detailed price breakdown."""
        return {
            "services": [
                {
                    "service_id": service.service_id,
                    "service_name": service.service_name,
                    "price": str(service.price),
                    "duration": service.duration,
                    "category": service.category
                }
                for service in self.services
            ],
            "subtotal": str(self.subtotal),
            "discount_amount": str(self.discount_amount),
            "taxable_amount": str(self.subtotal - self.discount_amount),
            "tax_rate": str(self.tax_rate),
            "tax_amount": str(self.tax_amount),
            "total_price": str(self.total_price),
            "total_duration": self.total_duration,
            "service_count": len(self.services)
        }