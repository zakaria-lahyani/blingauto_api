import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

from app.features.bookings.use_cases import (
    CreateBookingUseCase,
    CreateBookingRequest,
    CancelBookingUseCase,
    CancelBookingRequest,
    UpdateBookingUseCase,
    UpdateBookingRequest,
    GetBookingUseCase,
    GetBookingRequest,
)
from app.features.bookings.domain import Booking, BookingService, BookingType, BookingStatus


@pytest.mark.integration
class TestBookingWorkflows:
    """Test complete booking workflows integration."""
    
    @pytest.fixture
    def booking_workflow_setup(
        self,
        mock_booking_repository,
        mock_service_repository,
        mock_vehicle_repository,
        mock_customer_repository,
        mock_notification_service,
        mock_payment_service,
        mock_cache_service,
        mock_event_service,
        mock_lock_service,
    ):
        """Setup for booking workflow tests."""
        return {
            "create_use_case": CreateBookingUseCase(
                booking_repository=mock_booking_repository,
                service_repository=mock_service_repository,
                vehicle_repository=mock_vehicle_repository,
                customer_repository=mock_customer_repository,
                notification_service=mock_notification_service,
                event_service=mock_event_service,
                lock_service=mock_lock_service,
            ),
            "cancel_use_case": CancelBookingUseCase(
                booking_repository=mock_booking_repository,
                customer_repository=mock_customer_repository,
                notification_service=mock_notification_service,
                payment_service=mock_payment_service,
                event_service=mock_event_service,
                cache_service=mock_cache_service,
            ),
            "update_use_case": UpdateBookingUseCase(
                booking_repository=mock_booking_repository,
                service_repository=mock_service_repository,
                vehicle_repository=mock_vehicle_repository,
                customer_repository=mock_customer_repository,
                notification_service=mock_notification_service,
                event_service=mock_event_service,
                cache_service=mock_cache_service,
                lock_service=mock_lock_service,
            ),
            "get_use_case": GetBookingUseCase(
                booking_repository=mock_booking_repository,
                service_repository=mock_service_repository,
                vehicle_repository=mock_vehicle_repository,
                customer_repository=mock_customer_repository,
                cache_service=mock_cache_service,
            ),
            "repositories": {
                "booking": mock_booking_repository,
                "service": mock_service_repository,
                "vehicle": mock_vehicle_repository,
                "customer": mock_customer_repository,
            },
            "services": {
                "notification": mock_notification_service,
                "payment": mock_payment_service,
                "cache": mock_cache_service,
                "event": mock_event_service,
                "lock": mock_lock_service,
            },
        }
    
    async def test_complete_booking_lifecycle(
        self,
        booking_workflow_setup,
        sample_services_data,
        sample_customer_data,
        sample_vehicle_data,
    ):
        """Test complete booking lifecycle: create -> update -> cancel."""
        setup = booking_workflow_setup
        
        # Step 1: Create booking
        scheduled_time = datetime.now() + timedelta(hours=24)
        
        # Setup mocks for creation
        setup["repositories"]["customer"].exists.return_value = True
        setup["repositories"]["vehicle"].validate_customer_vehicle.return_value = True
        setup["repositories"]["service"].get_multiple_by_ids.return_value = sample_services_data
        setup["services"]["lock"].acquire_time_slot_lock.return_value = "lock_123"
        setup["repositories"]["booking"].find_conflicting_bookings.return_value = []
        
        # Create the booking entity that will be returned
        created_booking = Booking.create(
            customer_id="customer_123",
            vehicle_id="vehicle_123",
            services=[
                BookingService(
                    service_id=svc["id"],
                    name=svc["name"],
                    price=svc["price"],
                    duration_minutes=svc["duration_minutes"],
                )
                for svc in sample_services_data
            ],
            scheduled_at=scheduled_time,
            booking_type=BookingType.SCHEDULED,
            notes="Integration test booking",
        )
        
        setup["repositories"]["booking"].create.return_value = created_booking
        setup["repositories"]["customer"].get_by_id.return_value = sample_customer_data
        setup["repositories"]["vehicle"].get_by_id.return_value = sample_vehicle_data
        
        create_request = CreateBookingRequest(
            customer_id="customer_123",
            vehicle_id="vehicle_123",
            service_ids=["service_1", "service_2"],
            scheduled_at=scheduled_time,
            booking_type="SCHEDULED",
            notes="Integration test booking",
        )
        
        create_response = await setup["create_use_case"].execute(create_request)
        
        # Verify creation
        assert create_response.booking_id == created_booking.id
        assert create_response.total_price == 40.0  # 25.0 + 15.0
        setup["services"]["event"].publish_booking_created.assert_called_once()
        setup["services"]["notification"].send_booking_confirmation.assert_called_once()
        
        # Step 2: Update booking
        setup["repositories"]["booking"].get_by_id.return_value = created_booking
        setup["services"]["lock"].acquire_booking_lock.return_value = "update_lock_456"
        setup["repositories"]["booking"].find_conflicting_bookings.return_value = []
        
        # Update to a different time
        new_scheduled_time = datetime.now() + timedelta(hours=48)
        update_request = UpdateBookingRequest(
            booking_id=created_booking.id,
            updated_by="customer_123",
            scheduled_at=new_scheduled_time,
            notes="Updated integration test booking",
        )
        
        # Mock the updated booking
        updated_booking = created_booking
        updated_booking.reschedule(new_scheduled_time)
        updated_booking.update_notes("Updated integration test booking")
        setup["repositories"]["booking"].update.return_value = updated_booking
        
        update_response = await setup["update_use_case"].execute(update_request)
        
        # Verify update
        assert update_response.booking_id == created_booking.id
        assert "scheduled_at" in update_response.changes_made
        assert "notes" in update_response.changes_made
        setup["services"]["event"].publish_booking_updated.assert_called_once()
        setup["services"]["cache"].delete_booking.assert_called()
        
        # Step 3: Cancel booking
        cancel_request = CancelBookingRequest(
            booking_id=created_booking.id,
            cancelled_by="customer_123",
            reason="Integration test cancellation",
        )
        
        # Mock cancellation
        cancelled_booking = updated_booking
        cancelled_booking.cancel("customer_123", "Integration test cancellation")
        setup["repositories"]["booking"].update.return_value = cancelled_booking
        setup["services"]["payment"].refund_payment.return_value = {
            "status": "succeeded",
            "refund_id": "refund_123",
            "amount_refunded": 40.0,
        }
        
        cancel_response = await setup["cancel_use_case"].execute(cancel_request)
        
        # Verify cancellation
        assert cancel_response.booking_id == created_booking.id
        assert cancel_response.status == BookingStatus.CANCELLED.value
        assert cancel_response.refund_amount == 40.0  # Full refund (24+ hours)
        setup["services"]["event"].publish_booking_cancelled.assert_called_once()
        setup["services"]["notification"].send_booking_cancellation.assert_called_once()
    
    async def test_concurrent_booking_prevention(
        self,
        booking_workflow_setup,
        sample_services_data,
    ):
        """Test that concurrent bookings for same time slot are prevented."""
        setup = booking_workflow_setup
        
        # Setup for first booking attempt
        scheduled_time = datetime.now() + timedelta(hours=24)
        setup["repositories"]["customer"].exists.return_value = True
        setup["repositories"]["vehicle"].validate_customer_vehicle.return_value = True
        setup["repositories"]["service"].get_multiple_by_ids.return_value = sample_services_data
        
        # First booking acquires lock successfully
        setup["services"]["lock"].acquire_time_slot_lock.return_value = "lock_123"
        setup["repositories"]["booking"].find_conflicting_bookings.return_value = []
        
        created_booking = Booking.create(
            customer_id="customer_123",
            vehicle_id="vehicle_123",
            services=[
                BookingService(
                    service_id=svc["id"],
                    name=svc["name"],
                    price=svc["price"],
                    duration_minutes=svc["duration_minutes"],
                )
                for svc in sample_services_data
            ],
            scheduled_at=scheduled_time,
            booking_type=BookingType.SCHEDULED,
        )
        setup["repositories"]["booking"].create.return_value = created_booking
        
        create_request = CreateBookingRequest(
            customer_id="customer_123",
            vehicle_id="vehicle_123",
            service_ids=["service_1", "service_2"],
            scheduled_at=scheduled_time,
            booking_type="SCHEDULED",
        )
        
        # First booking succeeds
        response1 = await setup["create_use_case"].execute(create_request)
        assert response1.booking_id == created_booking.id
        
        # Second booking attempt fails to acquire lock
        setup["services"]["lock"].acquire_time_slot_lock.return_value = None
        
        create_request2 = CreateBookingRequest(
            customer_id="customer_456",
            vehicle_id="vehicle_456",
            service_ids=["service_1"],
            scheduled_at=scheduled_time,
            booking_type="SCHEDULED",
        )
        
        # Second booking should fail
        from app.core.errors import BusinessRuleViolationError
        with pytest.raises(BusinessRuleViolationError, match="Time slot is being booked"):
            await setup["create_use_case"].execute(create_request2)
    
    async def test_booking_caching_workflow(
        self,
        booking_workflow_setup,
        sample_booking,
        sample_customer_data,
        sample_vehicle_data,
    ):
        """Test booking caching during get operations."""
        setup = booking_workflow_setup
        
        # Test cache miss -> repository -> cache set
        setup["services"]["cache"].get_booking.return_value = None
        setup["repositories"]["booking"].get_by_id.return_value = sample_booking
        setup["repositories"]["customer"].get_by_id.return_value = sample_customer_data
        setup["repositories"]["vehicle"].get_by_id.return_value = sample_vehicle_data
        
        get_request = GetBookingRequest(
            booking_id=sample_booking.id,
            requested_by="customer_123",
        )
        
        response = await setup["get_use_case"].execute(get_request)
        
        # Verify cache operations
        setup["services"]["cache"].get_booking.assert_called_once_with(sample_booking.id)
        setup["repositories"]["booking"].get_by_id.assert_called_once_with(sample_booking.id)
        setup["services"]["cache"].set_booking.assert_called_once_with(sample_booking, ttl=3600)
        
        assert response.id == sample_booking.id
        
        # Test cache hit
        setup["services"]["cache"].get_booking.return_value = sample_booking
        setup["repositories"]["booking"].get_by_id.reset_mock()
        
        response2 = await setup["get_use_case"].execute(get_request)
        
        # Should not call repository on cache hit
        setup["repositories"]["booking"].get_by_id.assert_not_called()
        assert response2.id == sample_booking.id
    
    async def test_event_driven_workflow(
        self,
        booking_workflow_setup,
        sample_services_data,
    ):
        """Test event publishing throughout booking workflow."""
        setup = booking_workflow_setup
        
        # Setup for booking creation
        scheduled_time = datetime.now() + timedelta(hours=24)
        setup["repositories"]["customer"].exists.return_value = True
        setup["repositories"]["vehicle"].validate_customer_vehicle.return_value = True
        setup["repositories"]["service"].get_multiple_by_ids.return_value = sample_services_data
        setup["services"]["lock"].acquire_time_slot_lock.return_value = "lock_123"
        setup["repositories"]["booking"].find_conflicting_bookings.return_value = []
        
        created_booking = Booking.create(
            customer_id="customer_123",
            vehicle_id="vehicle_123",
            services=[
                BookingService(
                    service_id=svc["id"],
                    name=svc["name"],
                    price=svc["price"],
                    duration_minutes=svc["duration_minutes"],
                )
                for svc in sample_services_data
            ],
            scheduled_at=scheduled_time,
            booking_type=BookingType.SCHEDULED,
        )
        setup["repositories"]["booking"].create.return_value = created_booking
        
        # Create booking
        create_request = CreateBookingRequest(
            customer_id="customer_123",
            vehicle_id="vehicle_123",
            service_ids=["service_1", "service_2"],
            scheduled_at=scheduled_time,
            booking_type="SCHEDULED",
        )
        
        await setup["create_use_case"].execute(create_request)
        
        # Verify creation event
        setup["services"]["event"].publish_booking_created.assert_called_once_with(created_booking)
        
        # Cancel booking
        setup["repositories"]["booking"].get_by_id.return_value = created_booking
        cancelled_booking = created_booking
        cancelled_booking.cancel("customer_123", "Test cancellation")
        setup["repositories"]["booking"].update.return_value = cancelled_booking
        
        cancel_request = CancelBookingRequest(
            booking_id=created_booking.id,
            cancelled_by="customer_123",
            reason="Test cancellation",
        )
        
        await setup["cancel_use_case"].execute(cancel_request)
        
        # Verify cancellation event
        setup["services"]["event"].publish_booking_cancelled.assert_called_once_with(
            cancelled_booking, "customer_123", "Test cancellation"
        )
    
    async def test_notification_workflow(
        self,
        booking_workflow_setup,
        sample_services_data,
        sample_customer_data,
        sample_vehicle_data,
    ):
        """Test notification workflow throughout booking lifecycle."""
        setup = booking_workflow_setup
        
        # Setup for booking creation
        scheduled_time = datetime.now() + timedelta(hours=24)
        setup["repositories"]["customer"].exists.return_value = True
        setup["repositories"]["vehicle"].validate_customer_vehicle.return_value = True
        setup["repositories"]["service"].get_multiple_by_ids.return_value = sample_services_data
        setup["services"]["lock"].acquire_time_slot_lock.return_value = "lock_123"
        setup["repositories"]["booking"].find_conflicting_bookings.return_value = []
        
        created_booking = Booking.create(
            customer_id="customer_123",
            vehicle_id="vehicle_123",
            services=[
                BookingService(
                    service_id=svc["id"],
                    name=svc["name"],
                    price=svc["price"],
                    duration_minutes=svc["duration_minutes"],
                )
                for svc in sample_services_data
            ],
            scheduled_at=scheduled_time,
            booking_type=BookingType.SCHEDULED,
        )
        setup["repositories"]["booking"].create.return_value = created_booking
        setup["repositories"]["customer"].get_by_id.return_value = sample_customer_data
        setup["repositories"]["vehicle"].get_by_id.return_value = sample_vehicle_data
        
        # Create booking
        create_request = CreateBookingRequest(
            customer_id="customer_123",
            vehicle_id="vehicle_123",
            service_ids=["service_1", "service_2"],
            scheduled_at=scheduled_time,
            booking_type="SCHEDULED",
        )
        
        await setup["create_use_case"].execute(create_request)
        
        # Verify confirmation notification
        setup["services"]["notification"].send_booking_confirmation.assert_called_once_with(
            sample_customer_data["email"],
            created_booking,
            sample_customer_data,
            sample_services_data,
            sample_vehicle_data,
        )
        
        # Update booking
        setup["repositories"]["booking"].get_by_id.return_value = created_booking
        setup["services"]["lock"].acquire_booking_lock.return_value = "update_lock"
        
        updated_booking = created_booking
        updated_booking.update_notes("Updated notes")
        setup["repositories"]["booking"].update.return_value = updated_booking
        
        update_request = UpdateBookingRequest(
            booking_id=created_booking.id,
            updated_by="customer_123",
            notes="Updated notes",
        )
        
        await setup["update_use_case"].execute(update_request)
        
        # Verify update notification
        setup["services"]["notification"].send_booking_updated.assert_called_once()
        
        # Cancel booking
        cancelled_booking = updated_booking
        cancelled_booking.cancel("customer_123", "Test cancellation")
        setup["repositories"]["booking"].update.return_value = cancelled_booking
        
        cancel_request = CancelBookingRequest(
            booking_id=created_booking.id,
            cancelled_by="customer_123",
            reason="Test cancellation",
        )
        
        await setup["cancel_use_case"].execute(cancel_request)
        
        # Verify cancellation notification
        setup["services"]["notification"].send_booking_cancellation.assert_called_once_with(
            sample_customer_data["email"],
            cancelled_booking,
            sample_customer_data,
        )