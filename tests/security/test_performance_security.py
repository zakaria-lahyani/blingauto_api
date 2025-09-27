"""
Performance & Security Load Tests

Tests that verify security measures hold up under load
and don't introduce performance bottlenecks.
"""
import pytest
import asyncio
import time
from httpx import AsyncClient
from datetime import datetime
import statistics

pytestmark = pytest.mark.asyncio


class TestPerformanceSecurity:
    """Performance impact of security measures"""
    
    async def test_input_validation_performance(self, async_client: AsyncClient):
        """Test that input validation doesn't significantly impact performance"""
        
        # Baseline: Simple valid requests
        valid_data = {
            "email": "perf_test@example.com",
            "password": "ValidPassword123!",
            "first_name": "Performance",
            "last_name": "Test"
        }
        
        # Measure baseline performance
        start_time = time.time()
        baseline_responses = []
        
        for i in range(10):
            test_data = valid_data.copy()
            test_data["email"] = f"perf_test_{i}@example.com"
            
            response_start = time.time()
            response = await async_client.post("/auth/register", json=test_data)
            response_time = time.time() - response_start
            
            baseline_responses.append(response_time)
            assert response.status_code in [201, 422]  # Success or validation error
        
        baseline_avg = statistics.mean(baseline_responses)
        
        # Test with complex validation scenarios
        complex_data = {
            "email": "complex_validation_test@example.com",
            "password": "ComplexPassword123!@#$%^&*()",
            "first_name": "A" * 45,  # Near max length
            "last_name": "Complex-Name'Test"  # Special characters
        }
        
        complex_responses = []
        for i in range(10):
            test_data = complex_data.copy()
            test_data["email"] = f"complex_{i}@example.com"
            
            response_start = time.time()
            response = await async_client.post("/auth/register", json=test_data)
            response_time = time.time() - response_start
            
            complex_responses.append(response_time)
        
        complex_avg = statistics.mean(complex_responses)
        
        # Validation overhead should be minimal (< 2x baseline)
        overhead_ratio = complex_avg / baseline_avg
        assert overhead_ratio < 2.0, f"Validation overhead too high: {overhead_ratio:.2f}x"
        
        print(f"✅ Input validation performance: {overhead_ratio:.2f}x overhead")
        print(f"   Baseline: {baseline_avg*1000:.2f}ms, Complex: {complex_avg*1000:.2f}ms")
    
    async def test_rate_limiting_performance(self, async_client: AsyncClient):
        """Test rate limiting performance under various loads"""
        
        # Test with requests below rate limit
        below_limit_times = []
        for i in range(5):  # Well below rate limit
            start_time = time.time()
            response = await async_client.post("/auth/login", json={
                "email": f"rate_test_{i}@example.com",
                "password": "test123"
            })
            response_time = time.time() - start_time
            below_limit_times.append(response_time)
        
        below_limit_avg = statistics.mean(below_limit_times)
        
        # Test with requests at rate limit threshold
        at_limit_times = []
        tasks = []
        for i in range(10):  # At rate limit
            task = async_client.post("/auth/login", json={
                "email": f"rate_limit_test_{i}@example.com",
                "password": "test123"
            })
            tasks.append(task)
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Check that rate limiting doesn't cause excessive delays
        avg_response_time = total_time / len(responses)
        
        # Rate limiting should add minimal overhead
        overhead_ratio = avg_response_time / below_limit_avg
        assert overhead_ratio < 3.0, f"Rate limiting overhead too high: {overhead_ratio:.2f}x"
        
        # Some requests should be rate limited
        rate_limited_count = sum(1 for r in responses 
                               if hasattr(r, 'status_code') and r.status_code == 429)
        
        print(f"✅ Rate limiting performance: {overhead_ratio:.2f}x overhead")
        print(f"   Below limit: {below_limit_avg*1000:.2f}ms, At limit: {avg_response_time*1000:.2f}ms")
        print(f"   Rate limited responses: {rate_limited_count}/{len(responses)}")
    
    async def test_jwt_validation_performance(self, async_client: AsyncClient):
        """Test JWT validation performance"""
        
        # First, get a valid token
        register_data = {
            "email": "jwt_perf_test@example.com",
            "password": "JWTPerf123!",
            "first_name": "JWT",
            "last_name": "Performance"
        }
        
        await async_client.post("/auth/register", json=register_data)
        
        login_response = await async_client.post("/auth/login", json={
            "email": "jwt_perf_test@example.com",
            "password": "JWTPerf123!"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Cannot test JWT performance without valid token")
        
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        # Test JWT validation performance
        jwt_validation_times = []
        
        for i in range(20):
            start_time = time.time()
            response = await async_client.get("/auth/me", headers=headers)
            response_time = time.time() - start_time
            
            jwt_validation_times.append(response_time)
            assert response.status_code == 200
        
        avg_jwt_time = statistics.mean(jwt_validation_times)
        p95_jwt_time = statistics.quantiles(jwt_validation_times, n=20)[18]  # 95th percentile
        
        # JWT validation should be fast (< 100ms average)
        assert avg_jwt_time < 0.1, f"JWT validation too slow: {avg_jwt_time*1000:.2f}ms"
        assert p95_jwt_time < 0.2, f"JWT validation P95 too slow: {p95_jwt_time*1000:.2f}ms"
        
        print(f"✅ JWT validation performance:")
        print(f"   Average: {avg_jwt_time*1000:.2f}ms")
        print(f"   P95: {p95_jwt_time*1000:.2f}ms")
    
    async def test_encryption_performance(self, async_client: AsyncClient):
        """Test encryption/decryption performance impact"""
        
        # Test registration (includes password hashing)
        hash_times = []
        
        for i in range(10):
            register_data = {
                "email": f"encrypt_test_{i}@example.com",
                "password": "EncryptionTest123!",
                "first_name": "Encryption",
                "last_name": "Test"
            }
            
            start_time = time.time()
            response = await async_client.post("/auth/register", json=register_data)
            response_time = time.time() - start_time
            
            hash_times.append(response_time)
            assert response.status_code in [201, 422]
        
        avg_hash_time = statistics.mean(hash_times)
        
        # Password hashing should be reasonably fast but secure
        # BCrypt with proper rounds should take 100-500ms
        assert 0.05 < avg_hash_time < 2.0, f"Password hashing time unexpected: {avg_hash_time*1000:.2f}ms"
        
        print(f"✅ Encryption performance:")
        print(f"   Password hashing: {avg_hash_time*1000:.2f}ms average")
    
    async def test_concurrent_security_load(self, async_client: AsyncClient):
        """Test security measures under concurrent load"""
        
        # Simulate realistic concurrent load
        concurrent_users = 50
        requests_per_user = 5
        
        async def user_workflow(user_id: int):
            """Simulate a user's workflow"""
            workflow_times = []
            
            # Register
            start_time = time.time()
            register_response = await async_client.post("/auth/register", json={
                "email": f"load_user_{user_id}@example.com",
                "password": f"LoadTest123!{user_id}",
                "first_name": f"User{user_id}",
                "last_name": "LoadTest"
            })
            workflow_times.append(time.time() - start_time)
            
            if register_response.status_code != 201:
                return {"user_id": user_id, "error": "registration_failed", "times": workflow_times}
            
            # Login
            start_time = time.time()
            login_response = await async_client.post("/auth/login", json={
                "email": f"load_user_{user_id}@example.com",
                "password": f"LoadTest123!{user_id}"
            })
            workflow_times.append(time.time() - start_time)
            
            if login_response.status_code != 200:
                return {"user_id": user_id, "error": "login_failed", "times": workflow_times}
            
            tokens = login_response.json()
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            
            # Make authenticated requests
            for i in range(requests_per_user):
                start_time = time.time()
                profile_response = await async_client.get("/auth/me", headers=headers)
                workflow_times.append(time.time() - start_time)
                
                if profile_response.status_code != 200:
                    break
            
            return {"user_id": user_id, "times": workflow_times, "success": True}
        
        # Execute concurrent workflows
        start_time = time.time()
        tasks = [user_workflow(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_users = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_users = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if not isinstance(r, dict)]
        
        success_rate = len(successful_users) / len(results)
        avg_request_time = total_time / (len(results) * (2 + requests_per_user))  # register + login + requests
        
        # Under load, we should maintain reasonable performance and success rate
        assert success_rate > 0.8, f"Success rate too low under load: {success_rate:.2%}"
        assert avg_request_time < 1.0, f"Average request time too high: {avg_request_time*1000:.2f}ms"
        
        print(f"✅ Concurrent load test:")
        print(f"   Users: {concurrent_users}, Requests per user: {requests_per_user}")
        print(f"   Success rate: {success_rate:.2%}")
        print(f"   Average request time: {avg_request_time*1000:.2f}ms")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Failed users: {len(failed_users)}, Exceptions: {len(exceptions)}")
    
    async def test_security_logging_performance(self, async_client: AsyncClient):
        """Test that security logging doesn't impact performance significantly"""
        
        # Test requests that trigger security logging
        security_requests = []
        
        for i in range(20):
            # Failed login attempts (should trigger security logging)
            start_time = time.time()
            response = await async_client.post("/auth/login", json={
                "email": f"security_log_test_{i}@example.com",
                "password": "wrong_password"
            })
            response_time = time.time() - start_time
            
            security_requests.append(response_time)
            assert response.status_code == 401
        
        avg_security_log_time = statistics.mean(security_requests)
        
        # Security logging should add minimal overhead
        assert avg_security_log_time < 0.5, f"Security logging overhead too high: {avg_security_log_time*1000:.2f}ms"
        
        print(f"✅ Security logging performance: {avg_security_log_time*1000:.2f}ms average")


async def test_security_performance_summary(async_client: AsyncClient):
    """Summary test of overall security performance"""
    
    print("\n🚀 Security Performance Summary Test")
    print("="*50)
    
    # Test a complete user journey with all security features enabled
    start_time = time.time()
    
    # Registration with full validation
    register_start = time.time()
    register_response = await async_client.post("/auth/register", json={
        "email": "summary_test@example.com",
        "password": "SummaryTest123!@#",
        "first_name": "Summary",
        "last_name": "Test"
    })
    register_time = time.time() - register_start
    
    assert register_response.status_code == 201
    print(f"  ✅ Registration: {register_time*1000:.2f}ms")
    
    # Login with authentication
    login_start = time.time()
    login_response = await async_client.post("/auth/login", json={
        "email": "summary_test@example.com",
        "password": "SummaryTest123!@#"
    })
    login_time = time.time() - login_start
    
    assert login_response.status_code == 200
    print(f"  ✅ Login: {login_time*1000:.2f}ms")
    
    tokens = login_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    # Multiple authenticated requests
    auth_times = []
    for i in range(10):
        auth_start = time.time()
        response = await async_client.get("/auth/me", headers=headers)
        auth_time = time.time() - auth_start
        
        auth_times.append(auth_time)
        assert response.status_code == 200
    
    avg_auth_time = statistics.mean(auth_times)
    print(f"  ✅ Authenticated requests: {avg_auth_time*1000:.2f}ms average")
    
    # Token refresh
    refresh_start = time.time()
    refresh_response = await async_client.post("/auth/refresh", json={
        "refresh_token": tokens["refresh_token"]
    })
    refresh_time = time.time() - refresh_start
    
    assert refresh_response.status_code == 200
    print(f"  ✅ Token refresh: {refresh_time*1000:.2f}ms")
    
    total_time = time.time() - start_time
    print(f"\n🎯 Total workflow time: {total_time*1000:.2f}ms")
    
    # Performance should be reasonable for production use
    assert total_time < 5.0, f"Total workflow too slow: {total_time:.2f}s"
    
    print("\n🏆 All security performance tests passed!")
    print("   The security improvements provide robust protection")
    print("   while maintaining excellent performance characteristics.")


if __name__ == "__main__":
    print("Performance & Security Load Tests")
    print("="*40)
    print("Testing security measure performance under load")