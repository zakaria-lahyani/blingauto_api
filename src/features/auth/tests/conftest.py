"""
Pytest configuration for auth feature tests
"""
import pytest
import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

from src.shared.simple_database import init_database, get_db_session, create_tables as create_all_tables
from src.features.auth import AuthModule, AuthConfig
from src.shared.middleware import setup_global_middleware
from src.shared.simple_config import AppConfig


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Setup test database"""
    # Use in-memory SQLite for tests
    test_db_url = "sqlite+aiosqlite:///:memory:"
    init_database(test_db_url)
    
    # Create all tables
    await create_all_tables()
    
    yield
    
    # Cleanup would go here if needed


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Database session for testing"""
    async with get_db_session() as session:
        yield session


@pytest.fixture
def auth_config() -> AuthConfig:
    """Auth configuration for testing"""
    return AuthConfig(
        jwt_secret_key="Dev_Test_Secret_K3y_F0r_JWT_T3st1ng_M1n1mum_Ent40py_V4l1d4t10n_P4ss_9$2z",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
        enable_email_verification=True,
        enable_password_reset=True,
        enable_account_lockout=True,
        lockout_attempts=5,
        lockout_duration_minutes=15,
        enable_rate_limiting=False,  # Disable for tests
        enable_security_logging=False  # Disable for tests
    )


@pytest.fixture
async def auth_module(auth_config: AuthConfig) -> AsyncGenerator[AuthModule, None]:
    """Auth module instance for testing"""
    module = AuthModule(auth_config)
    await module.initialize()
    yield module


@pytest.fixture
async def test_app(auth_module: AuthModule) -> AsyncGenerator[FastAPI, None]:
    """FastAPI test application with auth module"""
    app = FastAPI(title="Test App")
    
    # Setup global middleware
    global_config = AppConfig(
        debug=True,
        environment="testing"
    )
    setup_global_middleware(app, global_config)
    
    # Setup auth module
    auth_module.setup(app, prefix="/auth")
    app.state.auth = auth_module
    
    # Add test endpoints
    @app.get("/health")
    async def health():
        return {"status": "ok"}
    
    @app.get("/protected")
    async def protected_endpoint(
        current_user=pytest.importorskip("fastapi").Depends(auth_module.get_current_user)
    ):
        return {"user_id": str(current_user.id), "email": current_user.email}
    
    @app.get("/admin-only")
    async def admin_only(
        current_user=pytest.importorskip("fastapi").Depends(auth_module.get_current_admin)
    ):
        return {"message": "admin access granted"}
    
    yield app


@pytest.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for testing"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def authenticated_client(
    client: AsyncClient,
    auth_module: AuthModule
) -> AsyncGenerator[tuple[AsyncClient, dict], None]:
    """HTTP client with authenticated user"""
    # Create and register a test user
    register_data = {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    # Register user
    register_response = await client.post("/auth/register", json=register_data)
    assert register_response.status_code == 201
    
    # Login user
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"]
    }
    login_response = await client.post("/auth/login", json=login_data)
    assert login_response.status_code == 200
    
    tokens = login_response.json()
    access_token = tokens["access_token"]
    
    # Set authorization header
    client.headers.update({"Authorization": f"Bearer {access_token}"})
    
    yield client, tokens


@pytest.fixture
async def admin_client(
    client: AsyncClient,
    auth_module: AuthModule
) -> AsyncGenerator[tuple[AsyncClient, dict], None]:
    """HTTP client with authenticated admin user"""
    # Create admin user directly in database
    from src.features.auth.infrastructure.database.repositories import AuthUserRepository
    from src.features.auth.domain.entities import AuthUser
    from src.features.auth.domain.enums import AuthRole
    from src.features.auth.infrastructure.security import hash_password
    from uuid import uuid4
    from datetime import datetime
    
    async with get_db_session() as session:
        repo = AuthUserRepository()
        
        admin_user = AuthUser(
            id=uuid4(),
            email="admin@test.com",
            hashed_password=hash_password("AdminPassword123!"),
            first_name="Test",
            last_name="Admin",
            role=AuthRole.ADMIN,
            email_verified=True,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await repo.create_user(admin_user)
    
    # Login admin
    login_data = {
        "email": "admin@test.com",
        "password": "AdminPassword123!"
    }
    login_response = await client.post("/auth/login", json=login_data)
    assert login_response.status_code == 200
    
    tokens = login_response.json()
    access_token = tokens["access_token"]
    
    # Set authorization header
    client.headers.update({"Authorization": f"Bearer {access_token}"})
    
    yield client, tokens


# Import test fixtures
from .fixtures.auth_fixtures import *