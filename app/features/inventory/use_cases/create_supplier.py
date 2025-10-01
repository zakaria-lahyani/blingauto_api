"""Create supplier use case."""

from dataclasses import dataclass
from typing import Optional
import uuid

from app.features.inventory.domain.entities import Supplier
from app.features.inventory.domain.policies import SupplierManagementPolicy
from app.features.inventory.ports.repositories import ISupplierRepository


@dataclass
class CreateSupplierRequest:
    """Request to create supplier."""

    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    payment_terms: Optional[str] = None
    rating: Optional[int] = None
    notes: Optional[str] = None


class CreateSupplierUseCase:
    """Use case for creating a new supplier."""

    def __init__(self, repository: ISupplierRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: CreateSupplierRequest) -> Supplier:
        """Create supplier."""
        # Validate
        self._validate_request(request)
        SupplierManagementPolicy.validate_contact_info(request.email, request.phone)
        SupplierManagementPolicy.validate_rating(request.rating)

        # Create supplier
        supplier = Supplier(
            id=str(uuid.uuid4()),
            name=request.name,
            contact_person=request.contact_person,
            email=request.email,
            phone=request.phone,
            address=request.address,
            payment_terms=request.payment_terms,
            is_active=True,
            rating=request.rating,
            notes=request.notes,
        )

        created = await self._repository.create(supplier)
        return created

    def _validate_request(self, request: CreateSupplierRequest) -> None:
        """Validate request."""
        if not request.name or not request.name.strip():
            raise ValueError("Supplier name is required")
