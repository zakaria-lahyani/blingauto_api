import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.features.auth.domain import (
    User,
    UserRole,
    UserStatus,
    PasswordResetToken,
    EmailVerificationToken,
    RefreshToken,
)
from app.features.auth.adapters.repositories import (
    UserRepository,
    PasswordResetTokenRepository,
    EmailVerificationTokenRepository,
    RefreshTokenRepository,
)
from app.features.auth.adapters.models import (
    UserModel,
    PasswordResetTokenModel,
    EmailVerificationTokenModel,
    RefreshTokenModel,
)


@pytest.fixture(scope="function")
def test_db():
    """Create test database session."""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def user_repository(test_db):
    """Create user repository with test database."""
    return UserRepository(test_db)


@pytest.fixture
def password_reset_repository(test_db):
    """Create password reset token repository with test database."""
    return PasswordResetTokenRepository(test_db)


@pytest.fixture
def email_verification_repository(test_db):
    """Create email verification token repository with test database."""
    return EmailVerificationTokenRepository(test_db)


@pytest.fixture
def refresh_token_repository(test_db):
    """Create refresh token repository with test database."""
    return RefreshTokenRepository(test_db)


class TestUserRepository:
    """Test UserRepository database operations."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, user_repository):
        """Test creating a user in database."""
        user = User.create(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            hashed_password="hashed_password",
            role=UserRole.CLIENT,
            phone_number="+1234567890",
        )
        
        created_user = await user_repository.create(user)
        
        assert created_user.id == user.id
        assert created_user.email == user.email
        assert created_user.first_name == user.first_name
        assert created_user.last_name == user.last_name
        assert created_user.role == user.role
        assert created_user.status == user.status
        assert created_user.phone_number == user.phone_number
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, user_repository):
        """Test retrieving user by ID."""
        # Create user first
        user = User.create(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            hashed_password="hashed_password",
        )
        await user_repository.create(user)
        
        # Retrieve user
        retrieved_user = await user_repository.get_by_id(user.id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert retrieved_user.email == user.email
    
    @pytest.mark.asyncio
    async def test_get_user_by_email(self, user_repository):
        """Test retrieving user by email."""
        # Create user first
        user = User.create(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            hashed_password="hashed_password",
        )
        await user_repository.create(user)
        
        # Retrieve user by email
        retrieved_user = await user_repository.get_by_email("test@example.com")
        
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
        assert retrieved_user.id == user.id
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, user_repository):
        """Test retrieving non-existent user returns None."""
        user = await user_repository.get_by_id("nonexistent_id")
        assert user is None
        
        user = await user_repository.get_by_email("nonexistent@example.com")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_update_user(self, user_repository):
        """Test updating user in database."""
        # Create user first
        user = User.create(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            hashed_password="hashed_password",
        )
        await user_repository.create(user)
        
        # Update user
        user.first_name = "Jane"
        user.verify_email()
        
        updated_user = await user_repository.update(user)
        
        assert updated_user.first_name == "Jane"
        assert updated_user.email_verified == True
        assert updated_user.status == UserStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_email_exists(self, user_repository):
        """Test checking if email exists."""
        # Initially email doesn't exist
        exists = await user_repository.email_exists("test@example.com")
        assert not exists
        
        # Create user
        user = User.create(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            hashed_password="hashed_password",
        )
        await user_repository.create(user)
        
        # Now email exists
        exists = await user_repository.email_exists("test@example.com")
        assert exists
        
        # Different email doesn't exist
        exists = await user_repository.email_exists("other@example.com")
        assert not exists
    
    @pytest.mark.asyncio
    async def test_list_users(self, user_repository):
        """Test listing users with pagination."""
        # Create multiple users
        users = []
        for i in range(5):
            user = User.create(
                email=f"user{i}@example.com",
                first_name=f"User{i}",
                last_name="Test",
                hashed_password="hashed_password",
                role=UserRole.CLIENT if i < 3 else UserRole.WASHER,
            )
            await user_repository.create(user)
            users.append(user)
        
        # List all users
        all_users = await user_repository.list(offset=0, limit=10)
        assert len(all_users) == 5
        
        # Test pagination
        first_page = await user_repository.list(offset=0, limit=2)
        assert len(first_page) == 2
        
        second_page = await user_repository.list(offset=2, limit=2)
        assert len(second_page) == 2
        
        # Test role filter
        clients = await user_repository.list(role="client")
        assert len(clients) == 3
        
        washers = await user_repository.list(role="washer")
        assert len(washers) == 2
    
    @pytest.mark.asyncio
    async def test_count_users(self, user_repository):
        """Test counting users with filters."""
        # Create users with different roles
        for i in range(3):
            user = User.create(
                email=f"client{i}@example.com",
                first_name=f"Client{i}",
                last_name="Test",
                hashed_password="hashed_password",
                role=UserRole.CLIENT,
            )
            await user_repository.create(user)
        
        for i in range(2):
            user = User.create(
                email=f"washer{i}@example.com",
                first_name=f"Washer{i}",
                last_name="Test",
                hashed_password="hashed_password",
                role=UserRole.WASHER,
            )
            await user_repository.create(user)
        
        # Count all users
        total_count = await user_repository.count()
        assert total_count == 5
        
        # Count by role
        client_count = await user_repository.count(role="client")
        assert client_count == 3
        
        washer_count = await user_repository.count(role="washer")
        assert washer_count == 2
        
        # Count by status
        inactive_count = await user_repository.count(status="inactive")
        assert inactive_count == 5  # All users start inactive


class TestPasswordResetTokenRepository:
    """Test PasswordResetTokenRepository database operations."""
    
    @pytest.mark.asyncio
    async def test_create_token(self, password_reset_repository):
        """Test creating password reset token."""
        token = PasswordResetToken.create(user_id="user_123")
        
        created_token = await password_reset_repository.create(token)
        
        assert created_token.token == token.token
        assert created_token.user_id == token.user_id
        assert created_token.created_at == token.created_at
        assert created_token.expires_at == token.expires_at
        assert not created_token.used
    
    @pytest.mark.asyncio
    async def test_get_token_by_token_string(self, password_reset_repository):
        """Test retrieving token by token string."""
        token = PasswordResetToken.create(user_id="user_123")
        await password_reset_repository.create(token)
        
        retrieved_token = await password_reset_repository.get_by_token(token.token)
        
        assert retrieved_token is not None
        assert retrieved_token.token == token.token
        assert retrieved_token.user_id == token.user_id
    
    @pytest.mark.asyncio
    async def test_mark_token_as_used(self, password_reset_repository):
        """Test marking token as used."""
        token = PasswordResetToken.create(user_id="user_123")
        await password_reset_repository.create(token)
        
        success = await password_reset_repository.mark_as_used(token.token)
        assert success
        
        retrieved_token = await password_reset_repository.get_by_token(token.token)
        assert retrieved_token.used
    
    @pytest.mark.asyncio
    async def test_delete_expired_tokens(self, password_reset_repository):
        """Test deleting expired tokens."""
        # Create expired token
        past_time = datetime.utcnow() - timedelta(hours=2)
        expired_token = PasswordResetToken(
            token="expired_token",
            user_id="user_123",
            created_at=past_time,
            expires_at=past_time,
            used=False,
        )
        await password_reset_repository.create(expired_token)
        
        # Create valid token
        valid_token = PasswordResetToken.create(user_id="user_456")
        await password_reset_repository.create(valid_token)
        
        # Delete expired tokens
        deleted_count = await password_reset_repository.delete_expired()
        assert deleted_count == 1
        
        # Valid token should still exist
        retrieved_token = await password_reset_repository.get_by_token(valid_token.token)
        assert retrieved_token is not None
        
        # Expired token should be gone
        retrieved_expired = await password_reset_repository.get_by_token("expired_token")
        assert retrieved_expired is None


class TestEmailVerificationTokenRepository:
    """Test EmailVerificationTokenRepository database operations."""
    
    @pytest.mark.asyncio
    async def test_create_token(self, email_verification_repository):
        """Test creating email verification token."""
        token = EmailVerificationToken.create(
            user_id="user_123",
            email="test@example.com"
        )
        
        created_token = await email_verification_repository.create(token)
        
        assert created_token.token == token.token
        assert created_token.user_id == token.user_id
        assert created_token.email == token.email
        assert not created_token.used
    
    @pytest.mark.asyncio
    async def test_get_token_by_token_string(self, email_verification_repository):
        """Test retrieving token by token string."""
        token = EmailVerificationToken.create(
            user_id="user_123",
            email="test@example.com"
        )
        await email_verification_repository.create(token)
        
        retrieved_token = await email_verification_repository.get_by_token(token.token)
        
        assert retrieved_token is not None
        assert retrieved_token.token == token.token
        assert retrieved_token.email == token.email


class TestRefreshTokenRepository:
    """Test RefreshTokenRepository database operations."""
    
    @pytest.mark.asyncio
    async def test_create_token(self, refresh_token_repository):
        """Test creating refresh token."""
        token = RefreshToken.create(user_id="user_123")
        
        created_token = await refresh_token_repository.create(token)
        
        assert created_token.token == token.token
        assert created_token.user_id == token.user_id
        assert not created_token.revoked
    
    @pytest.mark.asyncio
    async def test_revoke_token(self, refresh_token_repository):
        """Test revoking refresh token."""
        token = RefreshToken.create(user_id="user_123")
        await refresh_token_repository.create(token)
        
        success = await refresh_token_repository.revoke(token.token)
        assert success
        
        retrieved_token = await refresh_token_repository.get_by_token(token.token)
        assert retrieved_token.revoked
    
    @pytest.mark.asyncio
    async def test_revoke_all_for_user(self, refresh_token_repository):
        """Test revoking all tokens for a user."""
        # Create multiple tokens for same user
        tokens = []
        for i in range(3):
            token = RefreshToken.create(user_id="user_123")
            await refresh_token_repository.create(token)
            tokens.append(token)
        
        # Create token for different user
        other_token = RefreshToken.create(user_id="user_456")
        await refresh_token_repository.create(other_token)
        
        # Revoke all tokens for user_123
        revoked_count = await refresh_token_repository.revoke_all_for_user("user_123")
        assert revoked_count == 3
        
        # Check that all tokens for user_123 are revoked
        for token in tokens:
            retrieved = await refresh_token_repository.get_by_token(token.token)
            assert retrieved.revoked
        
        # Check that other user's token is not revoked
        retrieved_other = await refresh_token_repository.get_by_token(other_token.token)
        assert not retrieved_other.revoked