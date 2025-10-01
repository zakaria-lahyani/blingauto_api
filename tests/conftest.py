"""Shared pytest configuration and fixtures."""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any, AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from app.core.db import Base, get_db


# Configure async test environment
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database and session."""
    # Create async engine for testing
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    # Drop tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with overridden database."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def auth_headers(client: AsyncClient) -> Dict[str, str]:
    """Create authenticated user and return auth headers."""
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "TestPass123!",
            "full_name": "Test User",
            "phone": "+1234567890"
        }
    )

    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "TestPass123!"
        }
    )

    access_token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
async def admin_headers(client: AsyncClient, test_db: AsyncSession) -> Dict[str, str]:
    """Create admin user and return auth headers."""
    # Register user
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@example.com",
            "password": "AdminPass123!",
            "full_name": "Admin User"
        }
    )
    user_id = register_response.json()["id"]

    # Manually update user role to admin in database
    from app.features.auth.adapters.repositories import SqlUserRepository
    repo = SqlUserRepository(test_db)
    user = await repo.get_by_id(user_id)
    user.role = "admin"
    await repo.update(user)
    await test_db.commit()

    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com",
            "password": "AdminPass123!"
        }
    )

    access_token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
async def manager_headers(client: AsyncClient, test_db: AsyncSession) -> Dict[str, str]:
    """Create manager user and return auth headers."""
    # Register user
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "manager@example.com",
            "password": "ManagerPass123!",
            "full_name": "Manager User"
        }
    )
    user_id = register_response.json()["id"]

    # Manually update user role to manager in database
    from app.features.auth.adapters.repositories import SqlUserRepository
    repo = SqlUserRepository(test_db)
    user = await repo.get_by_id(user_id)
    user.role = "manager"
    await repo.update(user)
    await test_db.commit()

    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "manager@example.com",
            "password": "ManagerPass123!"
        }
    )

    access_token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


# Test database configuration
@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Test database URL."""
    return TEST_DATABASE_URL


@pytest.fixture(scope="session")
def app_config() -> Dict[str, Any]:
    """Test application configuration."""
    return {
        "database_url": TEST_DATABASE_URL,
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
