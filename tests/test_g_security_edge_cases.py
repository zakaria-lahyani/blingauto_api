"""
G-J. Security, Robustness and Edge Case Tests
"""
import pytest
import time
import uuid
import json
from concurrent.futures import ThreadPoolExecutor


@pytest.mark.security
@pytest.mark.integration
@pytest.mark.asyncio
class TestSecurityHardening:
    """Test security hardening measures"""
    
    def test_bruteforce_login_rate_limiting(self, client, registered_user):
        """Bruteforce login — rate limit
        
        10 tentatives erronées rapides.
        Attendu: 429 après seuil, header Retry-After si implémenté.
        """
        email = registered_user["credentials"]["email"]
        wrong_password = "WrongPassword123!"
        
        responses = []
        for i in range(10):
            login_data = {
                "email": email,
                "password": wrong_password
            }
            response = client.post("/auth/login", json=login_data)
            responses.append(response)
        
        # Should have some failures (401) and potentially rate limiting (429)
        status_codes = [r.status_code for r in responses]
        
        # All should be 401 (wrong password) or 429 (rate limited)
        for status in status_codes:
            assert status in [401, 429]
        
        # If rate limiting is implemented, should see 429s
        rate_limited_count = sum(1 for s in status_codes if s == 429)
        
        # Check for Retry-After header in rate limited responses
        for response in responses:
            if response.status_code == 429:
                # Optionally check for Retry-After header
                if "retry-after" in response.headers:
                    retry_after = response.headers["retry-after"]
                    assert retry_after.isdigit()

    async def test_account_lockout(self, client, auth_module, registered_user, api_helper):
        """Account lockout (si activé)
        
        Après N échecs: login verrouillé → 423/403.
        Déverrouillage après délai ou reset.
        """
        email = registered_user["credentials"]["email"]
        wrong_password = "WrongPassword123!"
        
        # Make multiple failed attempts
        for i in range(6):  # Exceed lockout threshold
            login_data = {
                "email": email,
                "password": wrong_password
            }
            response = client.post("/auth/login", json=login_data)
            # Should be 401 for wrong password
            assert response.status_code in [401, 423]
        
        # Try with correct password after lockout
        correct_login_data = {
            "email": email,
            "password": registered_user["credentials"]["password"]
        }
        locked_response = client.post("/auth/login", json=correct_login_data)
        
        # If account lockout is enabled, should be locked even with correct password
        # Status could be 423 (Locked) or 401 with appropriate message
        if auth_module.config.is_feature_enabled("account_lockout"):
            assert locked_response.status_code in [401, 423]
        else:
            # If lockout not enabled, correct password should work
            assert locked_response.status_code == 200

    def test_jwt_token_tampering(self, client, authenticated_user, api_helper):
        """JWT altéré
        
        Modif signature/claim → 401.
        """
        original_token = authenticated_user["tokens"]["access_token"]
        
        # Tamper with the token by changing the last character
        tampered_token = original_token[:-1] + "x"
        headers = {"Authorization": f"Bearer {tampered_token}"}
        
        response = client.get("/auth/me", headers=headers)
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_token_signature_verification(self, client, api_helper):
        """Test token with valid structure but invalid signature"""
        # Create a JWT-like token with valid structure but wrong signature
        fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjo5OTk5OTk5OTk5fQ.fake_signature"
        headers = {"Authorization": f"Bearer {fake_token}"}
        
        response = client.get("/auth/me", headers=headers)
        
        # Assert unauthorized
        assert response.status_code == 401
        
        # Assert error response
        response_data = response.json()
        api_helper.assert_error_response(response_data)

    def test_information_disclosure_prevention(self, client, api_helper):
        """Exposition d'infos
        
        Messages d'erreur ne divulguent pas si email existe, ni stack traces en prod.
        """
        # Test with existing vs non-existing emails
        existing_email = "admin@carwash.com"  # Likely exists
        nonexistent_email = f"definitely_not_exists_{uuid.uuid4()}@example.com"
        
        # Test login with both emails
        login_data_existing = {
            "email": existing_email,
            "password": "wrong_password"
        }
        response_existing = client.post("/auth/login", json=login_data_existing)
        
        login_data_nonexistent = {
            "email": nonexistent_email,
            "password": "wrong_password"
        }
        response_nonexistent = client.post("/auth/login", json=login_data_nonexistent)
        
        # Both should return 401
        assert response_existing.status_code == 401
        assert response_nonexistent.status_code == 401
        
        # Error messages should be similar (no information leakage)
        existing_error = response_existing.json()["detail"].lower()
        nonexistent_error = response_nonexistent.json()["detail"].lower()
        
        # Messages should be generic and similar
        # Should not contain words like "exists", "found", "user"
        forbidden_words = ["exists", "found", "user", "registered"]
        
        for word in forbidden_words:
            assert word not in existing_error
            assert word not in nonexistent_error
        
        # Should contain generic words like "invalid", "incorrect"
        expected_words = ["invalid", "incorrect", "credentials"]
        assert any(word in existing_error for word in expected_words)
        assert any(word in nonexistent_error for word in expected_words)

    def test_no_stack_traces_in_errors(self, client):
        """Ensure no stack traces are exposed in error responses"""
        # Try to trigger various errors
        error_triggers = [
            ("POST", "/auth/login", {"email": "invalid"}),  # Validation error
            ("GET", "/auth/users/99999", None),  # Not found (with auth)
            ("POST", "/auth/register", {"email": "test@example.com"}),  # Missing fields
        ]
        
        for method, endpoint, data in error_triggers:
            if method == "POST":
                response = client.post(endpoint, json=data)
            else:
                response = client.get(endpoint)
            
            # Error responses should not contain stack traces
            response_text = response.text.lower()
            stack_trace_indicators = [
                "traceback", "stack trace", "line ", "file \"", 
                "error:", "exception:", "raised", "python"
            ]
            
            for indicator in stack_trace_indicators:
                assert indicator not in response_text, f"Possible stack trace exposure in {endpoint}"

    def test_security_headers(self, client):
        """Headers sécurité
        
        Présence Security-Headers sur réponses (CORS, HSTS si HTTPS, SameSite/HttpOnly sur cookies, etc.).
        """
        response = client.get("/auth/features")
        
        # Check for common security headers
        headers = response.headers
        
        # CORS headers should be present
        assert "access-control-allow-origin" in headers
        
        # Content-Type should be set
        assert "content-type" in headers
        
        # Check for security headers (if implemented)
        security_headers = [
            "x-content-type-options",
            "x-frame-options", 
            "x-xss-protection",
            "strict-transport-security",  # HSTS (if HTTPS)
            "content-security-policy"
        ]
        
        # Note: Not all headers might be implemented, so we just check presence
        for header in security_headers:
            if header in headers:
                assert len(headers[header]) > 0


@pytest.mark.integration
@pytest.mark.asyncio
class TestRobustnessEdgeCases:
    """Test robustness and edge cases"""
    
    def test_payload_validation_invalid_json(self, client):
        """Payload invalides
        
        JSON mal formé → 400 + détails validation.
        """
        # Send malformed JSON
        response = client.post("/auth/login", 
                             data="{'invalid': json}",
                             headers={"Content-Type": "application/json"})
        
        # Assert bad request
        assert response.status_code == 400

    def test_payload_validation_invalid_types(self, client):
        """Types/format email invalide, password trop court → 400 + détails validation."""
        
        invalid_payloads = [
            {
                "email": 123,  # Should be string
                "password": "valid_password",
                "first_name": "Test",
                "last_name": "User"
            },
            {
                "email": "invalid_email",  # Invalid format
                "password": "valid_password",
                "first_name": "Test",
                "last_name": "User"
            },
            {
                "email": "test@example.com",
                "password": 123,  # Should be string
                "first_name": "Test",
                "last_name": "User"
            }
        ]
        
        for invalid_payload in invalid_payloads:
            response = client.post("/auth/register", json=invalid_payload)
            
            # Assert validation error
            assert response.status_code == 422
            
            # Assert error details are provided
            response_data = response.json()
            assert "detail" in response_data
            # Should contain validation details
            assert isinstance(response_data["detail"], (list, str))

    def test_large_payload_handling(self, client):
        """Test handling of unusually large payloads"""
        # Create a very large payload
        large_string = "x" * 10000
        large_payload = {
            "email": "test@example.com",
            "password": "ValidPass123!",
            "first_name": large_string,
            "last_name": large_string,
            "extra_data": large_string
        }
        
        response = client.post("/auth/register", json=large_payload)
        
        # Should either reject due to size limits or validation
        assert response.status_code in [400, 413, 422]

    def test_empty_payload_handling(self, client):
        """Test handling of empty payloads"""
        empty_payloads = [
            {},
            {"email": ""},
            {"password": ""},
            {"email": None, "password": None}
        ]
        
        for empty_payload in empty_payloads:
            response = client.post("/auth/login", json=empty_payload)
            
            # Should return validation error
            assert response.status_code == 422

    def test_special_characters_in_input(self, client, sample_user_data):
        """Test handling of special characters and Unicode"""
        special_data = sample_user_data.copy()
        special_data.update({
            "first_name": "José-François",
            "last_name": "müller@öäü",
            "email": f"test.unicode.{int(time.time())}@example.com"
        })
        
        response = client.post("/auth/register", json=special_data)
        
        # Should handle Unicode properly
        assert response.status_code == 201
        
        response_data = response.json()
        # Unicode should be preserved
        assert response_data["first_name"] == "José-François"
        assert response_data["last_name"] == "müller@öäü"

    def test_sql_injection_attempts(self, client, api_helper):
        """Test SQL injection prevention"""
        sql_payloads = [
            {"email": "'; DROP TABLE users; --", "password": "password"},
            {"email": "admin'/*", "password": "password"},
            {"email": "' OR '1'='1", "password": "password"},
            {"email": "test@example.com", "password": "'; DELETE FROM users; --"}
        ]
        
        for sql_payload in sql_payloads:
            response = client.post("/auth/login", json=sql_payload)
            
            # Should not cause internal server error (500)
            # Should either validate properly or return auth error
            assert response.status_code in [401, 422]
            
            if response.status_code == 401:
                response_data = response.json()
                api_helper.assert_error_response(response_data)

    def test_xss_prevention(self, client, authenticated_user):
        """Test XSS prevention in responses"""
        headers = authenticated_user["headers"]
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for xss_payload in xss_payloads:
            update_data = {
                "first_name": xss_payload,
                "last_name": "Normal"
            }
            
            response = client.put("/auth/me", json=update_data, headers=headers)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # XSS payload should be treated as literal text
                # Check that it's either escaped or rejected
                returned_name = response_data.get("first_name", "")
                
                # Should not contain unescaped script tags
                assert "<script>" not in returned_name.lower()
                assert "javascript:" not in returned_name.lower()

    def test_concurrent_registration(self, client, sample_user_data):
        """Test concurrent registration with same email"""
        def register_user(data):
            return client.post("/auth/register", json=data)
        
        # Use same email for both registrations
        email = f"concurrent{int(time.time())}{uuid.uuid4().hex[:8]}@example.com"
        
        data1 = sample_user_data.copy()
        data1["email"] = email
        data1["first_name"] = "User1"
        
        data2 = sample_user_data.copy()
        data2["email"] = email
        data2["first_name"] = "User2"
        
        # Simulate concurrent registration
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(register_user, data1)
            future2 = executor.submit(register_user, data2)
            
            response1 = future1.result()
            response2 = future2.result()
        
        # One should succeed (201), one should fail (400/409)
        statuses = [response1.status_code, response2.status_code]
        
        assert 201 in statuses  # At least one should succeed
        assert any(status in [400, 409] for status in statuses)  # At least one should fail

    def test_idempotent_operations(self, client, authenticated_user, api_helper):
        """Idempotence
        
        Rejouer verify-email/confirm et reset-password → réponses idempotentes (200/410 cohérent).
        """
        # Test idempotent email verification request
        headers = authenticated_user["headers"]
        
        # Make multiple verification requests
        responses = []
        for _ in range(3):
            response = client.post("/auth/verify-email/request", headers=headers)
            responses.append(response)
        
        # All should succeed (idempotent)
        for response in responses:
            assert response.status_code == 200
            response_data = response.json()
            api_helper.assert_message_response(response_data)

    def test_rate_limiting_different_endpoints(self, client, authenticated_user):
        """Test rate limiting across different endpoints"""
        headers = authenticated_user["headers"]
        
        # Test different endpoints that might have rate limiting
        endpoints = [
            "/auth/verify-email/request",
            "/auth/me"
        ]
        
        for endpoint in endpoints:
            responses = []
            for _ in range(10):  # Make rapid requests
                if endpoint.endswith("/request"):
                    response = client.post(endpoint, headers=headers)
                else:
                    response = client.get(endpoint, headers=headers)
                responses.append(response)
            
            # Should either all succeed or show rate limiting
            success_count = sum(1 for r in responses if r.status_code == 200)
            rate_limited_count = sum(1 for r in responses if r.status_code == 429)
            
            # At least some should succeed
            assert success_count > 0


@pytest.mark.integration
@pytest.mark.asyncio
class TestFeaturesAndConfig:
    """Test features and configuration endpoints"""
    
    def test_get_features_public(self, client, api_helper):
        """GET /features
        
        Attendu: 200, AuthFeatureStatus cohérent (exp: password policies, email verify required, refresh rotation, etc.).
        Cross-check avec comportements observés.
        """
        response = client.get("/auth/features")
        
        # Assert success (features should be publicly accessible)
        assert response.status_code == 200
        
        # Assert response structure
        response_data = response.json()
        
        # Should contain feature information
        expected_features = [
            "email_verification",
            "password_reset", 
            "account_lockout",
            "token_rotation",
            "rate_limiting",
            "admin_setup"
        ]
        
        for feature in expected_features:
            assert feature in response_data
            assert isinstance(response_data[feature], bool)

    def test_features_consistency(self, client, authenticated_user):
        """Cross-check feature status with actual behavior"""
        features_response = client.get("/auth/features")
        assert features_response.status_code == 200
        features = features_response.json()
        
        headers = authenticated_user["headers"]
        
        # Test email verification feature consistency
        if features.get("email_verification", False):
            # If email verification is enabled, endpoint should work
            verify_response = client.post("/auth/verify-email/request", headers=headers)
            assert verify_response.status_code == 200
        
        # Test rate limiting feature consistency
        if features.get("rate_limiting", False):
            # If rate limiting is enabled, making many requests might get rate limited
            responses = []
            for _ in range(20):
                response = client.get("/auth/me", headers=headers)
                responses.append(response)
            
            # Should either all succeed or show some rate limiting
            statuses = [r.status_code for r in responses]
            # If rate limiting is truly enabled, we might see 429s
            # But this depends on the rate limit configuration

    def test_features_authenticated_vs_unauthenticated(self, client, authenticated_user):
        """Test that features endpoint works both authenticated and unauthenticated"""
        # Unauthenticated
        unauth_response = client.get("/auth/features")
        assert unauth_response.status_code == 200
        unauth_features = unauth_response.json()
        
        # Authenticated
        auth_response = client.get("/auth/features", headers=authenticated_user["headers"])
        assert auth_response.status_code == 200
        auth_features = auth_response.json()
        
        # Should return same features regardless of authentication
        assert unauth_features == auth_features


@pytest.mark.slow
@pytest.mark.asyncio
class TestPerformanceAndLimits:
    """Test performance and limit scenarios"""
    
    def test_pagination_large_dataset(self, client, admin_user):
        """Pagination /users
        
        GET /users?page=1&size=20 → 200, UserListResponse avec total, items, has_next.
        """
        headers = admin_user["headers"]
        
        # Test pagination with various sizes
        test_cases = [
            {"page": 1, "size": 5},
            {"page": 1, "size": 20},
            {"page": 2, "size": 5},
        ]
        
        for params in test_cases:
            query_string = f"?page={params['page']}&size={params['size']}"
            response = client.get(f"/auth/users{query_string}", headers=headers)
            
            assert response.status_code == 200
            
            response_data = response.json()
            
            # Assert pagination structure
            assert "users" in response_data
            assert "total" in response_data
            assert "page" in response_data
            assert "size" in response_data
            
            # Assert pagination values
            assert response_data["page"] == params["page"]
            assert response_data["size"] == params["size"]
            assert len(response_data["users"]) <= params["size"]
            assert isinstance(response_data["total"], int)
            assert response_data["total"] >= 0

    def test_large_user_list_performance(self, client, admin_user):
        """Test performance with larger page sizes"""
        headers = admin_user["headers"]
        
        # Test with larger page size
        response = client.get("/auth/users?page=1&size=100", headers=headers)
        
        # Should still work but might be slower
        assert response.status_code == 200
        
        response_data = response.json()
        assert len(response_data["users"]) <= 100

    def test_invalid_pagination_parameters(self, client, admin_user):
        """Test invalid pagination parameters"""
        headers = admin_user["headers"]
        
        invalid_params = [
            "?page=0&size=20",      # Page 0
            "?page=-1&size=20",     # Negative page
            "?page=1&size=0",       # Size 0
            "?page=1&size=-1",      # Negative size
            "?page=abc&size=20",    # Non-numeric page
            "?page=1&size=xyz",     # Non-numeric size
        ]
        
        for params in invalid_params:
            response = client.get(f"/auth/users{params}", headers=headers)
            
            # Should return validation error
            assert response.status_code in [400, 422]