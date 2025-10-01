import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from app.core.errors import NotFoundError, ValidationError, BusinessRuleViolationError
from app.features.bookings.use_cases import CreateBookingUseCase, CreateBookingRequest
from app.features.bookings.domain import BookingType


class TestCreateBookingUseCase:
    """Test create booking use case."""
    
    @pytest.fixture
    def create_booking_use_case(
        self,
        mock_booking_repository,
        mock_service_repository,
        mock_vehicle_repository,
        mock_customer_repository,
        mock_notification_service,
        mock_event_service,
        mock_lock_service,
    ):
        """Create the use case with mocked dependencies."""
        return CreateBookingUseCase(
            booking_repository=mock_booking_repository,
            service_repository=mock_service_repository,
            vehicle_repository=mock_vehicle_repository,
            customer_repository=mock_customer_repository,
            notification_service=mock_notification_service,
            event_service=mock_event_service,
            lock_service=mock_lock_service,
        )
    
    @pytest.fixture
    def valid_create_request(self):
        """Create a valid booking creation request."""
        return CreateBookingRequest(
            customer_id="customer_123",
            vehicle_id="vehicle_123",
            service_ids=["service_1", "service_2"],
            scheduled_at=datetime.now() + timedelta(hours=24),
            booking_type="SCHEDULED",
            notes="Test booking",
            phone_number="+1234567890",
        )
    
    async def test_create_booking_success(
        self,
        create_booking_use_case,
        valid_create_request,
        sample_booking,
        sample_services_data,
        sample_customer_data,
        sample_vehicle_data,
        mock_booking_repository,
        mock_service_repository,
        mock_vehicle_repository,
        mock_customer_repository,
        mock_notification_service,
        mock_event_service,
        mock_lock_service,
    ):
        """Test successful booking creation."""
        # Setup mocks
        mock_customer_repository.exists.return_value = True
        mock_vehicle_repository.validate_customer_vehicle.return_value = True
        mock_service_repository.get_multiple_by_ids.return_value = sample_services_data
        mock_lock_service.acquire_time_slot_lock.return_value = "lock_123"
        mock_booking_repository.find_conflicting_bookings.return_value = []
        mock_booking_repository.create.return_value = sample_booking
        mock_customer_repository.get_by_id.return_value = sample_customer_data
        mock_vehicle_repository.get_by_id.return_value = sample_vehicle_data
        
        # Execute use case
        response = await create_booking_use_case.execute(valid_create_request)
        
        # Verify response
        assert response.booking_id == sample_booking.id
        assert response.status == sample_booking.status.value
        assert response.total_price == sample_booking.total_price
        assert response.estimated_duration == sample_booking.estimated_duration_minutes
        assert len(response.services) == len(sample_booking.services)
        
        # Verify repository calls
        mock_customer_repository.exists.assert_called_once_with("customer_123")
        mock_vehicle_repository.validate_customer_vehicle.assert_called_once_with(
            "customer_123", "vehicle_123"
        )
        mock_service_repository.get_multiple_by_ids.assert_called_once_with(
            ["service_1", "service_2"]
        )
        mock_booking_repository.create.assert_called_once()
        
        # Verify event and notification calls
        mock_event_service.publish_booking_created.assert_called_once_with(sample_booking)
        mock_notification_service.send_booking_confirmation.assert_called_once()
        
        # Verify lock management
        mock_lock_service.acquire_time_slot_lock.assert_called_once()
        mock_lock_service.release_lock.assert_called_once_with("lock_123")
    
    async def test_create_booking_fails_customer_not_found(
        self,
        create_booking_use_case,
        valid_create_request,
        mock_customer_repository,
    ):
        """Test booking creation fails when customer not found."""
        mock_customer_repository.exists.return_value = False
        
        with pytest.raises(NotFoundError, match="Customer customer_123 not found"):
            await create_booking_use_case.execute(valid_create_request)
    
    async def test_create_booking_fails_vehicle_not_owned(
        self,
        create_booking_use_case,
        valid_create_request,
        mock_customer_repository,
        mock_vehicle_repository,
    ):
        """Test booking creation fails when vehicle not owned by customer."""
        mock_customer_repository.exists.return_value = True
        mock_vehicle_repository.validate_customer_vehicle.return_value = False
        
        with pytest.raises(ValidationError, match="Vehicle does not belong to customer"):
            await create_booking_use_case.execute(valid_create_request)
    
    async def test_create_booking_fails_services_not_found(
        self,
        create_booking_use_case,
        valid_create_request,
        mock_customer_repository,
        mock_vehicle_repository,
        mock_service_repository,
    ):
        """Test booking creation fails when some services not found."""
        mock_customer_repository.exists.return_value = True
        mock_vehicle_repository.validate_customer_vehicle.return_value = True
        # Return only one service instead of two
        mock_service_repository.get_multiple_by_ids.return_value = [
            {
                "id": "service_1",
                "name": "Basic Wash",
                "price": 25.0,
                "duration_minutes": 30,
            }
        ]
        
        with pytest.raises(ValidationError, match="One or more services not found"):
            await create_booking_use_case.execute(valid_create_request)
    
    async def test_create_booking_fails_invalid_booking_type(
        self,
        create_booking_use_case,
        valid_create_request,
        mock_customer_repository,
        mock_vehicle_repository,
        mock_service_repository,
        sample_services_data,
    ):
        """Test booking creation fails with invalid booking type."""
        mock_customer_repository.exists.return_value = True
        mock_vehicle_repository.validate_customer_vehicle.return_value = True
        mock_service_repository.get_multiple_by_ids.return_value = sample_services_data
        
        # Set invalid booking type
        valid_create_request.booking_type = "INVALID_TYPE"
        
        with pytest.raises(ValidationError, match="Invalid booking type"):
            await create_booking_use_case.execute(valid_create_request)
    
    async def test_create_booking_fails_cannot_acquire_lock(
        self,
        create_booking_use_case,
        valid_create_request,
        mock_customer_repository,
        mock_vehicle_repository,
        mock_service_repository,
        mock_lock_service,
        sample_services_data,
    ):
        """Test booking creation fails when cannot acquire time slot lock."""
        mock_customer_repository.exists.return_value = True
        mock_vehicle_repository.validate_customer_vehicle.return_value = True
        mock_service_repository.get_multiple_by_ids.return_value = sample_services_data
        mock_lock_service.acquire_time_slot_lock.return_value = None  # Cannot acquire lock
        
        with pytest.raises(BusinessRuleViolationError, match="Time slot is being booked"):
            await create_booking_use_case.execute(valid_create_request)
    
    async def test_create_booking_fails_conflicting_bookings(
        self,
        create_booking_use_case,
        valid_create_request,
        sample_booking,
        sample_services_data,
        mock_customer_repository,
        mock_vehicle_repository,
        mock_service_repository,
        mock_lock_service,
        mock_booking_repository,
    ):
        """Test booking creation fails when conflicting bookings exist."""
        mock_customer_repository.exists.return_value = True
        mock_vehicle_repository.validate_customer_vehicle.return_value = True
        mock_service_repository.get_multiple_by_ids.return_value = sample_services_data
        mock_lock_service.acquire_time_slot_lock.return_value = "lock_123"
        mock_booking_repository.find_conflicting_bookings.return_value = [sample_booking]
        
        with pytest.raises(BusinessRuleViolationError, match="Time slot conflicts"):
            await create_booking_use_case.execute(valid_create_request)
        
        # Verify lock is released even on failure
        mock_lock_service.release_lock.assert_called_once_with("lock_123")
    
    async def test_create_booking_handles_notification_failure(
        self,
        create_booking_use_case,
        valid_create_request,
        sample_booking,
        sample_services_data,
        sample_customer_data,
        sample_vehicle_data,
        mock_booking_repository,
        mock_service_repository,
        mock_vehicle_repository,
        mock_customer_repository,
        mock_notification_service,
        mock_event_service,
        mock_lock_service,
    ):
        """Test booking creation continues even if notification fails."""
        # Setup mocks
        mock_customer_repository.exists.return_value = True
        mock_vehicle_repository.validate_customer_vehicle.return_value = True
        mock_service_repository.get_multiple_by_ids.return_value = sample_services_data
        mock_lock_service.acquire_time_slot_lock.return_value = "lock_123"
        mock_booking_repository.find_conflicting_bookings.return_value = []
        mock_booking_repository.create.return_value = sample_booking
        mock_customer_repository.get_by_id.return_value = sample_customer_data
        mock_vehicle_repository.get_by_id.return_value = sample_vehicle_data
        
        # Make notification fail
        mock_notification_service.send_booking_confirmation.return_value = False
        
        # Execute use case - should still succeed
        response = await create_booking_use_case.execute(valid_create_request)
        
        # Verify response
        assert response.booking_id == sample_booking.id
        
        # Verify notification was attempted
        mock_notification_service.send_booking_confirmation.assert_called_once()
    
    async def test_create_booking_handles_event_failure(
        self,
        create_booking_use_case,
        valid_create_request,
        sample_booking,
        sample_services_data,
        mock_booking_repository,
        mock_service_repository,
        mock_vehicle_repository,
        mock_customer_repository,
        mock_notification_service,
        mock_event_service,
        mock_lock_service,
    ):
        """Test booking creation continues even if event publishing fails."""
        # Setup mocks
        mock_customer_repository.exists.return_value = True
        mock_vehicle_repository.validate_customer_vehicle.return_value = True
        mock_service_repository.get_multiple_by_ids.return_value = sample_services_data
        mock_lock_service.acquire_time_slot_lock.return_value = "lock_123"
        mock_booking_repository.find_conflicting_bookings.return_value = []
        mock_booking_repository.create.return_value = sample_booking
        
        # Make event publishing fail
        mock_event_service.publish_booking_created.return_value = False
        
        # Execute use case - should still succeed
        response = await create_booking_use_case.execute(valid_create_request)
        
        # Verify response
        assert response.booking_id == sample_booking.id
        
        # Verify event was attempted
        mock_event_service.publish_booking_created.assert_called_once()
    
    async def test_create_booking_walk_in_type(
        self,
        create_booking_use_case,
        valid_create_request,
        sample_booking,
        sample_services_data,
        mock_booking_repository,
        mock_service_repository,
        mock_vehicle_repository,
        mock_customer_repository,
        mock_lock_service,
    ):
        """Test booking creation with walk-in type."""
        # Setup for walk-in booking
        valid_create_request.booking_type = "WALK_IN"
        valid_create_request.scheduled_at = datetime.now() + timedelta(minutes=30)
        
        # Setup mocks
        mock_customer_repository.exists.return_value = True
        mock_vehicle_repository.validate_customer_vehicle.return_value = True
        mock_service_repository.get_multiple_by_ids.return_value = sample_services_data
        mock_lock_service.acquire_time_slot_lock.return_value = "lock_123"
        mock_booking_repository.find_conflicting_bookings.return_value = []
        mock_booking_repository.create.return_value = sample_booking
        
        # Execute use case
        response = await create_booking_use_case.execute(valid_create_request)
        
        # Verify response
        assert response.booking_id == sample_booking.id