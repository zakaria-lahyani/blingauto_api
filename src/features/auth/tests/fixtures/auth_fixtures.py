"""
Auth test fixtures and factories
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Any
from uuid import uuid4
from faker import Faker

from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole
from src.features.auth.config import AuthConfig
from src.features.auth.infrastructure.security import hash_password
from src.features.auth.infrastructure.database.repositories import AuthUserRepository
from src.shared.database import get_db_session

fake = Faker()


@pytest.fixture
def auth_config() -> AuthConfig:
    """Auth configuration for testing"""
    return AuthConfig(
        jwt_secret_key="test-secret-key-for-testing-only",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
        enable_email_verification=True,
        enable_password_reset=True,
        enable_account_lockout=True,
        lockout_attempts=5,
        lockout_duration_minutes=15
    )


@pytest.fixture
def user_data() -> Dict[str, Any]:
    """Generate test user data"""
    return {
        "email": fake.email(),
        "password": "TestPassword123!",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "role": AuthRole.CLIENT
    }


@pytest.fixture
def admin_data() -> Dict[str, Any]:
    """Generate test admin data"""
    return {
        "email": "admin@test.com",
        "password": "AdminPassword123!",
        "first_name": "Test",
        "last_name": "Admin",
        "role": AuthRole.ADMIN
    }


@pytest.fixture
def manager_data() -> Dict[str, Any]:
    """Generate test manager data"""
    return {
        "email": "manager@test.com",
        "password": "ManagerPassword123!",
        "first_name": "Test",
        "last_name": "Manager",
        "role": AuthRole.MANAGER
    }


@pytest.fixture
def washer_data() -> Dict[str, Any]:
    """Generate test washer data"""
    return {
        "email": "washer@test.com",
        "password": "WasherPassword123!",
        "first_name": "Test",
        "last_name": "Washer",
        "role": AuthRole.WASHER
    }


@pytest.fixture
async def auth_user_repository() -> AsyncGenerator[AuthUserRepository, None]:
    """Auth user repository for testing"""
    repo = AuthUserRepository()
    yield repo


async def create_test_user(
    user_data: Dict[str, Any],
    verified: bool = True,
    locked: bool = False
) -> AuthUser:
    """Create a test user in the database"""
    async with get_db_session() as session:
        repo = AuthUserRepository()
        
        # Hash password
        hashed_password = hash_password(user_data["password"])
        
        # Create user entity
        user = AuthUser(
            id=uuid4(),
            email=user_data["email"],
            hashed_password=hashed_password,
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            role=user_data["role"],
            email_verified=verified,
            is_active=not locked,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database
        saved_user = await repo.create_user(user)
        return saved_user


@pytest.fixture
async def test_user(user_data: Dict[str, Any]) -> AsyncGenerator[AuthUser, None]:
    """Create a test user"""
    user = await create_test_user(user_data)
    yield user


@pytest.fixture
async def verified_user(user_data: Dict[str, Any]) -> AsyncGenerator[AuthUser, None]:
    """Create a verified test user"""
    user = await create_test_user(user_data, verified=True)
    yield user


@pytest.fixture
async def unverified_user(user_data: Dict[str, Any]) -> AsyncGenerator[AuthUser, None]:
    """Create an unverified test user"""
    user = await create_test_user(user_data, verified=False)
    yield user


@pytest.fixture
async def locked_user(user_data: Dict[str, Any]) -> AsyncGenerator[AuthUser, None]:
    """Create a locked test user"""
    user = await create_test_user(user_data, verified=True, locked=True)
    yield user


@pytest.fixture
async def admin_user(admin_data: Dict[str, Any]) -> AsyncGenerator[AuthUser, None]:
    """Create a test admin user"""
    user = await create_test_user(admin_data, verified=True)
    yield user


@pytest.fixture
async def manager_user(manager_data: Dict[str, Any]) -> AsyncGenerator[AuthUser, None]:
    """Create a test manager user"""
    user = await create_test_user(manager_data, verified=True)
    yield user


@pytest.fixture
async def washer_user(washer_data: Dict[str, Any]) -> AsyncGenerator[AuthUser, None]:
    """Create a test washer user"""
    user = await create_test_user(washer_data, verified=True)
    yield user


@pytest.fixture
def valid_jwt_payload() -> Dict[str, Any]:
    """Valid JWT payload for testing"""
    return {
        "sub": str(uuid4()),
        "email": "test@example.com",
        "role": "client",
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "iat": datetime.utcnow()
    }


@pytest.fixture
def expired_jwt_payload() -> Dict[str, Any]:
    """Expired JWT payload for testing"""
    return {
        "sub": str(uuid4()),
        "email": "test@example.com",
        "role": "client",
        "type": "access",
        "exp": datetime.utcnow() - timedelta(minutes=30),
        "iat": datetime.utcnow() - timedelta(hours=1)
    }


@pytest.fixture
def invalid_jwt_payload() -> Dict[str, Any]:
    """Invalid JWT payload for testing"""
    return {
        "sub": str(uuid4()),
        "email": "test@example.com",
        # Missing required fields
    }


class AuthTestHelpers:
    """Helper class for auth testing"""
    
    @staticmethod
    def create_login_payload(email: str, password: str) -> Dict[str, str]:
        """Create login request payload"""
        return {
            "email": email,
            "password": password
        }
    
    @staticmethod
    def create_register_payload(
        email: str = None,
        password: str = None,
        first_name: str = None,
        last_name: str = None
    ) -> Dict[str, str]:
        """Create registration request payload"""
        return {
            "email": email or fake.email(),
            "password": password or "TestPassword123!",
            "first_name": first_name or fake.first_name(),
            "last_name": last_name or fake.last_name()
        }
    
    @staticmethod
    def create_password_reset_payload(email: str) -> Dict[str, str]:
        """Create password reset request payload"""
        return {"email": email}
    
    @staticmethod
    def create_change_password_payload(
        current_password: str,
        new_password: str
    ) -> Dict[str, str]:
        """Create change password request payload"""
        return {
            "current_password": current_password,
            "new_password": new_password
        }


@pytest.fixture
def auth_helpers() -> AuthTestHelpers:
    """Auth test helpers"""
    return AuthTestHelpers()