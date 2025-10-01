import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import asyncio
import os

from app.features.auth.domain import (
    User,
    UserRole,
    UserStatus,
    PasswordResetToken,
    EmailVerificationToken,
    RefreshToken,
)
from app.features.auth.ports import (
    IUserRepository,
    IPasswordResetTokenRepository,
    IEmailVerificationTokenRepository,
    IRefreshTokenRepository,
    IPasswordHasher,
    ITokenService,
    IEmailService,
    ICacheService,
)




@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User.create(
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        hashed_password="hashed_password_123",
        role=UserRole.CLIENT,
        phone_number="+1234567890",
    )


@pytest.fixture
def admin_user():
    """Create an admin user for testing."""
    user = User.create(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        hashed_password="hashed_admin_password",
        role=UserRole.ADMIN,
    )
    user.verify_email()  # Make admin active
    return user


@pytest.fixture
def mock_user_repository():
    """Mock user repository."""
    mock = Mock(spec=IUserRepository)
    mock.get_by_id = AsyncMock()
    mock.get_by_email = AsyncMock()
    mock.create = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    mock.list = AsyncMock()
    mock.count = AsyncMock()
    mock.email_exists = AsyncMock()
    return mock


@pytest.fixture
def mock_password_reset_repository():
    """Mock password reset token repository."""
    mock = Mock(spec=IPasswordResetTokenRepository)
    mock.create = AsyncMock()
    mock.get_by_token = AsyncMock()
    mock.mark_as_used = AsyncMock()
    mock.delete_expired = AsyncMock()
    return mock


@pytest.fixture
def mock_email_verification_repository():
    """Mock email verification token repository."""
    mock = Mock(spec=IEmailVerificationTokenRepository)
    mock.create = AsyncMock()
    mock.get_by_token = AsyncMock()
    mock.mark_as_used = AsyncMock()
    mock.delete_expired = AsyncMock()
    return mock


@pytest.fixture
def mock_refresh_token_repository():
    """Mock refresh token repository."""
    mock = Mock(spec=IRefreshTokenRepository)
    mock.create = AsyncMock()
    mock.get_by_token = AsyncMock()
    mock.revoke = AsyncMock()
    mock.revoke_all_for_user = AsyncMock()
    mock.delete_expired = AsyncMock()
    return mock


@pytest.fixture
def mock_password_hasher():
    """Mock password hasher."""
    mock = Mock(spec=IPasswordHasher)
    mock.hash.return_value = "hashed_password"
    mock.verify.return_value = True
    return mock


@pytest.fixture
def mock_token_service():
    """Mock token service."""
    mock = Mock(spec=ITokenService)
    mock.create_access_token.return_value = "access_token_123"
    mock.create_refresh_token.return_value = "refresh_token_123"
    mock.validate_access_token.return_value = {"sub": "user_id", "role": "client"}
    mock.validate_refresh_token.return_value = {"sub": "user_id"}
    return mock


@pytest.fixture
def mock_email_service():
    """Mock email service."""
    mock = Mock(spec=IEmailService)
    mock.send_verification_email = AsyncMock(return_value=True)
    mock.send_password_reset_email = AsyncMock(return_value=True)
    mock.send_welcome_email = AsyncMock(return_value=True)
    mock.send_account_locked_email = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_cache_service():
    """Mock cache service."""
    mock = Mock(spec=ICacheService)
    mock.get_user = AsyncMock()
    mock.set_user = AsyncMock(return_value=True)
    mock.delete_user = AsyncMock(return_value=True)
    mock.get_session = AsyncMock()
    mock.set_session = AsyncMock(return_value=True)
    mock.delete_session = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def password_reset_token():
    """Create a password reset token for testing."""
    return PasswordResetToken.create(user_id="user_123")


@pytest.fixture
def email_verification_token():
    """Create an email verification token for testing."""
    return EmailVerificationToken.create(
        user_id="user_123",
        email="test@example.com"
    )


@pytest.fixture
def refresh_token():
    """Create a refresh token for testing."""
    return RefreshToken.create(user_id="user_123")


# Test environment configuration
@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """Set up test environment variables."""
    test_env = {
        "ENVIRONMENT": "testing",
        "DATABASE_URL": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "REDIS_URL": "",  # Disable Redis for tests
        "DEBUG": "false",
        "LOG_LEVEL": "ERROR",  # Reduce logging noise in tests
    }
    
    with patch.dict(os.environ, test_env, clear=True):
        yield


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()