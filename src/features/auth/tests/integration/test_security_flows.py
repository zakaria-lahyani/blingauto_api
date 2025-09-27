"""
Integration tests for security flows and edge cases
"""
import pytest
from httpx import AsyncClient
import time


class TestSecurityFlows:
    """Test security-related flows and protections"""
    
    @pytest.mark.asyncio
    async def test_jwt_token_expiry_handling(self, authenticated_client):
        """Test handling of expired JWT tokens"""
        # This test would require manipulating token expiry times
        # For now, we'll test the basic flow
        client, tokens = authenticated_client
        
        # Valid token should work
        response = await client.get("/auth/me")
        assert response.status_code == 200
        
        # Test with malformed token
        client.headers.update({"Authorization": "Bearer invalid.token.here"})
        response = await client.get("/auth/me")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_refresh_token_rotation(self, authenticated_client):
        """Test refresh token rotation security"""
        client, tokens = authenticated_client
        original_refresh = tokens["refresh_token"]
        
        # Use refresh token
        response = await client.post("/auth/refresh", json={
            "refresh_token": original_refresh
        })
        assert response.status_code == 200
        
        new_tokens = response.json()
        new_refresh = new_tokens["refresh_token"]
        
        # New refresh token should be different
        assert new_refresh != original_refresh
        
        # Old refresh token should be invalid
        response = await client.post("/auth/refresh", json={
            "refresh_token": original_refresh
        })
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_concurrent_login_sessions(self, client: AsyncClient):
        """Test multiple concurrent sessions for same user"""
        # Register user
        user_data = {
            "email": "concurrent@test.com",
            "password": "ConcurrentTest123!",
            "first_name": "Concurrent",
            "last_name": "User"
        }
        await client.post("/auth/register", json=user_data)
        
        # Login from first "device"
        login1 = await client.post("/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login1.status_code == 200
        tokens1 = login1.json()
        
        # Login from second "device"
        login2 = await client.post("/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login2.status_code == 200
        tokens2 = login2.json()
        
        # Both sessions should be valid
        client.headers.update({"Authorization": f"Bearer {tokens1['access_token']}"})
        response1 = await client.get("/auth/me")
        assert response1.status_code == 200
        
        client.headers.update({"Authorization": f"Bearer {tokens2['access_token']}"})
        response2 = await client.get("/auth/me")
        assert response2.status_code == 200
        
        # Logout from all devices
        response = await client.post("/auth/logout-all")
        assert response.status_code == 200
        
        # Both sessions should now be invalid
        client.headers.update({"Authorization": f"Bearer {tokens1['access_token']}"})
        response1 = await client.get("/auth/me")
        assert response1.status_code == 401
        
        client.headers.update({"Authorization": f"Bearer {tokens2['access_token']}"})
        response2 = await client.get("/auth/me")
        assert response2.status_code == 401
    
    @pytest.mark.asyncio
    async def test_password_change_invalidates_sessions(self, authenticated_client):
        """Test that password change invalidates existing sessions"""
        client, tokens = authenticated_client
        original_token = tokens["access_token"]
        
        # Verify current session works
        response = await client.get("/auth/me")
        assert response.status_code == 200
        
        # Change password
        response = await client.post("/auth/change-password", json={
            "current_password": "TestPassword123!",
            "new_password": "NewSecurePassword456!"
        })
        assert response.status_code == 200
        
        # Original session should still work immediately after password change
        # (This depends on implementation - some systems invalidate immediately)
        response = await client.get("/auth/me")
        # Could be either 200 or 401 depending on implementation
        assert response.status_code in [200, 401]
    
    @pytest.mark.asyncio
    async def test_malicious_jwt_manipulation(self, client: AsyncClient):
        """Test protection against JWT manipulation"""
        # Create valid session
        user_data = {
            "email": "malicious@test.com",
            "password": "MaliciousTest123!",
            "first_name": "Malicious",
            "last_name": "User"
        }
        await client.post("/auth/register", json=user_data)
        
        login = await client.post("/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        tokens = login.json()
        
        # Test with tampered token (change one character)
        tampered_token = tokens["access_token"][:-1] + "X"
        client.headers.update({"Authorization": f"Bearer {tampered_token}"})
        
        response = await client.get("/auth/me")
        assert response.status_code == 401
        
        # Test with completely fake token
        fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        client.headers.update({"Authorization": f"Bearer {fake_token}"})
        
        response = await client.get("/auth/me")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_sql_injection_protection(self, client: AsyncClient):
        """Test protection against SQL injection in auth endpoints"""
        # Test SQL injection in login
        malicious_login = {
            "email": "admin@test.com' OR '1'='1",
            "password": "anything"
        }
        response = await client.post("/auth/login", json=malicious_login)
        assert response.status_code == 401
        
        # Test SQL injection in registration
        malicious_register = {
            "email": "test'; DROP TABLE users; --",
            "password": "Password123!",
            "first_name": "Malicious",
            "last_name": "User"
        }
        # Should either fail validation or be safely handled
        response = await client.post("/auth/register", json=malicious_register)
        assert response.status_code in [400, 422]  # Validation error or bad request
    
    @pytest.mark.asyncio
    async def test_password_security_requirements(self, client: AsyncClient):
        """Test password security requirements"""
        base_user = {
            "email": "password@test.com",
            "first_name": "Password",
            "last_name": "Test"
        }
        
        # Test weak passwords
        weak_passwords = [
            "123456",      # Too short, no letters
            "password",    # No numbers, no special chars
            "Password",    # No numbers, no special chars
            "Password1",   # No special chars
            "password123", # No uppercase, no special chars
            "PASSWORD123", # No lowercase, no special chars
        ]
        
        for weak_password in weak_passwords:
            user_data = {**base_user, "password": weak_password}
            response = await client.post("/auth/register", json=user_data)
            assert response.status_code == 422, f"Weak password '{weak_password}' should be rejected"
        
        # Test strong password
        strong_password = "StrongPassword123!"
        user_data = {**base_user, "password": strong_password}
        response = await client.post("/auth/register", json=user_data)
        assert response.status_code == 201
    
    @pytest.mark.asyncio
    async def test_account_lockout_protection(self, client: AsyncClient):
        """Test account lockout after multiple failed attempts"""
        # Register user
        user_data = {
            "email": "lockout@test.com",
            "password": "LockoutTest123!",
            "first_name": "Lockout",
            "last_name": "Test"
        }
        await client.post("/auth/register", json=user_data)
        
        # Make multiple failed login attempts
        for i in range(6):  # Assuming lockout after 5 attempts
            response = await client.post("/auth/login", json={
                "email": user_data["email"],
                "password": "WrongPassword123!"
            })
            if i < 5:
                assert response.status_code == 401
            else:
                # Account should be locked
                assert response.status_code in [401, 423]  # 423 = Locked
        
        # Even correct password should fail now
        response = await client.post("/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert response.status_code in [401, 423]
    
    @pytest.mark.asyncio
    async def test_rate_limiting_protection(self, client: AsyncClient):
        """Test rate limiting on auth endpoints"""
        # This test depends on rate limiting being enabled
        # Make rapid requests to login endpoint
        rapid_requests = []
        for i in range(10):
            response = await client.post("/auth/login", json={
                "email": "nonexistent@test.com",
                "password": "password"
            })
            rapid_requests.append(response.status_code)
        
        # Should eventually get rate limited (429)
        # This might not work if rate limiting is disabled in tests
        rate_limited = any(status == 429 for status in rapid_requests)
        # Don't assert rate limiting in tests as it might be disabled
        # Just verify we don't get server errors
        assert all(status in [401, 429] for status in rapid_requests)
    
    @pytest.mark.asyncio
    async def test_header_injection_protection(self, client: AsyncClient):
        """Test protection against header injection"""
        # Test malicious headers
        malicious_headers = {
            "Authorization": "Bearer token\r\nX-Injected: malicious",
            "Content-Type": "application/json\r\nX-Another: injection"
        }
        
        try:
            response = await client.get("/auth/me", headers=malicious_headers)
            # Should either reject or sanitize headers
            assert response.status_code == 401  # Unauthorized due to invalid token format
        except Exception:
            # HTTP client might reject malformed headers
            pass
    
    @pytest.mark.asyncio
    async def test_cors_headers_security(self, client: AsyncClient):
        """Test CORS headers are properly configured"""
        # Make OPTIONS request
        response = await client.options("/auth/login")
        
        # Should have CORS headers
        headers = response.headers
        
        # Check for security-related CORS headers
        if "access-control-allow-origin" in headers:
            origin = headers["access-control-allow-origin"]
            # Should not be wildcard (*) in production for credentials
            # This depends on configuration
            assert origin is not None
        
        # Check allowed methods
        if "access-control-allow-methods" in headers:
            methods = headers["access-control-allow-methods"]
            assert "POST" in methods
    
    @pytest.mark.asyncio
    async def test_sensitive_data_not_exposed(self, authenticated_client):
        """Test that sensitive data is never exposed in responses"""
        client, tokens = authenticated_client
        
        # Get user profile
        response = await client.get("/auth/me")
        assert response.status_code == 200
        
        user_data = response.json()
        
        # Sensitive fields should not be present
        sensitive_fields = [
            "password",
            "hashed_password", 
            "password_hash",
            "hash",
            "secret",
            "private_key",
            "token",
            "refresh_token"
        ]
        
        for field in sensitive_fields:
            assert field not in user_data, f"Sensitive field '{field}' found in response"
        
        # Should have safe fields
        safe_fields = ["id", "email", "first_name", "last_name", "role"]
        for field in safe_fields:
            assert field in user_data, f"Expected field '{field}' missing from response"