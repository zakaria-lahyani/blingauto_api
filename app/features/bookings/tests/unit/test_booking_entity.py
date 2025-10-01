import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.errors import ValidationError, BusinessRuleViolationError
from app.features.bookings.domain import (
    Booking,
    BookingService,
    BookingType,
    BookingStatus,
)


class TestBookingEntity:
    """Test booking entity business logic."""
    
    def test_create_booking_success(self, sample_booking_services):
        """Test successful booking creation."""
        scheduled_time = datetime.now() + timedelta(hours=24)
        
        booking = Booking.create(
            customer_id="customer_123",
            vehicle_id="vehicle_123",
            services=sample_booking_services,
            scheduled_at=scheduled_time,
            booking_type=BookingType.SCHEDULED,
            notes="Test booking",
            phone_number="+1234567890",
        )
        
        assert booking.customer_id == "customer_123"
        assert booking.vehicle_id == "vehicle_123"
        assert len(booking.services) == 2
        assert booking.status == BookingStatus.PENDING
        assert booking.booking_type == BookingType.SCHEDULED
        assert booking.total_price == 40.0  # 25.0 + 15.0
        assert booking.estimated_duration_minutes == 50  # 30 + 20
        assert booking.notes == "Test booking"
        assert booking.phone_number == "+1234567890"
        assert booking.created_at is not None
        assert booking.updated_at is not None
        assert booking.cancelled_at is None
    
    def test_create_booking_validates_services_count(self):
        """Test booking creation validates service count limits."""
        scheduled_time = datetime.now() + timedelta(hours=24)
        
        # Test minimum services
        with pytest.raises(ValidationError, match="at least 1 service"):
            Booking.create(
                customer_id="customer_123",
                vehicle_id="vehicle_123",
                services=[],
                scheduled_at=scheduled_time,
                booking_type=BookingType.SCHEDULED,
            )
        
        # Test maximum services
        too_many_services = [
            BookingService(f"service_{i}", f"Service {i}", 10.0, 15)
            for i in range(11)
        ]
        with pytest.raises(ValidationError, match="maximum of 10 services"):
            Booking.create(
                customer_id="customer_123",
                vehicle_id="vehicle_123",
                services=too_many_services,
                scheduled_at=scheduled_time,
                booking_type=BookingType.SCHEDULED,
            )
    
    def test_create_booking_validates_future_time(self, sample_booking_services):
        """Test booking creation validates future scheduling."""
        past_time = datetime.now() - timedelta(hours=1)
        
        with pytest.raises(ValidationError, match="must be in the future"):
            Booking.create(
                customer_id="customer_123",
                vehicle_id="vehicle_123",
                services=sample_booking_services,
                scheduled_at=past_time,
                booking_type=BookingType.SCHEDULED,
            )
    
    def test_create_booking_validates_phone_number(self, sample_booking_services):
        """Test booking creation validates phone number format."""
        scheduled_time = datetime.now() + timedelta(hours=24)
        
        with pytest.raises(ValidationError, match="Invalid phone number"):
            Booking.create(
                customer_id="customer_123",
                vehicle_id="vehicle_123",
                services=sample_booking_services,
                scheduled_at=scheduled_time,
                booking_type=BookingType.SCHEDULED,
                phone_number="invalid-phone",
            )
    
    def test_cancel_booking_success(self, sample_booking):
        """Test successful booking cancellation."""
        sample_booking.cancel("customer_123", "Customer request")
        
        assert sample_booking.status == BookingStatus.CANCELLED
        assert sample_booking.cancelled_by == "customer_123"
        assert sample_booking.cancellation_reason == "Customer request"
        assert sample_booking.cancelled_at is not None
        assert sample_booking.updated_at > sample_booking.created_at
    
    def test_cancel_booking_validates_status(self, sample_booking):
        """Test cancellation validation on booking status."""
        # Cancel the booking first
        sample_booking.cancel("customer_123", "First cancellation")
        
        # Try to cancel again
        with pytest.raises(BusinessRuleViolationError, match="cannot be cancelled"):
            sample_booking.cancel("customer_123", "Second cancellation")
    
    def test_confirm_booking_success(self, sample_booking):
        """Test successful booking confirmation."""
        sample_booking.confirm()
        
        assert sample_booking.status == BookingStatus.CONFIRMED
        assert sample_booking.updated_at > sample_booking.created_at
    
    def test_confirm_booking_validates_status(self, sample_booking):
        """Test confirmation validation on booking status."""
        sample_booking.cancel("customer_123", "Cancelled")
        
        with pytest.raises(BusinessRuleViolationError, match="cannot be confirmed"):
            sample_booking.confirm()
    
    def test_complete_booking_success(self, sample_booking):
        """Test successful booking completion."""
        sample_booking.confirm()  # Must be confirmed first
        sample_booking.complete()
        
        assert sample_booking.status == BookingStatus.COMPLETED
        assert sample_booking.updated_at > sample_booking.created_at
    
    def test_complete_booking_validates_status(self, sample_booking):
        """Test completion validation on booking status."""
        # Try to complete without confirming first
        with pytest.raises(BusinessRuleViolationError, match="cannot be completed"):
            sample_booking.complete()
    
    def test_reschedule_booking_success(self, sample_booking):
        """Test successful booking rescheduling."""
        new_time = datetime.now() + timedelta(hours=48)
        old_time = sample_booking.scheduled_at
        
        sample_booking.reschedule(new_time)
        
        assert sample_booking.scheduled_at == new_time
        assert sample_booking.scheduled_at != old_time
        assert sample_booking.updated_at > sample_booking.created_at
    
    def test_reschedule_booking_validates_future_time(self, sample_booking):
        """Test rescheduling validates future time."""
        past_time = datetime.now() - timedelta(hours=1)
        
        with pytest.raises(ValidationError, match="must be in the future"):
            sample_booking.reschedule(past_time)
    
    def test_reschedule_booking_validates_status(self, sample_booking):
        """Test rescheduling validation on booking status."""
        sample_booking.cancel("customer_123", "Cancelled")
        new_time = datetime.now() + timedelta(hours=48)
        
        with pytest.raises(BusinessRuleViolationError, match="cannot be rescheduled"):
            sample_booking.reschedule(new_time)
    
    def test_update_services_success(self, sample_booking):
        """Test successful services update."""
        new_services = [
            BookingService("service_new", "Premium Wash", 50.0, 60),
        ]
        
        sample_booking.update_services(new_services)
        
        assert len(sample_booking.services) == 1
        assert sample_booking.services[0].name == "Premium Wash"
        assert sample_booking.total_price == 50.0
        assert sample_booking.estimated_duration_minutes == 60
        assert sample_booking.updated_at > sample_booking.created_at
    
    def test_update_services_validates_count(self, sample_booking):
        """Test services update validates count limits."""
        with pytest.raises(ValidationError, match="at least 1 service"):
            sample_booking.update_services([])
    
    def test_update_services_validates_status(self, sample_booking):
        """Test services update validation on booking status."""
        sample_booking.confirm()
        sample_booking.complete()
        
        new_services = [
            BookingService("service_new", "New Service", 30.0, 45),
        ]
        
        with pytest.raises(BusinessRuleViolationError, match="cannot be modified"):
            sample_booking.update_services(new_services)
    
    def test_update_notes_success(self, sample_booking):
        """Test successful notes update."""
        new_notes = "Updated notes for the booking"
        
        sample_booking.update_notes(new_notes)
        
        assert sample_booking.notes == new_notes
        assert sample_booking.updated_at > sample_booking.created_at
    
    def test_update_phone_number_success(self, sample_booking):
        """Test successful phone number update."""
        new_phone = "+9876543210"
        
        sample_booking.update_phone_number(new_phone)
        
        assert sample_booking.phone_number == new_phone
        assert sample_booking.updated_at > sample_booking.created_at
    
    def test_update_phone_number_validates_format(self, sample_booking):
        """Test phone number update validates format."""
        with pytest.raises(ValidationError, match="Invalid phone number"):
            sample_booking.update_phone_number("invalid-phone")
    
    def test_booking_equality(self, sample_booking_services):
        """Test booking equality comparison."""
        scheduled_time = datetime.now() + timedelta(hours=24)
        
        booking1 = Booking.create(
            customer_id="customer_123",
            vehicle_id="vehicle_123",
            services=sample_booking_services,
            scheduled_at=scheduled_time,
            booking_type=BookingType.SCHEDULED,
        )
        
        booking2 = Booking.create(
            customer_id="customer_456",
            vehicle_id="vehicle_456",
            services=sample_booking_services,
            scheduled_at=scheduled_time,
            booking_type=BookingType.SCHEDULED,
        )
        
        # Same booking
        assert booking1 == booking1
        
        # Different bookings
        assert booking1 != booking2
        
        # Compare with non-booking object
        assert booking1 != "not_a_booking"
    
    def test_booking_hash(self, sample_booking):
        """Test booking hash implementation."""
        booking_hash = hash(sample_booking)
        assert isinstance(booking_hash, int)
        
        # Hash should be consistent
        assert hash(sample_booking) == booking_hash
    
    def test_walk_in_booking_special_handling(self):
        """Test walk-in booking special handling."""
        services = [
            BookingService("service_quick", "Quick Wash", 20.0, 15),
        ]
        
        # Walk-in bookings can be scheduled closer to current time
        near_future = datetime.now() + timedelta(minutes=5)
        
        booking = Booking.create(
            customer_id="customer_456",
            vehicle_id="vehicle_456",
            services=services,
            scheduled_at=near_future,
            booking_type=BookingType.WALK_IN,
        )
        
        assert booking.booking_type == BookingType.WALK_IN
        assert booking.scheduled_at == near_future
    
    def test_booking_service_validation(self):
        """Test booking service validation."""
        scheduled_time = datetime.now() + timedelta(hours=24)
        
        # Test invalid service price
        with pytest.raises(ValidationError):
            invalid_service = BookingService("service_1", "Service", -10.0, 30)
            Booking.create(
                customer_id="customer_123",
                vehicle_id="vehicle_123",
                services=[invalid_service],
                scheduled_at=scheduled_time,
                booking_type=BookingType.SCHEDULED,
            )
        
        # Test invalid service duration
        with pytest.raises(ValidationError):
            invalid_service = BookingService("service_1", "Service", 25.0, 0)
            Booking.create(
                customer_id="customer_123",
                vehicle_id="vehicle_123",
                services=[invalid_service],
                scheduled_at=scheduled_time,
                booking_type=BookingType.SCHEDULED,
            )