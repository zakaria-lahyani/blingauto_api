"""Walk-in domain policies - business rules."""

from decimal import Decimal
from typing import List

from .entities import WalkInService, WalkInServiceItem
from .enums import WalkInStatus, PaymentStatus


class WalkInPricingPolicy:
    """Business rules for walk-in pricing."""

    MAX_DISCOUNT_PERCENT = Decimal("50.00")  # Max 50% discount
    MIN_SERVICE_PRICE = Decimal("5.00")  # Minimum service price

    @staticmethod
    def validate_discount(total_amount: Decimal, discount_amount: Decimal) -> None:
        """
        Validate discount amount.

        Args:
            total_amount: Total service amount
            discount_amount: Discount to apply

        Raises:
            ValueError: If discount is invalid
        """
        if discount_amount < 0:
            raise ValueError("Discount cannot be negative")

        if discount_amount > total_amount:
            raise ValueError("Discount cannot exceed total amount")

        # Check discount percentage
        discount_percent = (discount_amount / total_amount) * Decimal("100")
        if discount_percent > WalkInPricingPolicy.MAX_DISCOUNT_PERCENT:
            raise ValueError(
                f"Discount cannot exceed {WalkInPricingPolicy.MAX_DISCOUNT_PERCENT}%"
            )

    @staticmethod
    def validate_service_price(price: Decimal) -> None:
        """
        Validate service price.

        Args:
            price: Service price

        Raises:
            ValueError: If price is invalid
        """
        if price < WalkInPricingPolicy.MIN_SERVICE_PRICE:
            raise ValueError(
                f"Service price cannot be less than {WalkInPricingPolicy.MIN_SERVICE_PRICE}"
            )

    @staticmethod
    def calculate_total_with_services(
        services: List[WalkInServiceItem],
        discount_amount: Decimal = Decimal("0.00"),
    ) -> Decimal:
        """
        Calculate total amount with services and discount.

        Args:
            services: List of service items
            discount_amount: Discount to apply

        Returns:
            Decimal: Final amount
        """
        total = sum(item.subtotal for item in services)
        return total - discount_amount

    @staticmethod
    def can_apply_discount(walkin: WalkInService) -> bool:
        """
        Check if discount can be applied.

        Args:
            walkin: Walk-in service

        Returns:
            bool: True if discount can be applied
        """
        # Cannot apply discount to completed or cancelled services
        if walkin.status in [WalkInStatus.COMPLETED, WalkInStatus.CANCELLED]:
            return False

        # Cannot apply discount if already paid
        if walkin.payment_status == PaymentStatus.PAID:
            return False

        return True


class WalkInPaymentPolicy:
    """Business rules for walk-in payments."""

    @staticmethod
    def can_mark_as_paid(walkin: WalkInService) -> bool:
        """
        Check if walk-in can be marked as paid.

        Args:
            walkin: Walk-in service

        Returns:
            bool: True if can be marked as paid
        """
        # Must have services
        if not walkin.services:
            return False

        # Cannot pay cancelled service
        if walkin.status == WalkInStatus.CANCELLED:
            return False

        # Already paid
        if walkin.payment_status == PaymentStatus.PAID:
            return False

        # Must have positive amount
        if walkin.final_amount <= 0:
            return False

        return True

    @staticmethod
    def can_refund(walkin: WalkInService) -> bool:
        """
        Check if walk-in can be refunded.

        Args:
            walkin: Walk-in service

        Returns:
            bool: True if can be refunded
        """
        # Must be paid
        if walkin.payment_status != PaymentStatus.PAID:
            return False

        # Cannot refund if service is in progress
        if walkin.status == WalkInStatus.IN_PROGRESS:
            return False

        return True

    @staticmethod
    def validate_payment_amount(walkin: WalkInService, amount: Decimal) -> None:
        """
        Validate payment amount matches final amount.

        Args:
            walkin: Walk-in service
            amount: Payment amount

        Raises:
            ValueError: If amount doesn't match
        """
        if amount != walkin.final_amount:
            raise ValueError(
                f"Payment amount ({amount}) must match final amount ({walkin.final_amount})"
            )

    @staticmethod
    def can_complete_without_payment(walkin: WalkInService) -> bool:
        """
        Check if service can be completed without payment.

        Some businesses allow completing service before payment.

        Args:
            walkin: Walk-in service

        Returns:
            bool: True if can complete without payment
        """
        # For walk-ins, typically payment is required before completion
        # But this can be configured per business
        return False  # Default: payment required

    @staticmethod
    def calculate_change(amount_paid: Decimal, amount_due: Decimal) -> Decimal:
        """
        Calculate change to return.

        Args:
            amount_paid: Amount paid by customer
            amount_due: Amount due

        Returns:
            Decimal: Change to return

        Raises:
            ValueError: If payment is insufficient
        """
        if amount_paid < amount_due:
            raise ValueError(f"Insufficient payment: {amount_paid} < {amount_due}")

        return amount_paid - amount_due
