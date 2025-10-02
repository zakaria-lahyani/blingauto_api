"""Create walk-in service use case."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import uuid

from app.features.walkins.domain.entities import WalkInService
from app.features.walkins.domain.enums import WalkInStatus, PaymentStatus, VehicleSize
from app.features.walkins.ports.repositories import IWalkInRepository


@dataclass
class CreateWalkInRequest:
    """Request to create walk-in service."""

    vehicle_make: str
    vehicle_model: str
    vehicle_color: str
    vehicle_size: VehicleSize
    license_plate: Optional[str]
    customer_name: Optional[str]
    customer_phone: Optional[str]
    created_by_id: str  # Staff/washer ID
    notes: Optional[str] = None


class CreateWalkInUseCase:
    """Use case for creating a new walk-in service."""

    def __init__(self, repository: IWalkInRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: CreateWalkInRequest) -> WalkInService:
        """
        Create a new walk-in service.

        Args:
            request: Create walk-in request

        Returns:
            Created walk-in service

        Raises:
            ValueError: If validation fails
        """
        # Validate request
        self._validate_request(request)

        # Generate service number (WI-20251002-001)
        now = datetime.now(timezone.utc)
        date_prefix = now.strftime("%Y%m%d")
        service_number = await self._repository.get_next_service_number(date_prefix)

        # Create walk-in entity
        walkin = WalkInService(
            id=str(uuid.uuid4()),
            service_number=service_number,
            vehicle_make=request.vehicle_make,
            vehicle_model=request.vehicle_model,
            vehicle_color=request.vehicle_color,
            vehicle_size=request.vehicle_size,
            license_plate=request.license_plate,
            customer_name=request.customer_name,
            customer_phone=request.customer_phone,
            status=WalkInStatus.IN_PROGRESS,
            payment_status=PaymentStatus.PENDING,
            services=[],  # Empty initially
            total_amount=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            final_amount=Decimal("0.00"),
            paid_amount=Decimal("0.00"),
            created_by_id=request.created_by_id,
            started_at=now,
            notes=request.notes,
        )

        # Save to repository
        created = await self._repository.create(walkin)

        return created

    def _validate_request(self, request: CreateWalkInRequest) -> None:
        """Validate create request."""
        if not request.vehicle_make or not request.vehicle_make.strip():
            raise ValueError("Vehicle make is required")

        if not request.vehicle_model or not request.vehicle_model.strip():
            raise ValueError("Vehicle model is required")

        if not request.vehicle_color or not request.vehicle_color.strip():
            raise ValueError("Vehicle color is required")

        if not request.created_by_id or not request.created_by_id.strip():
            raise ValueError("Created by ID is required")

        # Validate phone format if provided
        if request.customer_phone:
            phone = request.customer_phone.strip()
            if len(phone) < 10:
                raise ValueError("Customer phone must be at least 10 digits")
