"""Get service name for analytics - Public use case."""

from dataclasses import dataclass
from typing import Optional

from app.features.services.ports.repositories import IServiceRepository


@dataclass
class GetServiceNameRequest:
    """Request for service name."""

    service_id: str


class GetServiceNameUseCase:
    """Public use case for analytics to get service name."""

    def __init__(self, service_repository: IServiceRepository):
        self._repository = service_repository

    async def execute(self, request: GetServiceNameRequest) -> Optional[str]:
        """Get service name by ID."""
        service = await self._repository.get_by_id(request.service_id)
        return service.name if service else None
