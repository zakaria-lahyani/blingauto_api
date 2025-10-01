"""Shared pytest configuration and fixtures."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Generator, Dict, Any

# Test database configuration
@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Test database URL."""
    return "sqlite:///test.db"


@pytest.fixture(scope="session") 
def app_config() -> Dict[str, Any]:
    """Test application configuration."""
    return {
        "database_url": "sqlite:///test.db",
        "jwt_secret": "test-secret-key",
        "jwt_access_token_expire_minutes": 60,
        "jwt_refresh_token_expire_days": 30,
        "email_verification_expire_hours": 24,
        "password_reset_expire_hours": 1,
        "rate_limit_per_minute": 100,
        "environment": "test",
        "debug": True,
    }


# Time-related fixtures
@pytest.fixture
def now() -> datetime:
    """Current time for testing."""
    return datetime.utcnow()


@pytest.fixture  
def future_time() -> datetime:
    """Future time for testing (2 hours from now)."""
    return datetime.utcnow() + timedelta(hours=2)


@pytest.fixture
def past_time() -> datetime:
    """Past time for testing (2 hours ago)."""
    return datetime.utcnow() - timedelta(hours=2)


# Common test data
@pytest.fixture
def test_email() -> str:
    """Test email address."""
    return "test@example.com"


@pytest.fixture
def test_password() -> str:
    """Test password."""
    return "TestPassword123!"


@pytest.fixture
def test_price() -> Decimal:
    """Test price value."""
    return Decimal("25.00")


@pytest.fixture
def test_customer_id() -> str:
    """Test customer ID."""
    return "test-customer-123"


@pytest.fixture
def test_service_id() -> str:
    """Test service ID."""
    return "test-service-456"


@pytest.fixture
def test_vehicle_id() -> str:
    """Test vehicle ID."""
    return "test-vehicle-789"


# Mock fixtures
@pytest.fixture
def mock_datetime(monkeypatch):
    """Mock datetime.utcnow()."""
    from datetime import datetime
    
    mock_now = datetime(2023, 6, 15, 12, 0, 0)
    
    class MockDatetime:
        @staticmethod
        def utcnow():
            return mock_now
            
        @staticmethod
        def now():
            return mock_now
    
    monkeypatch.setattr("datetime.datetime", MockDatetime)
    return mock_now


# Database cleanup
@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up database after each test."""
    yield
    # Cleanup logic here if needed
    pass