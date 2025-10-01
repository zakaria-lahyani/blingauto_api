"""
API Integration Tests for Authentication Feature

Tests all auth endpoints including:
- User registration
- Login/logout
- Token refresh
- Email verification
- Password reset
- Profile management
- Admin user management
"""

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
class TestAuthRegistration:
    """Test user registration endpoints."""

    async def test_register_new_user(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User",
                "phone": "+1234567890"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["role"] == "client"
        assert "id" in data

    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with existing email fails."""
        # Register first user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "SecurePass123!",
                "full_name": "First User"
            }
        )

        # Try to register with same email
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "DifferentPass123!",
                "full_name": "Second User"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "weak",
                "full_name": "Weak Password User"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
                "full_name": "Invalid Email"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
class TestAuthLogin:
    """Test login and authentication endpoints."""

    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        # Register user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "SecurePass123!",
                "full_name": "Login Test"
            }
        )

        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "SecurePass123!"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient):
        """Test login with wrong password fails."""
        # Register user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "CorrectPass123!",
                "full_name": "Wrong Password Test"
            }
        )

        # Try login with wrong password
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "WrongPass123!"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user fails."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "AnyPass123!"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestAuthToken:
    """Test token management endpoints."""

    async def test_refresh_token(self, client: AsyncClient):
        """Test token refresh."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "SecurePass123!",
                "full_name": "Refresh Test"
            }
        )

        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "refresh@example.com",
                "password": "SecurePass123!"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token fails."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_logout(self, client: AsyncClient, auth_headers: dict):
        """Test logout."""
        response = await client.post(
            "/api/v1/auth/logout",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestAuthProfile:
    """Test user profile endpoints."""

    async def test_get_profile(self, client: AsyncClient, auth_headers: dict):
        """Test getting user profile."""
        response = await client.get(
            "/api/v1/auth/profile",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "email" in data
        assert "full_name" in data

    async def test_update_profile(self, client: AsyncClient, auth_headers: dict):
        """Test updating user profile."""
        response = await client.put(
            "/api/v1/auth/profile",
            headers=auth_headers,
            json={
                "full_name": "Updated Name",
                "phone": "+9876543210"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["phone"] == "+9876543210"

    async def test_change_password(self, client: AsyncClient, auth_headers: dict):
        """Test changing password."""
        response = await client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json={
                "old_password": "SecurePass123!",
                "new_password": "NewSecurePass123!"
            }
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestAuthEmailVerification:
    """Test email verification endpoints."""

    async def test_request_verification_email(self, client: AsyncClient, auth_headers: dict):
        """Test requesting verification email."""
        response = await client.post(
            "/api/v1/auth/verify-email/request",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestAuthPasswordReset:
    """Test password reset endpoints."""

    async def test_request_password_reset(self, client: AsyncClient):
        """Test requesting password reset."""
        # Register user first
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "reset@example.com",
                "password": "SecurePass123!",
                "full_name": "Reset Test"
            }
        )

        response = await client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "reset@example.com"}
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestAuthAdminEndpoints:
    """Test admin user management endpoints."""

    async def test_list_users_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test listing users as admin."""
        response = await client.get(
            "/api/v1/auth/users",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    async def test_list_users_as_non_admin(self, client: AsyncClient, auth_headers: dict):
        """Test listing users as non-admin fails."""
        response = await client.get(
            "/api/v1/auth/users",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_update_user_role_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test updating user role as admin."""
        # Register a user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "roletest@example.com",
                "password": "SecurePass123!",
                "full_name": "Role Test"
            }
        )
        user_id = register_response.json()["id"]

        # Update role
        response = await client.put(
            f"/api/v1/auth/users/{user_id}/role",
            headers=admin_headers,
            json={"role": "manager"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "manager"
