"""
List Mobile Teams Use Case

Retrieves all mobile teams with optional filtering.
Available to Manager, Admin, and Washer roles.
"""

from dataclasses import dataclass
from typing import List, Optional

from ..domain.entities import ResourceStatus
from ..ports.repositories import IMobileTeamRepository


@dataclass
class ListMobileTeamsRequest:
    """Request DTO for listing mobile teams."""
    status: Optional[ResourceStatus] = None
    include_inactive: bool = False


@dataclass
class MobileTeamDTO:
    """Data transfer object for mobile team information."""
    id: str
    team_name: str
    base_location: dict
    service_radius_km: str
    daily_capacity: int
    equipment_types: List[str]
    status: str
    created_at: str
    updated_at: str


@dataclass
class ListMobileTeamsResponse:
    """Response DTO for listing mobile teams."""
    mobile_teams: List[MobileTeamDTO]
    total_count: int
    active_count: int
    inactive_count: int


class ListMobileTeamsUseCase:
    """
    Use case for listing mobile teams.

    Business Rules:
    - RG-FAC-003: List all configured mobile teams
    - Filtering by status available
    - Can exclude inactive teams
    """

    def __init__(self, mobile_team_repository: IMobileTeamRepository):
        """
        Initialize use case with dependencies.

        Args:
            mobile_team_repository: Repository for mobile team data
        """
        self._repository = mobile_team_repository

    async def execute(self, request: ListMobileTeamsRequest) -> ListMobileTeamsResponse:
        """
        Execute mobile team listing.

        Args:
            request: List mobile teams request with filters

        Returns:
            ListMobileTeamsResponse with mobile team data and counts
        """
        # Retrieve mobile teams from repository
        mobile_teams = await self._repository.list_all(
            status=request.status,
            include_inactive=request.include_inactive
        )

        # Get counts by status for dashboard
        active_count = await self._repository.count_by_status(ResourceStatus.ACTIVE)
        inactive_count = await self._repository.count_by_status(ResourceStatus.INACTIVE)

        # Convert to DTOs
        mobile_team_dtos = []
        for team in mobile_teams:
            mobile_team_dtos.append(MobileTeamDTO(
                id=team.id,
                team_name=team.team_name,
                base_location={
                    "latitude": str(team.base_location.latitude),
                    "longitude": str(team.base_location.longitude)
                },
                service_radius_km=str(team.service_radius_km),
                daily_capacity=team.daily_capacity,
                equipment_types=team.equipment_types,
                status=team.status.value,
                created_at=team.created_at.isoformat(),
                updated_at=team.updated_at.isoformat()
            ))

        return ListMobileTeamsResponse(
            mobile_teams=mobile_team_dtos,
            total_count=len(mobile_team_dtos),
            active_count=active_count,
            inactive_count=inactive_count
        )
