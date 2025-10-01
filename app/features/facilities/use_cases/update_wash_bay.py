"""
Update Wash Bay Use Case

Updates existing wash bay configuration.
Manager and Admin roles can update wash bays.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from ..domain.entities import WashBay, VehicleSize, ResourceStatus, Location
from ..ports.repositories import IWashBayRepository
from app.core.errors import NotFoundError, ValidationError


@dataclass
class UpdateWashBayRequest:
    """Request DTO for updating a wash bay."""
    wash_bay_id: str
    bay_number: Optional[str] = None
    max_vehicle_size: Optional[VehicleSize] = None
    equipment_types: Optional[List[str]] = None
    status: Optional[ResourceStatus] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


@dataclass
class UpdateWashBayResponse:
    """Response DTO for wash bay update."""
    id: str
    bay_number: str
    max_vehicle_size: str
    equipment_types: List[str]
    status: str
    location: Optional[dict]
    updated_at: str


class UpdateWashBayUseCase:
    """
    Use case for updating a wash bay.

    Business Rules:
    - RG-FAC-001: Bay number must remain unique if changed
    - RG-FAC-001: Can update equipment types
    - RG-FAC-001: Can change status for maintenance
    - RG-FAC-002: Can update max vehicle size
    """

    def __init__(self, wash_bay_repository: IWashBayRepository):
        """
        Initialize use case with dependencies.

        Args:
            wash_bay_repository: Repository for wash bay persistence
        """
        self._repository = wash_bay_repository

    async def execute(self, request: UpdateWashBayRequest) -> UpdateWashBayResponse:
        """
        Execute wash bay update.

        Args:
            request: Update wash bay request data

        Returns:
            UpdateWashBayResponse with updated wash bay data

        Raises:
            NotFoundError: If wash bay doesn't exist
            ValidationError: If update data is invalid
        """
        # Retrieve existing wash bay
        wash_bay = await self._repository.get_by_id(request.wash_bay_id)
        if not wash_bay:
            raise NotFoundError(
                message=f"Wash bay with ID '{request.wash_bay_id}' not found",
                code="WASH_BAY_NOT_FOUND"
            )

        # Update bay number if provided and different
        if request.bay_number and request.bay_number != wash_bay.bay_number:
            # Check uniqueness - RG-FAC-001
            existing_bay = await self._repository.get_by_bay_number(request.bay_number)
            if existing_bay and existing_bay.id != wash_bay.id:
                raise ValidationError(
                    message=f"Wash bay with number '{request.bay_number}' already exists",
                    code="BAY_NUMBER_EXISTS"
                )
            wash_bay.bay_number = request.bay_number

        # Update max vehicle size if provided - RG-FAC-002
        if request.max_vehicle_size:
            wash_bay.max_vehicle_size = request.max_vehicle_size

        # Update equipment types if provided - RG-FAC-001
        if request.equipment_types is not None:
            wash_bay.update_equipment(request.equipment_types)

        # Update status if provided - RG-FAC-001
        if request.status:
            if request.status == ResourceStatus.ACTIVE:
                wash_bay.activate()
            elif request.status in (ResourceStatus.MAINTENANCE, ResourceStatus.INACTIVE):
                wash_bay.deactivate()

        # Update location if coordinates provided
        if request.latitude is not None and request.longitude is not None:
            try:
                wash_bay.location = Location(
                    latitude=request.latitude,
                    longitude=request.longitude
                )
            except ValidationError as e:
                raise ValidationError(
                    message=f"Invalid location coordinates: {str(e)}",
                    code="INVALID_LOCATION"
                )

        # Persist updates
        updated_bay = await self._repository.update(wash_bay)

        # Build response
        location_dict = None
        if updated_bay.location:
            location_dict = {
                "latitude": str(updated_bay.location.latitude),
                "longitude": str(updated_bay.location.longitude)
            }

        return UpdateWashBayResponse(
            id=updated_bay.id,
            bay_number=updated_bay.bay_number,
            max_vehicle_size=updated_bay.max_vehicle_size.value,
            equipment_types=updated_bay.equipment_types,
            status=updated_bay.status.value,
            location=location_dict,
            updated_at=updated_bay.updated_at.isoformat()
        )
