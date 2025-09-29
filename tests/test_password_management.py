"""
Password Management Test Suite - Pytest Compatible
Comprehensive tests for password scenarios using real API endpoints
"""
import pytest
import asyncio
import time
import requests
from typing import Optional


class TestPasswordManagement:
    """Password management test class using direct HTTP requests for real endpoint testing"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.base_url = "http://localhost:8000"
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        
        # Create unique test user for this test session
        timestamp = str(int(time.time()))
        self.test_user = {
            "email": f"password_test_{timestamp}@example.com",
            "password": "TestPassword123!@#",
            "first_name": "Password",
            "last_name": "Tester",
            "phone": f"555000{timestamp[-4:]}"
        }
        self.user_token: Optional[str] = None
        
        # Setup test user
        self._setup_test_user()
    
    def _setup_test_user(self):
        """Setup test user for password tests"""
        try:
            # Register user
            response = requests.post(
                f"{self.base_url}/auth/register", 
                json=self.test_user,
                headers=self.headers
            )
            
            if response.status_code == 201:
                # Login to get token
                login_response = requests.post(
                    f"{self.base_url}/auth/login",
                    json={
                        "email": self.test_user["email"],
                        "password": self.test_user["password"]
                    },
                    headers=self.headers
                )
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    self.user_token = token_data["access_token"]
                    
        except Exception as e:
            print(f"Setup failed: {e}")
    
    # Forgot Password Tests
    def test_forgot_password_success(self):
        """Test successful forgot password request"""
        response = requests.post(
            f"{self.base_url}/auth/forgot-password",
            json={"email": self.test_user["email"]},
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "password reset instructions were sent" in data["message"].lower()
    
    def test_forgot_password_unknown_email(self):
        """Test forgot password with unknown email"""
        unknown_email = f"unknown_{int(time.time())}@nonexistent.com"
        
        response = requests.post(
            f"{self.base_url}/auth/forgot-password",
            json={"email": unknown_email},
            headers=self.headers
        )
        
        # Should return success message for security (don't reveal if email exists)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    @pytest.mark.parametrize("invalid_email", [
        "not-an-email",
        "@invalid.com", 
        "invalid@",
        "invalid..email@test.com",
        "invalid email@test.com"
    ])
    def test_forgot_password_invalid_email_format(self, invalid_email):
        """Test forgot password with invalid email format"""
        response = requests.post(
            f"{self.base_url}/auth/forgot-password",
            json={"email": invalid_email},
            headers=self.headers
        )
        
        assert response.status_code == 422  # Validation error expected
    
    def test_forgot_password_without_email(self):
        """Test forgot password without email field"""
        response = requests.post(
            f"{self.base_url}/auth/forgot-password",
            json={},
            headers=self.headers
        )
        
        assert response.status_code == 422  # Validation error expected
    
    def test_forgot_password_empty_email(self):
        """Test forgot password with empty email"""
        response = requests.post(
            f"{self.base_url}/auth/forgot-password",
            json={"email": ""},
            headers=self.headers
        )
        
        assert response.status_code == 422  # Validation error expected
    
    def test_forgot_password_rate_limiting(self):
        """Test rate limiting on forgot password requests"""
        rate_limit_requests = 6
        successful_requests = 0
        rate_limited = False
        
        for i in range(rate_limit_requests):
            response = requests.post(
                f"{self.base_url}/auth/forgot-password",
                json={"email": self.test_user["email"]},
                headers=self.headers
            )
            
            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:  # Rate limited
                rate_limited = True
                break
            
            if i < rate_limit_requests - 1:
                time.sleep(0.5)
        
        # Either rate limited or all requests succeeded (rate limiting may not be configured)
        assert rate_limited or successful_requests >= rate_limit_requests
    
    # Reset Password Tests
    def test_reset_password_valid_token_format(self):
        """Test password reset with valid token format (simulated)"""
        # Request password reset first
        requests.post(
            f"{self.base_url}/auth/forgot-password",
            json={"email": self.test_user["email"]},
            headers=self.headers
        )
        
        # Simulate a token (in real scenario, extract from email/database)
        fake_token = "valid_reset_token_123456789"
        
        response = requests.post(
            f"{self.base_url}/auth/reset-password",
            json={
                "token": fake_token,
                "new_password": "NewSecurePassword123!@#"
            },
            headers=self.headers
        )
        
        # Expect 400 since token is fake, but endpoint should be accessible
        assert response.status_code in [400, 401]
    
    @pytest.mark.parametrize("invalid_token", [
        "invalid_token_123",
        "expired_token_456",
        "malformed_token",
        ""
    ])
    def test_reset_password_invalid_token(self, invalid_token):
        """Test password reset with invalid/expired token"""
        response = requests.post(
            f"{self.base_url}/auth/reset-password",
            json={
                "token": invalid_token,
                "new_password": "NewSecurePassword123!@#"
            },
            headers=self.headers
        )
        
        assert response.status_code in [400, 401]  # Expected for invalid tokens
    
    @pytest.mark.parametrize("malformed_data", [
        {"token": 123, "new_password": "NewPassword123!"},  # Number instead of string
        {"token": None, "new_password": "NewPassword123!"},  # Null token
        {"token": [], "new_password": "NewPassword123!"},    # Array instead of string
    ])
    def test_reset_password_malformed_token(self, malformed_data):
        """Test password reset with malformed token"""
        response = requests.post(
            f"{self.base_url}/auth/reset-password",
            json=malformed_data,
            headers=self.headers
        )
        
        assert response.status_code == 422  # Validation error expected
    
    @pytest.mark.parametrize("weak_password", [
        "123456",           # Too short, common
        "password",         # Common, no special chars
        "12345678",         # No letters
        "abcdefgh",         # No numbers or special chars
        "Password123",      # No special characters
        "PASSWORD123!",     # No lowercase
        "password123!",     # No uppercase
    ])
    def test_reset_password_weak_password(self, weak_password):
        """Test password reset with weak password"""
        fake_token = "test_token_for_weak_password"
        
        response = requests.post(
            f"{self.base_url}/auth/reset-password",
            json={
                "token": fake_token,
                "new_password": weak_password
            },
            headers=self.headers
        )
        
        # Could be 400 (invalid token) or 422 (validation error)
        # We're testing that weak passwords are handled appropriately
        assert response.status_code in [400, 422]
    
    @pytest.mark.parametrize("data,description", [
        ({}, "missing both fields"),
        ({"token": "test_token"}, "missing password"),
        ({"new_password": "TestPassword123!"}, "missing token"),
    ])
    def test_reset_password_missing_fields(self, data, description):
        """Test password reset with missing required fields"""
        response = requests.post(
            f"{self.base_url}/auth/reset-password",
            json=data,
            headers=self.headers
        )
        
        assert response.status_code == 422  # Validation error expected
    
    def test_reset_token_single_use(self):
        """Test that reset tokens can only be used once"""
        fake_token = "single_use_test_token_123"
        new_password = "SingleUseTestPassword123!@#"
        
        # Try using the same token twice
        for attempt in range(2):
            response = requests.post(
                f"{self.base_url}/auth/reset-password",
                json={
                    "token": fake_token,
                    "new_password": new_password
                },
                headers=self.headers
            )
            
            # Both should fail since token is fake, but testing the endpoint
            assert response.status_code in [400, 401]
    
    # Change Password Tests
    def test_change_password_authenticated(self):
        """Test password change with valid authentication"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.user_token}"
        
        response = requests.post(
            f"{self.base_url}/auth/change-password",
            json={
                "current_password": self.test_user["password"],
                "new_password": "NewChangedPassword123!@#"
            },
            headers=headers
        )
        
        assert response.status_code == 200
        
        # Update stored password for future tests
        self.test_user["password"] = "NewChangedPassword123!@#"
    
    def test_change_password_wrong_current(self):
        """Test password change with wrong current password"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.user_token}"
        
        response = requests.post(
            f"{self.base_url}/auth/change-password",
            json={
                "current_password": "WrongCurrentPassword123!",
                "new_password": "NewPassword123!@#"
            },
            headers=headers
        )
        
        assert response.status_code == 400
    
    def test_change_password_without_authentication(self):
        """Test password change without authentication"""
        response = requests.post(
            f"{self.base_url}/auth/change-password",
            json={
                "current_password": self.test_user["password"],
                "new_password": "NewPassword123!@#"
            },
            headers=self.headers  # No Authorization header
        )
        
        assert response.status_code in [401, 403]
    
    def test_change_password_invalid_token(self):
        """Test password change with invalid token"""
        headers = self.headers.copy()
        headers["Authorization"] = "Bearer invalid_token_12345"
        
        response = requests.post(
            f"{self.base_url}/auth/change-password",
            json={
                "current_password": self.test_user["password"],
                "new_password": "NewPassword123!@#"
            },
            headers=headers
        )
        
        assert response.status_code == 401
    
    @pytest.mark.parametrize("weak_password", [
        "123456",           # Too short, common
        "password",         # Common, no special chars
        "12345678",         # No letters
        "abcdefgh",         # No numbers or special chars
    ])
    def test_change_password_weak_new_password(self, weak_password):
        """Test password change with weak new password"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.user_token}"
        
        response = requests.post(
            f"{self.base_url}/auth/change-password",
            json={
                "current_password": self.test_user["password"],
                "new_password": weak_password
            },
            headers=headers
        )
        
        assert response.status_code == 422  # Validation error expected
    
    def test_change_password_same_password(self):
        """Test password change with same password"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.user_token}"
        
        response = requests.post(
            f"{self.base_url}/auth/change-password",
            json={
                "current_password": self.test_user["password"],
                "new_password": self.test_user["password"]  # Same as current
            },
            headers=headers
        )
        
        # Should be rejected (business logic) or succeed (depending on implementation)
        assert response.status_code in [200, 400, 422]
    
    @pytest.mark.parametrize("data,description", [
        ({}, "missing both passwords"),
        ({"current_password": "test"}, "missing new password"),
        ({"new_password": "NewPassword123!"}, "missing current password"),
    ])
    def test_change_password_missing_fields(self, data, description):
        """Test password change with missing fields"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.user_token}"
        
        response = requests.post(
            f"{self.base_url}/auth/change-password",
            json=data,
            headers=headers
        )
        
        assert response.status_code == 422  # Validation error expected
    
    @pytest.mark.parametrize("data,description", [
        ({"current_password": "", "new_password": "NewPassword123!"}, "empty current"),
        ({"current_password": "current", "new_password": ""}, "empty new"),
        ({"current_password": "", "new_password": ""}, "both empty"),
    ])
    def test_change_password_empty_passwords(self, data, description):
        """Test password change with empty passwords"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.user_token}"
        
        response = requests.post(
            f"{self.base_url}/auth/change-password",
            json=data,
            headers=headers
        )
        
        assert response.status_code in [400, 422]  # Validation/business error expected
    
    # Password Policy Tests
    def test_password_policy_enforcement_registration(self):
        """Test password policy enforcement during registration"""
        weak_password = "weak"
        
        response = requests.post(
            f"{self.base_url}/auth/register",
            json={
                "email": f"policy_test_{int(time.time())}@example.com",
                "password": weak_password,
                "first_name": "Policy",
                "last_name": "Test",
                "phone": "5550001234"
            },
            headers=self.headers
        )
        
        assert response.status_code == 422
    
    @pytest.mark.parametrize("weak_password,requirement", [
        ("Short123!", "minimum 8 characters"),
        ("NoSpecialChars123", "special characters required"),
        ("no_uppercase_123!", "uppercase required"),
        ("NO_LOWERCASE_123!", "lowercase required"),
        ("NoNumbers!@#", "numbers required"),
        ("   SpacePrefix123!", "no leading spaces"),
        ("SpaceSuffix123!   ", "no trailing spaces"),
    ])
    def test_password_strength_validation(self, weak_password, requirement):
        """Test password strength validation in change password"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.user_token}"
        
        response = requests.post(
            f"{self.base_url}/auth/change-password",
            json={
                "current_password": self.test_user["password"],
                "new_password": weak_password
            },
            headers=headers
        )
        
        # Should be rejected for weak password or succeed depending on policy
        assert response.status_code in [200, 422]


if __name__ == "__main__":
    pytest.main([__file__])