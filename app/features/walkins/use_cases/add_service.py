"""Add service to walk-in use case."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
import uuid

from app.features.walkins.domain.entities import WalkInService, WalkInServiceItem
from app.features.walkins.domain.enums import WalkInStatus
from app.features.walkins.ports.repositories import IWalkInRepository


@dataclass
class AddServiceRequest:
    """Request to add service to walk-in."""

    walkin_id: str
    service_id: str  # Reference to services feature
    service_name: str
    price: Decimal
    product_costs: Decimal = Decimal("0.00")
    quantity: int = 1
    notes: Optional[str] = None


class AddServiceUseCase:
    """Use case for adding a service to walk-in."""

    def __init__(self, repository: IWalkInRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: AddServiceRequest) -> WalkInService:
        """
        Add a service to walk-in.

        Args:
            request: Add service request

        Returns:
            Updated walk-in service

        Raises:
            ValueError: If validation fails
            LookupError: If walk-in not found
        """
        # Validate request
        self._validate_request(request)

        # Get walk-in
        walkin = await self._repository.get_by_id(request.walkin_id)
        if not walkin:
            raise LookupError(f"Walk-in service {request.walkin_id} not found")

        # Validate walk-in state
        if walkin.status == WalkInStatus.COMPLETED:
            raise ValueError("Cannot add services to completed walk-in")

        if walkin.status == WalkInStatus.CANCELLED:
            raise ValueError("Cannot add services to cancelled walk-in")

        # Create service item
        service_item = WalkInServiceItem(
            id=str(uuid.uuid4()),
            service_id=request.service_id,
            service_name=request.service_name,
            price=request.price,
            product_costs=request.product_costs,
            quantity=request.quantity,
            notes=request.notes,
        )

        # Add service to walk-in
        walkin.add_service(service_item)

        # Update in repository
        updated = await self._repository.update(walkin)

        return updated

    def _validate_request(self, request: AddServiceRequest) -> None:
        """Validate add service request."""
        if not request.walkin_id or not request.walkin_id.strip():
            raise ValueError("Walk-in ID is required")

        if not request.service_id or not request.service_id.strip():
            raise ValueError("Service ID is required")

        if not request.service_name or not request.service_name.strip():
            raise ValueError("Service name is required")

        if request.price < Decimal("0"):
            raise ValueError("Service price cannot be negative")

        if request.product_costs < Decimal("0"):
            raise ValueError("Product costs cannot be negative")

        if request.quantity < 1:
            raise ValueError("Quantity must be at least 1")
