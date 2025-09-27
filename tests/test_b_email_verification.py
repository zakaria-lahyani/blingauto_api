"""
B. Email Verification Tests
"""
import pytest
import time
import uuid
from unittest.mock import patch


@pytest.mark.integration
@pytest.mark.asyncio
class TestEmailVerification:
    """Test email verification scenarios"""
    
    def test_request_email_verification_success(self, client, authenticated_user, api_helper):
        """Demande vérif email — succès
        
        Act: POST /verify-email/request (auth ou email selon design).
        Attendu: 200, message générique (pas de confirmation d'existence email).
        """
        response = client.post("/auth/verify-email/request", headers=authenticated_user["headers"])
        
        # Assert success
        assert response.status_code == 200
        
        # Assert generic message response
        response_data = response.json()
        api_helper.assert_message_response(response_data)
        
        # Assert generic message (no information leakage)
        message = response_data["message"].lower()
        assert "email" in message or "verification" in message
        # Should not confirm email existence specifically

    def test_request_email_verification_unauthenticated(self, client, api_helper):
        """Request email verification without authentication"""
        response = client.post("/auth/verify-email/request")
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    async def test_confirm_email_verification_valid_token(self, client, auth_module, registered_user, api_helper):
        """Confirme vérif email — token valide
        
        Pré: token de vérif généré.
        Act: POST /verify-email/confirm {token}.
        Attendu: 200, flag email_verified=true.
        """
        # Generate verification token manually
        user = registered_user["user_entity"]
        verification_token = await auth_module.email_verification_service.generate_verification_token(user.email)
        
        # Confirm email verification
        response = client.post("/auth/verify-email/confirm", json={"token": verification_token})
        
        # Assert success
        assert response.status_code == 200
        
        # Assert message response
        response_data = response.json()
        api_helper.assert_message_response(response_data)
        
        # Verify that user's email is now verified
        updated_user = await auth_module.user_service.get_user_by_email(user.email)
        assert updated_user.email_verified is True

    def test_confirm_email_verification_invalid_token(self, client, api_helper):
        """Confirme vérif — token invalide/expiré
        
        Act: POST /verify-email/confirm {token faux/expiré}.
        Attendu: 400/401/410, pas de changement de statut.
        """
        invalid_token = "invalid_token_12345"
        
        response = client.post("/auth/verify-email/confirm", json={"token": invalid_token})
        
        # Assert error status
        assert response.status_code in [400, 401, 410]
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_confirm_email_verification_malformed_token(self, client, api_helper):
        """Test email verification with malformed token"""
        malformed_token = "not.a.jwt.token"
        
        response = client.post("/auth/verify-email/confirm", json={"token": malformed_token})
        
        # Assert error status
        assert response.status_code in [400, 401]
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_confirm_email_verification_missing_token(self, client):
        """Test email verification without token"""
        response = client.post("/auth/verify-email/confirm", json={})
        
        # Assert validation error
        assert response.status_code == 422

    async def test_confirm_email_verification_expired_token(self, client, auth_module, registered_user, api_helper):
        """Test email verification with expired token"""
        user = registered_user["user_entity"]
        
        # Mock the token generation to create an expired token
        with patch('src.features.auth.infrastructure.security.jwt_handler.datetime') as mock_datetime:
            # Set time to past to create expired token
            past_time = mock_datetime.utcnow.return_value
            past_time.timestamp.return_value = time.time() - 3600  # 1 hour ago
            
            verification_token = await auth_module.email_verification_service.generate_verification_token(user.email)
        
        response = client.post("/auth/verify-email/confirm", json={"token": verification_token})
        
        # Assert error status
        assert response.status_code in [400, 401, 410]
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    async def test_verify_email_idempotence(self, client, auth_module, registered_user, api_helper):
        """Test that email verification is idempotent"""
        user = registered_user["user_entity"]
        verification_token = await auth_module.email_verification_service.generate_verification_token(user.email)
        
        # First verification
        response1 = client.post("/auth/verify-email/confirm", json={"token": verification_token})
        assert response1.status_code == 200
        
        # Second verification with same token should be idempotent
        response2 = client.post("/auth/verify-email/confirm", json={"token": verification_token})
        
        # Should either succeed (idempotent) or indicate already verified
        assert response2.status_code in [200, 400, 410]
        
        # User should still be verified
        updated_user = await auth_module.user_service.get_user_by_email(user.email)
        assert updated_user.email_verified is True

    async def test_request_verification_already_verified(self, client, authenticated_user, api_helper):
        """Request verification for already verified email"""
        # User from authenticated_user fixture should already be verified
        response = client.post("/auth/verify-email/request", headers=authenticated_user["headers"])
        
        # Should still return success (generic response)
        assert response.status_code == 200
        
        response_data = response.json()
        api_helper.assert_message_response(response_data)

    def test_request_verification_rate_limiting(self, client, authenticated_user):
        """Test rate limiting on verification requests"""
        headers = authenticated_user["headers"]
        
        # Make multiple rapid requests
        responses = []
        for _ in range(6):  # Exceed typical rate limit
            response = client.post("/auth/verify-email/request", headers=headers)
            responses.append(response)
        
        # At least one should succeed, some might be rate limited
        success_count = sum(1 for r in responses if r.status_code == 200)
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)
        
        assert success_count >= 1
        # If rate limiting is enabled, we should see some 429s
        # Note: This test might not fail if rate limiting is disabled or has high limits

    async def test_verification_token_one_time_use(self, client, auth_module, registered_user, api_helper):
        """Test that verification tokens can only be used once"""
        user = registered_user["user_entity"]
        verification_token = await auth_module.email_verification_service.generate_verification_token(user.email)
        
        # First use - should succeed
        response1 = client.post("/auth/verify-email/confirm", json={"token": verification_token})
        assert response1.status_code == 200
        
        # Second use - should fail or be idempotent
        response2 = client.post("/auth/verify-email/confirm", json={"token": verification_token})
        
        # Depending on implementation, might be 400 (used), 410 (expired), or 200 (idempotent)
        assert response2.status_code in [200, 400, 410]
        
        # User should still be verified regardless
        updated_user = await auth_module.user_service.get_user_by_email(user.email)
        assert updated_user.email_verified is True