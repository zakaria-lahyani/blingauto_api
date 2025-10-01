"""Record payment for walk-in use case."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.features.walkins.domain.entities import WalkInService
from app.features.walkins.domain.enums import WalkInStatus, PaymentMethod
from app.features.walkins.domain.policies import WalkInPaymentPolicy
from app.features.walkins.ports.repositories import IWalkInRepository


@dataclass
class RecordPaymentRequest:
    """Request to record payment."""

    walkin_id: str
    amount: Decimal
    payment_method: PaymentMethod
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None


class RecordPaymentUseCase:
    """Use case for recording payment for walk-in."""

    def __init__(self, repository: IWalkInRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: RecordPaymentRequest) -> WalkInService:
        """
        Record payment for walk-in.

        Args:
            request: Record payment request

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
        if walkin.status == WalkInStatus.CANCELLED:
            raise ValueError("Cannot record payment for cancelled walk-in")

        if not walkin.services:
            raise ValueError("Cannot record payment - no services added")

        # Validate payment using policy
        WalkInPaymentPolicy.validate_payment(walkin.final_amount, request.amount)

        # Check for overpayment
        remaining = walkin.final_amount - walkin.paid_amount
        if request.amount > remaining:
            raise ValueError(
                f"Payment amount ${request.amount} exceeds remaining balance ${remaining}"
            )

        # Record payment
        walkin.record_payment(
            amount=request.amount,
            payment_method=request.payment_method,
            transaction_reference=request.transaction_reference,
            payment_date=datetime.utcnow(),
            notes=request.notes,
        )

        # Update in repository
        updated = await self._repository.update(walkin)

        return updated

    def _validate_request(self, request: RecordPaymentRequest) -> None:
        """Validate record payment request."""
        if not request.walkin_id or not request.walkin_id.strip():
            raise ValueError("Walk-in ID is required")

        if request.amount <= Decimal("0"):
            raise ValueError("Payment amount must be greater than zero")

        # Validate transaction reference for non-cash payments
        if request.payment_method != PaymentMethod.CASH:
            if not request.transaction_reference:
                raise ValueError(
                    f"Transaction reference is required for {request.payment_method.value} payments"
                )
