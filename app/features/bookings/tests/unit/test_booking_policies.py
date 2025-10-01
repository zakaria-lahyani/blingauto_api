import pytest
from datetime import datetime, timedelta

from app.core.errors import ValidationError, BusinessRuleViolationError
from app.features.bookings.domain import (
    Booking,
    BookingService,
    BookingType,
    BookingStatus,
)
from app.features.bookings.domain.policies import (
    BookingValidationPolicy,
    BookingSchedulingPolicy,
    BookingCancellationPolicy,
)


class TestBookingValidationPolicy:
    """Test booking validation policy."""
    
    def test_validate_booking_creation_success(self, sample_booking):
        """Test successful booking creation validation."""
        # Should not raise any exception
        BookingValidationPolicy.validate_booking_creation(sample_booking)
    
    def test_validate_booking_creation_fails_invalid_customer(self, sample_booking_services):
        """Test booking creation validation fails with invalid customer."""
        scheduled_time = datetime.now() + timedelta(hours=24)
        
        with pytest.raises(ValidationError, match="Customer ID cannot be empty"):
            booking = Booking.create(
                customer_id="",
                vehicle_id="vehicle_123",
                services=sample_booking_services,
                scheduled_at=scheduled_time,
                booking_type=BookingType.SCHEDULED,
            )
            BookingValidationPolicy.validate_booking_creation(booking)
    
    def test_validate_booking_creation_fails_invalid_vehicle(self, sample_booking_services):
        """Test booking creation validation fails with invalid vehicle."""
        scheduled_time = datetime.now() + timedelta(hours=24)
        
        with pytest.raises(ValidationError, match="Vehicle ID cannot be empty"):
            booking = Booking.create(
                customer_id="customer_123",
                vehicle_id="",
                services=sample_booking_services,
                scheduled_at=scheduled_time,
                booking_type=BookingType.SCHEDULED,
            )
            BookingValidationPolicy.validate_booking_creation(booking)
    
    def test_validate_booking_update_allowed_success(self, sample_booking):
        """Test booking update validation allows pending bookings."""
        # Should not raise any exception
        BookingValidationPolicy.validate_booking_update_allowed(sample_booking)
    
    def test_validate_booking_update_allowed_fails_completed(self, sample_booking):
        """Test booking update validation fails for completed bookings."""
        sample_booking.confirm()
        sample_booking.complete()
        
        with pytest.raises(BusinessRuleViolationError, match="cannot be updated"):
            BookingValidationPolicy.validate_booking_update_allowed(sample_booking)
    
    def test_validate_booking_update_allowed_fails_cancelled(self, sample_booking):
        """Test booking update validation fails for cancelled bookings."""
        sample_booking.cancel("customer_123", "Cancelled")
        
        with pytest.raises(BusinessRuleViolationError, match="cannot be updated"):
            BookingValidationPolicy.validate_booking_update_allowed(sample_booking)
    
    def test_validate_service_requirements_success(self, sample_booking_services):
        """Test service requirements validation success."""
        # Should not raise any exception
        BookingValidationPolicy.validate_service_requirements(sample_booking_services)
    
    def test_validate_service_requirements_fails_empty(self):
        """Test service requirements validation fails with empty services."""
        with pytest.raises(ValidationError, match="at least one service"):
            BookingValidationPolicy.validate_service_requirements([])
    
    def test_validate_service_requirements_fails_too_many(self):
        """Test service requirements validation fails with too many services."""
        too_many_services = [
            BookingService(f"service_{i}", f"Service {i}", 10.0, 15)
            for i in range(11)
        ]
        
        with pytest.raises(ValidationError, match="maximum of 10 services"):
            BookingValidationPolicy.validate_service_requirements(too_many_services)
    
    def test_validate_service_requirements_fails_invalid_price(self):
        """Test service requirements validation fails with invalid price."""
        invalid_service = BookingService("service_1", "Service", -10.0, 30)
        
        with pytest.raises(ValidationError, match="Service price must be positive"):
            BookingValidationPolicy.validate_service_requirements([invalid_service])
    
    def test_validate_service_requirements_fails_invalid_duration(self):
        """Test service requirements validation fails with invalid duration."""
        invalid_service = BookingService("service_1", "Service", 25.0, 0)
        
        with pytest.raises(ValidationError, match="Service duration must be positive"):
            BookingValidationPolicy.validate_service_requirements([invalid_service])


class TestBookingSchedulingPolicy:
    """Test booking scheduling policy."""
    
    def test_validate_scheduling_constraints_success(self, sample_booking):
        """Test scheduling constraints validation success."""
        conflicting_bookings = []
        
        # Should not raise any exception
        BookingSchedulingPolicy.validate_scheduling_constraints(
            sample_booking, conflicting_bookings
        )
    
    def test_validate_scheduling_constraints_fails_conflict(self, sample_booking):
        """Test scheduling constraints validation fails with conflicts."""
        # Create a conflicting booking
        conflicting_booking = Booking.create(
            customer_id="other_customer",
            vehicle_id="other_vehicle",
            services=[BookingService("service_1", "Service", 25.0, 30)],
            scheduled_at=sample_booking.scheduled_at,
            booking_type=BookingType.SCHEDULED,
        )
        
        with pytest.raises(BusinessRuleViolationError, match="conflicts with existing booking"):
            BookingSchedulingPolicy.validate_scheduling_constraints(
                sample_booking, [conflicting_booking]
            )
    
    def test_validate_future_scheduling_success(self, sample_booking):
        """Test future scheduling validation success."""
        # Should not raise any exception
        BookingSchedulingPolicy.validate_future_scheduling(sample_booking.scheduled_at)
    
    def test_validate_future_scheduling_fails_past_time(self):
        """Test future scheduling validation fails with past time."""
        past_time = datetime.now() - timedelta(hours=1)
        
        with pytest.raises(ValidationError, match="must be in the future"):
            BookingSchedulingPolicy.validate_future_scheduling(past_time)
    
    def test_validate_business_hours_success(self):
        """Test business hours validation success."""
        # Monday 10 AM
        business_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        # Ensure it's a weekday
        while business_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
            business_time += timedelta(days=1)
        
        # Should not raise any exception
        BookingSchedulingPolicy.validate_business_hours(business_time)
    
    def test_validate_business_hours_fails_weekend(self):
        """Test business hours validation fails on weekend."""
        # Get next Saturday
        now = datetime.now()
        days_until_saturday = (5 - now.weekday()) % 7
        if days_until_saturday == 0 and now.weekday() == 5:
            days_until_saturday = 0
        elif days_until_saturday == 0:
            days_until_saturday = 7
        
        saturday = now + timedelta(days=days_until_saturday)
        saturday = saturday.replace(hour=10, minute=0, second=0, microsecond=0)
        
        with pytest.raises(ValidationError, match="not available on weekends"):
            BookingSchedulingPolicy.validate_business_hours(saturday)
    
    def test_validate_business_hours_fails_early_morning(self):
        """Test business hours validation fails for early morning."""
        # Monday 6 AM
        early_time = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
        # Ensure it's a weekday
        while early_time.weekday() >= 5:
            early_time += timedelta(days=1)
        
        with pytest.raises(ValidationError, match="only available between"):
            BookingSchedulingPolicy.validate_business_hours(early_time)
    
    def test_validate_business_hours_fails_late_evening(self):
        """Test business hours validation fails for late evening."""
        # Monday 10 PM
        late_time = datetime.now().replace(hour=22, minute=0, second=0, microsecond=0)
        # Ensure it's a weekday
        while late_time.weekday() >= 5:
            late_time += timedelta(days=1)
        
        with pytest.raises(ValidationError, match="only available between"):
            BookingSchedulingPolicy.validate_business_hours(late_time)
    
    def test_validate_advance_booking_time_success(self):
        """Test advance booking time validation success."""
        future_time = datetime.now() + timedelta(hours=2)
        
        # Should not raise any exception
        BookingSchedulingPolicy.validate_advance_booking_time(future_time, BookingType.SCHEDULED)
    
    def test_validate_advance_booking_time_fails_too_soon(self):
        """Test advance booking time validation fails when too soon."""
        soon_time = datetime.now() + timedelta(minutes=30)
        
        with pytest.raises(ValidationError, match="at least 1 hour in advance"):
            BookingSchedulingPolicy.validate_advance_booking_time(soon_time, BookingType.SCHEDULED)
    
    def test_validate_advance_booking_time_allows_walk_in(self):
        """Test advance booking time allows walk-in bookings soon."""
        soon_time = datetime.now() + timedelta(minutes=15)
        
        # Should not raise any exception for walk-in
        BookingSchedulingPolicy.validate_advance_booking_time(soon_time, BookingType.WALK_IN)


class TestBookingCancellationPolicy:
    """Test booking cancellation policy."""
    
    def test_validate_cancellation_allowed_success(self, sample_booking):
        """Test cancellation validation allows pending bookings."""
        # Should not raise any exception
        BookingCancellationPolicy.validate_cancellation_allowed(sample_booking)
    
    def test_validate_cancellation_allowed_success_confirmed(self, sample_booking):
        """Test cancellation validation allows confirmed bookings."""
        sample_booking.confirm()
        
        # Should not raise any exception
        BookingCancellationPolicy.validate_cancellation_allowed(sample_booking)
    
    def test_validate_cancellation_allowed_fails_completed(self, sample_booking):
        """Test cancellation validation fails for completed bookings."""
        sample_booking.confirm()
        sample_booking.complete()
        
        with pytest.raises(BusinessRuleViolationError, match="cannot be cancelled"):
            BookingCancellationPolicy.validate_cancellation_allowed(sample_booking)
    
    def test_validate_cancellation_allowed_fails_already_cancelled(self, sample_booking):
        """Test cancellation validation fails for already cancelled bookings."""
        sample_booking.cancel("customer_123", "Already cancelled")
        
        with pytest.raises(BusinessRuleViolationError, match="cannot be cancelled"):
            BookingCancellationPolicy.validate_cancellation_allowed(sample_booking)
    
    def test_calculate_refund_amount_full_refund(self, sample_booking):
        """Test refund calculation for full refund (24+ hours before)."""
        # Booking is 24 hours in the future
        refund_amount = BookingCancellationPolicy.calculate_refund_amount(sample_booking)
        
        # Should get full refund
        assert refund_amount == sample_booking.total_price
    
    def test_calculate_refund_amount_partial_refund(self, sample_booking):
        """Test refund calculation for partial refund (2-24 hours before)."""
        # Reschedule to 4 hours in the future
        new_time = datetime.now() + timedelta(hours=4)
        sample_booking.reschedule(new_time)
        
        refund_amount = BookingCancellationPolicy.calculate_refund_amount(sample_booking)
        
        # Should get 50% refund
        expected_refund = sample_booking.total_price * 0.5
        assert refund_amount == expected_refund
    
    def test_calculate_refund_amount_no_refund(self, sample_booking):
        """Test refund calculation for no refund (less than 2 hours before)."""
        # Reschedule to 1 hour in the future
        new_time = datetime.now() + timedelta(hours=1)
        sample_booking.reschedule(new_time)
        
        refund_amount = BookingCancellationPolicy.calculate_refund_amount(sample_booking)
        
        # Should get no refund
        assert refund_amount == 0.0
    
    def test_validate_cancellation_timing_success(self, sample_booking):
        """Test cancellation timing validation success."""
        # Should not raise any exception (booking is 24+ hours away)
        BookingCancellationPolicy.validate_cancellation_timing(sample_booking)
    
    def test_validate_cancellation_timing_warns_no_refund(self, sample_booking):
        """Test cancellation timing validation warns about no refund."""
        # Reschedule to 1 hour in the future
        new_time = datetime.now() + timedelta(hours=1)
        sample_booking.reschedule(new_time)
        
        # Should not raise exception but would warn in real implementation
        # For testing, we just ensure it doesn't fail
        BookingCancellationPolicy.validate_cancellation_timing(sample_booking)
    
    def test_get_cancellation_fee_no_fee(self, sample_booking):
        """Test cancellation fee calculation for no fee."""
        fee = BookingCancellationPolicy.get_cancellation_fee(sample_booking)
        
        # 24+ hours before, no fee
        assert fee == 0.0
    
    def test_get_cancellation_fee_partial_fee(self, sample_booking):
        """Test cancellation fee calculation for partial fee."""
        # Reschedule to 4 hours in the future
        new_time = datetime.now() + timedelta(hours=4)
        sample_booking.reschedule(new_time)
        
        fee = BookingCancellationPolicy.get_cancellation_fee(sample_booking)
        
        # 2-24 hours before, 50% fee
        expected_fee = sample_booking.total_price * 0.5
        assert fee == expected_fee
    
    def test_get_cancellation_fee_full_fee(self, sample_booking):
        """Test cancellation fee calculation for full fee."""
        # Reschedule to 1 hour in the future
        new_time = datetime.now() + timedelta(hours=1)
        sample_booking.reschedule(new_time)
        
        fee = BookingCancellationPolicy.get_cancellation_fee(sample_booking)
        
        # Less than 2 hours before, full fee (100%)
        assert fee == sample_booking.total_price