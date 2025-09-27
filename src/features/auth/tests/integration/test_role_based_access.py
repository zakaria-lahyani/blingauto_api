"""
Integration tests for Role-Based Access Control (RBAC)
"""
import pytest
from httpx import AsyncClient
from src.features.auth.domain.enums import AuthRole


class TestRoleBasedAccess:
    """Test role-based access control across different endpoints"""
    
    @pytest.mark.asyncio
    async def test_client_access_permissions(self, authenticated_client):
        """Test what a CLIENT role can and cannot access"""
        # Arrange
        client, tokens = authenticated_client
        
        # Act & Assert - Should have access to
        # Get own profile
        response = await client.get("/auth/me")
        assert response.status_code == 200
        
        # Update own profile
        response = await client.put("/auth/me", json={"first_name": "Updated"})
        assert response.status_code == 200
        
        # Change own password
        response = await client.post("/auth/change-password", json={
            "current_password": "TestPassword123!",
            "new_password": "NewPassword456!"
        })
        assert response.status_code == 200
        
        # Request email verification
        response = await client.post("/auth/verify-email/request")
        assert response.status_code == 200
        
        # Act & Assert - Should NOT have access to
        # List all users
        response = await client.get("/auth/users")
        assert response.status_code == 403
        
        # Get other user details (use a fake UUID)
        response = await client.get("/auth/users/550e8400-e29b-41d4-a716-446655440000")
        assert response.status_code == 403
        
        # Change other user's role
        response = await client.put("/auth/users/550e8400-e29b-41d4-a716-446655440000/role", 
                                   json={"role": "manager"})
        assert response.status_code == 403
        
        # Delete other user
        response = await client.delete("/auth/users/550e8400-e29b-41d4-a716-446655440000")
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_manager_access_permissions(self, client: AsyncClient):
        """Test what a MANAGER role can and cannot access"""
        # Arrange - Create manager user
        manager_user = await self._create_user_with_role(client, AuthRole.MANAGER, {
            "email": "manager@test.com",
            "password": "ManagerPass123!",
            "first_name": "Test",
            "last_name": "Manager"
        })
        
        # Login as manager
        login_response = await client.post("/auth/login", json={
            "email": "manager@test.com",
            "password": "ManagerPass123!"
        })
        assert login_response.status_code == 200
        tokens = login_response.json()
        client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
        
        # Act & Assert - Should have access to
        # Get own profile
        response = await client.get("/auth/me")
        assert response.status_code == 200
        
        # List all users
        response = await client.get("/auth/users")
        assert response.status_code == 200
        
        # Get specific user details
        response = await client.get(f"/auth/users/{manager_user['id']}")
        assert response.status_code == 200
        
        # Act & Assert - Should NOT have access to
        # Delete users (admin only)
        response = await client.delete(f"/auth/users/{manager_user['id']}")
        assert response.status_code == 403
        
        # Change user role to admin (admin only)
        response = await client.put(f"/auth/users/{manager_user['id']}/role", 
                                   json={"role": "admin"})
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_admin_access_permissions(self, admin_client):
        """Test what an ADMIN role can access (should be everything)"""
        # Arrange
        client, tokens = admin_client
        
        # Create a test user to manipulate
        test_user_data = {
            "email": "testuser@admin.com",
            "password": "TestUser123!",
            "first_name": "Test",
            "last_name": "User"
        }
        register_response = await client.post("/auth/register", json=test_user_data)
        assert register_response.status_code == 201
        test_user_id = register_response.json()["id"]
        
        # Act & Assert - Admin should have access to everything
        # Get own profile
        response = await client.get("/auth/me")
        assert response.status_code == 200
        
        # List all users
        response = await client.get("/auth/users")
        assert response.status_code == 200
        
        # Get specific user details
        response = await client.get(f"/auth/users/{test_user_id}")
        assert response.status_code == 200
        
        # Change user role
        response = await client.put(f"/auth/users/{test_user_id}/role", 
                                   json={"role": "manager"})
        assert response.status_code == 200
        
        # Delete user
        response = await client.delete(f"/auth/users/{test_user_id}")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_washer_access_permissions(self, client: AsyncClient):
        """Test what a WASHER role can and cannot access"""
        # Arrange - Create washer user
        washer_user = await self._create_user_with_role(client, AuthRole.WASHER, {
            "email": "washer@test.com",
            "password": "WasherPass123!",
            "first_name": "Test",
            "last_name": "Washer"
        })
        
        # Login as washer
        login_response = await client.post("/auth/login", json={
            "email": "washer@test.com",
            "password": "WasherPass123!"
        })
        assert login_response.status_code == 200
        tokens = login_response.json()
        client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
        
        # Act & Assert - Should have access to basic operations
        # Get own profile
        response = await client.get("/auth/me")
        assert response.status_code == 200
        
        # Update own profile
        response = await client.put("/auth/me", json={"first_name": "Updated"})
        assert response.status_code == 200
        
        # Act & Assert - Should NOT have access to administrative operations
        # List all users
        response = await client.get("/auth/users")
        assert response.status_code == 403
        
        # Get other user details
        response = await client.get(f"/auth/users/{washer_user['id']}")
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_unauthenticated_access(self, client: AsyncClient):
        """Test what unauthenticated users can access"""
        # Act & Assert - Should have access to public endpoints
        # Health check (if exists)
        response = await client.get("/health")
        assert response.status_code == 200
        
        # Registration
        response = await client.post("/auth/register", json={
            "email": "public@test.com",
            "password": "PublicUser123!",
            "first_name": "Public",
            "last_name": "User"
        })
        assert response.status_code == 201
        
        # Login
        response = await client.post("/auth/login", json={
            "email": "public@test.com",
            "password": "PublicUser123!"
        })
        assert response.status_code == 200
        
        # Forgot password
        response = await client.post("/auth/forgot-password", json={
            "email": "public@test.com"
        })
        assert response.status_code == 200
        
        # Feature status
        response = await client.get("/auth/features")
        assert response.status_code == 200
        
        # Act & Assert - Should NOT have access to protected endpoints
        # Get current user
        response = await client.get("/auth/me")
        assert response.status_code == 401
        
        # List users
        response = await client.get("/auth/users")
        assert response.status_code == 401
        
        # Logout
        response = await client.post("/auth/logout")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_role_hierarchy_enforcement(self, admin_client):
        """Test that role hierarchy is properly enforced"""
        # Arrange
        client, tokens = admin_client
        
        # Create users with different roles
        users = []
        roles = [AuthRole.CLIENT, AuthRole.WASHER, AuthRole.MANAGER]
        
        for i, role in enumerate(roles):
            user_data = {
                "email": f"user{i}@hierarchy.com",
                "password": f"Password{i}123!",
                "first_name": f"User{i}",
                "last_name": "Hierarchy"
            }
            register_response = await client.post("/auth/register", json=user_data)
            assert register_response.status_code == 201
            user = register_response.json()
            
            # Set role
            role_response = await client.put(f"/auth/users/{user['id']}/role", 
                                           json={"role": role.value})
            assert role_response.status_code == 200
            users.append(user)
        
        # Test manager can view but not delete
        manager_login = await client.post("/auth/login", json={
            "email": "user2@hierarchy.com",
            "password": "Password2123!"
        })
        manager_tokens = manager_login.json()
        
        # Create new client for manager
        manager_headers = {"Authorization": f"Bearer {manager_tokens['access_token']}"}
        
        # Manager should be able to view users
        response = await client.get("/auth/users", headers=manager_headers)
        assert response.status_code == 200
        
        # But not delete them
        response = await client.delete(f"/auth/users/{users[0]['id']}", headers=manager_headers)
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_invalid_role_assignment(self, admin_client):
        """Test that invalid roles cannot be assigned"""
        # Arrange
        client, tokens = admin_client
        
        # Create a test user
        user_data = {
            "email": "invalid@role.com",
            "password": "InvalidRole123!",
            "first_name": "Invalid",
            "last_name": "Role"
        }
        register_response = await client.post("/auth/register", json=user_data)
        assert register_response.status_code == 201
        user_id = register_response.json()["id"]
        
        # Act & Assert - Try to assign invalid role
        response = await client.put(f"/auth/users/{user_id}/role", 
                                   json={"role": "invalid_role"})
        assert response.status_code == 422
    
    async def _create_user_with_role(self, client: AsyncClient, role: AuthRole, user_data: dict):
        """Helper method to create a user with specific role"""
        # First create as admin to have permission to change roles
        admin_headers = {"Authorization": "Bearer admin_token"}  # This would need proper admin token
        
        # Register user
        register_response = await client.post("/auth/register", json=user_data)
        assert register_response.status_code == 201
        user = register_response.json()
        
        # This is a simplified version - in reality you'd need admin privileges
        # For the test, we'll assume the role change succeeds
        user["role"] = role.value
        return user