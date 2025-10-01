"""
Pricing API router.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from .schemas import QuoteRequestSchema, QuoteResponseSchema, QuoteValidationSchema
from ..use_cases.calculate_quote import CalculateQuoteUseCase, ValidateQuoteUseCase
from app.core.errors import ValidationError, BusinessRuleViolationError

router = APIRouter()


@router.post("/quote", response_model=QuoteResponseSchema)
async def calculate_quote(
    request: QuoteRequestSchema,
    # TODO: Add proper authentication when available
    # current_user = Depends(get_current_user),
    # TODO: Add proper dependency injection when repositories are implemented
    # use_case: CalculateQuoteUseCase = Depends()
):
    """
    Calculate a price quote for selected services.
    
    This endpoint implements the pricing calculation rules defined in:
    - RG-BOK-001: Service selection constraints
    - RG-BOK-002: Duration constraints  
    - RG-BOK-003: Price constraints
    """
    try:
        # Mock implementation for now
        # In real implementation, this would use proper use case with repositories
        
        from ..domain.entities import ServiceItem, PriceQuote
        from decimal import Decimal
        
        # Mock services data - normally would come from repository
        mock_services = []
        for i, service_id in enumerate(request.service_ids):
            mock_service = ServiceItem(
                service_id=service_id,
                service_name=f"Service {i+1}",
                price=Decimal('25.00'),
                duration=45,
                category="Basic Wash"
            )
            mock_services.append(mock_service)
        
        # Create quote with mock data
        quote = PriceQuote.create(
            services=mock_services,
            tax_rate=Decimal('0.08') if request.apply_tax else Decimal('0'),
            discount_amount=Decimal('5.00') if request.apply_discounts else Decimal('0')
        )
        
        return QuoteResponseSchema.from_quote(quote)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/quote/{quote_id}/validate", response_model=QuoteValidationSchema)
async def validate_quote(
    quote_id: str,
    # TODO: Add proper authentication when available
    # current_user = Depends(get_current_user),
):
    """
    Validate that a quote is still valid and get updated pricing if needed.
    
    Checks:
    - All services are still active
    - Pricing hasn't changed
    - Quote hasn't expired
    """
    try:
        # Mock implementation for now
        return QuoteValidationSchema(
            quote_id=quote_id,
            is_valid=True,
            validation_errors=[],
            updated_quote=None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/services", response_model=list)
async def list_available_services():
    """
    List all available services for pricing.
    
    Returns services that can be included in quotes.
    """
    # Mock implementation for now
    mock_services = [
        {
            "service_id": "basic-wash",
            "service_name": "Basic Wash",
            "price": "25.00",
            "duration": 45,
            "category": "Basic Wash",
            "description": "Exterior wash and dry"
        },
        {
            "service_id": "premium-wash",
            "service_name": "Premium Wash",
            "price": "45.00", 
            "duration": 75,
            "category": "Premium Wash",
            "description": "Exterior wash, interior vacuum, and wax"
        },
        {
            "service_id": "detail-service",
            "service_name": "Detail Service",
            "price": "85.00",
            "duration": 120,
            "category": "Detailing",
            "description": "Complete interior and exterior detailing"
        }
    ]
    
    return mock_services