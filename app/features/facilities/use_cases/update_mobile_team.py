"""
Update Mobile Team Use Case

Updates existing mobile team configuration.
Manager and Admin roles can update mobile teams.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from ..domain.entities import MobileTeam, ResourceStatus, Location
from ..ports.repositories import IMobileTeamRepository
from app.core.errors import NotFoundError, ValidationError


@dataclass
class UpdateMobileTeamRequest:
    """Request DTO for updating a mobile team."""
    team_id: str
    team_name: Optional[str] = None
    base_latitude: Optional[Decimal] = None
    base_longitude: Optional[Decimal] = None
    service_radius_km: Optional[Decimal] = None
    daily_capacity: Optional[int] = None
    equipment_types: Optional[List[str]] = None
    status: Optional[ResourceStatus] = None


@dataclass
class UpdateMobileTeamResponse:
    """Response DTO for mobile team update."""
    id: str
    team_name: str
    base_location: dict
    service_radius_km: str
    daily_capacity: int
    equipment_types: List[str]
    status: str
    updated_at: str


class UpdateMobileTeamUseCase:
    """
    Use case for updating a mobile team.

    Business Rules:
    - RG-FAC-003: Team name must remain unique if changed
    - RG-FAC-003: Can update service radius
    - RG-FAC-003: Can update daily capacity
    - RG-FAC-004: Can update base location
    """

    def __init__(self, mobile_team_repository: IMobileTeamRepository):
        """
        Initialize use case with dependencies.

        Args:
            mobile_team_repository: Repository for mobile team persistence
        """
        self._repository = mobile_team_repository

    async def execute(self, request: UpdateMobileTeamRequest) -> UpdateMobileTeamResponse:
        """
        Execute mobile team update.

        Args:
            request: Update mobile team request data

        Returns:
            UpdateMobileTeamResponse with updated mobile team data

        Raises:
            NotFoundError: If mobile team doesn't exist
            ValidationError: If update data is invalid
        """
        # Retrieve existing mobile team
        mobile_team = await self._repository.get_by_id(request.team_id)
        if not mobile_team:
            raise NotFoundError(
                message=f"Mobile team with ID '{request.team_id}' not found",
                code="MOBILE_TEAM_NOT_FOUND"
            )

        # Update team name if provided and different - RG-FAC-003
        if request.team_name and request.team_name != mobile_team.team_name:
            existing_team = await self._repository.get_by_name(request.team_name)
            if existing_team and existing_team.id != mobile_team.id:
                raise ValidationError(
                    message=f"Mobile team with name '{request.team_name}' already exists",
                    code="TEAM_NAME_EXISTS"
                )
            mobile_team.team_name = request.team_name

        # Update base location if provided - RG-FAC-004
        if request.base_latitude is not None and request.base_longitude is not None:
            try:
                mobile_team.base_location = Location(
                    latitude=request.base_latitude,
                    longitude=request.base_longitude
                )
            except ValidationError as e:
                raise ValidationError(
                    message=f"Invalid base location coordinates: {str(e)}",
                    code="INVALID_LOCATION"
                )

        # Update service radius if provided - RG-FAC-003, RG-FAC-004
        if request.service_radius_km is not None:
            mobile_team.update_service_radius(request.service_radius_km)

        # Update daily capacity if provided - RG-FAC-003
        if request.daily_capacity is not None:
            mobile_team.update_capacity(request.daily_capacity)

        # Update equipment types if provided
        if request.equipment_types is not None:
            mobile_team.equipment_types = request.equipment_types

        # Update status if provided
        if request.status:
            if request.status == ResourceStatus.ACTIVE:
                mobile_team.activate()
            else:
                mobile_team.deactivate()

        # Persist updates
        updated_team = await self._repository.update(mobile_team)

        # Build response
        return UpdateMobileTeamResponse(
            id=updated_team.id,
            team_name=updated_team.team_name,
            base_location={
                "latitude": str(updated_team.base_location.latitude),
                "longitude": str(updated_team.base_location.longitude)
            },
            service_radius_km=str(updated_team.service_radius_km),
            daily_capacity=updated_team.daily_capacity,
            equipment_types=updated_team.equipment_types,
            status=updated_team.status.value,
            updated_at=updated_team.updated_at.isoformat()
        )
