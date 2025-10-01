"""
Create Wash Bay Use Case

Implements RG-FAC-001: Wash bay configuration management.
Manager and Admin roles can create new wash bays.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from ..domain.entities import WashBay, VehicleSize, Location
from ..ports.repositories import IWashBayRepository
from app.core.errors import ValidationError, BusinessRuleViolationError


@dataclass
class CreateWashBayRequest:
    """Request DTO for creating a wash bay."""
    bay_number: str
    max_vehicle_size: VehicleSize
    equipment_types: List[str]
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


@dataclass
class CreateWashBayResponse:
    """Response DTO for wash bay creation."""
    id: str
    bay_number: str
    max_vehicle_size: str
    equipment_types: List[str]
    status: str
    created_at: str
    location: Optional[dict] = None


class CreateWashBayUseCase:
    """
    Use case for creating a new wash bay.

    Business Rules:
    - RG-FAC-001: Bay number must be unique
    - RG-FAC-001: Max vehicle size must be specified
    - RG-FAC-001: Equipment types can be specified
    - RG-FAC-001: Initial status is ACTIVE
    """

    def __init__(self, wash_bay_repository: IWashBayRepository):
        """
        Initialize use case with dependencies.

        Args:
            wash_bay_repository: Repository for wash bay persistence
        """
        self._repository = wash_bay_repository

    async def execute(self, request: CreateWashBayRequest) -> CreateWashBayResponse:
        """
        Execute wash bay creation.

        Args:
            request: Create wash bay request data

        Returns:
            CreateWashBayResponse with created wash bay data

        Raises:
            ValidationError: If input data is invalid
            BusinessRuleViolationError: If bay number already exists
        """
        # Validate bay number uniqueness - RG-FAC-001
        existing_bay = await self._repository.get_by_bay_number(request.bay_number)
        if existing_bay:
            raise BusinessRuleViolationError(
                message=f"Wash bay with number '{request.bay_number}' already exists",
                code="BAY_NUMBER_EXISTS"
            )

        # Create location if coordinates provided
        location = None
        if request.latitude is not None and request.longitude is not None:
            try:
                location = Location(
                    latitude=request.latitude,
                    longitude=request.longitude
                )
            except ValidationError as e:
                raise ValidationError(
                    message=f"Invalid location coordinates: {str(e)}",
                    code="INVALID_LOCATION"
                )

        # Create wash bay entity - RG-FAC-001
        wash_bay = WashBay.create(
            bay_number=request.bay_number,
            max_vehicle_size=request.max_vehicle_size,
            equipment_types=request.equipment_types,
            location=location
        )

        # Persist wash bay
        created_bay = await self._repository.create(wash_bay)

        # Build response
        location_dict = None
        if created_bay.location:
            location_dict = {
                "latitude": str(created_bay.location.latitude),
                "longitude": str(created_bay.location.longitude)
            }

        return CreateWashBayResponse(
            id=created_bay.id,
            bay_number=created_bay.bay_number,
            max_vehicle_size=created_bay.max_vehicle_size.value,
            equipment_types=created_bay.equipment_types,
            status=created_bay.status.value,
            location=location_dict,
            created_at=created_bay.created_at.isoformat()
        )
