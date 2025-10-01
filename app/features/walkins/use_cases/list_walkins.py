"""List walk-in services use case."""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from app.features.walkins.domain.entities import WalkInService
from app.features.walkins.domain.enums import WalkInStatus, PaymentStatus
from app.features.walkins.ports.repositories import IWalkInRepository


@dataclass
class ListWalkInsRequest:
    """Request to list walk-ins with filters."""

    status: Optional[WalkInStatus] = None
    payment_status: Optional[PaymentStatus] = None
    created_by_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: int = 50
    offset: int = 0


class ListWalkInsUseCase:
    """Use case for listing walk-in services with filters."""

    def __init__(self, repository: IWalkInRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: ListWalkInsRequest) -> List[WalkInService]:
        """
        List walk-in services with filters.

        Args:
            request: List walk-ins request with filters

        Returns:
            List of walk-in services

        Raises:
            ValueError: If validation fails
        """
        # Validate request
        self._validate_request(request)

        # Get from repository
        walkins = await self._repository.list_with_filters(
            status=request.status,
            payment_status=request.payment_status,
            created_by_id=request.created_by_id,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit,
            offset=request.offset,
        )

        return walkins

    def _validate_request(self, request: ListWalkInsRequest) -> None:
        """Validate list request."""
        if request.limit < 1:
            raise ValueError("Limit must be at least 1")

        if request.limit > 200:
            raise ValueError("Limit cannot exceed 200")

        if request.offset < 0:
            raise ValueError("Offset cannot be negative")

        if request.start_date and request.end_date:
            if request.start_date > request.end_date:
                raise ValueError("Start date cannot be after end date")
