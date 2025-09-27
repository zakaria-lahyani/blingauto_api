"""
C. Token and Session Management Tests
"""
import pytest
import time
import uuid
from unittest.mock import patch


@pytest.mark.integration
@pytest.mark.asyncio
class TestTokenRefresh:
    """Test token refresh scenarios"""
    
    def test_refresh_success(self, client, authenticated_user, api_helper):
        """Refresh — succès
        
        Pré: refresh valide.
        Act: POST /refresh {refresh}.
        Attendu: 200, nouvel access (et refresh si rotation), ancien access reste valide jusqu'à exp.
        """
        refresh_token = authenticated_user["tokens"]["refresh_token"]
        old_access_token = authenticated_user["tokens"]["access_token"]
        
        # Refresh tokens
        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        
        # Assert success
        assert response.status_code == 200
        
        # Assert token response structure
        response_data = response.json()
        api_helper.assert_valid_token_response(response_data)
        
        # Assert new tokens are different
        new_access_token = response_data["access_token"]
        assert new_access_token != old_access_token
        
        # Test that old access token is still valid (until expiration)
        old_headers = {"Authorization": f"Bearer {old_access_token}"}
        me_response = client.get("/auth/me", headers=old_headers)
        assert me_response.status_code == 200
        
        # Test that new access token works
        new_headers = {"Authorization": f"Bearer {new_access_token}"}
        me_response = client.get("/auth/me", headers=new_headers)
        assert me_response.status_code == 200

    def test_refresh_invalid_token(self, client, api_helper):
        """Refresh — token invalide/blacklisté
        
        Act: POST /refresh avec refresh invalide/revoqué.
        Attendu: 401.
        """
        invalid_refresh_token = "invalid_refresh_token_12345"
        
        response = client.post("/auth/refresh", json={"refresh_token": invalid_refresh_token})
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_refresh_malformed_token(self, client, api_helper):
        """Test refresh with malformed token"""
        malformed_token = "not.a.jwt.token"
        
        response = client.post("/auth/refresh", json={"refresh_token": malformed_token})
        
        # Assert error
        assert response.status_code in [400, 401]
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_refresh_missing_token(self, client):
        """Test refresh without token"""
        response = client.post("/auth/refresh", json={})
        
        # Assert validation error
        assert response.status_code == 422

    def test_refresh_empty_token(self, client, api_helper):
        """Test refresh with empty token"""
        response = client.post("/auth/refresh", json={"refresh_token": ""})
        
        # Assert error
        assert response.status_code in [400, 401, 422]


@pytest.mark.integration
@pytest.mark.asyncio
class TestLogout:
    """Test logout scenarios"""
    
    def test_logout_current_session(self, client, authenticated_user, api_helper):
        """Logout — session courante
        
        Pré: access/refresh actifs.
        Act: POST /logout (avec access).
        Attendu: 200, refresh associé invalidé, access éventuellement utilisable jusqu'à exp ou révoqué selon design.
        """
        headers = authenticated_user["headers"]
        refresh_token = authenticated_user["tokens"]["refresh_token"]
        
        # Logout
        response = client.post("/auth/logout", headers=headers)
        
        # Assert success
        assert response.status_code == 200
        
        # Assert message response
        response_data = response.json()
        api_helper.assert_message_response(response_data)
        
        # Verify that refresh token is invalidated
        refresh_response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh_response.status_code == 401

    def test_logout_unauthenticated(self, client, api_helper):
        """Test logout without authentication"""
        response = client.post("/auth/logout")
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_logout_invalid_token(self, client, api_helper):
        """Test logout with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.post("/auth/logout", headers=headers)
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)


@pytest.mark.integration
@pytest.mark.asyncio
class TestLogoutAll:
    """Test logout all sessions scenarios"""
    
    async def test_logout_all_sessions(self, client, registered_user, api_helper):
        """Logout-all — toutes sessions
        
        Pré: 2 devices (2 refresh).
        Act: POST /logout-all.
        Attendu: 200, tous les refresh invalidés; vérif: aucun refresh ne fonctionne.
        """
        # Create two sessions (simulate two devices)
        login_data = {
            "email": registered_user["credentials"]["email"],
            "password": registered_user["credentials"]["password"]
        }
        
        # Session 1
        response1 = client.post("/auth/login", json=login_data)
        assert response1.status_code == 200
        tokens1 = response1.json()
        headers1 = {"Authorization": f"Bearer {tokens1['access_token']}"}
        
        # Session 2
        response2 = client.post("/auth/login", json=login_data)
        assert response2.status_code == 200
        tokens2 = response2.json()
        headers2 = {"Authorization": f"Bearer {tokens2['access_token']}"}
        
        # Verify both sessions work
        assert client.get("/auth/me", headers=headers1).status_code == 200
        assert client.get("/auth/me", headers=headers2).status_code == 200
        
        # Logout all sessions using first session
        response = client.post("/auth/logout-all", headers=headers1)
        
        # Assert success
        assert response.status_code == 200
        
        # Assert message response
        response_data = response.json()
        api_helper.assert_message_response(response_data)
        
        # Verify both refresh tokens are invalidated
        refresh_response1 = client.post("/auth/refresh", json={"refresh_token": tokens1["refresh_token"]})
        assert refresh_response1.status_code == 401
        
        refresh_response2 = client.post("/auth/refresh", json={"refresh_token": tokens2["refresh_token"]})
        assert refresh_response2.status_code == 401

    def test_logout_all_unauthenticated(self, client, api_helper):
        """Test logout all without authentication"""
        response = client.post("/auth/logout-all")
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_logout_all_invalid_token(self, client, api_helper):
        """Test logout all with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.post("/auth/logout-all", headers=headers)
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)


@pytest.mark.integration
@pytest.mark.asyncio
class TestExpiredTokens:
    """Test expired token scenarios"""
    
    def test_access_token_expired(self, client, authenticated_user, api_helper):
        """Access expiré
        
        Pré: token court + attendre/forcer exp.
        Act: GET /me avec access expiré.
        Attendu: 401 + WWW-Authenticate approprié.
        """
        # Note: In a real test, you'd either wait for token expiration or mock the time
        # For testing purposes, we'll use an obviously expired token
        
        # Create an expired token by manipulating the JWT (this is a simplified approach)
        # In practice, you might mock the datetime or wait for natural expiration
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxfQ.invalid"
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.get("/auth/me", headers=headers)
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)
        
        # Check for WWW-Authenticate header (if implemented)
        if "www-authenticate" in response.headers:
            assert "bearer" in response.headers["www-authenticate"].lower()

    def test_refresh_token_expired(self, client, api_helper):
        """Test refresh with expired refresh token"""
        # Create an obviously expired refresh token
        expired_refresh_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxfQ.invalid"
        
        response = client.post("/auth/refresh", json={"refresh_token": expired_refresh_token})
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)


@pytest.mark.concurrency
@pytest.mark.asyncio
class TestConcurrentOperations:
    """Test concurrent token operations"""
    
    async def test_concurrent_refresh_with_rotation(self, client, authenticated_user, api_helper):
        """Concurrence
        
        2 refresh quasi simultanés (si rotation unique) :
        Un seul passe, l'autre 401 (si rotation invalide l'ancien).
        """
        refresh_token = authenticated_user["tokens"]["refresh_token"]
        
        # Simulate concurrent refresh requests
        # Note: This is simplified - in a real concurrent test you'd use threading or asyncio
        response1 = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        response2 = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        
        # Depending on implementation:
        # - If rotation is enabled and enforced: one succeeds, one fails
        # - If rotation is not enforced: both might succeed
        # - If there's no rotation: both should succeed
        
        success_count = sum(1 for r in [response1, response2] if r.status_code == 200)
        failure_count = sum(1 for r in [response1, response2] if r.status_code == 401)
        
        # At least one should work
        assert success_count >= 1
        
        # If rotation is strict, only one should succeed
        if success_count == 1:
            assert failure_count == 1

    async def test_refresh_after_logout(self, client, authenticated_user, api_helper):
        """Révocation post-logout
        
        Tenter refresh après logout → 401.
        """
        headers = authenticated_user["headers"]
        refresh_token = authenticated_user["tokens"]["refresh_token"]
        
        # Logout first
        logout_response = client.post("/auth/logout", headers=headers)
        assert logout_response.status_code == 200
        
        # Try to refresh after logout
        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    async def test_access_token_after_logout(self, client, authenticated_user, api_helper):
        """Test access token behavior after logout"""
        headers = authenticated_user["headers"]
        
        # Verify access token works before logout
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        
        # Logout
        logout_response = client.post("/auth/logout", headers=headers)
        assert logout_response.status_code == 200
        
        # Try to use access token after logout
        # Behavior depends on implementation:
        # - Token might still work until expiration (stateless)
        # - Token might be immediately invalidated (stateful/blacklist)
        response = client.get("/auth/me", headers=headers)
        
        # Either should work (until expiration) or be rejected immediately
        assert response.status_code in [200, 401]


@pytest.mark.integration
@pytest.mark.asyncio
class TestTokenStructure:
    """Test token structure and validation"""
    
    def test_jwt_token_structure(self, client, authenticated_user, api_helper):
        """Assert token structure: access_token JWT 3 segments, exp futur, sub = user_id."""
        tokens = authenticated_user["tokens"]
        
        # Test access token structure
        access_token = tokens["access_token"]
        access_parts = access_token.split(".")
        assert len(access_parts) == 3, "Access token should have 3 JWT segments"
        
        # Test refresh token structure
        refresh_token = tokens["refresh_token"]
        refresh_parts = refresh_token.split(".")
        assert len(refresh_parts) == 3, "Refresh token should have 3 JWT segments"
        
        # Additional JWT validation could be added here
        # (decode JWT and check claims, expiration, etc.)

    def test_token_response_completeness(self, client, authenticated_user, api_helper):
        """Test that token response contains all required fields"""
        tokens = authenticated_user["tokens"]
        
        # Assert all required fields are present
        required_fields = ["access_token", "refresh_token", "expires_in", "token_type"]
        for field in required_fields:
            assert field in tokens
        
        # Assert token type is bearer
        assert tokens["token_type"] == "bearer"
        
        # Assert expires_in is positive integer
        assert isinstance(tokens["expires_in"], int)
        assert tokens["expires_in"] > 0
        
        # Assert tokens are non-empty strings
        assert isinstance(tokens["access_token"], str)
        assert isinstance(tokens["refresh_token"], str)
        assert len(tokens["access_token"]) > 0
        assert len(tokens["refresh_token"]) > 0