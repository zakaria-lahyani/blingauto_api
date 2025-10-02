"""
Pricing adapters - Repository implementations.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.pricing.ports.repositories import IServiceCatalogRepository
from app.features.pricing.domain.entities import ServiceItem
from app.features.services.adapters import SqlServiceRepository


class ServiceCatalogAdapter(IServiceCatalogRepository):
    """
    Adapter that implements IServiceCatalogRepository using the services feature.

    This adapter delegates to the services feature's repository and converts
    Service domain objects to ServiceItem domain objects used by pricing.
    """

    def __init__(self, service_repository: SqlServiceRepository):
        self._service_repo = service_repository

    async def get_service_by_id(self, service_id: str) -> Optional[ServiceItem]:
        """Get service by ID."""
        service = await self._service_repo.get_by_id(service_id)

        if not service or not service.is_active:
            return None

        return ServiceItem(
            service_id=service.id,
            name=service.name,
            base_price=service.base_price,
            estimated_duration_minutes=service.duration_minutes,
            is_active=service.is_active
        )

    async def get_services_by_ids(self, service_ids: List[str]) -> List[ServiceItem]:
        """Get multiple services by IDs."""
        services = await self._service_repo.get_multiple_by_ids(service_ids)

        # Convert to ServiceItem and filter only active services
        return [
            ServiceItem(
                service_id=service.id,
                name=service.name,
                base_price=service.base_price,
                estimated_duration_minutes=service.duration_minutes,
                is_active=service.is_active
            )
            for service in services
            if service.is_active
        ]

    async def get_all_active_services(self) -> List[ServiceItem]:
        """Get all active services."""
        services = await self._service_repo.list_all(is_active=True)

        return [
            ServiceItem(
                service_id=service.id,
                name=service.name,
                base_price=service.base_price,
                estimated_duration_minutes=service.duration_minutes,
                is_active=service.is_active
            )
            for service in services
        ]

    async def is_service_active(self, service_id: str) -> bool:
        """Check if service is active."""
        service = await self._service_repo.get_by_id(service_id)
        return service is not None and service.is_active
