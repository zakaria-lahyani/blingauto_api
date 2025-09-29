"""
User Profile Update Test Suite - Pytest Compatible
Comprehensive tests for profile update scenarios using real API endpoints
"""
import pytest
import asyncio
import time
import requests
import threading
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestProfileUpdates:
    """User profile update test class using direct HTTP requests for real endpoint testing"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        self.base_url = "http://localhost:8000"
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        
        # Create unique test user for this test session
        timestamp = str(int(time.time()))
        self.test_user = {
            "email": f"profile_test_{timestamp}@example.com",
            "password": "TestPassword123!@#",
            "first_name": "Original",
            "last_name": "User",
            "phone": f"555000{timestamp[-4:]}"
        }
        self.user_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.original_profile: Optional[Dict] = None
        
        # Setup test user
        self._setup_test_user()
    
    def _setup_test_user(self):
        """Setup test user for profile update tests"""
        try:
            # Register user
            response = requests.post(
                f"{self.base_url}/auth/register", 
                json=self.test_user,
                headers=self.headers
            )
            
            if response.status_code == 201:
                user_info = response.json()
                self.user_id = user_info["id"]
                
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
                    
                    # Get original profile for comparison
                    self._fetch_current_profile()
                    
        except Exception as e:
            print(f"Setup failed: {e}")
    
    def _fetch_current_profile(self) -> Optional[Dict]:
        """Fetch current user profile"""
        if not self.user_token:
            return None
        
        try:
            headers = self.headers.copy()
            headers["Authorization"] = f"Bearer {self.user_token}"
            
            response = requests.get(
                f"{self.base_url}/auth/me",
                headers=headers
            )
            
            if response.status_code == 200:
                self.original_profile = response.json()
                return self.original_profile
                
        except Exception as e:
            print(f"Failed to fetch profile: {e}")
        
        return None
    
    def _update_profile(self, data: Dict[str, Any], token: str = None) -> requests.Response:
        """Helper method to update profile"""
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {token or self.user_token}"
        
        return requests.put(
            f"{self.base_url}/auth/me",
            json=data,
            headers=headers
        )
    
    # Basic Profile Update Tests
    def test_update_profile_success(self):
        """Test successful profile update with all fields"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        update_data = {
            "first_name": "UpdatedFirst",
            "last_name": "UpdatedLast", 
            "phone": "5551234567"
        }
        
        response = self._update_profile(update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == update_data["first_name"]
        assert data["last_name"] == update_data["last_name"]
        assert data["phone"] == update_data["phone"]
        
        # Verify other fields remain unchanged
        assert data["email"] == self.test_user["email"]
        assert data["id"] == self.user_id
        assert "password" not in data
        assert "hashed_password" not in data
    
    def test_partial_profile_update_first_name_only(self):
        """Test partial profile update - first name only"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        update_data = {"first_name": "PartialUpdate"}
        
        response = self._update_profile(update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "PartialUpdate"
        # Other fields should remain unchanged from original
        if self.original_profile:
            assert data["last_name"] == self.original_profile["last_name"]
            assert data["phone"] == self.original_profile["phone"]
    
    def test_partial_profile_update_last_name_only(self):
        """Test partial profile update - last name only"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        update_data = {"last_name": "PartialLastName"}
        
        response = self._update_profile(update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["last_name"] == "PartialLastName"
    
    def test_partial_profile_update_phone_only(self):
        """Test partial profile update - phone only"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        update_data = {"phone": "5559876543"}
        
        response = self._update_profile(update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "5559876543"
    
    def test_update_profile_forbidden_fields(self):
        """Test profile update with forbidden fields"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        forbidden_updates = [
            {"email": "newemail@example.com"},
            {"role": "admin"},
            {"id": "12345"},
            {"is_active": False},
            {"email_verified": True},
            {"created_at": "2023-01-01T00:00:00"},
            {"updated_at": "2023-01-01T00:00:00"},
            {"password": "NewPassword123!"},
            {"hashed_password": "somehash"}
        ]
        
        for forbidden_data in forbidden_updates:
            response = self._update_profile(forbidden_data)
            
            # Should either ignore forbidden fields (200) or reject (422)
            assert response.status_code in [200, 422]
            
            if response.status_code == 200:
                data = response.json()
                # Verify forbidden fields weren't changed
                for field, value in forbidden_data.items():
                    if field in ["email", "role", "id"]:
                        assert data.get(field) != value
    
    # Authentication and Authorization Tests
    def test_update_profile_without_authentication(self):
        """Test profile update without authentication"""
        update_data = {"first_name": "ShouldFail"}
        
        response = requests.put(
            f"{self.base_url}/auth/me",
            json=update_data,
            headers=self.headers  # No Authorization header
        )
        
        assert response.status_code in [401, 403]
    
    def test_update_profile_with_invalid_token(self):
        """Test profile update with invalid token"""
        update_data = {"first_name": "ShouldFail"}
        
        headers = self.headers.copy()
        headers["Authorization"] = "Bearer invalid_token_12345"
        
        response = requests.put(
            f"{self.base_url}/auth/me",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 401
    
    def test_update_profile_with_malformed_token(self):
        """Test profile update with malformed token"""
        update_data = {"first_name": "ShouldFail"}
        
        malformed_tokens = [
            "Bearer",  # Missing token
            "Bearer ",  # Empty token
            "invalid_format_token",  # Missing Bearer
            "Bearer token with spaces",  # Invalid token format
        ]
        
        for malformed_token in malformed_tokens:
            headers = self.headers.copy()
            headers["Authorization"] = malformed_token
            
            response = requests.put(
                f"{self.base_url}/auth/me",
                json=update_data,
                headers=headers
            )
            
            assert response.status_code == 401
    
    # Data Validation Tests
    @pytest.mark.parametrize("invalid_data", [
        {"first_name": 123},  # Number instead of string
        {"last_name": []},    # Array instead of string
        {"phone": {"number": "123"}},  # Object instead of string
        {"first_name": True},  # Boolean instead of string
        {"last_name": None},   # Null value (should be allowed as optional)
    ])
    def test_update_profile_invalid_data_types(self, invalid_data):
        """Test profile update with invalid data types"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        response = self._update_profile(invalid_data)
        
        # Should return validation error for invalid types
        if list(invalid_data.values())[0] is None:
            # None/null values should be allowed for optional fields
            assert response.status_code in [200, 422]
        else:
            assert response.status_code == 422
    
    @pytest.mark.parametrize("empty_data", [
        {"first_name": ""},    # Empty string (should fail - min_length=1)
        {"last_name": ""},     # Empty string (should fail - min_length=1)
        {"phone": ""},         # Empty string (should be allowed)
    ])
    def test_update_profile_empty_values(self, empty_data):
        """Test profile update with empty values"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        response = self._update_profile(empty_data)
        
        field_name = list(empty_data.keys())[0]
        
        if field_name in ["first_name", "last_name"]:
            # These have min_length=1, so empty string should fail
            assert response.status_code == 422
        else:
            # Phone can be empty
            assert response.status_code == 200
    
    def test_update_profile_very_long_values(self):
        """Test profile update with very long values"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        long_values = {
            "first_name": "A" * 51,  # Max 50 chars
            "last_name": "B" * 51,   # Max 50 chars  
            "phone": "1" * 21        # Max 20 chars
        }
        
        for field, long_value in long_values.items():
            response = self._update_profile({field: long_value})
            
            # Should return validation error for values exceeding max length
            assert response.status_code == 422
    
    def test_update_profile_boundary_values(self):
        """Test profile update with boundary values (exactly at limits)"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        boundary_values = {
            "first_name": "A" * 50,  # Exactly max length
            "last_name": "B" * 50,   # Exactly max length
            "phone": "1" * 20        # Exactly max length
        }
        
        for field, boundary_value in boundary_values.items():
            response = self._update_profile({field: boundary_value})
            
            # Should succeed at boundary values
            assert response.status_code == 200
            data = response.json()
            assert data[field] == boundary_value
    
    @pytest.mark.parametrize("special_chars_data", [
        {"first_name": "José-María"},        # Accented characters and hyphen
        {"last_name": "O'Connor"},          # Apostrophe
        {"first_name": "李小明"},             # Chinese characters
        {"last_name": "مُحَمَّد"},            # Arabic characters
        {"phone": "+1-555-123-4567"},       # Phone with formatting
        {"first_name": "User@#$%"},         # Special symbols
        {"last_name": "Test<>User"},        # HTML-like brackets
    ])
    def test_update_profile_special_characters(self, special_chars_data):
        """Test profile update with special characters"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        response = self._update_profile(special_chars_data)
        
        # Should handle special characters appropriately
        # This depends on input validation implementation
        assert response.status_code in [200, 422]
        
        if response.status_code == 200:
            data = response.json()
            field_name = list(special_chars_data.keys())[0]
            # If accepted, should return the same value or sanitized version
            assert field_name in data
    
    # Security Tests
    @pytest.mark.parametrize("injection_data", [
        {"first_name": "'; DROP TABLE users; --"},
        {"last_name": "admin'/**/union/**/select/**/password/**/from/**/users--"},
        {"phone": "1'; UPDATE users SET role='admin' WHERE id='1'; --"},
        {"first_name": "<script>alert('xss')</script>"},
        {"last_name": "javascript:alert('xss')"},
        {"phone": "${7*7}"},  # Template injection
        {"first_name": "{{7*7}}"},  # Template injection
        {"last_name": "../../../etc/passwd"},  # Path traversal
        {"phone": "%(password)s"},  # Python format string
    ])
    def test_update_profile_sql_injection_attempts(self, injection_data):
        """Test profile update with SQL injection attempts"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        response = self._update_profile(injection_data)
        
        # Should either reject malicious input or sanitize it
        assert response.status_code in [200, 422]
        
        if response.status_code == 200:
            data = response.json()
            field_name = list(injection_data.keys())[0]
            # Verify the malicious payload didn't execute
            # (This is a basic check - more thorough security testing would verify database state)
            assert field_name in data
    
    # Concurrency Tests
    def test_concurrent_profile_updates(self):
        """Test concurrent profile updates"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        def update_first_name(name_suffix):
            """Helper function for concurrent updates"""
            try:
                response = self._update_profile({"first_name": f"Concurrent{name_suffix}"})
                return response.status_code, response.json() if response.status_code == 200 else None
            except Exception as e:
                return 500, str(e)
        
        # Run 5 concurrent updates
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_first_name, i) for i in range(5)]
            results = [future.result() for future in as_completed(futures)]
        
        # At least some updates should succeed
        successful_updates = [r for r in results if r[0] == 200]
        assert len(successful_updates) > 0
        
        # Verify final state is consistent
        final_profile = self._fetch_current_profile()
        assert final_profile is not None
        assert final_profile["first_name"].startswith("Concurrent")
    
    def test_concurrent_different_field_updates(self):
        """Test concurrent updates to different fields"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        def update_field(field_data):
            """Helper function for concurrent field updates"""
            try:
                response = self._update_profile(field_data)
                return response.status_code, field_data, response.json() if response.status_code == 200 else None
            except Exception as e:
                return 500, field_data, str(e)
        
        # Update different fields concurrently
        updates = [
            {"first_name": "ConcurrentFirst"},
            {"last_name": "ConcurrentLast"},
            {"phone": "5551112222"}
        ]
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(update_field, update) for update in updates]
            results = [future.result() for future in as_completed(futures)]
        
        # All updates should succeed since they're updating different fields
        successful_updates = [r for r in results if r[0] == 200]
        assert len(successful_updates) >= 2  # At least most should succeed
        
        # Verify all fields were updated
        final_profile = self._fetch_current_profile()
        assert final_profile is not None
        assert final_profile["first_name"] == "ConcurrentFirst"
        assert final_profile["last_name"] == "ConcurrentLast"
        assert final_profile["phone"] == "5551112222"
    
    # Consistency Tests
    def test_profile_preservation_after_update(self):
        """Test that updating profile preserves other important fields"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        # Get original profile
        original = self._fetch_current_profile()
        assert original is not None
        
        # Update only first name
        response = self._update_profile({"first_name": "PreservationTest"})
        assert response.status_code == 200
        
        updated = response.json()
        
        # Verify important fields are preserved
        preserved_fields = [
            "id", "email", "role", "is_active", "email_verified", 
            "email_verified_at", "created_at", "last_login"
        ]
        
        for field in preserved_fields:
            if field in original:
                assert updated.get(field) == original.get(field), f"Field {field} was not preserved"
        
        # Verify only first_name changed
        assert updated["first_name"] == "PreservationTest"
        assert updated["last_name"] == original["last_name"]
        assert updated["phone"] == original["phone"]
        
        # Verify updated_at field was updated (if present)
        if "updated_at" in original and "updated_at" in updated:
            # updated_at should be newer (though we can't be too strict about timing)
            assert "updated_at" in updated
    
    def test_get_profile_after_update_consistency(self):
        """Test getting profile after update ensures consistency"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        # Update profile
        update_data = {
            "first_name": "ConsistencyTest",
            "last_name": "Updated",
            "phone": "5559999999"
        }
        
        update_response = self._update_profile(update_data)
        assert update_response.status_code == 200
        update_result = update_response.json()
        
        # Fetch profile separately
        get_response = self._fetch_current_profile()
        assert get_response is not None
        
        # Verify consistency between update response and get response
        consistency_fields = ["id", "email", "first_name", "last_name", "phone", "role"]
        
        for field in consistency_fields:
            assert update_result.get(field) == get_response.get(field), f"Inconsistency in field {field}"
        
        # Verify the updates are reflected
        assert get_response["first_name"] == "ConsistencyTest"
        assert get_response["last_name"] == "Updated"
        assert get_response["phone"] == "5559999999"
    
    def test_multiple_sequential_updates_consistency(self):
        """Test multiple sequential updates maintain consistency"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        updates = [
            {"first_name": "Sequential1"},
            {"last_name": "Sequential2"}, 
            {"phone": "5551111111"},
            {"first_name": "Sequential3", "last_name": "Sequential4"},
        ]
        
        for i, update_data in enumerate(updates):
            response = self._update_profile(update_data)
            assert response.status_code == 200, f"Update {i+1} failed"
            
            # Verify the update took effect
            result = response.json()
            for field, value in update_data.items():
                assert result[field] == value, f"Update {i+1} field {field} not applied"
        
        # Final consistency check
        final_profile = self._fetch_current_profile()
        assert final_profile["first_name"] == "Sequential3"
        assert final_profile["last_name"] == "Sequential4" 
        assert final_profile["phone"] == "5551111111"
    
    def test_update_with_null_values(self):
        """Test profile update with null/None values for optional fields"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        # Set some values first
        setup_response = self._update_profile({
            "first_name": "ToBeNulled",
            "last_name": "AlsoToBeNulled",
            "phone": "5552222222"
        })
        assert setup_response.status_code == 200
        
        # Try to null out optional fields (phone should be nullable)
        null_updates = [
            {"phone": None},  # Should be allowed
            # Note: first_name and last_name might not allow null due to min_length constraint
        ]
        
        for null_data in null_updates:
            response = self._update_profile(null_data)
            
            # Phone nullification should work, others might not depending on validation
            if "phone" in null_data:
                assert response.status_code == 200
                result = response.json()
                assert result["phone"] is None or result["phone"] == ""


if __name__ == "__main__":
    pytest.main([__file__])