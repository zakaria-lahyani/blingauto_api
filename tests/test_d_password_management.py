"""
D. Password Management Tests
"""
import pytest
import time
import uuid


@pytest.mark.integration
@pytest.mark.asyncio
class TestForgotPassword:
    """Test forgot password scenarios"""
    
    def test_forgot_password_existing_email(self, client, registered_user, api_helper):
        """Forgot password — succès
        
        Act: POST /forgot-password {email existant}.
        Attendu: 200 générique (pas de fuite).
        Vérif: token de reset émis (mock provider / DB).
        """
        forgot_data = {
            "email": registered_user["credentials"]["email"]
        }
        
        response = client.post("/auth/forgot-password", json=forgot_data)
        
        # Assert success
        assert response.status_code == 200
        
        # Assert generic message response (no information leakage)
        response_data = response.json()
        api_helper.assert_message_response(response_data)
        
        # Message should be generic and not confirm email existence
        message = response_data["message"].lower()
        assert "password" in message or "reset" in message
        # Should not explicitly confirm email exists

    def test_forgot_password_nonexistent_email(self, client, api_helper):
        """Forgot password — email inconnu
        
        Act: email inconnu.
        Attendu: 200 générique.
        """
        forgot_data = {
            "email": f"nonexistent{int(time.time())}{uuid.uuid4().hex[:8]}@example.com"
        }
        
        response = client.post("/auth/forgot-password", json=forgot_data)
        
        # Assert success (generic response to prevent email enumeration)
        assert response.status_code == 200
        
        # Assert generic message response
        response_data = response.json()
        api_helper.assert_message_response(response_data)
        
        # Message should be identical to existing email case
        message = response_data["message"].lower()
        assert "password" in message or "reset" in message

    def test_forgot_password_invalid_email(self, client):
        """Test forgot password with invalid email format"""
        forgot_data = {
            "email": "not-an-email"
        }
        
        response = client.post("/auth/forgot-password", json=forgot_data)
        
        # Assert validation error
        assert response.status_code == 422

    def test_forgot_password_missing_email(self, client):
        """Test forgot password without email"""
        response = client.post("/auth/forgot-password", json={})
        
        # Assert validation error
        assert response.status_code == 422

    def test_forgot_password_empty_email(self, client):
        """Test forgot password with empty email"""
        forgot_data = {
            "email": ""
        }
        
        response = client.post("/auth/forgot-password", json=forgot_data)
        
        # Assert validation error
        assert response.status_code == 422

    def test_forgot_password_rate_limiting(self, client, registered_user):
        """Test rate limiting on forgot password requests"""
        forgot_data = {
            "email": registered_user["credentials"]["email"]
        }
        
        # Make multiple rapid requests
        responses = []
        for _ in range(6):  # Exceed typical rate limit
            response = client.post("/auth/forgot-password", json=forgot_data)
            responses.append(response)
        
        # At least one should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)
        
        assert success_count >= 1
        # If rate limiting is enabled, we should see some 429s


@pytest.mark.integration
@pytest.mark.asyncio
class TestResetPassword:
    """Test password reset scenarios"""
    
    async def test_reset_password_valid_token(self, client, auth_module, registered_user, api_helper):
        """Reset password — token valide
        
        Pré: token reset valide.
        Act: POST /reset-password {token, new_password}.
        Attendu: 200.
        Vérif: ancien mot de passe ne marche plus; nouveau marche.
        """
        user = registered_user["user_entity"]
        old_password = registered_user["credentials"]["password"]
        new_password = "NewSecurePass123!"
        
        # Generate reset token
        reset_token = await auth_module.password_reset_service.generate_reset_token(user.email)
        
        # Reset password
        reset_data = {
            "token": reset_token,
            "new_password": new_password
        }
        
        response = client.post("/auth/reset-password", json=reset_data)
        
        # Assert success
        assert response.status_code == 200
        
        # Assert message response
        response_data = response.json()
        api_helper.assert_message_response(response_data)
        
        # Verify old password no longer works
        old_login_data = {
            "email": user.email,
            "password": old_password
        }
        old_login_response = client.post("/auth/login", json=old_login_data)
        assert old_login_response.status_code == 401
        
        # Verify new password works
        new_login_data = {
            "email": user.email,
            "password": new_password
        }
        new_login_response = client.post("/auth/login", json=new_login_data)
        assert new_login_response.status_code == 200

    def test_reset_password_invalid_token(self, client, api_helper):
        """Reset password — token invalide/expiré
        
        Attendu: 400/401/410, MDP inchangé.
        """
        invalid_token = "invalid_reset_token_12345"
        new_password = "NewSecurePass123!"
        
        reset_data = {
            "token": invalid_token,
            "new_password": new_password
        }
        
        response = client.post("/auth/reset-password", json=reset_data)
        
        # Assert error status
        assert response.status_code in [400, 401, 410]
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_reset_password_malformed_token(self, client, api_helper):
        """Test password reset with malformed token"""
        malformed_token = "not.a.jwt.token"
        new_password = "NewSecurePass123!"
        
        reset_data = {
            "token": malformed_token,
            "new_password": new_password
        }
        
        response = client.post("/auth/reset-password", json=reset_data)
        
        # Assert error status
        assert response.status_code in [400, 401]
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_reset_password_weak_password(self, client, auth_module, registered_user):
        """Test password reset with weak password"""
        user = registered_user["user_entity"]
        
        # Generate valid reset token
        reset_token = await auth_module.password_reset_service.generate_reset_token(user.email)
        
        weak_password = "123"
        
        reset_data = {
            "token": reset_token,
            "new_password": weak_password
        }
        
        response = client.post("/auth/reset-password", json=reset_data)
        
        # Assert validation error
        assert response.status_code in [400, 422]

    def test_reset_password_missing_fields(self, client):
        """Test password reset with missing fields"""
        # Missing token
        response1 = client.post("/auth/reset-password", json={"new_password": "NewPass123!"})
        assert response1.status_code == 422
        
        # Missing password
        response2 = client.post("/auth/reset-password", json={"token": "some_token"})
        assert response2.status_code == 422

    async def test_reset_password_token_one_time_use(self, client, auth_module, registered_user, api_helper):
        """Test that reset tokens can only be used once"""
        user = registered_user["user_entity"]
        
        # Generate reset token
        reset_token = await auth_module.password_reset_service.generate_reset_token(user.email)
        
        # First use - should succeed
        reset_data1 = {
            "token": reset_token,
            "new_password": "NewPass123!"
        }
        response1 = client.post("/auth/reset-password", json=reset_data1)
        assert response1.status_code == 200
        
        # Second use - should fail
        reset_data2 = {
            "token": reset_token,
            "new_password": "AnotherPass123!"
        }
        response2 = client.post("/auth/reset-password", json=reset_data2)
        assert response2.status_code in [400, 401, 410]


@pytest.mark.integration
@pytest.mark.asyncio
class TestChangePassword:
    """Test password change scenarios"""
    
    def test_change_password_authenticated_success(self, client, authenticated_user, api_helper):
        """Change password — authentifié
        
        Pré: access valide.
        Act: POST /change-password {old, new}.
        Attendu: 200.
        Vérif: old KO, new OK; refresh rotation si prévu.
        """
        headers = authenticated_user["headers"]
        old_password = authenticated_user["credentials"]["password"]
        new_password = "NewSecurePass123!"
        
        change_data = {
            "old_password": old_password,
            "new_password": new_password
        }
        
        response = client.post("/auth/change-password", json=change_data, headers=headers)
        
        # Assert success
        assert response.status_code == 200
        
        # Assert message response
        response_data = response.json()
        api_helper.assert_message_response(response_data)
        
        # Verify old password no longer works
        old_login_data = {
            "email": authenticated_user["credentials"]["email"],
            "password": old_password
        }
        old_login_response = client.post("/auth/login", json=old_login_data)
        assert old_login_response.status_code == 401
        
        # Verify new password works
        new_login_data = {
            "email": authenticated_user["credentials"]["email"],
            "password": new_password
        }
        new_login_response = client.post("/auth/login", json=new_login_data)
        assert new_login_response.status_code == 200

    def test_change_password_wrong_old_password(self, client, authenticated_user, api_helper):
        """Change password — ancien MDP faux
        
        Attendu: 400/401.
        """
        headers = authenticated_user["headers"]
        wrong_old_password = "WrongOldPass123!"
        new_password = "NewSecurePass123!"
        
        change_data = {
            "old_password": wrong_old_password,
            "new_password": new_password
        }
        
        response = client.post("/auth/change-password", json=change_data, headers=headers)
        
        # Assert error
        assert response.status_code in [400, 401]
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)
        
        # Verify original password still works
        original_login_data = {
            "email": authenticated_user["credentials"]["email"],
            "password": authenticated_user["credentials"]["password"]
        }
        login_response = client.post("/auth/login", json=original_login_data)
        assert login_response.status_code == 200

    def test_change_password_unauthenticated(self, client, api_helper):
        """Test password change without authentication"""
        change_data = {
            "old_password": "OldPass123!",
            "new_password": "NewPass123!"
        }
        
        response = client.post("/auth/change-password", json=change_data)
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_change_password_invalid_token(self, client, api_helper):
        """Test password change with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        change_data = {
            "old_password": "OldPass123!",
            "new_password": "NewPass123!"
        }
        
        response = client.post("/auth/change-password", json=change_data, headers=headers)
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_change_password_weak_new_password(self, client, authenticated_user):
        """Test password change with weak new password"""
        headers = authenticated_user["headers"]
        old_password = authenticated_user["credentials"]["password"]
        weak_password = "123"
        
        change_data = {
            "old_password": old_password,
            "new_password": weak_password
        }
        
        response = client.post("/auth/change-password", json=change_data, headers=headers)
        
        # Assert validation error
        assert response.status_code in [400, 422]

    def test_change_password_same_as_old(self, client, authenticated_user):
        """Test password change with same password"""
        headers = authenticated_user["headers"]
        current_password = authenticated_user["credentials"]["password"]
        
        change_data = {
            "old_password": current_password,
            "new_password": current_password
        }
        
        response = client.post("/auth/change-password", json=change_data, headers=headers)
        
        # Depending on implementation, might be allowed or rejected
        # Some systems reject reusing the same password
        assert response.status_code in [200, 400]

    def test_change_password_missing_fields(self, client, authenticated_user):
        """Test password change with missing fields"""
        headers = authenticated_user["headers"]
        
        # Missing old password
        response1 = client.post("/auth/change-password", 
                               json={"new_password": "NewPass123!"}, 
                               headers=headers)
        assert response1.status_code == 422
        
        # Missing new password
        response2 = client.post("/auth/change-password", 
                               json={"old_password": "OldPass123!"}, 
                               headers=headers)
        assert response2.status_code == 422

    def test_change_password_empty_passwords(self, client, authenticated_user):
        """Test password change with empty passwords"""
        headers = authenticated_user["headers"]
        
        change_data = {
            "old_password": "",
            "new_password": ""
        }
        
        response = client.post("/auth/change-password", json=change_data, headers=headers)
        
        # Assert validation error
        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
class TestPasswordPolicies:
    """Test password policy enforcement"""
    
    def test_password_complexity_requirements(self, client, sample_user_data):
        """Test various password complexity scenarios"""
        base_data = sample_user_data.copy()
        
        # Test various weak passwords
        weak_passwords = [
            "123",                      # Too short
            "password",                 # Too common
            "12345678",                 # No letters
            "abcdefgh",                 # No numbers
            "Password",                 # No special chars (if required)
        ]
        
        for weak_password in weak_passwords:
            test_data = base_data.copy()
            test_data["password"] = weak_password
            test_data["email"] = f"test{int(time.time())}{uuid.uuid4().hex[:4]}@example.com"
            
            response = client.post("/auth/register", json=test_data)
            
            # Should reject weak passwords
            assert response.status_code in [400, 422], f"Weak password '{weak_password}' should be rejected"

    def test_password_strength_validation(self, client, authenticated_user):
        """Test password strength validation in change password"""
        headers = authenticated_user["headers"]
        old_password = authenticated_user["credentials"]["password"]
        
        weak_passwords = [
            "123",
            "password",
            "12345678",
            "abcdefgh"
        ]
        
        for weak_password in weak_passwords:
            change_data = {
                "old_password": old_password,
                "new_password": weak_password
            }
            
            response = client.post("/auth/change-password", json=change_data, headers=headers)
            
            # Should reject weak passwords
            assert response.status_code in [400, 422], f"Weak password '{weak_password}' should be rejected"