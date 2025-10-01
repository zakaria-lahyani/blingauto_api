from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Tuple

from .exceptions import BusinessRuleViolationError, ValidationError
from .entities import BookingStatus, BookingType, VehicleSize


class BookingValidationPolicy:
    """
    Booking validation policies implementing business rules.
    RG-BOK-001 to RG-BOK-004: Service and time constraints
    """
    
    MIN_SERVICES = 1
    MAX_SERVICES = 10
    MIN_TOTAL_DURATION = 30  # minutes
    MAX_TOTAL_DURATION = 240  # minutes (4 hours)
    MIN_PRICE = Decimal("0.00")
    MAX_PRICE = Decimal("10000.00")
    MAX_ADVANCE_DAYS = 90
    MIN_ADVANCE_HOURS = 2
    
    @staticmethod
    def validate_service_count(service_count: int) -> bool:
        """Validate number of services - RG-BOK-001"""
        if service_count < BookingValidationPolicy.MIN_SERVICES:
            raise ValidationError(
                f"Minimum {BookingValidationPolicy.MIN_SERVICES} service required"
            )
        
        if service_count > BookingValidationPolicy.MAX_SERVICES:
            raise ValidationError(
                f"Maximum {BookingValidationPolicy.MAX_SERVICES} services allowed"
            )
        
        return True
    
    @staticmethod
    def validate_duration_limits(total_duration: int) -> bool:
        """Validate total duration limits - RG-BOK-002"""
        if total_duration < BookingValidationPolicy.MIN_TOTAL_DURATION:
            raise ValidationError(
                f"Total duration must be at least {BookingValidationPolicy.MIN_TOTAL_DURATION} minutes"
            )
        
        if total_duration > BookingValidationPolicy.MAX_TOTAL_DURATION:
            raise ValidationError(
                f"Total duration cannot exceed {BookingValidationPolicy.MAX_TOTAL_DURATION} minutes"
            )
        
        return True
    
    @staticmethod
    def validate_price_limits(total_price: Decimal) -> bool:
        """Validate total price limits - RG-BOK-003"""
        if total_price < BookingValidationPolicy.MIN_PRICE:
            raise ValidationError(
                f"Total price must be at least ${BookingValidationPolicy.MIN_PRICE}"
            )
        
        if total_price > BookingValidationPolicy.MAX_PRICE:
            raise ValidationError(
                f"Total price cannot exceed ${BookingValidationPolicy.MAX_PRICE}"
            )
        
        return True
    
    @staticmethod
    def validate_scheduling_time(scheduled_at: datetime) -> bool:
        """Validate scheduling time constraints - RG-BOK-004"""
        now = datetime.utcnow()
        
        # Cannot schedule in the past
        if scheduled_at <= now:
            raise ValidationError("Cannot schedule appointments in the past")
        
        # Check minimum advance notice
        min_advance_time = now + timedelta(hours=BookingValidationPolicy.MIN_ADVANCE_HOURS)
        if scheduled_at < min_advance_time:
            raise ValidationError(
                f"Booking must be scheduled at least {BookingValidationPolicy.MIN_ADVANCE_HOURS} hours in advance"
            )
        
        # Check maximum advance notice
        max_advance_time = now + timedelta(days=BookingValidationPolicy.MAX_ADVANCE_DAYS)
        if scheduled_at > max_advance_time:
            raise ValidationError(
                f"Cannot schedule more than {BookingValidationPolicy.MAX_ADVANCE_DAYS} days in advance"
            )
        
        return True


class BookingTypePolicy:
    """
    Booking type specific policies.
    RG-BOK-005: Mobile bookings, RG-BOK-006: Stationary bookings, RG-BOK-007: Vehicle sizes
    """
    
    VALID_VEHICLE_SIZES = [size.value for size in VehicleSize]
    
    @staticmethod
    def validate_mobile_booking(customer_location: dict) -> bool:
        """Validate mobile booking requirements - RG-BOK-005"""
        if not customer_location:
            raise ValidationError("Customer location is required for mobile bookings")
        
        if not isinstance(customer_location, dict):
            raise ValidationError("Customer location must be a dictionary")
        
        if "lat" not in customer_location or "lng" not in customer_location:
            raise ValidationError(
                "Customer location must contain 'lat' and 'lng' coordinates"
            )
        
        # Validate coordinate types and ranges
        try:
            lat = float(customer_location["lat"])
            lng = float(customer_location["lng"])
            
            if not (-90 <= lat <= 90):
                raise ValidationError("Latitude must be between -90 and 90")
            
            if not (-180 <= lng <= 180):
                raise ValidationError("Longitude must be between -180 and 180")
            
        except (ValueError, TypeError):
            raise ValidationError("Coordinates must be valid numbers")
        
        return True
    
    @staticmethod
    def validate_stationary_booking() -> bool:
        """Validate stationary booking requirements - RG-BOK-006"""
        # Stationary bookings don't require customer location
        # They use the facility's wash bay resources
        return True
    
    @staticmethod
    def validate_vehicle_size(vehicle_size: str) -> bool:
        """Validate vehicle size - RG-BOK-007"""
        if vehicle_size not in BookingTypePolicy.VALID_VEHICLE_SIZES:
            raise ValidationError(
                f"Vehicle size must be one of: {BookingTypePolicy.VALID_VEHICLE_SIZES}"
            )
        
        return True


class BookingStateTransitionPolicy:
    """
    Booking state transition policies.
    RG-BOK-008: Booking states, RG-BOK-009: State transitions
    """
    
    # Valid state transitions
    ALLOWED_TRANSITIONS = {
        BookingStatus.PENDING: [BookingStatus.CONFIRMED, BookingStatus.CANCELLED],
        BookingStatus.CONFIRMED: [BookingStatus.IN_PROGRESS, BookingStatus.CANCELLED, BookingStatus.NO_SHOW],
        BookingStatus.IN_PROGRESS: [BookingStatus.COMPLETED],
        BookingStatus.COMPLETED: [],  # Terminal state
        BookingStatus.CANCELLED: [],  # Terminal state
        BookingStatus.NO_SHOW: [],   # Terminal state
    }
    
    @staticmethod
    def can_transition(from_status: BookingStatus, to_status: BookingStatus) -> bool:
        """Check if state transition is allowed - RG-BOK-009"""
        allowed = BookingStateTransitionPolicy.ALLOWED_TRANSITIONS.get(from_status, [])
        return to_status in allowed
    
    @staticmethod
    def validate_transition(from_status: BookingStatus, to_status: BookingStatus) -> bool:
        """Validate state transition with proper error - RG-BOK-009"""
        if not BookingStateTransitionPolicy.can_transition(from_status, to_status):
            raise BusinessRuleViolationError(
                f"Cannot transition from {from_status.value} to {to_status.value}",
                rule="RG-BOK-009"
            )
        
        return True


class CancellationPolicy:
    """
    Cancellation fee calculation policy.
    RG-BOK-010: Cancellation fee rules
    """
    
    @staticmethod
    def calculate_cancellation_fee(
        scheduled_at: datetime,
        total_price: Decimal,
        cancellation_time: datetime = None
    ) -> Decimal:
        """
        Calculate cancellation fee based on time until appointment.
        RG-BOK-010: Cancellation fee schedule
        """
        if cancellation_time is None:
            cancellation_time = datetime.utcnow()
        
        time_until = scheduled_at - cancellation_time
        
        if time_until.total_seconds() < 0:
            # Past due - 100% fee
            return total_price
        
        hours_until = time_until.total_seconds() / 3600
        
        if hours_until < 2:
            # Less than 2 hours - 100%
            return total_price
        elif hours_until < 6:
            # 2-6 hours - 50%
            return total_price * Decimal("0.50")
        elif hours_until < 24:
            # 6-24 hours - 25%
            return total_price * Decimal("0.25")
        else:
            # More than 24 hours - 0%
            return Decimal("0.00")
    
    @staticmethod
    def get_cancellation_fee_percentage(hours_until: float) -> int:
        """Get cancellation fee percentage for display purposes."""
        if hours_until < 2:
            return 100
        elif hours_until < 6:
            return 50
        elif hours_until < 24:
            return 25
        else:
            return 0


class NoShowPolicy:
    """
    No-show handling policy.
    RG-BOK-011: No-show management
    """
    
    GRACE_PERIOD_MINUTES = 30
    NO_SHOW_FEE_PERCENTAGE = 100  # 100% of booking price
    
    @staticmethod
    def can_mark_no_show(scheduled_at: datetime, current_time: datetime = None) -> bool:
        """Check if booking can be marked as no-show - RG-BOK-011"""
        if current_time is None:
            current_time = datetime.utcnow()
        
        grace_end = scheduled_at + timedelta(minutes=NoShowPolicy.GRACE_PERIOD_MINUTES)
        return current_time >= grace_end
    
    @staticmethod
    def calculate_no_show_fee(total_price: Decimal) -> Decimal:
        """Calculate no-show fee - RG-BOK-011"""
        return total_price  # 100% fee for no-show


class ReschedulingPolicy:
    """
    Rescheduling policy.
    RG-BOK-012: Rescheduling constraints
    """
    
    MIN_RESCHEDULE_NOTICE_HOURS = 2
    
    @staticmethod
    def can_reschedule(
        current_status: BookingStatus,
        current_scheduled_at: datetime,
        new_scheduled_at: datetime,
        current_time: datetime = None
    ) -> bool:
        """Check if booking can be rescheduled - RG-BOK-012"""
        if current_time is None:
            current_time = datetime.utcnow()
        
        # Can only reschedule pending or confirmed bookings
        if current_status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            return False
        
        # Check minimum notice for new time
        min_notice_time = current_time + timedelta(hours=ReschedulingPolicy.MIN_RESCHEDULE_NOTICE_HOURS)
        return new_scheduled_at >= min_notice_time
    
    @staticmethod
    def validate_reschedule(
        current_status: BookingStatus,
        current_scheduled_at: datetime,
        new_scheduled_at: datetime,
        current_time: datetime = None
    ) -> bool:
        """Validate rescheduling with proper errors - RG-BOK-012"""
        if current_time is None:
            current_time = datetime.utcnow()
        
        if current_status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            raise BusinessRuleViolationError(
                "Can only reschedule pending or confirmed bookings",
                rule="RG-BOK-012"
            )
        
        min_notice_time = current_time + timedelta(hours=ReschedulingPolicy.MIN_RESCHEDULE_NOTICE_HOURS)
        if new_scheduled_at < min_notice_time:
            raise BusinessRuleViolationError(
                f"Rescheduling requires at least {ReschedulingPolicy.MIN_RESCHEDULE_NOTICE_HOURS} hours notice",
                rule="RG-BOK-012"
            )
        
        return True


class ServiceModificationPolicy:
    """
    Service modification policies.
    RG-BOK-013: Adding services, RG-BOK-014: Removing services
    """
    
    @staticmethod
    def can_add_service(current_status: BookingStatus, current_service_count: int) -> bool:
        """Check if service can be added - RG-BOK-013"""
        return (
            current_status == BookingStatus.PENDING and
            current_service_count < BookingValidationPolicy.MAX_SERVICES
        )
    
    @staticmethod
    def can_remove_service(current_status: BookingStatus, current_service_count: int) -> bool:
        """Check if service can be removed - RG-BOK-014"""
        return (
            current_status == BookingStatus.PENDING and
            current_service_count > BookingValidationPolicy.MIN_SERVICES
        )
    
    @staticmethod
    def validate_service_addition(current_status: BookingStatus, current_service_count: int) -> bool:
        """Validate service addition - RG-BOK-013"""
        if current_status != BookingStatus.PENDING:
            raise BusinessRuleViolationError(
                "Can only add services to pending bookings",
                rule="RG-BOK-013"
            )
        
        if current_service_count >= BookingValidationPolicy.MAX_SERVICES:
            raise BusinessRuleViolationError(
                f"Maximum {BookingValidationPolicy.MAX_SERVICES} services allowed",
                rule="RG-BOK-013"
            )
        
        return True
    
    @staticmethod
    def validate_service_removal(current_status: BookingStatus, current_service_count: int) -> bool:
        """Validate service removal - RG-BOK-014"""
        if current_status != BookingStatus.PENDING:
            raise BusinessRuleViolationError(
                "Can only remove services from pending bookings",
                rule="RG-BOK-014"
            )
        
        if current_service_count <= BookingValidationPolicy.MIN_SERVICES:
            raise BusinessRuleViolationError(
                f"Cannot remove service - minimum {BookingValidationPolicy.MIN_SERVICES} service required",
                rule="RG-BOK-014"
            )
        
        return True


class OvertimePolicy:
    """
    Overtime charges policy.
    RG-BOK-015: Overtime calculation
    """
    
    OVERTIME_CHARGE_PER_MINUTE = Decimal("1.00")
    
    @staticmethod
    def calculate_overtime_charges(
        expected_duration_minutes: int,
        actual_start_time: datetime,
        actual_end_time: datetime
    ) -> Decimal:
        """Calculate overtime charges - RG-BOK-015"""
        if not actual_start_time or not actual_end_time:
            return Decimal("0.00")
        
        actual_duration_seconds = (actual_end_time - actual_start_time).total_seconds()
        actual_duration_minutes = actual_duration_seconds / 60
        
        if actual_duration_minutes > expected_duration_minutes:
            overtime_minutes = actual_duration_minutes - expected_duration_minutes
            return Decimal(str(overtime_minutes)) * OvertimePolicy.OVERTIME_CHARGE_PER_MINUTE
        
        return Decimal("0.00")


class QualityRatingPolicy:
    """
    Quality rating policy.
    RG-BOK-016: Service quality rating
    """
    
    MAX_FEEDBACK_LENGTH = 1000
    
    @staticmethod
    def can_rate(current_status: BookingStatus, has_existing_rating: bool) -> bool:
        """Check if booking can be rated - RG-BOK-016"""
        return current_status == BookingStatus.COMPLETED and not has_existing_rating
    
    @staticmethod
    def validate_rating(
        current_status: BookingStatus,
        has_existing_rating: bool,
        feedback: str = None
    ) -> bool:
        """Validate quality rating - RG-BOK-016"""
        if current_status != BookingStatus.COMPLETED:
            raise BusinessRuleViolationError(
                "Can only rate completed bookings",
                rule="RG-BOK-016"
            )
        
        if has_existing_rating:
            raise BusinessRuleViolationError(
                "Booking has already been rated",
                rule="RG-BOK-016"
            )
        
        if feedback and len(feedback) > QualityRatingPolicy.MAX_FEEDBACK_LENGTH:
            raise ValidationError(
                f"Feedback cannot exceed {QualityRatingPolicy.MAX_FEEDBACK_LENGTH} characters"
            )
        
        return True


class BookingCancellationPolicy:
    """Combined policy for booking cancellation logic used by use cases."""
    
    @staticmethod
    def validate_cancellation_allowed(booking) -> bool:
        """Validate if booking can be cancelled."""
        if booking.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED, BookingStatus.NO_SHOW]:
            raise BusinessRuleViolationError(
                f"Cannot cancel booking with status: {booking.status.value}",
                rule="RG-BOK-009"
            )
        return True
    
    @staticmethod
    def calculate_refund_amount(booking) -> Decimal:
        """Calculate refund amount for cancelled booking."""
        return CancellationPolicy.calculate_cancellation_fee(
            booking.scheduled_at, booking.total_price
        )


class BookingSchedulingPolicy:
    """Combined policy for booking scheduling validation used by use cases."""
    
    @staticmethod
    def validate_scheduling_constraints(booking, conflicting_bookings: List) -> bool:
        """Validate scheduling constraints for booking."""
        # Check basic time validation
        BookingValidationPolicy.validate_scheduling_time(booking.scheduled_at)
        
        # Check for conflicts
        if conflicting_bookings:
            raise BusinessRuleViolationError(
                f"Time slot conflicts with existing booking at {booking.scheduled_at}",
                rule="RG-BOK-004"
            )
        
        # Check booking type specific constraints
        if booking.booking_type == BookingType.MOBILE:
            BookingTypePolicy.validate_mobile_booking(booking.customer_location)
        else:
            BookingTypePolicy.validate_stationary_booking()
        
        return True
    
    @staticmethod
    def validate_booking_creation(booking) -> bool:
        """Validate all constraints for creating a booking."""
        # Service validation
        BookingValidationPolicy.validate_service_count(len(booking.services))
        
        # Duration and price validation
        BookingValidationPolicy.validate_duration_limits(booking.estimated_duration_minutes)
        BookingValidationPolicy.validate_price_limits(booking.total_price)
        
        # Time validation
        BookingValidationPolicy.validate_scheduling_time(booking.scheduled_at)
        
        return True
    
    @staticmethod
    def validate_booking_update_allowed(booking) -> bool:
        """Validate if booking can be updated."""
        if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            raise BusinessRuleViolationError(
                f"Cannot update booking with status: {booking.status.value}",
                rule="RG-BOK-009"
            )
        return True