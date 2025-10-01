import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
from typing import List, Dict, Any

from app.features.bookings.domain import (
    Booking,
    BookingService,
    BookingType,
    BookingStatus,
)
from app.features.bookings.ports import (
    IBookingRepository,
    IServiceRepository,
    IVehicleRepository,
    ICustomerRepository,
    INotificationService,
    IPaymentService,
    ICacheService,
    IEventService,
    ILockService,
)


@pytest.fixture
def sample_booking_service():
    """Create a sample booking service."""
    return BookingService(
        service_id="service_123",
        name="Basic Wash",
        price=25.0,
        duration_minutes=30,
    )


@pytest.fixture
def sample_booking_services():
    """Create multiple sample booking services."""
    return [
        BookingService(
            service_id="service_1",
            name="Basic Wash",
            price=25.0,
            duration_minutes=30,
        ),
        BookingService(
            service_id="service_2",
            name="Interior Clean",
            price=15.0,
            duration_minutes=20,
        ),
    ]


@pytest.fixture
def sample_booking(sample_booking_services):
    """Create a sample booking."""
    scheduled_time = datetime.now() + timedelta(hours=24)
    return Booking.create(
        customer_id="customer_123",
        vehicle_id="vehicle_123",
        services=sample_booking_services,
        scheduled_at=scheduled_time,
        booking_type=BookingType.SCHEDULED,
        notes="Test booking",
        phone_number="+1234567890",
    )


@pytest.fixture
def walk_in_booking():
    """Create a walk-in booking."""
    services = [
        BookingService(
            service_id="service_quick",
            name="Quick Wash",
            price=20.0,
            duration_minutes=15,
        )
    ]
    return Booking.create(
        customer_id="customer_456",
        vehicle_id="vehicle_456",
        services=services,
        scheduled_at=datetime.now() + timedelta(minutes=30),
        booking_type=BookingType.WALK_IN,
        notes="Walk-in customer",
    )


@pytest.fixture
def mock_booking_repository():
    """Mock booking repository."""
    mock = Mock(spec=IBookingRepository)
    mock.get_by_id = AsyncMock()
    mock.create = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    mock.list_by_customer = AsyncMock()
    mock.list_by_date_range = AsyncMock()
    mock.list_by_status = AsyncMock()
    mock.count_by_customer = AsyncMock()
    mock.find_conflicting_bookings = AsyncMock()
    return mock


@pytest.fixture
def mock_service_repository():
    """Mock service repository."""
    mock = Mock(spec=IServiceRepository)
    mock.get_by_id = AsyncMock()
    mock.get_multiple_by_ids = AsyncMock()
    mock.list_active_services = AsyncMock()
    return mock


@pytest.fixture
def mock_vehicle_repository():
    """Mock vehicle repository."""
    mock = Mock(spec=IVehicleRepository)
    mock.get_by_id = AsyncMock()
    mock.get_customer_vehicles = AsyncMock()
    mock.validate_customer_vehicle = AsyncMock()
    return mock


@pytest.fixture
def mock_customer_repository():
    """Mock customer repository."""
    mock = Mock(spec=ICustomerRepository)
    mock.get_by_id = AsyncMock()
    mock.exists = AsyncMock()
    return mock


@pytest.fixture
def mock_notification_service():
    """Mock notification service."""
    mock = Mock(spec=INotificationService)
    mock.send_booking_confirmation = AsyncMock(return_value=True)
    mock.send_booking_cancellation = AsyncMock(return_value=True)
    mock.send_booking_reminder = AsyncMock(return_value=True)
    mock.send_booking_updated = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_payment_service():
    """Mock payment service."""
    mock = Mock(spec=IPaymentService)
    mock.create_payment_intent = AsyncMock()
    mock.confirm_payment = AsyncMock()
    mock.refund_payment = AsyncMock()
    mock.get_payment_status = AsyncMock()
    return mock


@pytest.fixture
def mock_cache_service():
    """Mock cache service."""
    mock = Mock(spec=ICacheService)
    mock.get_booking = AsyncMock()
    mock.set_booking = AsyncMock(return_value=True)
    mock.delete_booking = AsyncMock(return_value=True)
    mock.get_customer_bookings = AsyncMock()
    mock.set_customer_bookings = AsyncMock(return_value=True)
    mock.invalidate_customer_cache = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_event_service():
    """Mock event service."""
    mock = Mock(spec=IEventService)
    mock.publish_booking_created = AsyncMock(return_value=True)
    mock.publish_booking_confirmed = AsyncMock(return_value=True)
    mock.publish_booking_cancelled = AsyncMock(return_value=True)
    mock.publish_booking_completed = AsyncMock(return_value=True)
    mock.publish_booking_updated = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_lock_service():
    """Mock lock service."""
    mock = Mock(spec=ILockService)
    mock.acquire_booking_lock = AsyncMock(return_value="lock_123")
    mock.acquire_time_slot_lock = AsyncMock(return_value="lock_456")
    mock.release_lock = AsyncMock(return_value=True)
    mock.extend_lock = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def sample_services_data():
    """Sample services data from repository."""
    return [
        {
            "id": "service_1",
            "name": "Basic Wash",
            "price": 25.0,
            "duration_minutes": 30,
            "category_id": "wash_services",
            "active": True,
        },
        {
            "id": "service_2", 
            "name": "Interior Clean",
            "price": 15.0,
            "duration_minutes": 20,
            "category_id": "cleaning_services",
            "active": True,
        },
    ]


@pytest.fixture
def sample_customer_data():
    """Sample customer data from repository."""
    return {
        "id": "customer_123",
        "email": "customer@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890",
    }


@pytest.fixture
def sample_vehicle_data():
    """Sample vehicle data from repository."""
    return {
        "id": "vehicle_123",
        "customer_id": "customer_123",
        "make": "Toyota",
        "model": "Camry",
        "year": 2020,
        "license_plate": "ABC123",
        "color": "Blue",
    }