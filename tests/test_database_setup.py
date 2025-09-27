"""
Test database setup utilities for isolated testing
"""
import asyncio
import uuid
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.shared.database.base import Base
from src.shared.database.session import get_session


class TestDatabaseManager:
    """Manages isolated test databases"""
    
    def __init__(self):
        self.test_db_name = f"test_db_{uuid.uuid4().hex[:8]}"
        self.test_db_url = f"sqlite+aiosqlite:///:memory:"  # Use in-memory SQLite for fast tests
        self.engine = None
        self.session_factory = None
    
    async def setup_test_db(self):
        """Setup isolated test database"""
        # Create async engine for test database
        self.engine = create_async_engine(
            self.test_db_url,
            echo=False,  # Reduce noise in tests
            future=True
        )
        
        # Create all tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        return self.engine
    
    async def cleanup_test_db(self):
        """Cleanup test database"""
        if self.engine:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await self.engine.dispose()
    
    async def reset_db_state(self):
        """Reset database state between tests"""
        if self.engine:
            async with self.engine.begin() as conn:
                # Drop and recreate all tables
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
    
    async def get_test_session(self) -> AsyncSession:
        """Get test database session"""
        if not self.session_factory:
            await self.setup_test_db()
        
        return self.session_factory()


# Global test database manager
_test_db_manager: TestDatabaseManager = None


def get_test_db_manager() -> TestDatabaseManager:
    """Get or create test database manager"""
    global _test_db_manager
    if _test_db_manager is None:
        _test_db_manager = TestDatabaseManager()
    return _test_db_manager


@pytest_asyncio.fixture(scope="session")
async def test_db_engine():
    """Create test database engine for the session"""
    manager = get_test_db_manager()
    engine = await manager.setup_test_db()
    yield engine
    await manager.cleanup_test_db()


@pytest_asyncio.fixture
async def test_db_session(test_db_engine):
    """Create clean database session for each test"""
    manager = get_test_db_manager()
    
    # Reset database state
    await manager.reset_db_state()
    
    # Create new session
    session = await manager.get_test_session()
    
    try:
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture
async def override_db_dependency(test_db_session):
    """Override database dependency in FastAPI app"""
    from src.shared.database.session import get_session
    
    async def get_test_session():
        yield test_db_session
    
    return get_test_session


# Test-specific environment configuration
def setup_test_environment():
    """Setup test-specific environment variables"""
    # Use test-friendly rate limits
    os.environ["AUTH_CLIENT_RATE_LIMIT"] = "1000"  # High limits for tests
    os.environ["AUTH_ADMIN_RATE_LIMIT"] = "1000"
    os.environ["AUTH_MANAGER_RATE_LIMIT"] = "1000"
    os.environ["AUTH_WASHER_RATE_LIMIT"] = "1000"
    os.environ["AUTH_ENABLE_RATE_LIMITING"] = "false"  # Disable for faster tests
    
    # Disable email verification for tests
    os.environ["AUTH_ENABLE_EMAIL_VERIFICATION"] = "false"
    
    # Use test-friendly validation
    os.environ["AUTH_EMAIL_VERIFICATION_EXPIRE_HOURS"] = "24"
    os.environ["AUTH_PASSWORD_RESET_EXPIRE_HOURS"] = "2"
    
    # Disable some security features that slow down tests
    os.environ["AUTH_ENABLE_SECURITY_LOGGING"] = "false"
    
    # Use mock email for tests
    os.environ["AUTH_EMAIL_PROVIDER"] = "mock"


def cleanup_test_environment():
    """Cleanup test environment variables"""
    test_vars = [
        "AUTH_CLIENT_RATE_LIMIT",
        "AUTH_ADMIN_RATE_LIMIT", 
        "AUTH_MANAGER_RATE_LIMIT",
        "AUTH_WASHER_RATE_LIMIT",
        "AUTH_ENABLE_RATE_LIMITING",
        "AUTH_ENABLE_SECURITY_LOGGING"
    ]
    
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]


@pytest.fixture(scope="session", autouse=True)
def setup_test_session():
    """Setup test session configuration"""
    setup_test_environment()
    yield
    cleanup_test_environment()