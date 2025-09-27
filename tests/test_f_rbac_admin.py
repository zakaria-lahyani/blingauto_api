"""
F. RBAC Admin/Manager Tests
"""
import pytest
import time
import uuid


@pytest.mark.rbac
@pytest.mark.integration
@pytest.mark.asyncio
class TestListUsers:
    """Test user listing scenarios with role-based access"""
    
    def test_list_users_unauthenticated(self, client, api_helper):
        """List users — rôle requis
        
        Act: GET /users avec:
        Non-auth → 401
        """
        response = client.get("/auth/users")
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_list_users_unauthorized_role(self, client, authenticated_user, api_helper):
        """List users — rôle requis
        
        Auth non-autorisé (e.g., washer) → 403
        """
        # Regular client user should not be able to list users
        headers = authenticated_user["headers"]
        
        response = client.get("/auth/users", headers=headers)
        
        # Assert forbidden
        assert response.status_code == 403
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_list_users_unauthorized_washer(self, client, washer_user, api_helper):
        """Washer role should not be able to list users"""
        headers = washer_user["headers"]
        
        response = client.get("/auth/users", headers=headers)
        
        # Assert forbidden
        assert response.status_code == 403
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_list_users_admin_authorized(self, client, admin_user, api_helper):
        """List users — rôle requis
        
        Admin/Manager → 200 + pagination/sorting si applicable.
        """
        headers = admin_user["headers"]
        
        response = client.get("/auth/users", headers=headers)
        
        # Assert success
        assert response.status_code == 200
        
        # Assert response structure
        response_data = response.json()
        assert "users" in response_data
        assert "total" in response_data
        assert "page" in response_data
        assert "size" in response_data
        
        # Assert users list structure
        users = response_data["users"]
        assert isinstance(users, list)
        assert len(users) >= 1  # At least the admin user
        
        # Check user structure
        for user in users:
            api_helper.assert_valid_user_response(user)

    def test_list_users_manager_authorized(self, client, manager_user, api_helper):
        """Manager should be able to list users"""
        headers = manager_user["headers"]
        
        response = client.get("/auth/users", headers=headers)
        
        # Assert success
        assert response.status_code == 200
        
        # Assert response structure
        response_data = response.json()
        assert "users" in response_data
        assert isinstance(response_data["users"], list)

    def test_list_users_pagination(self, client, admin_user):
        """Test user listing with pagination"""
        headers = admin_user["headers"]
        
        # Test with pagination parameters
        response = client.get("/auth/users?page=1&size=5", headers=headers)
        
        # Assert success
        assert response.status_code == 200
        
        response_data = response.json()
        assert "users" in response_data
        assert "total" in response_data
        assert "page" in response_data
        assert "size" in response_data
        
        # Assert pagination values
        assert response_data["page"] == 1
        assert response_data["size"] == 5
        assert len(response_data["users"]) <= 5

    def test_list_users_filtering(self, client, admin_user):
        """Filtrage /users
        
        ?email=... renvoie liste filtrée, pas d'erreur.
        """
        headers = admin_user["headers"]
        
        # Test filtering by email (should not error even if no results)
        response = client.get("/auth/users?email=nonexistent@example.com", headers=headers)
        
        # Should not error
        assert response.status_code == 200
        
        response_data = response.json()
        assert "users" in response_data
        # Result might be empty, but structure should be valid
        assert isinstance(response_data["users"], list)


@pytest.mark.rbac
@pytest.mark.integration
@pytest.mark.asyncio
class TestGetUserById:
    """Test getting specific user by ID"""
    
    def test_get_user_admin_authorized(self, client, admin_user, registered_user, api_helper):
        """Get user by id — visibilité
        
        Admin: 200.
        """
        headers = admin_user["headers"]
        user_id = registered_user["user_data"]["id"]
        
        response = client.get(f"/auth/users/{user_id}", headers=headers)
        
        # Assert success
        assert response.status_code == 200
        
        # Assert user response structure
        response_data = response.json()
        api_helper.assert_valid_user_response(response_data)
        
        # Assert correct user
        assert response_data["id"] == user_id
        assert response_data["email"] == registered_user["credentials"]["email"]

    def test_get_user_unauthorized(self, client, authenticated_user, registered_user, api_helper):
        """Get user by id — visibilité
        
        Autre: 403 (ou 200 restreint si autorisé à voir partiel).
        """
        headers = authenticated_user["headers"]
        user_id = registered_user["user_data"]["id"]
        
        response = client.get(f"/auth/users/{user_id}", headers=headers)
        
        # Assert forbidden (regular users can't view other users)
        assert response.status_code == 403
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_get_user_self(self, client, authenticated_user, api_helper):
        """User should be able to view their own profile via /users/{id}"""
        headers = authenticated_user["headers"]
        user_id = authenticated_user["user_data"]["id"]
        
        response = client.get(f"/auth/users/{user_id}", headers=headers)
        
        # Depending on implementation, might be allowed or redirect to /me
        assert response.status_code in [200, 403]
        
        if response.status_code == 200:
            response_data = response.json()
            api_helper.assert_valid_user_response(response_data)
            assert response_data["id"] == user_id

    def test_get_user_nonexistent(self, client, admin_user, api_helper):
        """Test getting non-existent user"""
        headers = admin_user["headers"]
        nonexistent_id = 99999
        
        response = client.get(f"/auth/users/{nonexistent_id}", headers=headers)
        
        # Assert not found
        assert response.status_code == 404
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_get_user_invalid_id(self, client, admin_user):
        """Test getting user with invalid ID"""
        headers = admin_user["headers"]
        
        response = client.get("/auth/users/invalid_id", headers=headers)
        
        # Assert validation error
        assert response.status_code == 422

    def test_get_user_unauthenticated(self, client, registered_user, api_helper):
        """Test getting user without authentication"""
        user_id = registered_user["user_data"]["id"]
        
        response = client.get(f"/auth/users/{user_id}")
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)


@pytest.mark.rbac
@pytest.mark.integration
@pytest.mark.asyncio
class TestChangeUserRole:
    """Test changing user roles"""
    
    def test_change_user_role_admin_success(self, client, admin_user, registered_user, api_helper):
        """Change user role — contrôle strict
        
        Admin change rôle d'un autre user.
        Attendu: 200.
        """
        headers = admin_user["headers"]
        user_id = registered_user["user_data"]["id"]
        
        role_data = {
            "role": "manager"
        }
        
        response = client.put(f"/auth/users/{user_id}/role", json=role_data, headers=headers)
        
        # Assert success
        assert response.status_code == 200
        
        # Assert user response structure
        response_data = response.json()
        api_helper.assert_valid_user_response(response_data)
        
        # Assert role changed
        assert response_data["role"] == "manager"
        assert response_data["id"] == user_id

    def test_change_user_role_unauthorized(self, client, authenticated_user, registered_user, api_helper):
        """Change user role — contrôle strict
        
        Non-admin → 403.
        """
        headers = authenticated_user["headers"]
        user_id = registered_user["user_data"]["id"]
        
        role_data = {
            "role": "admin"
        }
        
        response = client.put(f"/auth/users/{user_id}/role", json=role_data, headers=headers)
        
        # Assert forbidden
        assert response.status_code == 403
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_change_own_role_forbidden(self, client, admin_user, api_helper):
        """Change user role — contrôle strict
        
        Auto-élévation (user change son rôle) → 403.
        """
        headers = admin_user["headers"]
        user_id = admin_user["user_data"]["id"]
        
        role_data = {
            "role": "client"  # Admin trying to demote themselves
        }
        
        response = client.put(f"/auth/users/{user_id}/role", json=role_data, headers=headers)
        
        # Assert forbidden (users shouldn't change their own role)
        assert response.status_code == 403
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_change_user_role_invalid_role(self, client, admin_user, registered_user):
        """Test changing user to invalid role"""
        headers = admin_user["headers"]
        user_id = registered_user["user_data"]["id"]
        
        role_data = {
            "role": "super_admin"  # Invalid role
        }
        
        response = client.put(f"/auth/users/{user_id}/role", json=role_data, headers=headers)
        
        # Assert validation error
        assert response.status_code == 422

    def test_change_user_role_nonexistent_user(self, client, admin_user, api_helper):
        """Test changing role of non-existent user"""
        headers = admin_user["headers"]
        nonexistent_id = 99999
        
        role_data = {
            "role": "manager"
        }
        
        response = client.put(f"/auth/users/{nonexistent_id}/role", json=role_data, headers=headers)
        
        # Assert not found
        assert response.status_code == 404
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_change_user_role_missing_role(self, client, admin_user, registered_user):
        """Test changing user role without specifying role"""
        headers = admin_user["headers"]
        user_id = registered_user["user_data"]["id"]
        
        response = client.put(f"/auth/users/{user_id}/role", json={}, headers=headers)
        
        # Assert validation error
        assert response.status_code == 422

    def test_change_user_role_manager_authorized(self, client, manager_user, registered_user, api_helper):
        """Test if manager can change user roles (depending on business rules)"""
        headers = manager_user["headers"]
        user_id = registered_user["user_data"]["id"]
        
        role_data = {
            "role": "washer"
        }
        
        response = client.put(f"/auth/users/{user_id}/role", json=role_data, headers=headers)
        
        # Depending on business rules, manager might or might not be allowed
        # This test documents the expected behavior
        assert response.status_code in [200, 403]


@pytest.mark.rbac
@pytest.mark.integration
@pytest.mark.asyncio
class TestDeleteUser:
    """Test user deletion scenarios"""
    
    def test_delete_user_admin_success(self, client, admin_user, registered_user, api_helper):
        """Delete user — règles
        
        Admin supprime autre user → 200/204.
        """
        headers = admin_user["headers"]
        user_id = registered_user["user_data"]["id"]
        
        response = client.delete(f"/auth/users/{user_id}", headers=headers)
        
        # Assert success
        assert response.status_code in [200, 204]
        
        if response.status_code == 200:
            response_data = response.json()
            api_helper.assert_message_response(response_data)
        
        # Verify user is actually deleted
        get_response = client.get(f"/auth/users/{user_id}", headers=headers)
        assert get_response.status_code == 404

    def test_delete_user_unauthorized(self, client, authenticated_user, registered_user, api_helper):
        """Delete user — règles
        
        Non-admin → 403.
        """
        headers = authenticated_user["headers"]
        user_id = registered_user["user_data"]["id"]
        
        response = client.delete(f"/auth/users/{user_id}", headers=headers)
        
        # Assert forbidden
        assert response.status_code == 403
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_delete_self_protection(self, client, admin_user, api_helper):
        """Delete user — règles
        
        Protection auto-suppression (optionnel): admin ne peut pas se supprimer si dernière instance → 400.
        """
        headers = admin_user["headers"]
        user_id = admin_user["user_data"]["id"]
        
        response = client.delete(f"/auth/users/{user_id}", headers=headers)
        
        # Depending on implementation, might be forbidden or allowed
        # If forbidden (self-protection), should be 400 or 403
        # If allowed, should be 200/204
        assert response.status_code in [200, 204, 400, 403]
        
        if response.status_code in [400, 403]:
            response_data = response.json()
            api_helper.assert_error_response(response_data)

    def test_delete_user_nonexistent(self, client, admin_user, api_helper):
        """Test deleting non-existent user"""
        headers = admin_user["headers"]
        nonexistent_id = 99999
        
        response = client.delete(f"/auth/users/{nonexistent_id}", headers=headers)
        
        # Assert not found
        assert response.status_code == 404
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_delete_user_invalid_id(self, client, admin_user):
        """Test deleting user with invalid ID"""
        headers = admin_user["headers"]
        
        response = client.delete("/auth/users/invalid_id", headers=headers)
        
        # Assert validation error
        assert response.status_code == 422

    def test_delete_user_unauthenticated(self, client, registered_user, api_helper):
        """Test deleting user without authentication"""
        user_id = registered_user["user_data"]["id"]
        
        response = client.delete(f"/auth/users/{user_id}")
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    async def test_delete_user_cascading_effects(self, client, admin_user, registered_user, auth_module):
        """Test that user deletion handles cascading effects properly"""
        headers = admin_user["headers"]
        user_id = registered_user["user_data"]["id"]
        user_email = registered_user["credentials"]["email"]
        
        # Delete user
        response = client.delete(f"/auth/users/{user_id}", headers=headers)
        assert response.status_code in [200, 204]
        
        # Verify user cannot login after deletion
        login_data = {
            "email": user_email,
            "password": registered_user["credentials"]["password"]
        }
        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == 401
        
        # Verify user doesn't appear in user list
        list_response = client.get("/auth/users", headers=headers)
        assert list_response.status_code == 200
        users = list_response.json()["users"]
        user_ids = [u["id"] for u in users]
        assert user_id not in user_ids


@pytest.mark.rbac
@pytest.mark.integration
@pytest.mark.asyncio
class TestRoleBasedAccess:
    """Test role-based access patterns"""
    
    def test_role_matrix_endpoints(self, client, admin_user, manager_user, washer_user, authenticated_user):
        """Test matrix: {anonymous, user, manager, admin} × {endpoint} → {200/401/403} attendu."""
        
        # Define test endpoints and expected access
        test_cases = [
            # (endpoint, method, data, {role: expected_status})
            ("/auth/users", "GET", None, {
                "anonymous": 401,
                "client": 403,
                "washer": 403,
                "manager": 200,
                "admin": 200
            }),
            ("/auth/features", "GET", None, {
                "anonymous": 200,  # Usually public
                "client": 200,
                "washer": 200,
                "manager": 200,
                "admin": 200
            }),
        ]
        
        users = {
            "anonymous": None,
            "client": authenticated_user,
            "washer": washer_user,
            "manager": manager_user,
            "admin": admin_user
        }
        
        for endpoint, method, data, expected_statuses in test_cases:
            for role, expected_status in expected_statuses.items():
                user = users[role]
                headers = user["headers"] if user else None
                
                if method == "GET":
                    response = client.get(endpoint, headers=headers)
                elif method == "POST":
                    response = client.post(endpoint, json=data, headers=headers)
                else:
                    continue
                
                assert response.status_code == expected_status, \
                    f"Role {role} accessing {method} {endpoint} should return {expected_status}, got {response.status_code}"

    def test_role_escalation_prevention(self, client, manager_user, authenticated_user, api_helper):
        """Assert invariants: un user non-admin ne voit jamais role d'autrui, ni ne peut l'éditer."""
        
        # Manager trying to escalate to admin
        headers = manager_user["headers"]
        user_id = authenticated_user["user_data"]["id"]
        
        # Try to escalate user to admin
        role_data = {"role": "admin"}
        response = client.put(f"/auth/users/{user_id}/role", json=role_data, headers=headers)
        
        # Depending on business rules, might be forbidden or restricted
        # At minimum, shouldn't allow escalation above manager's level
        if response.status_code == 200:
            # If allowed, verify the role change is appropriate
            response_data = response.json()
            # Manager shouldn't be able to create admins
            assert response_data["role"] != "admin"

    def test_data_visibility_by_role(self, client, admin_user, manager_user, authenticated_user):
        """Test that different roles see appropriate data"""
        
        # Admin should see all user data
        admin_response = client.get("/auth/users", headers=admin_user["headers"])
        assert admin_response.status_code == 200
        admin_data = admin_response.json()
        
        # Manager should see user data (depending on business rules)
        manager_response = client.get("/auth/users", headers=manager_user["headers"])
        assert manager_response.status_code == 200
        manager_data = manager_response.json()
        
        # Regular user should not see user list
        client_response = client.get("/auth/users", headers=authenticated_user["headers"])
        assert client_response.status_code == 403
        
        # Verify admin sees at least as much as manager
        assert len(admin_data["users"]) >= len(manager_data["users"])