"""
Booking domain entities
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Set
from uuid import UUID, uuid4

from .enums import BookingStatus, BookingType, CancellationPolicy, QualityRating
from src.shared.utils.timestamp import utc_now


class BookingService:
    """Individual service within a booking"""
    
    def __init__(
        self,
        service_id: UUID,
        service_name: str,
        price: Decimal,
        duration: int,  # in minutes
        id: Optional[UUID] = None
    ):
        # Validate business rules
        self._validate_service_data(service_name, price, duration)
        
        self.id = id or uuid4()
        self.service_id = service_id
        self.service_name = service_name.strip() if service_name else service_name
        self.price = price
        self.duration = duration
    
    def _validate_service_data(self, service_name: str, price: Decimal, duration: int) -> None:
        """Validate service data business rules"""
        if not service_name or not service_name.strip():
            raise ValueError("Service name is required")
        if len(service_name.strip()) > 100:
            raise ValueError("Service name cannot exceed 100 characters")
        
        if price <= 0:
            raise ValueError("Service price must be positive")
        
        if duration <= 0:
            raise ValueError("Service duration must be positive")
    
    def __eq__(self, other):
        if not isinstance(other, BookingService):
            return False
        return self.service_id == other.service_id
    
    def __hash__(self):
        return hash(self.service_id)
    
    def __str__(self) -> str:
        return f"BookingService(id={self.id}, service_id={self.service_id}, name='{self.service_name}', price={self.price})"


class Booking:
    """Booking entity with complete lifecycle management"""
    
    # Business constants
    MIN_SERVICES = 1
    MAX_SERVICES = 10
    MIN_TOTAL_DURATION = 30  # minutes
    MAX_TOTAL_DURATION = 240  # minutes
    MIN_PRICE = Decimal("0.00")
    MAX_PRICE = Decimal("10000.00")
    MAX_ADVANCE_DAYS = 90
    GRACE_PERIOD_MINUTES = 30
    MIN_RESCHEDULE_NOTICE_HOURS = 2
    OVERTIME_CHARGE_PER_MINUTE = Decimal("1.00")
    
    def __init__(
        self,
        customer_id: UUID,
        vehicle_id: UUID,
        scheduled_at: datetime,
        services: List[BookingService],
        booking_type: BookingType,
        notes: Optional[str] = None,
        customer_location: Optional[dict] = None,
        vehicle_size: str = "standard",
        id: Optional[UUID] = None,
        status: BookingStatus = BookingStatus.PENDING,
        total_price: Optional[Decimal] = None,
        total_duration: Optional[int] = None,
        cancellation_fee: Optional[Decimal] = None,
        quality_rating: Optional[QualityRating] = None,
        quality_feedback: Optional[str] = None,
        actual_start_time: Optional[datetime] = None,
        actual_end_time: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        # Validate business rules
        self._validate_services(services)
        self._validate_scheduled_time(scheduled_at)
        self._validate_booking_type_constraints(booking_type, customer_location, vehicle_size)
        
        self.id = id or uuid4()
        self.customer_id = customer_id
        self.vehicle_id = vehicle_id
        self.scheduled_at = scheduled_at
        self.services = list(services)  # Convert to list to ensure proper handling
        self.booking_type = booking_type
        self.notes = notes
        self.customer_location = customer_location
        self.vehicle_size = vehicle_size
        self.status = status
        
        # Calculate totals if not provided
        self.total_price = total_price or self._calculate_total_price()
        self.total_duration = total_duration or self._calculate_total_duration()
        
        self.cancellation_fee = cancellation_fee or Decimal("0.00")
        self.quality_rating = quality_rating
        self.quality_feedback = quality_feedback
        self.actual_start_time = actual_start_time
        self.actual_end_time = actual_end_time
        self.created_at = created_at or utc_now()
        self.updated_at = updated_at or utc_now()
        
        # Validate calculated totals
        self._validate_totals()
    
    def _validate_booking_type_constraints(self, booking_type: BookingType, customer_location: Optional[dict], vehicle_size: str) -> None:
        """Validate booking type specific constraints"""
        if booking_type == BookingType.MOBILE:
            if not customer_location:
                raise ValueError("Customer location is required for mobile bookings")
            if not isinstance(customer_location, dict) or 'lat' not in customer_location or 'lng' not in customer_location:
                raise ValueError("Customer location must contain 'lat' and 'lng' coordinates")
        elif booking_type == BookingType.IN_HOME:
            # For in-home bookings, customer_location should be None or facility location
            if customer_location:
                # Log warning that customer location is ignored for in-home bookings
                pass
        
        # Validate vehicle size
        valid_sizes = ["compact", "standard", "large", "oversized"]
        if vehicle_size not in valid_sizes:
            raise ValueError(f"Vehicle size must be one of: {valid_sizes}")
    
    def _validate_services(self, services: List[BookingService]) -> None:
        """Validate services business rules"""
        if not services:
            raise ValueError("At least one service must be selected")
        
        if len(services) < self.MIN_SERVICES:
            raise ValueError(f"Minimum {self.MIN_SERVICES} service required")
        
        if len(services) > self.MAX_SERVICES:
            raise ValueError(f"Maximum {self.MAX_SERVICES} services allowed")
        
        # Check for duplicate services
        service_ids = [service.service_id for service in services]
        if len(service_ids) != len(set(service_ids)):
            raise ValueError("Duplicate services are not allowed")
    
    def _validate_scheduled_time(self, scheduled_at: datetime) -> None:
        """Validate scheduling time business rules"""
        from src.shared.utils.timezone_handler import RobustTimezoneHandler, safe_datetime_compare
        
        now = utc_now()
        
        # Use robust timezone comparison
        if not safe_datetime_compare(now, scheduled_at):
            raise ValueError("Cannot schedule appointments in the past")
        
        max_advance_time = now + timedelta(days=self.MAX_ADVANCE_DAYS)
        if not safe_datetime_compare(scheduled_at, max_advance_time):
            raise ValueError(f"Cannot schedule more than {self.MAX_ADVANCE_DAYS} days in advance")
    
    def _validate_totals(self) -> None:
        """Validate calculated totals against business limits"""
        if self.total_duration < self.MIN_TOTAL_DURATION:
            raise ValueError(f"Total duration must be at least {self.MIN_TOTAL_DURATION} minutes")
        
        if self.total_duration > self.MAX_TOTAL_DURATION:
            raise ValueError(f"Total duration cannot exceed {self.MAX_TOTAL_DURATION} minutes")
        
        if self.total_price < self.MIN_PRICE:
            raise ValueError(f"Total price must be at least ${self.MIN_PRICE}")
        
        if self.total_price > self.MAX_PRICE:
            raise ValueError(f"Total price cannot exceed ${self.MAX_PRICE}")
    
    def _calculate_total_price(self) -> Decimal:
        """Calculate total price from all services"""
        return sum(service.price for service in self.services)
    
    def _calculate_total_duration(self) -> int:
        """Calculate total duration from all services"""
        return sum(service.duration for service in self.services)
    
    def confirm(self) -> None:
        """Confirm a pending booking"""
        if self.status != BookingStatus.PENDING:
            raise ValueError(f"Can only confirm pending bookings, current status: {self.status.value}")
        
        self.status = BookingStatus.CONFIRMED
        self.updated_at = utc_now()
    
    def start_service(self) -> None:
        """Start the service (mark as in progress)"""
        if self.status != BookingStatus.CONFIRMED:
            raise ValueError(f"Can only start confirmed bookings, current status: {self.status.value}")
        
        self.status = BookingStatus.IN_PROGRESS
        self.actual_start_time = utc_now()
        self.updated_at = utc_now()
    
    def complete_service(self, actual_end_time: Optional[datetime] = None) -> None:
        """Complete the service"""
        if self.status != BookingStatus.IN_PROGRESS:
            raise ValueError(f"Can only complete in-progress bookings, current status: {self.status.value}")
        
        self.status = BookingStatus.COMPLETED
        self.actual_end_time = actual_end_time or utc_now()
        self.updated_at = utc_now()
    
    def cancel(self, cancellation_time: Optional[datetime] = None) -> None:
        """Cancel the booking with appropriate fee calculation"""
        if self.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED, BookingStatus.NO_SHOW]:
            raise ValueError(f"Cannot cancel booking with status: {self.status.value}")
        
        cancel_time = cancellation_time or utc_now()
        self.cancellation_fee = self._calculate_cancellation_fee(cancel_time)
        self.status = BookingStatus.CANCELLED
        self.updated_at = utc_now()
    
    def mark_no_show(self) -> None:
        """Mark booking as no-show with full fee penalty"""
        if self.status not in [BookingStatus.CONFIRMED]:
            raise ValueError(f"Can only mark confirmed bookings as no-show, current status: {self.status.value}")
        
        self.status = BookingStatus.NO_SHOW
        self.cancellation_fee = self.total_price  # Full fee for no-show
        self.updated_at = utc_now()
    
    def reschedule(self, new_scheduled_at: datetime) -> None:
        """Reschedule the booking to a new time"""
        if self.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            raise ValueError(f"Can only reschedule pending or confirmed bookings, current status: {self.status.value}")
        
        # Validate new time
        self._validate_scheduled_time(new_scheduled_at)
        
        # Check minimum notice requirement
        now = utc_now()
        notice_hours = (new_scheduled_at - now).total_seconds() / 3600
        if notice_hours < self.MIN_RESCHEDULE_NOTICE_HOURS:
            raise ValueError(f"Minimum {self.MIN_RESCHEDULE_NOTICE_HOURS} hours notice required for rescheduling")
        
        self.scheduled_at = new_scheduled_at
        self.updated_at = utc_now()
    
    def rate_quality(self, rating: QualityRating, feedback: Optional[str] = None) -> None:
        """Rate the service quality (only after completion)"""
        if self.status != BookingStatus.COMPLETED:
            raise ValueError("Can only rate completed services")
        
        self.quality_rating = rating
        self.quality_feedback = feedback
        self.updated_at = utc_now()
    
    def add_service(self, service: BookingService) -> None:
        """Add a service to the booking (only for pending bookings)"""
        if self.status != BookingStatus.PENDING:
            raise ValueError("Can only modify services for pending bookings")
        
        if len(self.services) >= self.MAX_SERVICES:
            raise ValueError(f"Maximum {self.MAX_SERVICES} services allowed")
        
        if service in self.services:
            raise ValueError("Service already exists in booking")
        
        self.services.append(service)
        self.total_price = self._calculate_total_price()
        self.total_duration = self._calculate_total_duration()
        self._validate_totals()
        self.updated_at = utc_now()
    
    def remove_service(self, service_id: UUID) -> None:
        """Remove a service from the booking (only for pending bookings)"""
        if self.status != BookingStatus.PENDING:
            raise ValueError("Can only modify services for pending bookings")
        
        if len(self.services) <= self.MIN_SERVICES:
            raise ValueError(f"Minimum {self.MIN_SERVICES} service required")
        
        original_count = len(self.services)
        self.services = [s for s in self.services if s.service_id != service_id]
        if len(self.services) == original_count:
            raise ValueError("Service not found in booking")
        
        self.total_price = self._calculate_total_price()
        self.total_duration = self._calculate_total_duration()
        self.updated_at = utc_now()
    
    def _calculate_cancellation_fee(self, cancellation_time: datetime) -> Decimal:
        """Calculate cancellation fee based on notice period"""
        notice_hours = (self.scheduled_at - cancellation_time).total_seconds() / 3600
        
        if notice_hours > 24:
            return Decimal("0.00")  # Free cancellation
        elif notice_hours > 6:
            return self.total_price * Decimal("0.25")  # 25% fee
        elif notice_hours > 2:
            return self.total_price * Decimal("0.50")  # 50% fee
        else:
            return self.total_price  # 100% fee
    
    def get_cancellation_policy(self, cancellation_time: Optional[datetime] = None) -> CancellationPolicy:
        """Get the cancellation policy that would apply"""
        cancel_time = cancellation_time or utc_now()
        notice_hours = (self.scheduled_at - cancel_time).total_seconds() / 3600
        
        if notice_hours > 24:
            return CancellationPolicy.FREE
        elif notice_hours > 6:
            return CancellationPolicy.QUARTER_FEE
        elif notice_hours > 2:
            return CancellationPolicy.HALF_FEE
        else:
            return CancellationPolicy.FULL_FEE
    
    def is_no_show_eligible(self, current_time: Optional[datetime] = None) -> bool:
        """Check if booking is eligible to be marked as no-show"""
        now = current_time or utc_now()
        grace_period_end = self.scheduled_at + timedelta(minutes=self.GRACE_PERIOD_MINUTES)
        
        return (
            self.status == BookingStatus.CONFIRMED and
            now > grace_period_end
        )
    
    def get_expected_end_time(self) -> datetime:
        """Get expected end time based on scheduled time and duration"""
        return self.scheduled_at + timedelta(minutes=self.total_duration)
    
    def calculate_overtime_charge(self) -> Decimal:
        """Calculate overtime charges if service exceeded expected duration"""
        if not self.actual_end_time or not self.actual_start_time:
            return Decimal("0.00")
        
        actual_duration_minutes = (self.actual_end_time - self.actual_start_time).total_seconds() / 60
        if actual_duration_minutes <= self.total_duration:
            return Decimal("0.00")
        
        overtime_minutes = int(actual_duration_minutes - self.total_duration)
        return overtime_minutes * self.OVERTIME_CHARGE_PER_MINUTE
    
    @property
    def is_active(self) -> bool:
        """Check if booking is in an active state"""
        return self.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS]
    
    @property
    def is_completed(self) -> bool:
        """Check if booking is completed"""
        return self.status == BookingStatus.COMPLETED
    
    @property
    def is_cancelled(self) -> bool:
        """Check if booking is cancelled"""
        return self.status in [BookingStatus.CANCELLED, BookingStatus.NO_SHOW]
    
    @property
    def can_be_modified(self) -> bool:
        """Check if booking can be modified"""
        return self.status == BookingStatus.PENDING
    
    @property
    def can_be_rated(self) -> bool:
        """Check if booking can be rated"""
        return self.status == BookingStatus.COMPLETED and self.quality_rating is None
    
    @property
    def service_ids(self) -> List[UUID]:
        """Get list of service IDs"""
        return [service.service_id for service in self.services]
    
    @property
    def requires_wash_bay(self) -> bool:
        """Check if booking requires a wash bay (in-home type)"""
        return self.booking_type == BookingType.IN_HOME
    
    @property
    def requires_mobile_team(self) -> bool:
        """Check if booking requires a mobile team"""
        return self.booking_type == BookingType.MOBILE
    
    def get_resource_constraints(self) -> dict:
        """Get resource constraints based on booking type"""
        constraints = {
            "booking_type": self.booking_type.value,
            "vehicle_size": self.vehicle_size,
        }
        
        if self.booking_type == BookingType.MOBILE:
            constraints["customer_location"] = self.customer_location
            constraints["requires_mobile_team"] = True
            constraints["requires_wash_bay"] = False
        else:  # IN_HOME
            constraints["requires_mobile_team"] = False
            constraints["requires_wash_bay"] = True
            
        return constraints
    
    def __str__(self) -> str:
        return f"Booking(id={self.id}, customer={self.customer_id}, type={self.booking_type.value}, status={self.status.value}, scheduled={self.scheduled_at})"