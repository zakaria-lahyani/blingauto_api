"""
List Wash Bays Use Case

Retrieves all wash bays with optional filtering.
Available to Manager, Admin, and Washer roles.
"""

from dataclasses import dataclass
from typing import List, Optional

from ..domain.entities import ResourceStatus
from ..ports.repositories import IWashBayRepository


@dataclass
class ListWashBaysRequest:
    """Request DTO for listing wash bays."""
    status: Optional[ResourceStatus] = None
    include_inactive: bool = False


@dataclass
class WashBayDTO:
    """Data transfer object for wash bay information."""
    id: str
    bay_number: str
    max_vehicle_size: str
    equipment_types: List[str]
    status: str
    location: Optional[dict]
    created_at: str
    updated_at: str


@dataclass
class ListWashBaysResponse:
    """Response DTO for listing wash bays."""
    wash_bays: List[WashBayDTO]
    total_count: int
    active_count: int
    inactive_count: int
    maintenance_count: int


class ListWashBaysUseCase:
    """
    Use case for listing wash bays.

    Business Rules:
    - RG-FAC-001: List all configured wash bays
    - Filtering by status available
    - Can exclude inactive bays
    """

    def __init__(self, wash_bay_repository: IWashBayRepository):
        """
        Initialize use case with dependencies.

        Args:
            wash_bay_repository: Repository for wash bay data
        """
        self._repository = wash_bay_repository

    async def execute(self, request: ListWashBaysRequest) -> ListWashBaysResponse:
        """
        Execute wash bay listing.

        Args:
            request: List wash bays request with filters

        Returns:
            ListWashBaysResponse with wash bay data and counts
        """
        # Retrieve wash bays from repository
        wash_bays = await self._repository.list_all(
            status=request.status,
            include_inactive=request.include_inactive
        )

        # Get counts by status for dashboard
        active_count = await self._repository.count_by_status(ResourceStatus.ACTIVE)
        inactive_count = await self._repository.count_by_status(ResourceStatus.INACTIVE)
        maintenance_count = await self._repository.count_by_status(ResourceStatus.MAINTENANCE)

        # Convert to DTOs
        wash_bay_dtos = []
        for bay in wash_bays:
            location_dict = None
            if bay.location:
                location_dict = {
                    "latitude": str(bay.location.latitude),
                    "longitude": str(bay.location.longitude)
                }

            wash_bay_dtos.append(WashBayDTO(
                id=bay.id,
                bay_number=bay.bay_number,
                max_vehicle_size=bay.max_vehicle_size.value,
                equipment_types=bay.equipment_types,
                status=bay.status.value,
                location=location_dict,
                created_at=bay.created_at.isoformat(),
                updated_at=bay.updated_at.isoformat()
            ))

        return ListWashBaysResponse(
            wash_bays=wash_bay_dtos,
            total_count=len(wash_bay_dtos),
            active_count=active_count,
            inactive_count=inactive_count,
            maintenance_count=maintenance_count
        )
