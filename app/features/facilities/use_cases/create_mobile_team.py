"""
Create Mobile Team Use Case

Implements RG-FAC-003: Mobile team configuration management.
Manager and Admin roles can create new mobile teams.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List

from ..domain.entities import MobileTeam, Location
from ..ports.repositories import IMobileTeamRepository
from app.core.errors import ValidationError, BusinessRuleViolationError


@dataclass
class CreateMobileTeamRequest:
    """Request DTO for creating a mobile team."""
    team_name: str
    base_latitude: Decimal
    base_longitude: Decimal
    service_radius_km: Decimal = Decimal('50')
    daily_capacity: int = 8
    equipment_types: List[str] = None


@dataclass
class CreateMobileTeamResponse:
    """Response DTO for mobile team creation."""
    id: str
    team_name: str
    base_location: dict
    service_radius_km: str
    daily_capacity: int
    equipment_types: List[str]
    status: str
    created_at: str


class CreateMobileTeamUseCase:
    """
    Use case for creating a new mobile team.

    Business Rules:
    - RG-FAC-003: Team name must be unique
    - RG-FAC-003: Base location required
    - RG-FAC-003: Service radius defaults to 50km
    - RG-FAC-003: Daily capacity defaults to 8 vehicles
    - RG-FAC-004: Base location used for distance calculations
    """

    def __init__(self, mobile_team_repository: IMobileTeamRepository):
        """
        Initialize use case with dependencies.

        Args:
            mobile_team_repository: Repository for mobile team persistence
        """
        self._repository = mobile_team_repository

    async def execute(self, request: CreateMobileTeamRequest) -> CreateMobileTeamResponse:
        """
        Execute mobile team creation.

        Args:
            request: Create mobile team request data

        Returns:
            CreateMobileTeamResponse with created mobile team data

        Raises:
            ValidationError: If input data is invalid
            BusinessRuleViolationError: If team name already exists
        """
        # Validate team name uniqueness - RG-FAC-003
        existing_team = await self._repository.get_by_name(request.team_name)
        if existing_team:
            raise BusinessRuleViolationError(
                message=f"Mobile team with name '{request.team_name}' already exists",
                code="TEAM_NAME_EXISTS"
            )

        # Create base location - RG-FAC-003, RG-FAC-004
        try:
            base_location = Location(
                latitude=request.base_latitude,
                longitude=request.base_longitude
            )
        except ValidationError as e:
            raise ValidationError(
                message=f"Invalid base location coordinates: {str(e)}",
                code="INVALID_LOCATION"
            )

        # Create mobile team entity - RG-FAC-003
        mobile_team = MobileTeam.create(
            team_name=request.team_name,
            base_location=base_location,
            service_radius_km=request.service_radius_km,
            daily_capacity=request.daily_capacity,
            equipment_types=request.equipment_types or []
        )

        # Persist mobile team
        created_team = await self._repository.create(mobile_team)

        # Build response
        return CreateMobileTeamResponse(
            id=created_team.id,
            team_name=created_team.team_name,
            base_location={
                "latitude": str(created_team.base_location.latitude),
                "longitude": str(created_team.base_location.longitude)
            },
            service_radius_km=str(created_team.service_radius_km),
            daily_capacity=created_team.daily_capacity,
            equipment_types=created_team.equipment_types,
            status=created_team.status.value,
            created_at=created_team.created_at.isoformat()
        )
