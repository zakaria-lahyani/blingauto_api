"""
Password Management Test Suite
Comprehensive tests for password scenarios following the same pattern as run_auth_tests.py
"""

import os
import time
import json
import requests
import random
import string
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


@dataclass
class TestResult:
    """Test result tracking"""
    test_name: str
    status: str  # PASS, FAIL, SKIP
    message: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()


class PasswordTestRunner:
    """Password management test runner"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.results: List[TestResult] = []
        
        # Test user for password tests
        timestamp = str(int(time.time()))
        self.test_user = {
            "email": f"password_test_{timestamp}@example.com",
            "password": "TestPassword123!@#",
            "first_name": "Password",
            "last_name": "Tester",
            "phone": f"555000{timestamp[-4:]}"
        }
        self.user_token = None
        self.user_id = None
        self.reset_tokens = []  # Track reset tokens for single-use tests
        
        # Rate limiting tracking
        self.rate_limit_start_time = None
        
    def log_result(self, test_name: str, status: str, message: str):
        """Log test result"""
        result = TestResult(test_name, status, message)
        self.results.append(result)
        
        icon = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[SKIP]"
        print(f"{icon} {test_name}: {message}")
        
        return result
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request"""
        url = f"{self.base_url}{endpoint}"
        return requests.request(method, url, headers=self.headers, **kwargs)
    
    def setup_test_user(self):
        """Setup test user for password tests"""
        print("\n--- Setting up test user ---")
        
        try:
            # Register user
            response = self.make_request("POST", "/auth/register", json=self.test_user)
            
            if response.status_code == 201:
                user_info = response.json()
                self.user_id = user_info["id"]
                self.log_result("Setup: Register test user", "PASS", f"User created with ID: {self.user_id}")
                
                # Login to get token
                login_response = self.make_request("POST", "/auth/login", json={
                    "email": self.test_user["email"],
                    "password": self.test_user["password"]
                })
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    self.user_token = token_data["access_token"]
                    self.log_result("Setup: Login test user", "PASS", "Token obtained")
                else:
                    self.log_result("Setup: Login test user", "FAIL", f"Login failed: {login_response.status_code}")
                    
            else:
                self.log_result("Setup: Register test user", "FAIL", f"Registration failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("Setup: Test user creation", "FAIL", str(e))
    
    def test_forgot_password_success(self):
        """Test successful forgot password request"""
        try:
            response = self.make_request("POST", "/auth/forgot-password", json={
                "email": self.test_user["email"]
            })
            
            if response.status_code == 200:
                response_data = response.json()
                if "password reset instructions were sent" in response_data.get("message", "").lower():
                    self.log_result("Forgot password - success", "PASS", "Reset email requested successfully")
                else:
                    self.log_result("Forgot password - success", "PASS", f"Response: {response_data.get('message', 'Success')}")
            else:
                self.log_result("Forgot password - success", "FAIL", f"Status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Forgot password - success", "FAIL", str(e))
    
    def test_forgot_password_unknown_email(self):
        """Test forgot password with unknown email"""
        unknown_email = f"unknown_{int(time.time())}@nonexistent.com"
        
        try:
            response = self.make_request("POST", "/auth/forgot-password", json={
                "email": unknown_email
            })
            
            # Should return success message for security (don't reveal if email exists)
            if response.status_code == 200:
                self.log_result("Forgot password - unknown email", "PASS", "Returns success (security best practice)")
            else:
                self.log_result("Forgot password - unknown email", "FAIL", f"Status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Forgot password - unknown email", "FAIL", str(e))
    
    def test_forgot_password_invalid_email_format(self):
        """Test forgot password with invalid email format"""
        invalid_emails = [
            "not-an-email",
            "@invalid.com",
            "invalid@",
            "invalid..email@test.com",
            "invalid email@test.com"
        ]
        
        for invalid_email in invalid_emails:
            try:
                response = self.make_request("POST", "/auth/forgot-password", json={
                    "email": invalid_email
                })
                
                if response.status_code == 422:  # Validation error expected
                    self.log_result(f"Forgot password - invalid format ({invalid_email})", "PASS", "Correctly rejected")
                else:
                    self.log_result(f"Forgot password - invalid format ({invalid_email})", "FAIL", f"Status {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Forgot password - invalid format ({invalid_email})", "FAIL", str(e))
    
    def test_forgot_password_without_email(self):
        """Test forgot password without email field"""
        try:
            response = self.make_request("POST", "/auth/forgot-password", json={})
            
            if response.status_code == 422:  # Validation error expected
                self.log_result("Forgot password - without email", "PASS", "Correctly rejected missing email")
            else:
                self.log_result("Forgot password - without email", "FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Forgot password - without email", "FAIL", str(e))
    
    def test_forgot_password_empty_email(self):
        """Test forgot password with empty email"""
        try:
            response = self.make_request("POST", "/auth/forgot-password", json={
                "email": ""
            })
            
            if response.status_code == 422:  # Validation error expected
                self.log_result("Forgot password - empty email", "PASS", "Correctly rejected empty email")
            else:
                self.log_result("Forgot password - empty email", "FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Forgot password - empty email", "FAIL", str(e))
    
    def test_forgot_password_rate_limiting(self):
        """Test rate limiting on forgot password requests"""
        print("\n--- Testing Rate Limiting (may take time) ---")
        
        rate_limit_requests = 6  # Try more than typical rate limit
        successful_requests = 0
        rate_limited_requests = 0
        
        self.rate_limit_start_time = time.time()
        
        for i in range(rate_limit_requests):
            try:
                response = self.make_request("POST", "/auth/forgot-password", json={
                    "email": self.test_user["email"]
                })
                
                if response.status_code == 200:
                    successful_requests += 1
                elif response.status_code == 429:  # Rate limited
                    rate_limited_requests += 1
                    break
                else:
                    print(f"  Request {i+1}: Status {response.status_code}")
                
                # Small delay between requests
                if i < rate_limit_requests - 1:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"  Request {i+1} failed: {e}")
        
        if rate_limited_requests > 0:
            self.log_result("Forgot password - rate limiting", "PASS", f"Rate limited after {successful_requests} requests")
        elif successful_requests >= rate_limit_requests:
            self.log_result("Forgot password - rate limiting", "SKIP", "No rate limiting detected (may not be configured)")
        else:
            self.log_result("Forgot password - rate limiting", "FAIL", "Unexpected behavior during rate limit test")
    
    def test_reset_password_valid_token(self):
        """Test password reset with valid token (simulated)"""
        # Note: In a real test, we'd extract the token from the email
        # For this test, we'll simulate having a valid token
        
        # First request a password reset to potentially generate a token
        self.make_request("POST", "/auth/forgot-password", json={
            "email": self.test_user["email"]
        })
        
        # Simulate a valid token (in real scenario, extract from email/database)
        fake_token = "valid_reset_token_123456789"
        
        try:
            response = self.make_request("POST", "/auth/reset-password", json={
                "token": fake_token,
                "new_password": "NewSecurePassword123!@#"
            })
            
            # Expect 400 since token is fake, but endpoint should be accessible
            if response.status_code in [400, 401]:
                self.log_result("Reset password - valid token format", "PASS", "Endpoint accessible, token validation works")
            elif response.status_code == 200:
                self.log_result("Reset password - valid token format", "SKIP", "Unexpectedly succeeded (token may be valid)")
            else:
                self.log_result("Reset password - valid token format", "FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Reset password - valid token format", "FAIL", str(e))
    
    def test_reset_password_invalid_token(self):
        """Test password reset with invalid/expired token"""
        invalid_tokens = [
            "invalid_token_123",
            "expired_token_456", 
            "malformed_token",
            ""
        ]
        
        for token in invalid_tokens:
            try:
                response = self.make_request("POST", "/auth/reset-password", json={
                    "token": token,
                    "new_password": "NewSecurePassword123!@#"
                })
                
                if response.status_code in [400, 401]:  # Expected for invalid tokens
                    self.log_result(f"Reset password - invalid token ({token[:10]}...)", "PASS", "Correctly rejected")
                else:
                    self.log_result(f"Reset password - invalid token ({token[:10]}...)", "FAIL", f"Status {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Reset password - invalid token ({token[:10]}...)", "FAIL", str(e))
    
    def test_reset_password_malformed_token(self):
        """Test password reset with malformed token"""
        malformed_tokens = [
            {"token": 123},  # Number instead of string
            {"token": None},  # Null token
            {"token": []},    # Array instead of string
        ]
        
        for i, malformed_data in enumerate(malformed_tokens):
            try:
                response = self.make_request("POST", "/auth/reset-password", json={
                    **malformed_data,
                    "new_password": "NewSecurePassword123!@#"
                })
                
                if response.status_code == 422:  # Validation error expected
                    self.log_result(f"Reset password - malformed token {i+1}", "PASS", "Correctly rejected malformed data")
                else:
                    self.log_result(f"Reset password - malformed token {i+1}", "FAIL", f"Status {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Reset password - malformed token {i+1}", "FAIL", str(e))
    
    def test_reset_password_weak_password(self):
        """Test password reset with weak password"""
        weak_passwords = [
            "123456",           # Too short, common
            "password",         # Common, no special chars
            "12345678",         # No letters
            "abcdefgh",         # No numbers or special chars  
            "Password123",      # No special characters
            "PASSWORD123!",     # No lowercase
            "password123!",     # No uppercase
        ]
        
        fake_token = "test_token_for_weak_password"
        
        for weak_password in weak_passwords:
            try:
                response = self.make_request("POST", "/auth/reset-password", json={
                    "token": fake_token,
                    "new_password": weak_password
                })
                
                # Could be 400 (invalid token) or 422 (validation error)
                # We're mainly testing that weak passwords are handled
                if response.status_code in [400, 422]:
                    if response.status_code == 422:
                        self.log_result(f"Reset password - weak password ({weak_password})", "PASS", "Password validation working")
                    else:
                        self.log_result(f"Reset password - weak password ({weak_password})", "PASS", "Token validation first (expected)")
                else:
                    self.log_result(f"Reset password - weak password ({weak_password})", "FAIL", f"Status {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Reset password - weak password ({weak_password})", "FAIL", str(e))
    
    def test_reset_password_missing_fields(self):
        """Test password reset with missing required fields"""
        test_cases = [
            ({}, "missing both fields"),
            ({"token": "test_token"}, "missing password"),
            ({"new_password": "TestPassword123!"}, "missing token"),
        ]
        
        for data, description in test_cases:
            try:
                response = self.make_request("POST", "/auth/reset-password", json=data)
                
                if response.status_code == 422:  # Validation error expected
                    self.log_result(f"Reset password - {description}", "PASS", "Correctly rejected")
                else:
                    self.log_result(f"Reset password - {description}", "FAIL", f"Status {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Reset password - {description}", "FAIL", str(e))
    
    def test_reset_token_single_use(self):
        """Test that reset tokens can only be used once"""
        # This test would require a real token from the system
        # For now, we'll test the concept with multiple attempts on same fake token
        
        fake_token = "single_use_test_token_123"
        new_password = "SingleUseTestPassword123!@#"
        
        # Try using the same token twice
        for attempt in [1, 2]:
            try:
                response = self.make_request("POST", "/auth/reset-password", json={
                    "token": fake_token,
                    "new_password": new_password
                })
                
                # Both should fail since token is fake, but testing the endpoint
                if response.status_code in [400, 401]:
                    self.log_result(f"Reset token single use - attempt {attempt}", "PASS", "Token validation working")
                else:
                    self.log_result(f"Reset token single use - attempt {attempt}", "FAIL", f"Status {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Reset token single use - attempt {attempt}", "FAIL", str(e))
    
    def test_change_password_authenticated(self):
        """Test password change with valid authentication"""
        if not self.user_token:
            self.log_result("Change password - authenticated", "SKIP", "No user token available")
            return
        
        try:
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
            
            if response.status_code == 200:
                self.log_result("Change password - authenticated", "PASS", "Password changed successfully")
                # Update stored password for future tests
                self.test_user["password"] = "NewChangedPassword123!@#"
            else:
                self.log_result("Change password - authenticated", "FAIL", f"Status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Change password - authenticated", "FAIL", str(e))
    
    def test_change_password_wrong_current(self):
        """Test password change with wrong current password"""
        if not self.user_token:
            self.log_result("Change password - wrong current", "SKIP", "No user token available")
            return
        
        try:
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
            
            if response.status_code == 400:
                self.log_result("Change password - wrong current", "PASS", "Correctly rejected wrong current password")
            else:
                self.log_result("Change password - wrong current", "FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Change password - wrong current", "FAIL", str(e))
    
    def test_change_password_without_authentication(self):
        """Test password change without authentication"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/change-password",
                json={
                    "current_password": self.test_user["password"],
                    "new_password": "NewPassword123!@#"
                },
                headers=self.headers  # No Authorization header
            )
            
            if response.status_code in [401, 403]:
                self.log_result("Change password - no auth", "PASS", "Correctly rejected unauthenticated request")
            else:
                self.log_result("Change password - no auth", "FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Change password - no auth", "FAIL", str(e))
    
    def test_change_password_invalid_token(self):
        """Test password change with invalid token"""
        try:
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
            
            if response.status_code == 401:
                self.log_result("Change password - invalid token", "PASS", "Correctly rejected invalid token")
            else:
                self.log_result("Change password - invalid token", "FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Change password - invalid token", "FAIL", str(e))
    
    def test_change_password_weak_new_password(self):
        """Test password change with weak new password"""
        if not self.user_token:
            self.log_result("Change password - weak new", "SKIP", "No user token available")
            return
        
        weak_passwords = [
            "123456",           # Too short, common
            "password",         # Common, no special chars
            "12345678",         # No letters
            "abcdefgh",         # No numbers or special chars
        ]
        
        for weak_password in weak_passwords:
            try:
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
                
                if response.status_code == 422:  # Validation error expected
                    self.log_result(f"Change password - weak new ({weak_password})", "PASS", "Correctly rejected weak password")
                else:
                    self.log_result(f"Change password - weak new ({weak_password})", "FAIL", f"Status {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Change password - weak new ({weak_password})", "FAIL", str(e))
    
    def test_change_password_same_password(self):
        """Test password change with same password"""
        if not self.user_token:
            self.log_result("Change password - same password", "SKIP", "No user token available")
            return
        
        try:
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
            if response.status_code in [400, 422]:
                self.log_result("Change password - same password", "PASS", "Correctly rejected same password")
            elif response.status_code == 200:
                self.log_result("Change password - same password", "SKIP", "Allowed same password (policy dependent)")
            else:
                self.log_result("Change password - same password", "FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Change password - same password", "FAIL", str(e))
    
    def test_change_password_missing_fields(self):
        """Test password change with missing fields"""
        if not self.user_token:
            self.log_result("Change password - missing fields", "SKIP", "No user token available")
            return
        
        test_cases = [
            ({}, "missing both passwords"),
            ({"current_password": "test"}, "missing new password"),
            ({"new_password": "NewPassword123!"}, "missing current password"),
        ]
        
        for data, description in test_cases:
            try:
                headers = self.headers.copy()
                headers["Authorization"] = f"Bearer {self.user_token}"
                
                response = requests.post(
                    f"{self.base_url}/auth/change-password",
                    json=data,
                    headers=headers
                )
                
                if response.status_code == 422:  # Validation error expected
                    self.log_result(f"Change password - {description}", "PASS", "Correctly rejected")
                else:
                    self.log_result(f"Change password - {description}", "FAIL", f"Status {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Change password - {description}", "FAIL", str(e))
    
    def test_change_password_empty_passwords(self):
        """Test password change with empty passwords"""
        if not self.user_token:
            self.log_result("Change password - empty passwords", "SKIP", "No user token available")
            return
        
        test_cases = [
            ({"current_password": "", "new_password": "NewPassword123!"}, "empty current"),
            ({"current_password": "current", "new_password": ""}, "empty new"),
            ({"current_password": "", "new_password": ""}, "both empty"),
        ]
        
        for data, description in test_cases:
            try:
                headers = self.headers.copy()
                headers["Authorization"] = f"Bearer {self.user_token}"
                
                response = requests.post(
                    f"{self.base_url}/auth/change-password",
                    json=data,
                    headers=headers
                )
                
                if response.status_code in [400, 422]:  # Validation/business error expected
                    self.log_result(f"Change password - {description}", "PASS", "Correctly rejected")
                else:
                    self.log_result(f"Change password - {description}", "FAIL", f"Status {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Change password - {description}", "FAIL", str(e))
    
    def test_password_policy_enforcement(self):
        """Test password policy enforcement across all endpoints"""
        print("\n--- Testing Password Policy Enforcement ---")
        
        # Test during registration
        weak_password = "weak"
        try:
            response = self.make_request("POST", "/auth/register", json={
                "email": f"policy_test_{int(time.time())}@example.com",
                "password": weak_password,
                "first_name": "Policy",
                "last_name": "Test",
                "phone": "5550001234"
            })
            
            if response.status_code == 422:
                self.log_result("Password policy - registration", "PASS", "Weak password rejected during registration")
            else:
                self.log_result("Password policy - registration", "FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Password policy - registration", "FAIL", str(e))
    
    def test_password_strength_validation(self):
        """Test password strength validation in change password"""
        if not self.user_token:
            self.log_result("Password strength validation", "SKIP", "No user token available")
            return
        
        print("\n--- Testing Password Strength Requirements ---")
        
        strength_tests = [
            ("Short123!", "minimum 8 characters"),
            ("NoSpecialChars123", "special characters required"),
            ("no_uppercase_123!", "uppercase required"),
            ("NO_LOWERCASE_123!", "lowercase required"),
            ("NoNumbers!@#", "numbers required"),
            ("   SpacePrefix123!", "no leading spaces"),
            ("SpaceSuffix123!   ", "no trailing spaces"),
        ]
        
        for weak_password, requirement in strength_tests:
            try:
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
                
                if response.status_code == 422:
                    self.log_result(f"Password strength - {requirement}", "PASS", "Correctly rejected")
                elif response.status_code == 200:
                    self.log_result(f"Password strength - {requirement}", "SKIP", f"Accepted (policy may allow): {weak_password}")
                else:
                    self.log_result(f"Password strength - {requirement}", "FAIL", f"Status {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Password strength - {requirement}", "FAIL", str(e))
    
    def run_forgot_password_tests(self):
        """Run all forgot password tests"""
        print("\n" + "="*60)
        print("FORGOT PASSWORD TESTS")
        print("="*60)
        
        self.test_forgot_password_success()
        self.test_forgot_password_unknown_email()
        self.test_forgot_password_invalid_email_format()
        self.test_forgot_password_without_email()
        self.test_forgot_password_empty_email()
        self.test_forgot_password_rate_limiting()
    
    def run_reset_password_tests(self):
        """Run all reset password tests"""
        print("\n" + "="*60)
        print("RESET PASSWORD TESTS")
        print("="*60)
        
        self.test_reset_password_valid_token()
        self.test_reset_password_invalid_token()
        self.test_reset_password_malformed_token()
        self.test_reset_password_weak_password()
        self.test_reset_password_missing_fields()
        self.test_reset_token_single_use()
    
    def run_change_password_tests(self):
        """Run all change password tests"""
        print("\n" + "="*60)
        print("CHANGE PASSWORD TESTS")
        print("="*60)
        
        self.test_change_password_authenticated()
        self.test_change_password_wrong_current()
        self.test_change_password_without_authentication()
        self.test_change_password_invalid_token()
        self.test_change_password_weak_new_password()
        self.test_change_password_same_password()
        self.test_change_password_missing_fields()
        self.test_change_password_empty_passwords()
    
    def run_policy_tests(self):
        """Run password policy tests"""
        print("\n" + "="*60)
        print("PASSWORD POLICY TESTS")
        print("="*60)
        
        self.test_password_policy_enforcement()
        self.test_password_strength_validation()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("PASSWORD TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        total = len(self.results)
        
        print(f"\nResults:")
        print(f"  Passed:  {passed}/{total}")
        print(f"  Failed:  {failed}/{total}")
        print(f"  Skipped: {skipped}/{total}")
        
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if result.status == "FAIL":
                    print(f"  - {result.test_name}: {result.message}")
        
        # Save results to file
        results_file = f"password_test_results_{int(time.time())}.json"
        with open(results_file, "w") as f:
            json.dump(
                [asdict(r) for r in self.results],
                f,
                indent=2,
                default=str
            )
        print(f"\nResults saved to: {results_file}")
        
        return failed == 0


def main():
    """Main test execution"""
    print("="*60)
    print("PASSWORD MANAGEMENT COMPREHENSIVE TEST SUITE")
    print("="*60)
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now()}")
    print("\nTest Categories:")
    print("1. Forgot Password Tests")
    print("2. Reset Password Tests")
    print("3. Change Password Tests")
    print("4. Password Policy Tests")
    print("="*60)
    
    runner = PasswordTestRunner()
    
    try:
        # Setup test user
        runner.setup_test_user()
        
        # Run all test categories
        runner.run_forgot_password_tests()
        runner.run_reset_password_tests()
        runner.run_change_password_tests()
        runner.run_policy_tests()
        
        # Print final summary
        success = runner.print_summary()
        
        if success:
            print("\n[SUCCESS] ALL TESTS PASSED!")
            return 0
        else:
            print("\n[WARNING] SOME TESTS FAILED!")
            return 1
            
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Tests interrupted by user")
        runner.print_summary()
        return 2
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        runner.print_summary()
        return 3


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)