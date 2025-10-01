from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import uuid4

from .exceptions import ValidationError, BusinessRuleViolationError


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class BookingType(str, Enum):
    MOBILE = "mobile"
    STATIONARY = "stationary"


class VehicleSize(str, Enum):
    COMPACT = "compact"
    STANDARD = "standard"
    LARGE = "large"
    OVERSIZED = "oversized"


class QualityRating(int, Enum):
    ONE_STAR = 1
    TWO_STARS = 2
    THREE_STARS = 3
    FOUR_STARS = 4
    FIVE_STARS = 5


@dataclass
class BookingService:
    """Individual service within a booking - RG-BOK-001"""
    
    service_id: str
    name: str  # Changed from service_name to match use cases
    price: float  # Changed from Decimal to float for API compatibility
    duration_minutes: int  # Changed from duration to match use cases
    
    def __post_init__(self):
        """Validate service data according to business rules."""
        self._validate_service_data()
    
    @classmethod
    def create(
        cls,
        service_id: str,
        name: str,
        price: float,
        duration_minutes: int
    ) -> "BookingService":
        """Factory method to create a booking service."""
        return cls(
            service_id=service_id,
            name=name,
            price=price,
            duration_minutes=duration_minutes,
        )
    
    def _validate_service_data(self):
        """Validate service data business rules."""
        if not self.name or not self.name.strip():
            raise ValidationError("Service name is required", field="name")
        
        if len(self.name.strip()) > 100:
            raise ValidationError("Service name cannot exceed 100 characters", field="name")
        
        if self.price <= 0:
            raise ValidationError("Service price must be positive", field="price")
        
        if self.duration_minutes <= 0:
            raise ValidationError("Service duration must be positive", field="duration_minutes")


@dataclass
class Booking:
    """
    Booking aggregate root with complete lifecycle management.
    Implements business rules from REGLES_DE_GESTION.md sections RG-BOK-*.
    """
    
    # Business rule constants - from RG-BOK-001 to RG-BOK-015
    MIN_SERVICES = 1
    MAX_SERVICES = 10
    MIN_TOTAL_DURATION = 30  # minutes - RG-BOK-002
    MAX_TOTAL_DURATION = 240  # minutes - RG-BOK-002
    MIN_PRICE = Decimal("0.00")  # RG-BOK-003
    MAX_PRICE = Decimal("10000.00")  # RG-BOK-003
    MAX_ADVANCE_DAYS = 90  # RG-BOK-004
    MIN_ADVANCE_HOURS = 2  # RG-BOK-004
    GRACE_PERIOD_MINUTES = 30  # RG-BOK-011
    MIN_RESCHEDULE_NOTICE_HOURS = 2  # RG-BOK-012
    OVERTIME_CHARGE_PER_MINUTE = Decimal("1.00")  # RG-BOK-015
    
    id: str
    customer_id: str
    vehicle_id: str
    scheduled_at: datetime
    services: List[BookingService]
    booking_type: BookingType
    status: BookingStatus
    total_price: float  # Changed from Decimal to float for API compatibility
    estimated_duration_minutes: int  # Changed from total_duration to match use cases
    created_at: datetime
    updated_at: datetime

    # Resource allocation
    wash_bay_id: Optional[str] = None
    mobile_team_id: Optional[str] = None

    # Optional fields
    notes: Optional[str] = ""
    phone_number: Optional[str] = ""  # Added to match use cases
    customer_location: Optional[Dict[str, float]] = None  # {'lat': float, 'lng': float}
    cancellation_fee: float = 0.0  # Changed from Decimal to float
    quality_rating: Optional[QualityRating] = None
    quality_feedback: Optional[str] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    overtime_charges: float = 0.0  # Changed from Decimal to float
    # Cancellation tracking
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    cancellation_reason: Optional[str] = None
    # Payment tracking
    payment_intent_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate booking after initialization."""
        self._validate_services()
        self._validate_scheduled_time()
        self._validate_booking_type_constraints()
        self._validate_totals()
    
    @classmethod
    def create(
        cls,
        customer_id: str,
        vehicle_id: str,
        scheduled_at: datetime,
        services: List[BookingService],
        booking_type: BookingType,
        notes: Optional[str] = "",
        phone_number: Optional[str] = "",
        customer_location: Optional[Dict[str, float]] = None,
    ) -> "Booking":
        """
        Factory method to create a new booking.
        Enforces business rules RG-BOK-001 to RG-BOK-007.
        """
        now = datetime.utcnow()
        total_price = sum(service.price for service in services)
        estimated_duration = sum(service.duration_minutes for service in services)
        
        return cls(
            id=str(uuid4()),
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            scheduled_at=scheduled_at,
            services=services,
            booking_type=booking_type,
            status=BookingStatus.PENDING,
            total_price=total_price,
            estimated_duration_minutes=estimated_duration,
            created_at=now,
            updated_at=now,
            notes=notes or "",
            phone_number=phone_number or "",
            customer_location=customer_location,
        )
    
    def _validate_services(self):
        """Validate services business rules - RG-BOK-001"""
        if not self.services:
            raise ValidationError("At least one service must be selected", field="services")
        
        if len(self.services) < self.MIN_SERVICES:
            raise ValidationError(f"Minimum {self.MIN_SERVICES} service required", field="services")
        
        if len(self.services) > self.MAX_SERVICES:
            raise ValidationError(f"Maximum {self.MAX_SERVICES} services allowed", field="services")
        
        # Check for duplicate services
        service_ids = [service.service_id for service in self.services]
        if len(service_ids) != len(set(service_ids)):
            raise ValidationError("Duplicate services are not allowed", field="services")
    
    def _validate_scheduled_time(self):
        """Validate scheduling time business rules - RG-BOK-004"""
        now = datetime.utcnow()
        
        # Cannot schedule in the past
        if self.scheduled_at <= now:
            raise ValidationError("Cannot schedule appointments in the past", field="scheduled_at")
        
        # Check minimum advance notice
        min_advance_time = now + timedelta(hours=self.MIN_ADVANCE_HOURS)
        if self.scheduled_at < min_advance_time:
            raise ValidationError(
                f"Booking must be scheduled at least {self.MIN_ADVANCE_HOURS} hours in advance",
                field="scheduled_at"
            )
        
        # Check maximum advance notice
        max_advance_time = now + timedelta(days=self.MAX_ADVANCE_DAYS)
        if self.scheduled_at > max_advance_time:
            raise ValidationError(
                f"Cannot schedule more than {self.MAX_ADVANCE_DAYS} days in advance",
                field="scheduled_at"
            )
    
    def _validate_booking_type_constraints(self):
        """Validate booking type specific constraints - RG-BOK-005, RG-BOK-006"""
        if self.booking_type == BookingType.MOBILE:
            # RG-BOK-005: Mobile bookings require location
            if not self.customer_location:
                raise ValidationError(
                    "Customer location is required for mobile bookings",
                    field="customer_location"
                )
            
            if (
                not isinstance(self.customer_location, dict)
                or "lat" not in self.customer_location
                or "lng" not in self.customer_location
            ):
                raise ValidationError(
                    "Customer location must contain 'lat' and 'lng' coordinates",
                    field="customer_location"
                )
    
    def _validate_totals(self):
        """Validate calculated totals against business limits - RG-BOK-002, RG-BOK-003"""
        # Duration validation - RG-BOK-002
        if self.estimated_duration_minutes < self.MIN_TOTAL_DURATION:
            raise ValidationError(
                f"Total duration must be at least {self.MIN_TOTAL_DURATION} minutes",
                field="estimated_duration_minutes"
            )
        
        if self.estimated_duration_minutes > self.MAX_TOTAL_DURATION:
            raise ValidationError(
                f"Total duration cannot exceed {self.MAX_TOTAL_DURATION} minutes",
                field="estimated_duration_minutes"
            )
        
        # Price validation - RG-BOK-003
        if self.total_price < float(self.MIN_PRICE):
            raise ValidationError(f"Total price must be at least ${self.MIN_PRICE}", field="total_price")
        
        if self.total_price > float(self.MAX_PRICE):
            raise ValidationError(f"Total price cannot exceed ${self.MAX_PRICE}", field="total_price")
    
    def confirm(self):
        """Confirm a pending booking - RG-BOK-008, RG-BOK-009"""
        if self.status != BookingStatus.PENDING:
            raise BusinessRuleViolationError(
                f"Can only confirm pending bookings, current status: {self.status.value}",
                rule="RG-BOK-009"
            )
        
        self.status = BookingStatus.CONFIRMED
        self.updated_at = datetime.utcnow()
    
    def start_service(self):
        """Start the service (mark as in progress) - RG-BOK-008, RG-BOK-009"""
        if self.status != BookingStatus.CONFIRMED:
            raise BusinessRuleViolationError(
                f"Can only start confirmed bookings, current status: {self.status.value}",
                rule="RG-BOK-009"
            )
        
        self.status = BookingStatus.IN_PROGRESS
        self.actual_start_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def complete_service(self, actual_end_time: Optional[datetime] = None):
        """Complete the service - RG-BOK-008, RG-BOK-015"""
        if self.status != BookingStatus.IN_PROGRESS:
            raise BusinessRuleViolationError(
                f"Can only complete in-progress bookings, current status: {self.status.value}",
                rule="RG-BOK-009"
            )
        
        self.status = BookingStatus.COMPLETED
        self.actual_end_time = actual_end_time or datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Calculate overtime charges if applicable - RG-BOK-015
        self._calculate_overtime_charges()
    
    def cancel(self, cancelled_by: str, reason: str = "cancelled_by_customer"):
        """Cancel the booking with fee calculation - RG-BOK-010"""
        if self.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED, BookingStatus.NO_SHOW]:
            raise BusinessRuleViolationError(
                f"Cannot cancel booking with status: {self.status.value}",
                rule="RG-BOK-009"
            )
        
        # Calculate cancellation fee based on time until scheduled appointment
        self.cancellation_fee = self._calculate_cancellation_fee()
        self.status = BookingStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.cancelled_by = cancelled_by
        self.cancellation_reason = reason
        self.updated_at = datetime.utcnow()
        
        if reason:
            self.notes = f"{self.notes or ''}\nCancellation reason: {reason}".strip()
    
    def mark_no_show(self):
        """Mark booking as no-show - RG-BOK-011"""
        if self.status != BookingStatus.CONFIRMED:
            raise BusinessRuleViolationError(
                "Can only mark confirmed bookings as no-show",
                rule="RG-BOK-011"
            )
        
        # Check if grace period has passed
        grace_end = self.scheduled_at + timedelta(minutes=self.GRACE_PERIOD_MINUTES)
        if datetime.utcnow() < grace_end:
            raise BusinessRuleViolationError(
                f"Cannot mark as no-show until {self.GRACE_PERIOD_MINUTES} minutes after scheduled time",
                rule="RG-BOK-011"
            )
        
        self.status = BookingStatus.NO_SHOW
        self.cancellation_fee = self.total_price  # 100% fee for no-show
        self.updated_at = datetime.utcnow()
    
    def reschedule(self, new_scheduled_at: datetime):
        """Reschedule the booking - RG-BOK-012"""
        if self.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            raise BusinessRuleViolationError(
                "Can only reschedule pending or confirmed bookings",
                rule="RG-BOK-012"
            )
        
        # Check minimum notice for rescheduling
        min_notice_time = datetime.utcnow() + timedelta(hours=self.MIN_RESCHEDULE_NOTICE_HOURS)
        if new_scheduled_at < min_notice_time:
            raise BusinessRuleViolationError(
                f"Rescheduling requires at least {self.MIN_RESCHEDULE_NOTICE_HOURS} hours notice",
                rule="RG-BOK-012"
            )
        
        old_time = self.scheduled_at
        self.scheduled_at = new_scheduled_at
        self.updated_at = datetime.utcnow()
        
        # Validate new time
        self._validate_scheduled_time()
        
        # Add note about rescheduling
        self.notes = f"{self.notes or ''}\nRescheduled from {old_time.isoformat()} to {new_scheduled_at.isoformat()}".strip()
    
    def update_services(self, new_services: List[BookingService]):
        """Update the services for this booking (used by update use case)"""
        if self.status != BookingStatus.PENDING:
            raise BusinessRuleViolationError(
                "Can only update services for pending bookings",
                rule="RG-BOK-013"
            )
        
        self.services = new_services
        self._recalculate_totals()
        self._validate_totals()
        self.updated_at = datetime.utcnow()
    
    def update_notes(self, notes: str):
        """Update booking notes"""
        self.notes = notes
        self.updated_at = datetime.utcnow()
    
    def update_phone_number(self, phone_number: str):
        """Update booking phone number"""
        self.phone_number = phone_number
        self.updated_at = datetime.utcnow()
    
    def add_service(self, service: BookingService):
        """Add a service to the booking - RG-BOK-013"""
        if self.status != BookingStatus.PENDING:
            raise BusinessRuleViolationError(
                "Can only add services to pending bookings",
                rule="RG-BOK-013"
            )
        
        # Check if service already exists
        if any(s.service_id == service.service_id for s in self.services):
            raise BusinessRuleViolationError(
                "Service already exists in booking",
                rule="RG-BOK-001"
            )
        
        # Check max services limit
        if len(self.services) >= self.MAX_SERVICES:
            raise BusinessRuleViolationError(
                f"Maximum {self.MAX_SERVICES} services allowed",
                rule="RG-BOK-001"
            )
        
        self.services.append(service)
        self._recalculate_totals()
        self._validate_totals()
        self.updated_at = datetime.utcnow()
    
    def remove_service(self, service_id: str):
        """Remove a service from the booking - RG-BOK-014"""
        if self.status != BookingStatus.PENDING:
            raise BusinessRuleViolationError(
                "Can only remove services from pending bookings",
                rule="RG-BOK-014"
            )
        
        # Check minimum services requirement
        if len(self.services) <= self.MIN_SERVICES:
            raise BusinessRuleViolationError(
                f"Cannot remove service - minimum {self.MIN_SERVICES} service required",
                rule="RG-BOK-014"
            )
        
        # Find and remove service
        original_count = len(self.services)
        self.services = [s for s in self.services if s.service_id != service_id]
        
        if len(self.services) == original_count:
            raise ValidationError("Service not found in booking", field="service_id")
        
        self._recalculate_totals()
        self.updated_at = datetime.utcnow()
    
    def rate_quality(self, rating: QualityRating, feedback: Optional[str] = None):
        """Rate the service quality - RG-BOK-016"""
        if self.status != BookingStatus.COMPLETED:
            raise BusinessRuleViolationError(
                "Can only rate completed bookings",
                rule="RG-BOK-016"
            )
        
        if self.quality_rating is not None:
            raise BusinessRuleViolationError(
                "Booking has already been rated",
                rule="RG-BOK-016"
            )
        
        if feedback and len(feedback) > 1000:
            raise ValidationError("Feedback cannot exceed 1000 characters", field="feedback")
        
        self.quality_rating = rating
        self.quality_feedback = feedback
        self.updated_at = datetime.utcnow()
    
    def _calculate_cancellation_fee(self) -> float:
        """Calculate cancellation fee based on time until appointment - RG-BOK-010"""
        now = datetime.utcnow()
        time_until = self.scheduled_at - now
        
        if time_until.total_seconds() < 0:
            # Past due - 100% fee
            return self.total_price
        
        hours_until = time_until.total_seconds() / 3600
        
        if hours_until < 2:
            # Less than 2 hours - 100%
            return self.total_price
        elif hours_until < 6:
            # 2-6 hours - 50%
            return self.total_price * 0.50
        elif hours_until < 24:
            # 6-24 hours - 25%
            return self.total_price * 0.25
        else:
            # More than 24 hours - 0%
            return 0.0
    
    def _calculate_overtime_charges(self):
        """Calculate overtime charges if service exceeded expected duration - RG-BOK-015"""
        if not self.actual_start_time or not self.actual_end_time:
            return
        
        actual_duration = (self.actual_end_time - self.actual_start_time).total_seconds() / 60
        expected_duration = self.estimated_duration_minutes
        
        if actual_duration > expected_duration:
            overtime_minutes = actual_duration - expected_duration
            self.overtime_charges = overtime_minutes * 1.0  # $1.00 per minute
        else:
            self.overtime_charges = 0.0
    
    def _recalculate_totals(self):
        """Recalculate total price and duration from services."""
        self.total_price = sum(service.price for service in self.services)
        self.estimated_duration_minutes = sum(service.duration_minutes for service in self.services)
    
    @property
    def final_amount(self) -> float:
        """Get final amount including cancellation fees and overtime charges."""
        base_amount = self.total_price
        if self.status == BookingStatus.CANCELLED or self.status == BookingStatus.NO_SHOW:
            return self.cancellation_fee + self.overtime_charges
        return base_amount + self.overtime_charges
    
    @property
    def can_be_cancelled(self) -> bool:
        """Check if booking can be cancelled."""
        return self.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]
    
    @property
    def can_be_rescheduled(self) -> bool:
        """Check if booking can be rescheduled."""
        if self.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            return False
        
        min_notice_time = datetime.utcnow() + timedelta(hours=self.MIN_RESCHEDULE_NOTICE_HOURS)
        return self.scheduled_at > min_notice_time