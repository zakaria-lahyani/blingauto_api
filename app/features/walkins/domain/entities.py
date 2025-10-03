"""Walk-in domain entities."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict

from .enums import WalkInStatus, PaymentStatus, PaymentMethod, VehicleSize


@dataclass
class WalkInServiceItem:
    """
    Individual service in a walk-in.

    Represents a single service performed with pricing and cost tracking.
    """

    id: Optional[str] = None
    service_id: str = ""
    service_name: str = ""
    price: Decimal = Decimal("0.00")
    quantity: int = 1
    subtotal: Decimal = Decimal("0.00")
    notes: Optional[str] = None

    # Cost tracking for profit calculation
    product_costs: Decimal = Decimal("0.00")

    def __post_init__(self):
        """Calculate subtotal after initialization."""
        if self.subtotal == Decimal("0.00"):
            self.subtotal = self.price * Decimal(self.quantity)

    @property
    def profit(self) -> Decimal:
        """Calculate profit for this service item."""
        return self.subtotal - self.product_costs


@dataclass
class WalkInService:
    """
    Walk-in (non-booked) service record.

    Represents a quick service for a vehicle without prior booking.
    """

    id: str
    service_number: str  # WI-20251002-001

    # Vehicle info (simplified - no full registration)
    vehicle_make: str
    vehicle_model: str
    vehicle_color: str
    license_plate: str
    vehicle_size: VehicleSize

    # Service details
    services: List[WalkInServiceItem] = field(default_factory=list)
    total_amount: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    discount_reason: Optional[str] = None
    final_amount: Decimal = Decimal("0.00")
    paid_amount: Decimal = Decimal("0.00")

    # Staff and facility
    performed_by_staff_id: str = None
    wash_bay_id: Optional[str] = None
    created_by_id: Optional[str] = None
    completed_by_id: Optional[str] = None
    cancelled_by_id: Optional[str] = None

    # Timing
    started_at: datetime = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    duration_minutes: int = 0

    # Payment
    payment_status: PaymentStatus = PaymentStatus.PENDING
    payment_method: Optional[PaymentMethod] = None
    payment_date: Optional[datetime] = None
    payment_details: Optional[str] = None

    # Customer (optional)
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None

    status: WalkInStatus = WalkInStatus.IN_PROGRESS
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize calculated fields."""
        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)
        if self.total_amount == Decimal("0.00") and self.services:
            self.calculate_total()

    @property
    def is_completed(self) -> bool:
        """Check if service is completed."""
        return self.status == WalkInStatus.COMPLETED

    @property
    def is_paid(self) -> bool:
        """Check if service is paid."""
        return self.payment_status == PaymentStatus.PAID

    def add_service(self, service_item: WalkInServiceItem) -> None:
        """
        Add a service to the walk-in.

        Args:
            service_item: Service item to add
        """
        self.services.append(service_item)
        self.calculate_total()

    def remove_service(self, service_id: str) -> bool:
        """
        Remove a service from the walk-in.

        Args:
            service_id: ID of service to remove

        Returns:
            bool: True if removed, False if not found
        """
        original_length = len(self.services)
        self.services = [s for s in self.services if s.service_id != service_id]

        if len(self.services) < original_length:
            self.calculate_total()
            return True
        return False

    def calculate_total(self) -> Decimal:
        """
        Calculate total amount from all services.

        Returns:
            Decimal: Total amount
        """
        self.total_amount = sum(item.subtotal for item in self.services)
        self.final_amount = self.total_amount - self.discount_amount
        return self.final_amount

    def apply_discount(self, discount_percent: Decimal) -> None:
        """
        Apply percentage discount to the total.

        Args:
            discount_percent: Discount percentage (e.g., 10 for 10%)
        """
        if discount_percent < 0 or discount_percent > 100:
            raise ValueError("Discount must be between 0 and 100")

        self.discount_amount = (self.total_amount * discount_percent) / Decimal("100")
        self.final_amount = self.total_amount - self.discount_amount

    def apply_discount_amount(self, amount: Decimal) -> None:
        """
        Apply fixed discount amount.

        Args:
            amount: Discount amount
        """
        if amount < 0:
            raise ValueError("Discount amount cannot be negative")
        if amount > self.total_amount:
            raise ValueError("Discount cannot exceed total amount")

        self.discount_amount = amount
        self.final_amount = self.total_amount - self.discount_amount

    def calculate_profit(self) -> Decimal:
        """
        Calculate total profit (revenue - product costs).

        Returns:
            Decimal: Total profit
        """
        total_costs = sum(item.product_costs for item in self.services)
        return self.final_amount - total_costs

    def mark_as_paid(self, payment_method: PaymentMethod) -> None:
        """
        Mark service as paid.

        Args:
            payment_method: Method of payment
        """
        self.payment_status = PaymentStatus.PAID
        self.payment_method = payment_method
        self.payment_date = datetime.now(timezone.utc)

    def complete_service(self) -> None:
        """Complete the service and calculate duration."""
        if self.status == WalkInStatus.COMPLETED:
            raise ValueError("Service is already completed")

        self.status = WalkInStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_minutes = int(delta.total_seconds() / 60)

    def cancel_service(self, reason: Optional[str] = None) -> None:
        """
        Cancel the service.

        Args:
            reason: Reason for cancellation
        """
        if self.status == WalkInStatus.COMPLETED:
            raise ValueError("Cannot cancel completed service")

        if self.payment_status == PaymentStatus.PAID:
            self.payment_status = PaymentStatus.REFUNDED

        self.status = WalkInStatus.CANCELLED
        if reason:
            self.notes = f"Cancelled: {reason}" + (f"\n{self.notes}" if self.notes else "")


@dataclass
class DailyWalkInReport:
    """
    Daily walk-in summary.

    Aggregates statistics for a day's worth of walk-in services.
    """

    date: date
    total_services: int
    completed_services: int
    cancelled_services: int
    total_revenue: Decimal
    total_costs: Decimal
    total_profit: Decimal
    average_service_value: Decimal

    # Breakdown by service type
    services_by_type: Dict[str, int] = field(default_factory=dict)

    # Breakdown by payment method
    revenue_by_payment_method: Dict[PaymentMethod, Decimal] = field(default_factory=dict)

    # Breakdown by staff
    services_by_staff: Dict[str, int] = field(default_factory=dict)
    revenue_by_staff: Dict[str, Decimal] = field(default_factory=dict)

    # Vehicle size breakdown
    services_by_vehicle_size: Dict[VehicleSize, int] = field(default_factory=dict)

    @property
    def completion_rate(self) -> Decimal:
        """Calculate completion rate percentage."""
        if self.total_services == 0:
            return Decimal("0.00")
        return (Decimal(self.completed_services) / Decimal(self.total_services)) * Decimal("100")

    @property
    def profit_margin(self) -> Decimal:
        """Calculate profit margin percentage."""
        if self.total_revenue == 0:
            return Decimal("0.00")
        return (self.total_profit / self.total_revenue) * Decimal("100")
