"""
Delete Wash Bay Use Case

Soft deletes a wash bay (marks as deleted, preserves history).
Admin role only.
"""

from dataclasses import dataclass

from ..ports.repositories import IWashBayRepository
from app.core.errors import NotFoundError, BusinessRuleViolationError


@dataclass
class DeleteWashBayRequest:
    """Request DTO for deleting a wash bay."""
    wash_bay_id: str


@dataclass
class DeleteWashBayResponse:
    """Response DTO for wash bay deletion."""
    id: str
    bay_number: str
    deleted: bool
    message: str


class DeleteWashBayUseCase:
    """
    Use case for deleting a wash bay.

    Business Rules:
    - RG-FAC-001: Soft delete only (preserve history)
    - Cannot delete bay with active bookings (would be checked by bookings feature)
    - Admin only operation
    """

    def __init__(self, wash_bay_repository: IWashBayRepository):
        """
        Initialize use case with dependencies.

        Args:
            wash_bay_repository: Repository for wash bay persistence
        """
        self._repository = wash_bay_repository

    async def execute(self, request: DeleteWashBayRequest) -> DeleteWashBayResponse:
        """
        Execute wash bay deletion (soft delete).

        Args:
            request: Delete wash bay request data

        Returns:
            DeleteWashBayResponse with deletion confirmation

        Raises:
            NotFoundError: If wash bay doesn't exist
            BusinessRuleViolationError: If bay has active bookings
        """
        # Retrieve existing wash bay to get bay_number for response
        wash_bay = await self._repository.get_by_id(request.wash_bay_id)
        if not wash_bay:
            raise NotFoundError(
                message=f"Wash bay with ID '{request.wash_bay_id}' not found",
                code="WASH_BAY_NOT_FOUND"
            )

        # Perform soft delete
        deleted = await self._repository.delete(request.wash_bay_id)

        if not deleted:
            raise NotFoundError(
                message=f"Failed to delete wash bay with ID '{request.wash_bay_id}'",
                code="DELETE_FAILED"
            )

        return DeleteWashBayResponse(
            id=request.wash_bay_id,
            bay_number=wash_bay.bay_number,
            deleted=True,
            message=f"Wash bay '{wash_bay.bay_number}' has been deactivated"
        )
