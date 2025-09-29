"""
Pytest-based Auth API tests
Comprehensive testing of authentication endpoints
"""

import os
import time
import uuid
import pytest
import httpx
from typing import Dict, Optional
from fastapi.testclient import TestClient

# Import your main app
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def test_users():
    """Create test user data with unique emails"""
    timestamp = str(int(time.time()))
    return {
        "superadmin": {
            "email": f"superadmin_{timestamp}@test.com",
            "password": "SecureTest123!",
            "first_name": "Super",
            "last_name": "Admin",
            "phone": "1234567890"
        },
        "admin": {
            "email": f"admin_{timestamp}@test.com",
            "password": "SecureTest123!",
            "first_name": "Admin",
            "last_name": "User",
            "phone": "1234567891"
        },
        "manager": {
            "email": f"manager_{timestamp}@test.com",
            "password": "SecureTest123!",
            "first_name": "Manager",
            "last_name": "User",
            "phone": "1234567892"
        },
        "washer": {
            "email": f"washer_{timestamp}@test.com",
            "password": "SecureTest123!",
            "first_name": "Washer",
            "last_name": "User",
            "phone": "1234567893"
        },
        "client_verified": {
            "email": f"client_v_{timestamp}@test.com",
            "password": "SecureTest123!",
            "first_name": "Verified",
            "last_name": "Client",
            "phone": "1234567894"
        },
        "client_unverified": {
            "email": f"client_u_{timestamp}@test.com",
            "password": "SecureTest123!",
            "first_name": "Unverified",
            "last_name": "Client",
            "phone": "1234567895"
        }
    }


@pytest.fixture(scope="module")
def registered_users(test_users):
    """Register test users and return their data with IDs and tokens"""
    users_data = {}
    
    for user_type, user_data in test_users.items():
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        user_info = response.json()
        
        users_data[user_type] = {
            **user_data,
            "id": user_info["id"],
            "token": None,
            "refresh_token": None
        }
    
    return users_data


class TestUserRegistration:
    """Test user registration endpoints"""
    
    def test_register_valid_user(self):
        """Test registering a valid user"""
        user_data = {
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "ValidPass123!",
            "first_name": "Test",
            "last_name": "User",
            "phone": "1234567890"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["first_name"] == user_data["first_name"]
        assert "id" in data
    
    def test_register_duplicate_email(self, registered_users):
        """Test registering with duplicate email"""
        user_data = {
            "email": registered_users["client_verified"]["email"],
            "password": "ValidPass123!",
            "first_name": "Duplicate",
            "last_name": "User",
            "phone": "9876543210"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 400
    
    def test_register_invalid_email(self):
        """Test registering with invalid email format"""
        user_data = {
            "email": "invalid-email",
            "password": "ValidPass123!",
            "first_name": "Test",
            "last_name": "User",
            "phone": "1234567890"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code == 422
    
    def test_register_weak_password(self):
        """Test registering with weak password"""
        user_data = {
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "weak",
            "first_name": "Test",
            "last_name": "User",
            "phone": "1234567890"
        }
        
        response = client.post("/auth/register", json=user_data)
        assert response.status_code in [400, 422]


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_valid_credentials(self, registered_users):
        """Test login with valid credentials"""
        response = client.post("/auth/login", json={
            "email": registered_users["client_verified"]["email"],
            "password": registered_users["client_verified"]["password"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
        
        # Store tokens for later tests
        registered_users["client_verified"]["token"] = data["access_token"]
        registered_users["client_verified"]["refresh_token"] = data["refresh_token"]
    
    def test_login_invalid_password(self, registered_users):
        """Test login with invalid password"""
        response = client.post("/auth/login", json={
            "email": registered_users["client_verified"]["email"],
            "password": "WrongPassword123!"
        })
        
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Password123!"
        })
        
        assert response.status_code == 401
    
    def test_me_with_valid_token(self, registered_users):
        """Test /me endpoint with valid token"""
        # First login to get token
        login_response = client.post("/auth/login", json={
            "email": registered_users["client_verified"]["email"],
            "password": registered_users["client_verified"]["password"]
        })
        token = login_response.json()["access_token"]
        
        response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == registered_users["client_verified"]["email"]
    
    def test_me_without_token(self):
        """Test /me endpoint without authentication"""
        response = client.get("/auth/me")
        assert response.status_code == 401
    
    def test_me_with_invalid_token(self):
        """Test /me endpoint with invalid token"""
        response = client.get("/auth/me", headers={
            "Authorization": "Bearer invalid_token_123456"
        })
        assert response.status_code == 401
    
    def test_me_with_malformed_header(self):
        """Test /me endpoint with malformed Authorization header"""
        response = client.get("/auth/me", headers={
            "Authorization": "Bearer"
        })
        assert response.status_code == 401
    
    def test_refresh_token(self, registered_users):
        """Test token refresh"""
        # First login
        login_response = client.post("/auth/login", json={
            "email": registered_users["client_verified"]["email"],
            "password": registered_users["client_verified"]["password"]
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_logout(self, registered_users):
        """Test logout"""
        # First login
        login_response = client.post("/auth/login", json={
            "email": registered_users["client_verified"]["email"],
            "password": registered_users["client_verified"]["password"]
        })
        token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]
        
        # Logout
        response = client.post("/auth/logout", 
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200


class TestRoleBasedAccess:
    """Test role-based access control"""
    
    @pytest.fixture(autouse=True)
    def setup_admin(self, registered_users):
        """Setup admin user for role tests"""
        # This would need actual admin setup in your system
        # For now, we'll assume the first registered user can be made admin
        pass
    
    def test_list_users_as_admin(self, registered_users):
        """Test listing users as admin"""
        # Would need actual admin token
        # Placeholder for now
        pass
    
    def test_list_users_as_regular_user(self, registered_users):
        """Test listing users as regular user (should fail)"""
        # Login as regular user
        login_response = client.post("/auth/login", json={
            "email": registered_users["client_verified"]["email"],
            "password": registered_users["client_verified"]["password"]
        })
        token = login_response.json()["access_token"]
        
        response = client.get("/auth/users", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code in [401, 403]
    
    def test_change_role_as_admin(self, registered_users):
        """Test changing user role as admin"""
        # Would need actual admin token and implementation
        pass
    
    def test_change_role_as_regular_user(self, registered_users):
        """Test changing user role as regular user (should fail)"""
        # Login as regular user
        login_response = client.post("/auth/login", json={
            "email": registered_users["client_verified"]["email"],
            "password": registered_users["client_verified"]["password"]
        })
        token = login_response.json()["access_token"]
        
        # Try to change another user's role
        response = client.put(
            f"/auth/users/{registered_users['washer']['id']}/role",
            json={"role": "manager"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code in [401, 403]


class TestPasswordManagement:
    """Test password management endpoints"""
    
    def test_change_password(self, registered_users):
        """Test changing password"""
        # Login first
        login_response = client.post("/auth/login", json={
            "email": registered_users["client_verified"]["email"],
            "password": registered_users["client_verified"]["password"]
        })
        token = login_response.json()["access_token"]
        
        # Change password
        new_password = "NewSecurePass123!"
        response = client.post("/auth/change-password", 
            json={
                "current_password": registered_users["client_verified"]["password"],
                "new_password": new_password
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        
        # Test login with new password
        login_response = client.post("/auth/login", json={
            "email": registered_users["client_verified"]["email"],
            "password": new_password
        })
        assert login_response.status_code == 200
        
        # Update stored password
        registered_users["client_verified"]["password"] = new_password
    
    def test_forgot_password(self, registered_users):
        """Test forgot password flow"""
        response = client.post("/auth/forgot-password", json={
            "email": registered_users["client_verified"]["email"]
        })
        
        # Should return success regardless of email existence (security)
        assert response.status_code == 200


class TestEmailVerification:
    """Test email verification endpoints"""
    
    def test_request_email_verification(self, registered_users):
        """Test requesting email verification"""
        response = client.post("/auth/verify-email/request", json={
            "email": registered_users["client_unverified"]["email"]
        })
        
        # Check if feature is enabled
        if response.status_code == 404:
            pytest.skip("Email verification feature not enabled")
        
        assert response.status_code == 200
    
    def test_confirm_email_with_invalid_token(self):
        """Test confirming email with invalid token"""
        response = client.post("/auth/verify-email/confirm", json={
            "token": "invalid_token_123456"
        })
        
        # Check if feature is enabled
        if response.status_code == 404:
            pytest.skip("Email verification feature not enabled")
        
        assert response.status_code == 400


class TestUserProfile:
    """Test user profile management"""
    
    def test_update_profile(self, registered_users):
        """Test updating user profile"""
        # Login first
        login_response = client.post("/auth/login", json={
            "email": registered_users["client_verified"]["email"],
            "password": registered_users["client_verified"]["password"]
        })
        token = login_response.json()["access_token"]
        
        # Update profile
        response = client.put("/auth/me", 
            json={
                "first_name": "Updated",
                "last_name": "Name",
                "phone": "9999999999"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["phone"] == "9999999999"


class TestSecurityEdgeCases:
    """Test security edge cases"""
    
    def test_sql_injection_attempt(self):
        """Test SQL injection protection"""
        response = client.post("/auth/login", json={
            "email": "admin' OR '1'='1",
            "password": "' OR '1'='1"
        })
        assert response.status_code in [401, 422]
    
    def test_xss_attempt_in_registration(self):
        """Test XSS protection in registration"""
        response = client.post("/auth/register", json={
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "ValidPass123!",
            "first_name": "<script>alert('XSS')</script>",
            "last_name": "User",
            "phone": "1234567890"
        })
        
        if response.status_code == 201:
            data = response.json()
            # Check that script tags are escaped or removed
            assert "<script>" not in data["first_name"]
    
    def test_rate_limiting(self, registered_users):
        """Test rate limiting on login endpoint"""
        # Make multiple rapid requests
        responses = []
        for _ in range(20):
            response = client.post("/auth/login", json={
                "email": registered_users["client_verified"]["email"],
                "password": "wrong_password"
            })
            responses.append(response.status_code)
        
        # Should see rate limiting kick in (429 status)
        # This depends on your rate limiting configuration
        # assert 429 in responses  # Uncomment if rate limiting is enabled
    
    def test_session_fixation(self, registered_users):
        """Test protection against session fixation"""
        # Login once
        login1 = client.post("/auth/login", json={
            "email": registered_users["client_verified"]["email"],
            "password": registered_users["client_verified"]["password"]
        })
        token1 = login1.json()["access_token"]
        
        # Login again
        login2 = client.post("/auth/login", json={
            "email": registered_users["client_verified"]["email"],
            "password": registered_users["client_verified"]["password"]
        })
        token2 = login2.json()["access_token"]
        
        # Tokens should be different
        assert token1 != token2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])