"""Walk-in domain enumerations."""

from enum import Enum


class WalkInStatus(str, Enum):
    """Walk-in service status."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    """Payment status."""

    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    PARTIALLY_PAID = "partially_paid"


class PaymentMethod(str, Enum):
    """Payment method."""

    CASH = "cash"
    CARD = "card"
    MOBILE = "mobile"
    BANK_TRANSFER = "bank_transfer"


class VehicleSize(str, Enum):
    """Vehicle size classification."""

    COMPACT = "compact"
    STANDARD = "standard"
    LARGE = "large"
    OVERSIZED = "oversized"
