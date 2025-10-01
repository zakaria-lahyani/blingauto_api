import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from app.features.auth.domain import User, UserRole, UserStatus
from app.core.errors import ValidationError, BusinessRuleViolationError


class TestUserEntity:
    """Test User domain entity business rules."""
    
    def test_create_user_with_valid_data(self):
        """Test creating user with valid data."""
        user = User.create(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            hashed_password="hashed_password",
            role=UserRole.CLIENT,
            phone_number="+1234567890",
        )
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.full_name == "John Doe"
        assert user.role == UserRole.CLIENT
        assert user.status == UserStatus.INACTIVE
        assert user.phone_number == "+1234567890"
        assert not user.email_verified
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
    
    def test_email_validation_success(self):
        """Test valid email formats."""
        valid_emails = [
            "test@example.com",
            "user.name+tag@domain.co.uk",
            "test123@test-domain.com",
        ]
        
        for email in valid_emails:
            user = User.create(
                email=email,
                first_name="Test",
                last_name="User",
                hashed_password="hashed_password",
            )
            assert user.email == email.lower()
    
    def test_email_validation_failure(self):
        """Test invalid email formats - RG-AUTH-001."""
        invalid_emails = [
            "",
            "invalid",
            "test@",
            "@example.com",
            "test.example.com",
            "test..test@example.com",
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError) as exc_info:
                User.create(
                    email=email,
                    first_name="Test",
                    last_name="User",
                    hashed_password="hashed_password",
                )
            assert "email" in str(exc_info.value).lower()
    
    def test_email_length_validation(self):
        """Test email length validation - RG-AUTH-001."""
        # Email too long (> 255 characters)
        long_email = "a" * 250 + "@test.com"
        
        with pytest.raises(ValidationError) as exc_info:
            User.create(
                email=long_email,
                first_name="Test",
                last_name="User",
                hashed_password="hashed_password",
            )
        assert "255 characters" in str(exc_info.value)
    
    def test_name_validation_success(self):
        """Test valid name formats - RG-AUTH-003."""
        user = User.create(
            email="test@example.com",
            first_name="  john  ",  # Should be trimmed and title-cased
            last_name="  doe  ",   # Should be trimmed and title-cased
            hashed_password="hashed_password",
        )
        
        assert user.first_name == "John"
        assert user.last_name == "Doe"
    
    def test_name_validation_failure(self):
        """Test invalid name formats - RG-AUTH-003."""
        # Empty first name
        with pytest.raises(ValidationError) as exc_info:
            User.create(
                email="test@example.com",
                first_name="",
                last_name="Doe",
                hashed_password="hashed_password",
            )
        assert "first_name" in str(exc_info.value).lower()
        
        # Empty last name
        with pytest.raises(ValidationError) as exc_info:
            User.create(
                email="test@example.com",
                first_name="John",
                last_name="",
                hashed_password="hashed_password",
            )
        assert "last_name" in str(exc_info.value).lower()
        
        # Name too long
        long_name = "a" * 101
        with pytest.raises(ValidationError) as exc_info:
            User.create(
                email="test@example.com",
                first_name=long_name,
                last_name="Doe",
                hashed_password="hashed_password",
            )
        assert "100 characters" in str(exc_info.value)
    
    def test_phone_validation_success(self):
        """Test valid phone formats - RG-AUTH-004."""
        valid_phones = [
            "+1234567890",
            "1234567890",
            "+33123456789",
            None,  # Phone is optional
        ]
        
        for phone in valid_phones:
            user = User.create(
                email="test@example.com",
                first_name="Test",
                last_name="User",
                hashed_password="hashed_password",
                phone_number=phone,
            )
            assert user.phone_number == phone
    
    def test_phone_validation_failure(self):
        """Test invalid phone formats - RG-AUTH-004."""
        invalid_phones = [
            "abc123",
            "123-abc-4567",
            "+" * 25,  # Too long
        ]
        
        for phone in invalid_phones:
            with pytest.raises(ValidationError) as exc_info:
                User.create(
                    email="test@example.com",
                    first_name="Test",
                    last_name="User",
                    hashed_password="hashed_password",
                    phone_number=phone,
                )
            assert "phone" in str(exc_info.value).lower()
    
    def test_user_properties(self):
        """Test user property methods."""
        user = User.create(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            hashed_password="hashed_password",
            role=UserRole.ADMIN,
        )
        
        # Initially inactive
        assert not user.is_active
        assert not user.is_locked
        assert user.is_admin
        assert user.is_staff
        
        # After email verification
        user.verify_email()
        assert user.is_active
        assert user.email_verified
        assert user.status == UserStatus.ACTIVE
    
    def test_login_attempt_tracking(self):
        """Test failed login attempt tracking - RG-AUTH-006."""
        user = User.create(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_password",
        )
        user.verify_email()  # Make user active
        
        # Initially can login
        assert user.can_login()
        
        # Record failed attempts
        for i in range(4):
            user.record_failed_login()
            assert user.failed_login_attempts == i + 1
            assert not user.is_locked
        
        # 5th failed attempt should lock account
        user.record_failed_login()
        assert user.failed_login_attempts == 5
        assert user.is_locked
        assert user.locked_until is not None
        
        # Cannot login when locked
        with pytest.raises(BusinessRuleViolationError) as exc_info:
            user.can_login()
        assert "locked" in str(exc_info.value).lower()
    
    def test_successful_login_resets_attempts(self):
        """Test successful login resets failed attempts."""
        user = User.create(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_password",
        )
        user.verify_email()
        
        # Record some failed attempts
        user.record_failed_login()
        user.record_failed_login()
        assert user.failed_login_attempts == 2
        
        # Successful login resets
        user.record_successful_login()
        assert user.failed_login_attempts == 0
        assert user.locked_until is None
        assert user.last_login_at is not None
    
    def test_email_verification(self):
        """Test email verification process - RG-AUTH-007."""
        user = User.create(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_password",
        )
        
        # Initially unverified and inactive
        assert not user.email_verified
        assert user.status == UserStatus.INACTIVE
        
        # Cannot login without verification
        with pytest.raises(BusinessRuleViolationError) as exc_info:
            user.can_login()
        assert "verification" in str(exc_info.value).lower()
        
        # Verify email
        user.verify_email()
        assert user.email_verified
        assert user.email_verified_at is not None
        assert user.status == UserStatus.ACTIVE
        assert user.can_login()
        
        # Cannot verify again
        with pytest.raises(BusinessRuleViolationError) as exc_info:
            user.verify_email()
        assert "already verified" in str(exc_info.value).lower()
    
    def test_password_change(self):
        """Test password change functionality."""
        user = User.create(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="old_password",
        )
        
        original_changed_at = user.password_changed_at
        
        user.change_password("new_hashed_password")
        
        assert user.hashed_password == "new_hashed_password"
        assert user.password_changed_at != original_changed_at
        assert user.password_changed_at is not None
    
    def test_profile_update(self):
        """Test profile update functionality."""
        user = User.create(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            hashed_password="hashed_password",
            phone_number="+1234567890",
        )
        
        original_updated_at = user.updated_at
        
        user.update_profile(
            first_name="Jane",
            last_name="Smith",
            phone_number="+9876543210",
        )
        
        assert user.first_name == "Jane"
        assert user.last_name == "Smith"
        assert user.phone_number == "+9876543210"
        assert user.updated_at > original_updated_at
    
    def test_account_status_transitions(self):
        """Test account status transitions."""
        user = User.create(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_password",
        )
        
        # Start inactive
        assert user.status == UserStatus.INACTIVE
        
        # Verify email activates
        user.verify_email()
        assert user.status == UserStatus.ACTIVE
        
        # Can suspend active user
        user.suspend()
        assert user.status == UserStatus.SUSPENDED
        
        # Cannot suspend again
        with pytest.raises(BusinessRuleViolationError):
            user.suspend()
        
        # Can reactivate suspended user
        user.reactivate()
        assert user.status == UserStatus.ACTIVE
        
        # Can soft delete
        user.soft_delete()
        assert user.status == UserStatus.DELETED
        
        # Cannot reactivate deleted user
        with pytest.raises(BusinessRuleViolationError):
            user.reactivate()


class TestPasswordResetToken:
    """Test PasswordResetToken entity."""
    
    def test_create_token(self):
        """Test creating password reset token."""
        token = PasswordResetToken.create(user_id="user_123")
        
        assert token.token is not None
        assert token.user_id == "user_123"
        assert token.created_at is not None
        assert token.expires_at is not None
        assert not token.used
        assert token.is_valid
    
    def test_token_expiry(self):
        """Test token expiry logic."""
        # Create token with past expiry
        past_time = datetime.utcnow() - timedelta(hours=2)
        token = PasswordResetToken(
            token="test_token",
            user_id="user_123",
            created_at=past_time,
            expires_at=past_time,
            used=False,
        )
        
        assert token.is_expired
        assert not token.is_valid
    
    def test_token_usage(self):
        """Test token usage."""
        token = PasswordResetToken.create(user_id="user_123")
        
        assert token.is_valid
        
        # Use token
        token.use()
        assert token.used
        assert not token.is_valid
        
        # Cannot use again
        with pytest.raises(BusinessRuleViolationError) as exc_info:
            token.use()
        assert "already used" in str(exc_info.value).lower()


class TestEmailVerificationToken:
    """Test EmailVerificationToken entity."""
    
    def test_create_token(self):
        """Test creating email verification token."""
        token = EmailVerificationToken.create(
            user_id="user_123",
            email="test@example.com"
        )
        
        assert token.token is not None
        assert token.user_id == "user_123"
        assert token.email == "test@example.com"
        assert token.created_at is not None
        assert token.expires_at is not None
        assert not token.used
        assert token.is_valid
    
    def test_token_expiry_24_hours(self):
        """Test token expires after 24 hours."""
        # Create token with past expiry
        past_time = datetime.utcnow() - timedelta(hours=25)
        token = EmailVerificationToken(
            token="test_token",
            user_id="user_123",
            email="test@example.com",
            created_at=past_time,
            expires_at=past_time,
            used=False,
        )
        
        assert token.is_expired
        assert not token.is_valid


class TestRefreshToken:
    """Test RefreshToken entity."""
    
    def test_create_token(self):
        """Test creating refresh token."""
        token = RefreshToken.create(user_id="user_123")
        
        assert token.token is not None
        assert token.user_id == "user_123"
        assert token.created_at is not None
        assert token.expires_at is not None
        assert not token.revoked
        assert token.is_valid
    
    def test_token_revocation(self):
        """Test token revocation."""
        token = RefreshToken.create(user_id="user_123")
        
        assert token.is_valid
        
        token.revoke()
        assert token.revoked
        assert not token.is_valid
    
    def test_token_rotation(self):
        """Test token rotation."""
        original_token = RefreshToken.create(user_id="user_123")
        
        new_token = original_token.rotate()
        
        # Original token should be revoked
        assert original_token.revoked
        assert not original_token.is_valid
        
        # New token should be valid
        assert not new_token.revoked
        assert new_token.is_valid
        assert new_token.user_id == original_token.user_id
        assert new_token.token != original_token.token