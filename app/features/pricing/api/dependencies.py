"""Pricing API dependencies."""

from typing import Annotated
from fastapi import Depends

from app.features.services.api.dependencies import get_service_repository
from app.features.services.adapters import SqlServiceRepository
from app.features.pricing.adapters import ServiceCatalogAdapter
from app.features.pricing.use_cases.calculate_quote import (
    CalculateQuoteUseCase,
    ValidateQuoteUseCase,
)


def get_service_catalog(
    service_repo: Annotated[SqlServiceRepository, Depends(get_service_repository)],
) -> ServiceCatalogAdapter:
    """Get service catalog adapter."""
    return ServiceCatalogAdapter(service_repository=service_repo)


def get_calculate_quote_use_case(
    service_catalog: Annotated[ServiceCatalogAdapter, Depends(get_service_catalog)],
) -> CalculateQuoteUseCase:
    """Get calculate quote use case."""
    # For now, tax and discount services are optional (None)
    # TODO: Implement tax and discount service adapters when needed
    return CalculateQuoteUseCase(
        service_catalog=service_catalog,
        tax_service=None,
        discount_service=None,
    )


def get_validate_quote_use_case(
    service_catalog: Annotated[ServiceCatalogAdapter, Depends(get_service_catalog)],
) -> ValidateQuoteUseCase:
    """Get validate quote use case."""
    return ValidateQuoteUseCase(service_catalog=service_catalog)
