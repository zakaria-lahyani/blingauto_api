"""Update supplier use case."""

from dataclasses import dataclass
from typing import Optional

from app.features.inventory.domain.entities import Supplier
from app.features.inventory.domain.policies import SupplierManagementPolicy
from app.features.inventory.ports.repositories import ISupplierRepository


@dataclass
class UpdateSupplierRequest:
    """Request to update supplier."""

    supplier_id: str
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    payment_terms: Optional[str] = None
    is_active: Optional[bool] = None
    rating: Optional[int] = None
    notes: Optional[str] = None


class UpdateSupplierUseCase:
    """Use case for updating existing supplier."""

    def __init__(self, repository: ISupplierRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: UpdateSupplierRequest) -> Supplier:
        """Update supplier."""
        # Get existing supplier
        supplier = await self._repository.get_by_id(request.supplier_id)
        if not supplier:
            raise LookupError(f"Supplier {request.supplier_id} not found")

        # Update fields
        if request.name is not None:
            supplier.name = request.name
        if request.contact_person is not None:
            supplier.contact_person = request.contact_person
        if request.email is not None:
            supplier.email = request.email
        if request.phone is not None:
            supplier.phone = request.phone
        if request.address is not None:
            supplier.address = request.address
        if request.payment_terms is not None:
            supplier.payment_terms = request.payment_terms
        if request.is_active is not None:
            supplier.is_active = request.is_active
        if request.rating is not None:
            SupplierManagementPolicy.validate_rating(request.rating)
            supplier.rating = request.rating
        if request.notes is not None:
            supplier.notes = request.notes

        # Validate contact info
        SupplierManagementPolicy.validate_contact_info(supplier.email, supplier.phone)

        updated = await self._repository.update(supplier)
        return updated
