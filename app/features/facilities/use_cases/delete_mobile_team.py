"""
Delete Mobile Team Use Case

Soft deletes a mobile team (marks as deleted, preserves history).
Admin role only.
"""

from dataclasses import dataclass

from ..ports.repositories import IMobileTeamRepository
from app.core.errors import NotFoundError


@dataclass
class DeleteMobileTeamRequest:
    """Request DTO for deleting a mobile team."""
    team_id: str


@dataclass
class DeleteMobileTeamResponse:
    """Response DTO for mobile team deletion."""
    id: str
    team_name: str
    deleted: bool
    message: str


class DeleteMobileTeamUseCase:
    """
    Use case for deleting a mobile team.

    Business Rules:
    - RG-FAC-003: Soft delete only (preserve history)
    - Cannot delete team with active bookings
    - Admin only operation
    """

    def __init__(self, mobile_team_repository: IMobileTeamRepository):
        """
        Initialize use case with dependencies.

        Args:
            mobile_team_repository: Repository for mobile team persistence
        """
        self._repository = mobile_team_repository

    async def execute(self, request: DeleteMobileTeamRequest) -> DeleteMobileTeamResponse:
        """
        Execute mobile team deletion (soft delete).

        Args:
            request: Delete mobile team request data

        Returns:
            DeleteMobileTeamResponse with deletion confirmation

        Raises:
            NotFoundError: If mobile team doesn't exist
        """
        # Retrieve existing mobile team to get team_name for response
        mobile_team = await self._repository.get_by_id(request.team_id)
        if not mobile_team:
            raise NotFoundError(
                message=f"Mobile team with ID '{request.team_id}' not found",
                code="MOBILE_TEAM_NOT_FOUND"
            )

        # TODO: Check for active bookings via consumer-owned port if needed

        # Perform soft delete
        deleted = await self._repository.delete(request.team_id)

        if not deleted:
            raise NotFoundError(
                message=f"Failed to delete mobile team with ID '{request.team_id}'",
                code="DELETE_FAILED"
            )

        return DeleteMobileTeamResponse(
            id=request.team_id,
            team_name=mobile_team.team_name,
            deleted=True,
            message=f"Mobile team '{mobile_team.team_name}' has been deactivated"
        )
