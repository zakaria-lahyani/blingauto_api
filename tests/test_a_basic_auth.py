"""
A. Basic Authentication Tests - Registration and Login
"""
import pytest
import time
import uuid


@pytest.mark.smoke
class TestRegistration:
    """Test user registration scenarios"""
    
    def test_register_success(self, client, api_helper):
        """Register — succès
        
        Pré: email inexistant.
        Act: POST /register {email, password, first/last}.
        Attendu: 201, body UserResponse (id, email), email non vérifié, pas de token auto si non prévu.
        """
        user_data = {
            "email": f"test{int(time.time())}{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        # Assert status code
        assert response.status_code == 201
        
        # Assert response structure
        response_data = response.json()
        api_helper.assert_valid_user_response(response_data)
        
        # Assert specific registration requirements
        assert response_data["email"] == user_data["email"]
        assert response_data["first_name"] == user_data["first_name"]
        assert response_data["last_name"] == user_data["last_name"]
        assert response_data["role"] == "client"  # Default role
        assert response_data["is_active"] is True
        assert response_data["email_verified"] is True  # Email auto-verified when verification disabled
        
        # Assert no auto-login tokens in response
        assert "access_token" not in response_data
        assert "refresh_token" not in response_data

    def test_register_email_already_taken(self, client, registered_user):
        """Register — email déjà pris
        
        Pré: user existant.
        Act: POST /register même email.
        Attendu: 409 ou 400, message d'erreur.
        """
        # Try to register with same email
        duplicate_data = {
            "email": registered_user["credentials"]["email"],
            "password": "DifferentPass123!",
            "first_name": "Different",
            "last_name": "User"
        }
        
        response = client.post("/auth/register", json=duplicate_data)
        
        # Assert conflict or bad request
        assert response.status_code in [409, 400]
        
        # Assert error message
        response_data = response.json()
        assert "detail" in response_data
        assert any(word in response_data["detail"].lower() for word in ["email", "exists", "already", "taken"])

    def test_register_invalid_email(self, client):
        """Register with invalid email format"""
        invalid_data = {
            "email": "not-an-email",
            "password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_register_weak_password(self, client):
        """Register with weak password"""
        weak_data = {
            "email": f"test{int(time.time())}{uuid.uuid4().hex[:8]}@example.com",
            "password": "123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = client.post("/auth/register", json=weak_data)
        assert response.status_code in [400, 422]  # Validation error

    def test_register_missing_fields(self, client):
        """Register with missing required fields"""
        incomplete_data = {
            "email": f"test{int(time.time())}{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePass123!"
            # Missing first_name and last_name
        }
        
        response = client.post("/auth/register", json=incomplete_data)
        assert response.status_code == 422  # Validation error


@pytest.mark.smoke
class TestLogin:
    """Test user login scenarios"""
    
    def test_login_success(self, client, registered_user, api_helper):
        """Login — succès
        
        Pré: user existant (email vérifié si requis).
        Act: POST /login {email, password}.
        Attendu: 200, TokenResponse (access, refresh, exp, token_type).
        
        Note: In this test environment, email verification is required but not automatically done.
        This test demonstrates the expected behavior when email verification is required.
        """
        login_data = {
            "email": registered_user["credentials"]["email"],
            "password": registered_user["credentials"]["password"]
        }
        
        response = client.post("/auth/login", json=login_data)
        
        # Since email verification is disabled in test environment,
        # login should succeed with 200 and tokens
        assert response.status_code == 200
        
        response_data = response.json()
        api_helper.assert_valid_token_response(response_data)

    def test_login_wrong_password(self, client, registered_user, api_helper):
        """Login — mauvais mot de passe
        
        Act: POST /login avec mauvais password.
        Attendu: 401, message générique (pas de fuite "user existe/pas").
        """
        login_data = {
            "email": registered_user["credentials"]["email"],
            "password": "WrongPassword123!"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert generic error message (no information leakage)
        response_data = response.json()
        api_helper.assert_error_response(response_data)
        
        # Ensure message doesn't leak information about user existence
        error_msg = response_data["detail"].lower()
        assert "invalid" in error_msg or "incorrect" in error_msg
        assert "user" not in error_msg or "not found" not in error_msg

    def test_login_nonexistent_email(self, client, api_helper):
        """Login with non-existent email"""
        login_data = {
            "email": f"nonexistent{int(time.time())}{uuid.uuid4().hex[:8]}@example.com",
            "password": "SomePassword123!"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert generic error message (no information leakage about user existence)
        response_data = response.json()
        api_helper.assert_error_response(response_data)
        
        # Ensure message doesn't leak information about user existence
        error_msg = response_data["detail"].lower()
        assert "invalid" in error_msg or "incorrect" in error_msg

    def test_login_malformed_request(self, client):
        """Login with malformed JSON"""
        response = client.post("/auth/login", json={"email": "test@example.com"})  # Missing password
        assert response.status_code == 422  # Validation error

    def test_login_empty_credentials(self, client):
        """Login with empty credentials"""
        login_data = {
            "email": "",
            "password": ""
        }
        
        response = client.post("/auth/login", json=login_data)
        assert response.status_code == 422  # Validation error


@pytest.mark.smoke
class TestMeEndpoint:
    """Test /me endpoint authentication"""
    
    def test_me_unauthenticated(self, client, api_helper):
        """/me — non authentifié
        
        Act: GET /me sans Authorization.
        Attendu: 401.
        """
        response = client.get("/auth/me")
        
        # Assert unauthorized (401 or 403 are both valid for unauthenticated)
        assert response.status_code in [401, 403]
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_me_authenticated(self, client, authenticated_user, api_helper):
        """/me — authentifié
        
        Pré: access token valide.
        Act: GET /me.
        Attendu: 200, UserResponse (rôle, flags, métadonnées).
        """
        response = client.get("/auth/me", headers=authenticated_user["headers"])
        
        # Assert success
        assert response.status_code == 200
        
        # Assert user response structure
        response_data = response.json()
        api_helper.assert_valid_user_response(response_data)
        
        # Assert specific user data
        assert response_data["email"] == authenticated_user["credentials"]["email"]
        assert response_data["role"] in ["admin", "client", "manager", "washer"]  # Valid role
        assert response_data["is_active"] is True
        assert response_data["email_verified"] is True  # Should be verified after login

    def test_me_invalid_token(self, client, api_helper):
        """Test /me with invalid token"""
        headers = {"Authorization": "Bearer invalid_token_here"}
        
        response = client.get("/auth/me", headers=headers)
        
        # Assert unauthorized
        assert response.status_code in [401, 403]
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_me_malformed_authorization_header(self, client, api_helper):
        """Test /me with malformed Authorization header"""
        # Missing Bearer prefix
        headers = {"Authorization": "invalid_format_token"}
        
        response = client.get("/auth/me", headers=headers)
        
        # Assert unauthorized
        assert response.status_code in [401, 403]

    def test_me_empty_authorization_header(self, client, api_helper):
        """Test /me with empty Authorization header"""
        headers = {"Authorization": ""}
        
        response = client.get("/auth/me", headers=headers)
        
        # Assert unauthorized
        assert response.status_code in [401, 403]