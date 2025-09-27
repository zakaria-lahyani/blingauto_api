"""
Integration tests for Auth API endpoints
"""
import pytest
from httpx import AsyncClient


class TestAuthRegistration:
    """Test user registration endpoints"""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient):
        """Test successful user registration"""
        # Arrange
        user_data = {
            "email": "newuser@example.com",
            "password": "NewPassword123!",
            "first_name": "New",
            "last_name": "User"
        }
        
        # Act
        response = await client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["first_name"] == user_data["first_name"]
        assert data["last_name"] == user_data["last_name"]
        assert data["role"] == "client"
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email"""
        # Arrange
        user_data = {
            "email": "duplicate@example.com",
            "password": "Password123!",
            "first_name": "First",
            "last_name": "User"
        }
        
        # Register first user
        response1 = await client.post("/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Act - Try to register with same email
        response2 = await client.post("/auth/register", json=user_data)
        
        # Assert
        assert response2.status_code == 400
        data = response2.json()
        assert "already exists" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_user_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format"""
        # Arrange
        user_data = {
            "email": "invalid-email",
            "password": "Password123!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Act
        response = await client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_register_user_weak_password(self, client: AsyncClient):
        """Test registration with weak password"""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "weak",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Act
        response = await client.post("/auth/register", json=user_data)
        
        # Assert
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_register_user_missing_fields(self, client: AsyncClient):
        """Test registration with missing required fields"""
        # Arrange
        incomplete_data = {
            "email": "test@example.com",
            # Missing password, first_name, last_name
        }
        
        # Act
        response = await client.post("/auth/register", json=incomplete_data)
        
        # Assert
        assert response.status_code == 422


class TestAuthLogin:
    """Test user login endpoints"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Test successful user login"""
        # Arrange - Register a user first
        register_data = {
            "email": "logintest@example.com",
            "password": "LoginPassword123!",
            "first_name": "Login",
            "last_name": "Test"
        }
        register_response = await client.post("/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"]
        }
        
        # Act
        response = await client.post("/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == register_data["email"]
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials"""
        # Arrange
        login_data = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!"
        }
        
        # Act
        response = await client.post("/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "invalid credentials" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        """Test login with correct email but wrong password"""
        # Arrange - Register a user first
        register_data = {
            "email": "wrongpass@example.com",
            "password": "CorrectPassword123!",
            "first_name": "Wrong",
            "last_name": "Pass"
        }
        register_response = await client.post("/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        login_data = {
            "email": register_data["email"],
            "password": "WrongPassword123!"
        }
        
        # Act
        response = await client.post("/auth/login", json=login_data)
        
        # Assert
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_missing_fields(self, client: AsyncClient):
        """Test login with missing fields"""
        # Arrange
        incomplete_data = {
            "email": "test@example.com"
            # Missing password
        }
        
        # Act
        response = await client.post("/auth/login", json=incomplete_data)
        
        # Assert
        assert response.status_code == 422


class TestTokenOperations:
    """Test token-related operations"""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, authenticated_client):
        """Test successful token refresh"""
        # Arrange
        client, tokens = authenticated_client
        refresh_data = {
            "refresh_token": tokens["refresh_token"]
        }
        
        # Act
        response = await client.post("/auth/refresh", json=refresh_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        # New tokens should be different from old ones
        assert data["access_token"] != tokens["access_token"]
        assert data["refresh_token"] != tokens["refresh_token"]
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh with invalid token"""
        # Arrange
        refresh_data = {
            "refresh_token": "invalid.refresh.token"
        }
        
        # Act
        response = await client.post("/auth/refresh", json=refresh_data)
        
        # Assert
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_logout_success(self, authenticated_client):
        """Test successful logout"""
        # Arrange
        client, tokens = authenticated_client
        
        # Act
        response = await client.post("/auth/logout")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "logged out successfully" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_logout_all_devices_success(self, authenticated_client):
        """Test successful logout from all devices"""
        # Arrange
        client, tokens = authenticated_client
        
        # Act
        response = await client.post("/auth/logout-all")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "logged out from all devices" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_logout_without_auth(self, client: AsyncClient):
        """Test logout without authentication"""
        # Act
        response = await client.post("/auth/logout")
        
        # Assert
        assert response.status_code == 401


class TestProtectedEndpoints:
    """Test authentication-protected endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, authenticated_client):
        """Test getting current user profile"""
        # Arrange
        client, tokens = authenticated_client
        
        # Act
        response = await client.get("/auth/me")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "first_name" in data
        assert "last_name" in data
        assert "role" in data
        assert "password" not in data
        assert "hashed_password" not in data
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication"""
        # Act
        response = await client.get("/auth/me")
        
        # Assert
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_update_profile(self, authenticated_client):
        """Test updating user profile"""
        # Arrange
        client, tokens = authenticated_client
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        
        # Act
        response = await client.put("/auth/me", json=update_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
    
    @pytest.mark.asyncio
    async def test_change_password(self, authenticated_client):
        """Test changing user password"""
        # Arrange
        client, tokens = authenticated_client
        change_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewPassword456!"
        }
        
        # Act
        response = await client.post("/auth/change-password", json=change_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "password changed successfully" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, authenticated_client):
        """Test changing password with wrong current password"""
        # Arrange
        client, tokens = authenticated_client
        change_data = {
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword456!"
        }
        
        # Act
        response = await client.post("/auth/change-password", json=change_data)
        
        # Assert
        assert response.status_code == 400


class TestPasswordReset:
    """Test password reset functionality"""
    
    @pytest.mark.asyncio
    async def test_forgot_password(self, client: AsyncClient):
        """Test forgot password request"""
        # Arrange - Register a user first
        register_data = {
            "email": "forgot@example.com",
            "password": "ForgotPassword123!",
            "first_name": "Forgot",
            "last_name": "Test"
        }
        register_response = await client.post("/auth/register", json=register_data)
        assert register_response.status_code == 201
        
        forgot_data = {
            "email": register_data["email"]
        }
        
        # Act
        response = await client.post("/auth/forgot-password", json=forgot_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "reset instructions sent" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_email(self, client: AsyncClient):
        """Test forgot password with non-existent email"""
        # Arrange
        forgot_data = {
            "email": "nonexistent@example.com"
        }
        
        # Act
        response = await client.post("/auth/forgot-password", json=forgot_data)
        
        # Assert - Should still return 200 for security (don't reveal if email exists)
        assert response.status_code == 200


class TestAdminEndpoints:
    """Test admin-only endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_all_users_as_admin(self, admin_client):
        """Test getting all users as admin"""
        # Arrange
        client, tokens = admin_client
        
        # Act
        response = await client.get("/auth/users")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert isinstance(data["users"], list)
    
    @pytest.mark.asyncio
    async def test_get_all_users_as_regular_user(self, authenticated_client):
        """Test getting all users as regular user (should fail)"""
        # Arrange
        client, tokens = authenticated_client
        
        # Act
        response = await client.get("/auth/users")
        
        # Assert
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_delete_user_as_admin(self, admin_client):
        """Test deleting user as admin"""
        # Arrange
        client, tokens = admin_client
        
        # Create a user to delete
        user_data = {
            "email": "todelete@example.com",
            "password": "DeleteMe123!",
            "first_name": "To",
            "last_name": "Delete"
        }
        register_response = await client.post("/auth/register", json=user_data)
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]
        
        # Act
        response = await client.delete(f"/auth/users/{user_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_change_user_role_as_admin(self, admin_client):
        """Test changing user role as admin"""
        # Arrange
        client, tokens = admin_client
        
        # Create a user
        user_data = {
            "email": "rolechange@example.com",
            "password": "RoleChange123!",
            "first_name": "Role",
            "last_name": "Change"
        }
        register_response = await client.post("/auth/register", json=user_data)
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]
        
        role_data = {
            "role": "manager"
        }
        
        # Act
        response = await client.put(f"/auth/users/{user_id}/role", json=role_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "manager"


class TestEmailVerification:
    """Test email verification endpoints"""
    
    @pytest.mark.asyncio
    async def test_request_email_verification(self, authenticated_client):
        """Test requesting email verification"""
        # Arrange
        client, tokens = authenticated_client
        
        # Act
        response = await client.post("/auth/verify-email/request")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "verification email sent" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_request_email_verification_unauthorized(self, client: AsyncClient):
        """Test requesting email verification without auth"""
        # Act
        response = await client.post("/auth/verify-email/request")
        
        # Assert
        assert response.status_code == 401


class TestFeatureStatus:
    """Test feature status endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_auth_features(self, client: AsyncClient):
        """Test getting auth feature status"""
        # Act
        response = await client.get("/auth/features")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "features" in data
        assert isinstance(data["features"], dict)
        # Should contain feature status flags
        expected_features = [
            "email_verification",
            "password_reset", 
            "account_lockout",
            "token_rotation",
            "rate_limiting"
        ]
        for feature in expected_features:
            assert feature in data["features"]