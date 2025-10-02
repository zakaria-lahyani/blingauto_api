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
    use_case: CalculateQuoteUseCase = Depends(),
):
    """
    Calculate a price quote for selected services.

    This endpoint implements the pricing calculation rules defined in:
    - RG-BOK-001: Service selection constraints
    - RG-BOK-002: Duration constraints
    - RG-BOK-003: Price constraints
    """
    try:
        quote = await use_case.execute(
            service_ids=request.service_ids,
            apply_tax=request.apply_tax,
            apply_discounts=request.apply_discounts
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
    use_case: ValidateQuoteUseCase = Depends(),
):
    """
    Validate that a quote is still valid and get updated pricing if needed.

    Checks:
    - All services are still active
    - Pricing hasn't changed
    - Quote hasn't expired
    """
    try:
        result = await use_case.execute(quote_id=quote_id)

        return QuoteValidationSchema(
            quote_id=quote_id,
            is_valid=result["is_valid"],
            validation_errors=result.get("validation_errors", []),
            updated_quote=result.get("updated_quote")
        )

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


@router.get("/services", response_model=list)
async def list_available_services():
    """
    List all available services for pricing.

    Returns services that can be included in quotes.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Service listing endpoint requires proper dependency injection configuration"
    )