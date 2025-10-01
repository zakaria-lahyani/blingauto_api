import pytest

from app.features.auth.domain.policies import (
    PasswordPolicy,
    AccountLockoutPolicy,
    EmailPolicy,
    RoleTransitionPolicy,
    SessionPolicy,
)
from app.core.errors import ValidationError, BusinessRuleViolationError


class TestPasswordPolicy:
    """Test password policy validation - RG-AUTH-002."""
    
    def test_valid_passwords(self):
        """Test valid password formats."""
        valid_passwords = [
            "password123",
            "MySecurePass1",
            "complex_password_2024",
            "P@ssw0rd!",
            "a" * 8,  # Minimum length
            "a" * 127,  # Maximum length - 1
        ]
        
        for password in valid_passwords:
            assert PasswordPolicy.validate(password)
    
    def test_password_length_validation(self):
        """Test password length requirements."""
        # Too short
        with pytest.raises(ValidationError) as exc_info:
            PasswordPolicy.validate("short")
        assert "8 characters" in str(exc_info.value)
        
        # Too long
        long_password = "a" * 129
        with pytest.raises(ValidationError) as exc_info:
            PasswordPolicy.validate(long_password)
        assert "128 characters" in str(exc_info.value)
        
        # Empty password
        with pytest.raises(ValidationError) as exc_info:
            PasswordPolicy.validate("")
        assert "required" in str(exc_info.value).lower()
    
    def test_password_weakness_validation(self):
        """Test weak password detection."""
        weak_passwords = [
            "12345678",  # All numbers
            "password",  # Common weak password
            "qwerty123",  # Another common weak password
            "admin123",   # Common weak password
        ]
        
        for password in weak_passwords:
            with pytest.raises(ValidationError) as exc_info:
                PasswordPolicy.validate(password)
            assert "password" in str(exc_info.value).lower()
    
    def test_password_strength_calculation(self):
        """Test password strength scoring."""
        test_cases = [
            ("password", 30),  # Weak password
            ("Password1", 60),  # Medium password
            ("MyP@ssw0rd123", 100),  # Strong password
            ("short", 0),  # Too short
        ]
        
        for password, expected_min_score in test_cases:
            score = PasswordPolicy.calculate_strength(password)
            assert isinstance(score, int)
            assert 0 <= score <= 100
            if len(password) >= 8:  # Only check score for valid length
                assert score >= expected_min_score


class TestAccountLockoutPolicy:
    """Test account lockout policy - RG-AUTH-006."""
    
    def test_lockout_threshold(self):
        """Test lockout threshold detection."""
        # Below threshold
        assert not AccountLockoutPolicy.should_lock_account(4)
        
        # At threshold
        assert AccountLockoutPolicy.should_lock_account(5)
        
        # Above threshold
        assert AccountLockoutPolicy.should_lock_account(10)
    
    def test_lockout_duration_calculation(self):
        """Test progressive lockout duration."""
        test_cases = [
            (0, 0),    # No failures
            (3, 0),    # Below threshold
            (5, 30),   # First lockout
            (10, 60),  # Second violation
            (15, 90),  # Third violation
            (25, 120), # Fourth violation (max)
        ]
        
        for attempts, expected_duration in test_cases:
            duration = AccountLockoutPolicy.calculate_lockout_duration(attempts)
            assert duration == expected_duration


class TestEmailPolicy:
    """Test email validation policy - RG-AUTH-001."""
    
    def test_valid_emails(self):
        """Test valid email validation and normalization."""
        test_cases = [
            ("test@example.com", "test@example.com"),
            ("Test@Example.COM", "test@example.com"),  # Normalization
            ("  user@domain.org  ", "user@domain.org"),  # Trimming
            ("user.name+tag@sub.domain.co.uk", "user.name+tag@sub.domain.co.uk"),
        ]
        
        for input_email, expected_output in test_cases:
            result = EmailPolicy.validate_email(input_email)
            assert result == expected_output
    
    def test_invalid_emails(self):
        """Test invalid email detection."""
        invalid_emails = [
            "",
            "invalid",
            "test@",
            "@example.com",
            "test.example.com",
            "test..test@example.com",
            "a" * 250 + "@test.com",  # Too long
            "test@tempmail.com",  # Disposable email
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError) as exc_info:
                EmailPolicy.validate_email(email)
            assert "email" in str(exc_info.value).lower()
    
    def test_disposable_email_detection(self):
        """Test disposable email domain blocking."""
        disposable_emails = [
            "test@tempmail.com",
            "user@guerrillamail.com",
            "temp@10minutemail.com",
        ]
        
        for email in disposable_emails:
            with pytest.raises(ValidationError) as exc_info:
                EmailPolicy.validate_email(email)
            assert "disposable" in str(exc_info.value).lower()


class TestRoleTransitionPolicy:
    """Test role transition policy - RG-AUTH-009."""
    
    def test_valid_role_transitions(self):
        """Test allowed role transitions."""
        valid_transitions = [
            ("client", "washer"),
            ("washer", "client"),
            ("washer", "manager"),
            ("manager", "washer"),
            ("manager", "admin"),
            ("admin", "manager"),
            ("client", "client"),  # Same role
        ]
        
        for current, new in valid_transitions:
            assert RoleTransitionPolicy.can_transition(current, new)
    
    def test_invalid_role_transitions(self):
        """Test disallowed role transitions."""
        invalid_transitions = [
            ("client", "admin"),  # Cannot jump directly to admin
            ("client", "manager"),  # Cannot jump directly to manager
            ("washer", "admin"),  # Cannot jump directly to admin
        ]
        
        for current, new in invalid_transitions:
            assert not RoleTransitionPolicy.can_transition(current, new)
    
    def test_transition_validation_with_initiator(self):
        """Test transition validation with initiator role check."""
        # Admin can perform valid transitions
        assert RoleTransitionPolicy.validate_transition(
            current_role="client",
            new_role="washer",
            initiator_role="admin"
        )
        
        # Non-admin cannot change roles
        with pytest.raises(BusinessRuleViolationError) as exc_info:
            RoleTransitionPolicy.validate_transition(
                current_role="client",
                new_role="washer",
                initiator_role="manager"
            )
        assert "administrator" in str(exc_info.value).lower()
        
        # Admin cannot perform invalid transitions
        with pytest.raises(BusinessRuleViolationError) as exc_info:
            RoleTransitionPolicy.validate_transition(
                current_role="client",
                new_role="admin",
                initiator_role="admin"
            )
        assert "cannot transition" in str(exc_info.value).lower()


class TestSessionPolicy:
    """Test session management policy - RG-AUTH-005."""
    
    def test_refresh_token_rotation_policy(self):
        """Test refresh token rotation policy."""
        # Currently always rotates for security
        assert SessionPolicy.should_rotate_refresh_token(1)
        assert SessionPolicy.should_rotate_refresh_token(5)
        assert SessionPolicy.should_rotate_refresh_token(10)
    
    def test_session_expiry_check(self):
        """Test session expiry logic."""
        # With no last activity, not expired
        assert not SessionPolicy.is_session_expired(None)
        
        # Implementation placeholder - would need actual timestamp logic
        assert not SessionPolicy.is_session_expired("2024-01-01T12:00:00Z")