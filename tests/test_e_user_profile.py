"""
E. User Profile Tests
"""
import pytest
import time
import uuid


@pytest.mark.integration
@pytest.mark.asyncio
class TestUpdateProfile:
    """Test user profile update scenarios"""
    
    def test_update_profile_success(self, client, authenticated_user, api_helper):
        """Update /me — succès
        
        Act: PUT /me {first_name, phone, …}.
        Attendu: 200, valeurs mises à jour, champs non modifiables protégés (email si verrouillé).
        """
        headers = authenticated_user["headers"]
        
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone": "+1234567890"
        }
        
        response = client.put("/auth/me", json=update_data, headers=headers)
        
        # Assert success
        assert response.status_code == 200
        
        # Assert user response structure
        response_data = response.json()
        api_helper.assert_valid_user_response(response_data)
        
        # Assert updated values
        assert response_data["first_name"] == update_data["first_name"]
        assert response_data["last_name"] == update_data["last_name"]
        
        # Assert protected fields remain unchanged
        original_user = authenticated_user["user_data"]
        assert response_data["email"] == original_user["email"]
        assert response_data["role"] == original_user["role"]
        assert response_data["id"] == original_user["id"]
        
        # Verify changes persist
        me_response = client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["first_name"] == update_data["first_name"]
        assert me_data["last_name"] == update_data["last_name"]

    def test_update_profile_partial(self, client, authenticated_user, api_helper):
        """Test partial profile update"""
        headers = authenticated_user["headers"]
        
        # Update only first name
        update_data = {
            "first_name": "PartialUpdate"
        }
        
        response = client.put("/auth/me", json=update_data, headers=headers)
        
        # Assert success
        assert response.status_code == 200
        
        # Assert user response structure
        response_data = response.json()
        api_helper.assert_valid_user_response(response_data)
        
        # Assert updated field
        assert response_data["first_name"] == update_data["first_name"]
        
        # Assert other fields remain unchanged
        original_user = authenticated_user["user_data"]
        assert response_data["last_name"] == original_user["last_name"]
        assert response_data["email"] == original_user["email"]

    def test_update_profile_forbidden_fields(self, client, authenticated_user, api_helper):
        """Update /me — champs interdits
        
        Act: modif rôle / flags sensibles.
        Attendu: 403 ou champs ignorés.
        """
        headers = authenticated_user["headers"]
        original_user = authenticated_user["user_data"]
        
        # Try to update protected fields
        forbidden_update_data = {
            "first_name": "Allowed",
            "role": "admin",  # Should be forbidden
            "email": "hacker@evil.com",  # Should be forbidden
            "id": 99999,  # Should be forbidden
            "is_active": False,  # Should be forbidden
            "email_verified": False,  # Should be forbidden
        }
        
        response = client.put("/auth/me", json=forbidden_update_data, headers=headers)
        
        # Response should either:
        # 1. Succeed but ignore forbidden fields (200)
        # 2. Reject the request entirely (403)
        # 3. Return validation error (422)
        assert response.status_code in [200, 403, 422]
        
        if response.status_code == 200:
            response_data = response.json()
            api_helper.assert_valid_user_response(response_data)
            
            # Assert allowed field was updated
            assert response_data["first_name"] == "Allowed"
            
            # Assert forbidden fields were ignored/protected
            assert response_data["role"] == original_user["role"]
            assert response_data["email"] == original_user["email"]
            assert response_data["id"] == original_user["id"]
            assert response_data["is_active"] == original_user["is_active"]

    def test_update_profile_unauthenticated(self, client, api_helper):
        """Test profile update without authentication"""
        update_data = {
            "first_name": "Should",
            "last_name": "Fail"
        }
        
        response = client.put("/auth/me", json=update_data)
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_update_profile_invalid_token(self, client, api_helper):
        """Test profile update with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        update_data = {
            "first_name": "Should",
            "last_name": "Fail"
        }
        
        response = client.put("/auth/me", json=update_data, headers=headers)
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_update_profile_invalid_data_types(self, client, authenticated_user):
        """Test profile update with invalid data types"""
        headers = authenticated_user["headers"]
        
        # Test invalid data types
        invalid_updates = [
            {"first_name": 123},  # Should be string
            {"last_name": None},  # Should be string
            {"phone": True},      # Should be string
        ]
        
        for invalid_data in invalid_updates:
            response = client.put("/auth/me", json=invalid_data, headers=headers)
            
            # Should return validation error
            assert response.status_code == 422

    def test_update_profile_empty_values(self, client, authenticated_user, api_helper):
        """Test profile update with empty values"""
        headers = authenticated_user["headers"]
        
        update_data = {
            "first_name": "",
            "last_name": "",
        }
        
        response = client.put("/auth/me", json=update_data, headers=headers)
        
        # Depending on validation rules, might be allowed or rejected
        assert response.status_code in [200, 400, 422]
        
        if response.status_code == 200:
            response_data = response.json()
            # Empty strings might be allowed
            assert response_data["first_name"] == ""
            assert response_data["last_name"] == ""

    def test_update_profile_long_values(self, client, authenticated_user):
        """Test profile update with very long values"""
        headers = authenticated_user["headers"]
        
        # Very long string (usually fields have length limits)
        long_string = "x" * 1000
        
        update_data = {
            "first_name": long_string,
            "last_name": long_string,
        }
        
        response = client.put("/auth/me", json=update_data, headers=headers)
        
        # Should reject overly long values
        assert response.status_code in [400, 422]

    def test_update_profile_special_characters(self, client, authenticated_user, api_helper):
        """Test profile update with special characters"""
        headers = authenticated_user["headers"]
        
        update_data = {
            "first_name": "José",
            "last_name": "O'Connor-Smith",
        }
        
        response = client.put("/auth/me", json=update_data, headers=headers)
        
        # Should handle Unicode and special characters properly
        assert response.status_code == 200
        
        response_data = response.json()
        api_helper.assert_valid_user_response(response_data)
        
        # Assert special characters are preserved
        assert response_data["first_name"] == "José"
        assert response_data["last_name"] == "O'Connor-Smith"

    def test_update_profile_sql_injection_attempt(self, client, authenticated_user, api_helper):
        """Test profile update with SQL injection attempts"""
        headers = authenticated_user["headers"]
        
        # SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "admin'/*",
            "' OR '1'='1",
            "<script>alert('xss')</script>",
        ]
        
        for malicious_input in malicious_inputs:
            update_data = {
                "first_name": malicious_input,
                "last_name": "Normal"
            }
            
            response = client.put("/auth/me", json=update_data, headers=headers)
            
            # Should either accept as normal text or reject
            assert response.status_code in [200, 400, 422]
            
            if response.status_code == 200:
                response_data = response.json()
                # Should be treated as literal text, not executed
                assert response_data["first_name"] == malicious_input

    def test_update_profile_concurrent_updates(self, client, authenticated_user, api_helper):
        """Test concurrent profile updates"""
        headers = authenticated_user["headers"]
        
        # Simulate concurrent updates
        update_data1 = {"first_name": "Concurrent1"}
        update_data2 = {"first_name": "Concurrent2"}
        
        # Make two rapid updates
        response1 = client.put("/auth/me", json=update_data1, headers=headers)
        response2 = client.put("/auth/me", json=update_data2, headers=headers)
        
        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Final state should reflect the last update
        me_response = client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200
        me_data = me_response.json()
        
        # Should have one of the updated values
        assert me_data["first_name"] in ["Concurrent1", "Concurrent2"]

    def test_update_profile_preserve_other_fields(self, client, authenticated_user, api_helper):
        """Test that updating profile preserves other important fields"""
        headers = authenticated_user["headers"]
        
        # Get current profile
        current_response = client.get("/auth/me", headers=headers)
        assert current_response.status_code == 200
        current_data = current_response.json()
        
        # Update only first name
        update_data = {
            "first_name": "PreserveTest"
        }
        
        response = client.put("/auth/me", json=update_data, headers=headers)
        assert response.status_code == 200
        
        response_data = response.json()
        api_helper.assert_valid_user_response(response_data)
        
        # Assert updated field
        assert response_data["first_name"] == "PreserveTest"
        
        # Assert all other important fields are preserved
        preserved_fields = ["id", "email", "role", "is_active", "email_verified", "last_name"]
        for field in preserved_fields:
            if field in current_data:
                assert response_data[field] == current_data[field], f"Field {field} should be preserved"

    def test_get_profile_after_update(self, client, authenticated_user, api_helper):
        """Test getting profile after update to ensure consistency"""
        headers = authenticated_user["headers"]
        
        # Update profile
        update_data = {
            "first_name": "ConsistencyTest",
            "last_name": "Updated"
        }
        
        update_response = client.put("/auth/me", json=update_data, headers=headers)
        assert update_response.status_code == 200
        update_result = update_response.json()
        
        # Get profile
        get_response = client.get("/auth/me", headers=headers)
        assert get_response.status_code == 200
        get_result = get_response.json()
        
        # Both responses should be identical
        assert update_result == get_result
        
        # Assert updated values are present in both
        assert update_result["first_name"] == "ConsistencyTest"
        assert update_result["last_name"] == "Updated"
        assert get_result["first_name"] == "ConsistencyTest"
        assert get_result["last_name"] == "Updated"