import pytest
from decimal import Decimal
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock

from app.features.services.domain import Category, Service, CategoryStatus, ServiceStatus
from app.features.services.ports import (
    ICategoryRepository,
    IServiceRepository,
    IBookingRepository,
    ICacheService,
    IEventService,
    INotificationService,
    IAuditService,
    IAnalyticsService,
)


@pytest.fixture
def mock_category_repository():
    """Mock category repository."""
    repo = Mock(spec=ICategoryRepository)
    repo.get_by_id = AsyncMock()
    repo.get_by_name = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.list_all = AsyncMock()
    repo.count = AsyncMock()
    repo.list_active = AsyncMock()
    repo.count_services_in_category = AsyncMock()
    repo.exists_by_name = AsyncMock()
    return repo


@pytest.fixture
def mock_service_repository():
    """Mock service repository."""
    repo = Mock(spec=IServiceRepository)
    repo.get_by_id = AsyncMock()
    repo.get_by_name_in_category = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.list_by_category = AsyncMock()
    repo.list_all = AsyncMock()
    repo.list_popular = AsyncMock()
    repo.list_by_price_range = AsyncMock()
    repo.list_by_duration_range = AsyncMock()
    repo.count_by_category = AsyncMock()
    repo.count_popular_in_category = AsyncMock()
    repo.exists_by_name_in_category = AsyncMock()
    repo.get_multiple_by_ids = AsyncMock()
    repo.search_services = AsyncMock()
    return repo


@pytest.fixture
def mock_booking_repository():
    """Mock booking repository."""
    repo = Mock(spec=IBookingRepository)
    repo.count_bookings_for_service = AsyncMock()
    repo.get_service_revenue = AsyncMock()
    repo.get_popular_services_by_bookings = AsyncMock()
    return repo


@pytest.fixture
def mock_cache_service():
    """Mock cache service."""
    service = Mock(spec=ICacheService)
    service.get_category = AsyncMock()
    service.set_category = AsyncMock()
    service.delete_category = AsyncMock()
    service.get_service = AsyncMock()
    service.set_service = AsyncMock()
    service.delete_service = AsyncMock()
    service.get_popular_services = AsyncMock()
    service.set_popular_services = AsyncMock()
    service.get_category_services = AsyncMock()
    service.set_category_services = AsyncMock()
    service.delete_category_services = AsyncMock()
    service.invalidate_services_cache = AsyncMock()
    return service


@pytest.fixture
def mock_event_service():
    """Mock event service."""
    service = Mock(spec=IEventService)
    service.publish_category_created = AsyncMock(return_value=True)
    service.publish_category_updated = AsyncMock(return_value=True)
    service.publish_category_deactivated = AsyncMock(return_value=True)
    service.publish_service_created = AsyncMock(return_value=True)
    service.publish_service_updated = AsyncMock(return_value=True)
    service.publish_service_price_changed = AsyncMock(return_value=True)
    service.publish_service_deactivated = AsyncMock(return_value=True)
    service.publish_service_archived = AsyncMock(return_value=True)
    service.publish_service_marked_popular = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_notification_service():
    """Mock notification service."""
    service = Mock(spec=INotificationService)
    service.notify_service_price_change = AsyncMock(return_value=True)
    service.notify_new_service_available = AsyncMock(return_value=True)
    service.notify_service_discontinued = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_audit_service():
    """Mock audit service."""
    service = Mock(spec=IAuditService)
    service.log_category_creation = AsyncMock(return_value=True)
    service.log_category_update = AsyncMock(return_value=True)
    service.log_category_deactivation = AsyncMock(return_value=True)
    service.log_service_creation = AsyncMock(return_value=True)
    service.log_service_update = AsyncMock(return_value=True)
    service.log_service_price_change = AsyncMock(return_value=True)
    service.log_service_deactivation = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_analytics_service():
    """Mock analytics service."""
    service = Mock(spec=IAnalyticsService)
    service.get_service_performance_metrics = AsyncMock()
    service.get_category_performance_metrics = AsyncMock()
    service.get_demand_forecast = AsyncMock()
    service.get_pricing_recommendations = AsyncMock()
    service.get_service_comparison = AsyncMock()
    return service


@pytest.fixture
def sample_category():
    """Sample category for testing."""
    return Category.create(
        name="Exterior Cleaning",
        description="External car wash services",
        display_order=1,
    )


@pytest.fixture
def sample_service():
    """Sample service for testing."""
    return Service.create(
        category_id="cat_123",
        name="Basic Wash",
        description="Standard exterior wash",
        price=Decimal("25.00"),
        duration_minutes=30,
    )


@pytest.fixture
def sample_popular_service():
    """Sample popular service for testing."""
    service = Service.create(
        category_id="cat_123",
        name="Premium Wash",
        description="Premium exterior and interior wash",
        price=Decimal("45.00"),
        duration_minutes=60,
        is_popular=True,
    )
    return service


@pytest.fixture
def admin_user():
    """Mock admin user."""
    user = Mock()
    user.id = "admin_123"
    user.email = "admin@test.com"
    user.role = "admin"
    return user


@pytest.fixture
def manager_user():
    """Mock manager user."""
    user = Mock()
    user.id = "manager_123"
    user.email = "manager@test.com"
    user.role = "manager"
    return user


@pytest.fixture
def regular_user():
    """Mock regular user."""
    user = Mock()
    user.id = "user_123"
    user.email = "user@test.com"
    user.role = "customer"
    return user