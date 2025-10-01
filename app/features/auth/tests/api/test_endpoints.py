import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from app.core.db import Base, get_db
from app.features.auth.api import auth_router
from app.features.auth.domain import User, UserRole, UserStatus


@pytest.fixture(scope="function")
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def app(test_db):
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(auth_router)
    
    # Override database dependency
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_user_data():
    """Sample user registration data."""
    return {
        "email": "test@example.com",
        "password": "securepassword123",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890"
    }


@pytest.fixture
def admin_user_data():
    """Sample admin user data."""
    return {
        "email": "admin@example.com",
        "password": "adminpassword123",
        "first_name": "Admin",
        "last_name": "User"
    }


class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""
    
    @patch('app.features.auth.adapters.services.EmailServiceAdapter.send_verification_email')
    def test_register_user_success(self, mock_email, client, sample_user_data):
        """Test successful user registration."""
        mock_email.return_value = True
        
        response = client.post("/api/auth/register", json=sample_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["full_name"] == "John Doe"
        assert "verification" in data["message"].lower()
        assert "user_id" in data
    
    def test_register_user_invalid_email(self, client):
        """Test registration with invalid email."""
        invalid_data = {
            "email": "invalid-email",
            "password": "securepassword123",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        response = client.post("/api/auth/register", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "email" in str(data).lower()
    
    def test_register_user_weak_password(self, client):
        """Test registration with weak password."""
        weak_data = {
            "email": "test@example.com",
            "password": "weak",  # Too short
            "first_name": "John",
            "last_name": "Doe"
        }
        
        response = client.post("/api/auth/register", json=weak_data)
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.features.auth.adapters.services.EmailServiceAdapter.send_verification_email')
    def test_register_duplicate_email(self, mock_email, client, sample_user_data):
        """Test registration with duplicate email."""
        mock_email.return_value = True
        
        # Register first user
        response1 = client.post("/api/auth/register", json=sample_user_data)
        assert response1.status_code == 201
        
        # Try to register with same email
        response2 = client.post("/api/auth/register", json=sample_user_data)
        assert response2.status_code == 409  # Conflict
        data = response2.json()
        assert "already registered" in data["error"]["message"].lower()
    
    @patch('app.features.auth.adapters.services.EmailServiceAdapter.send_verification_email')
    @patch('app.features.auth.adapters.services.EmailServiceAdapter.send_welcome_email')
    def test_login_success(self, mock_welcome, mock_verification, client, sample_user_data):
        """Test successful login."""
        mock_verification.return_value = True
        mock_welcome.return_value = True
        
        # Register and verify user first
        register_response = client.post("/api/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        # Get verification token from response
        verification_token = register_response.json()["verification_token"]
        
        # Verify email
        verify_response = client.post(
            "/api/auth/verify-email", 
            json={"token": verification_token}
        )
        assert verify_response.status_code == 200
        
        # Now login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["email"] == sample_user_data["email"]
        assert data["role"] == "client"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "invalid email or password" in data["error"]["message"].lower()
    
    @patch('app.features.auth.adapters.services.EmailServiceAdapter.send_verification_email')
    def test_login_unverified_email(self, mock_email, client, sample_user_data):
        """Test login with unverified email."""
        mock_email.return_value = True
        
        # Register user but don't verify email
        register_response = client.post("/api/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        
        # Try to login without verification
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "verification" in data["error"]["message"].lower()
    
    @patch('app.features.auth.adapters.services.EmailServiceAdapter.send_verification_email')
    @patch('app.features.auth.adapters.services.EmailServiceAdapter.send_welcome_email')
    def test_refresh_token_success(self, mock_welcome, mock_verification, client, sample_user_data):
        """Test successful token refresh."""
        mock_verification.return_value = True
        mock_welcome.return_value = True
        
        # Register, verify, and login user
        register_response = client.post("/api/auth/register", json=sample_user_data)
        verification_token = register_response.json()["verification_token"]
        
        client.post("/api/auth/verify-email", json={"token": verification_token})
        
        login_response = client.post("/api/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        login_data = login_response.json()
        
        # Refresh token
        refresh_response = client.post("/api/auth/refresh", json={
            "refresh_token": login_data["refresh_token"]
        })
        
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        assert "refresh_token" in refresh_data
        assert refresh_data["token_type"] == "bearer"
    
    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token."""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid_refresh_token"
        })
        
        assert response.status_code == 401
        data = response.json()
        assert "invalid refresh token" in data["error"]["message"].lower()
    
    @patch('app.features.auth.adapters.services.EmailServiceAdapter.send_verification_email')
    @patch('app.features.auth.adapters.services.EmailServiceAdapter.send_welcome_email')
    def test_verify_email_success(self, mock_welcome, mock_verification, client, sample_user_data):
        """Test successful email verification."""
        mock_verification.return_value = True
        mock_welcome.return_value = True
        
        # Register user
        register_response = client.post("/api/auth/register", json=sample_user_data)
        verification_token = register_response.json()["verification_token"]
        
        # Verify email
        response = client.post("/api/auth/verify-email", json={
            "token": verification_token
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "verified successfully" in data["message"].lower()
    
    def test_verify_email_invalid_token(self, client):
        """Test email verification with invalid token."""
        response = client.post("/api/auth/verify-email", json={
            "token": "invalid_verification_token"
        })
        
        assert response.status_code == 404
        data = response.json()
        assert "verification token" in data["error"]["message"].lower()
    
    @patch('app.features.auth.adapters.services.EmailServiceAdapter.send_password_reset_email')
    def test_request_password_reset(self, mock_email, client, sample_user_data):
        """Test password reset request."""
        mock_email.return_value = True
        
        # Register user first
        client.post("/api/auth/register", json=sample_user_data)
        
        # Request password reset
        response = client.post("/api/auth/request-password-reset", json={
            "email": sample_user_data["email"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "password reset link" in data["message"].lower()
    
    def test_request_password_reset_nonexistent_email(self, client):
        """Test password reset request for non-existent email."""
        response = client.post("/api/auth/request-password-reset", json={
            "email": "nonexistent@example.com"
        })
        
        # Should still return success for security (don't reveal if email exists)
        assert response.status_code == 200
        data = response.json()
        assert "password reset link" in data["message"].lower()


class TestUserManagementEndpoints:
    """Test user management API endpoints."""
    
    @patch('app.features.auth.adapters.services.EmailServiceAdapter.send_verification_email')
    @patch('app.features.auth.adapters.services.EmailServiceAdapter.send_welcome_email')
    def test_get_current_user_profile(self, mock_welcome, mock_verification, client, sample_user_data):
        """Test getting current user profile."""
        mock_verification.return_value = True
        mock_welcome.return_value = True
        
        # Register, verify, and login user
        register_response = client.post("/api/auth/register", json=sample_user_data)
        verification_token = register_response.json()["verification_token"]
        
        client.post("/api/auth/verify-email", json={"token": verification_token})
        
        login_response = client.post("/api/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        access_token = login_response.json()["access_token"]
        
        # Get profile
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["first_name"] == sample_user_data["first_name"]
        assert data["last_name"] == sample_user_data["last_name"]
        assert data["role"] == "client"
        assert data["email_verified"] == True
    
    def test_get_profile_without_auth(self, client):
        """Test getting profile without authentication."""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 401
    
    def test_get_profile_with_invalid_token(self, client):
        """Test getting profile with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/auth/me", headers=headers)
        
        assert response.status_code == 401


class TestAdminEndpoints:
    """Test admin-only endpoints."""
    
    @patch('app.features.auth.adapters.services.EmailServiceAdapter.send_verification_email')
    @patch('app.features.auth.adapters.services.EmailServiceAdapter.send_welcome_email')
    def test_list_users_as_admin(self, mock_welcome, mock_verification, client, admin_user_data, sample_user_data):
        """Test listing users as admin."""
        mock_verification.return_value = True
        mock_welcome.return_value = True
        
        # Create and verify admin user
        admin_register = client.post("/api/auth/register", json={**admin_user_data, "role": "admin"})
        admin_token = admin_register.json()["verification_token"]
        client.post("/api/auth/verify-email", json={"token": admin_token})
        
        admin_login = client.post("/api/auth/login", json={
            "email": admin_user_data["email"],
            "password": admin_user_data["password"]
        })
        admin_access_token = admin_login.json()["access_token"]
        
        # Create regular user
        client.post("/api/auth/register", json=sample_user_data)
        
        # List users as admin
        headers = {"Authorization": f"Bearer {admin_access_token}"}
        response = client.get("/api/auth/users", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert len(data["users"]) >= 1  # At least the admin user
    
    @patch('app.features.auth.adapters.services.EmailServiceAdapter.send_verification_email')
    @patch('app.features.auth.adapters.services.EmailServiceAdapter.send_welcome_email')
    def test_list_users_as_non_admin(self, mock_welcome, mock_verification, client, sample_user_data):
        """Test listing users as non-admin should fail."""
        mock_verification.return_value = True
        mock_welcome.return_value = True
        
        # Register, verify, and login regular user
        register_response = client.post("/api/auth/register", json=sample_user_data)
        verification_token = register_response.json()["verification_token"]
        
        client.post("/api/auth/verify-email", json={"token": verification_token})
        
        login_response = client.post("/api/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        access_token = login_response.json()["access_token"]
        
        # Try to list users as regular user
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/auth/users", headers=headers)
        
        assert response.status_code == 403  # Forbidden
    
    def test_list_users_without_auth(self, client):
        """Test listing users without authentication."""
        response = client.get("/api/auth/users")
        
        assert response.status_code == 401


class TestValidationAndErrorHandling:
    """Test validation and error handling."""
    
    def test_missing_required_fields(self, client):
        """Test registration with missing required fields."""
        incomplete_data = {
            "email": "test@example.com",
            # Missing password, first_name, last_name
        }
        
        response = client.post("/api/auth/register", json=incomplete_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert "validation" in data["error"]["message"].lower()
    
    def test_invalid_json(self, client):
        """Test request with invalid JSON."""
        response = client.post(
            "/api/auth/register",
            data="invalid json",
            headers={"content-type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_malformed_email(self, client):
        """Test various malformed email formats."""
        malformed_emails = [
            "not-an-email",
            "@example.com",
            "test@",
            "test..test@example.com",
        ]
        
        for email in malformed_emails:
            data = {
                "email": email,
                "password": "securepassword123",
                "first_name": "Test",
                "last_name": "User"
            }
            
            response = client.post("/api/auth/register", json=data)
            assert response.status_code == 422, f"Email {email} should be invalid"
    
    def test_rate_limiting_simulation(self, client):
        """Test rate limiting behavior (if implemented)."""
        # This would test rate limiting if it's implemented
        # For now, just ensure multiple requests don't crash the system
        
        for i in range(10):
            response = client.post("/api/auth/request-password-reset", json={
                "email": f"test{i}@example.com"
            })
            # Should not crash, but might be rate limited
            assert response.status_code in [200, 429]