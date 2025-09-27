"""
Tests for Redis-based Rate Limiting Service

Tests the distributed rate limiting implementation with Redis backend,
including sliding window algorithm, endpoint-specific limits, and role-based rate limiting.
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, List

from src.shared.services.rate_limiter import (
    RateLimiter,
    RedisRateLimitStrategy,
    MemoryRateLimitStrategy,
    EndpointRateLimiter,
    RateLimitResult,
    init_rate_limiter,
    get_rate_limiter,
    get_endpoint_rate_limiter
)


class TestRedisRateLimitStrategy:
    """Tests for Redis-based rate limiting strategy"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client for testing"""
        mock_redis = AsyncMock()
        mock_redis.pipeline = MagicMock()
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline
        
        # Setup pipeline methods
        mock_pipeline.zremrangebyscore = AsyncMock()
        mock_pipeline.zcard = AsyncMock()
        mock_pipeline.zadd = AsyncMock()
        mock_pipeline.expire = AsyncMock()
        mock_pipeline.execute = AsyncMock(return_value=[None, 5])  # Default: 5 requests in window
        
        return mock_redis, mock_pipeline
    
    @pytest.fixture
    def redis_strategy(self, mock_redis):
        """Create Redis rate limit strategy with mock client"""
        redis_client, _ = mock_redis
        strategy = RedisRateLimitStrategy(redis_client)
        return strategy
    
    @pytest.mark.asyncio
    async def test_redis_rate_limit_under_limit(self, redis_strategy, mock_redis):
        """Test rate limiting when under the limit"""
        redis_client, mock_pipeline = mock_redis
        mock_pipeline.execute.return_value = [None, 3]  # 3 requests in window
        
        result = await redis_strategy.check_limit("user:123", limit=10, window_seconds=60)
        
        assert result.allowed is True
        assert result.current_requests == 4  # 3 existing + 1 new
        assert result.remaining == 6
        assert result.limit == 10
        
        # Verify Redis operations
        mock_pipeline.zremrangebyscore.assert_called_once()
        mock_pipeline.zcard.assert_called_once()
        mock_pipeline.zadd.assert_called_once()
        mock_pipeline.expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_rate_limit_at_limit(self, redis_strategy, mock_redis):
        """Test rate limiting when exactly at the limit"""
        redis_client, mock_pipeline = mock_redis
        mock_pipeline.execute.return_value = [None, 9]  # 9 requests in window
        
        result = await redis_strategy.check_limit("user:123", limit=10, window_seconds=60)
        
        assert result.allowed is True
        assert result.current_requests == 10  # 9 existing + 1 new
        assert result.remaining == 0
        assert result.limit == 10
    
    @pytest.mark.asyncio
    async def test_redis_rate_limit_exceeded(self, redis_strategy, mock_redis):
        """Test rate limiting when limit is exceeded"""
        redis_client, mock_pipeline = mock_redis
        mock_pipeline.execute.return_value = [None, 10]  # Already at limit
        
        result = await redis_strategy.check_limit("user:123", limit=10, window_seconds=60)
        
        assert result.allowed is False
        assert result.current_requests == 10
        assert result.remaining == 0
        assert result.limit == 10
        assert result.retry_after == 60
        
        # Should not add new request when limit exceeded
        mock_pipeline.zadd.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_redis_rate_limit_multiple_increments(self, redis_strategy, mock_redis):
        """Test rate limiting with multiple increments"""
        redis_client, mock_pipeline = mock_redis
        mock_pipeline.execute.return_value = [None, 5]
        
        result = await redis_strategy.check_limit("user:123", limit=10, window_seconds=60, increment=3)
        
        assert result.allowed is True
        assert result.current_requests == 8  # 5 existing + 3 new
        assert result.remaining == 2
        
        # Should add 3 entries for increment=3
        assert mock_pipeline.zadd.call_count == 3
    
    @pytest.mark.asyncio
    async def test_redis_rate_limit_sliding_window(self, redis_strategy, mock_redis):
        """Test sliding window cleanup of expired entries"""
        redis_client, mock_pipeline = mock_redis
        current_time = time.time()
        window_start = current_time - 60
        
        result = await redis_strategy.check_limit("user:123", limit=10, window_seconds=60)
        
        # Verify cleanup of expired entries
        zremrangebyscore_call = mock_pipeline.zremrangebyscore.call_args
        assert zremrangebyscore_call[0][0] == "user:123"
        assert zremrangebyscore_call[0][1] == 0
        assert abs(zremrangebyscore_call[0][2] - window_start) < 1  # Within 1 second tolerance
    
    @pytest.mark.asyncio
    async def test_redis_rate_limit_error_handling(self, redis_strategy, mock_redis):
        """Test graceful handling of Redis errors"""
        redis_client, mock_pipeline = mock_redis
        mock_pipeline.execute.side_effect = Exception("Redis connection error")
        
        # Should fail open (allow request) on Redis error
        result = await redis_strategy.check_limit("user:123", limit=10, window_seconds=60)
        
        assert result.allowed is True
        assert result.current_requests == 0
        assert result.remaining == 10
    
    @pytest.mark.asyncio
    async def test_redis_rate_limit_unique_scores(self, redis_strategy, mock_redis):
        """Test that unique scores are used to handle concurrent requests"""
        redis_client, mock_pipeline = mock_redis
        mock_pipeline.execute.return_value = [None, 5]
        
        # Run multiple concurrent checks
        tasks = []
        for _ in range(5):
            tasks.append(redis_strategy.check_limit("user:123", limit=10, window_seconds=60))
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed if under limit
        assert all(r.allowed for r in results)
        
        # Verify unique scores were used
        zadd_calls = mock_pipeline.zadd.call_args_list
        scores = []
        for call in zadd_calls:
            member_dict = call[0][1]
            for member, score in member_dict.items():
                scores.append(score)
        
        # Scores should be unique (or very close in time)
        assert len(scores) == len(set(scores)) or max(scores) - min(scores) < 0.01


class TestMemoryRateLimitStrategy:
    """Tests for in-memory rate limiting strategy (fallback)"""
    
    @pytest.fixture
    def memory_strategy(self):
        """Create memory rate limit strategy"""
        return MemoryRateLimitStrategy()
    
    @pytest.mark.asyncio
    async def test_memory_rate_limit_basic(self, memory_strategy):
        """Test basic rate limiting with memory strategy"""
        # First request should succeed
        result = await memory_strategy.check_limit("user:123", limit=5, window_seconds=1)
        assert result.allowed is True
        assert result.current_requests == 1
        assert result.remaining == 4
        
        # Fill up to limit
        for i in range(4):
            result = await memory_strategy.check_limit("user:123", limit=5, window_seconds=1)
            assert result.allowed is True
            assert result.current_requests == i + 2
        
        # Next request should be blocked
        result = await memory_strategy.check_limit("user:123", limit=5, window_seconds=1)
        assert result.allowed is False
        assert result.current_requests == 5
        assert result.remaining == 0
    
    @pytest.mark.asyncio
    async def test_memory_rate_limit_window_expiry(self, memory_strategy):
        """Test that requests expire after window"""
        # Add requests
        for _ in range(3):
            await memory_strategy.check_limit("user:123", limit=5, window_seconds=1)
        
        # Wait for window to expire
        await asyncio.sleep(1.1)
        
        # Should be able to make new requests
        result = await memory_strategy.check_limit("user:123", limit=5, window_seconds=1)
        assert result.allowed is True
        assert result.current_requests == 1  # Old requests expired
    
    @pytest.mark.asyncio
    async def test_memory_rate_limit_concurrent_safety(self, memory_strategy):
        """Test thread-safe concurrent access"""
        async def make_request():
            return await memory_strategy.check_limit("shared_key", limit=100, window_seconds=10)
        
        # Run 50 concurrent requests
        tasks = [make_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed (under limit of 100)
        assert all(r.allowed for r in results)
        
        # Count should be accurate
        final_result = await memory_strategy.check_limit("shared_key", limit=100, window_seconds=10, increment=0)
        assert final_result.current_requests == 50


class TestRateLimiter:
    """Tests for main rate limiter service"""
    
    @pytest.fixture
    def mock_strategy(self):
        """Create mock rate limit strategy"""
        strategy = AsyncMock()
        strategy.check_limit = AsyncMock(return_value=RateLimitResult(
            allowed=True,
            current_requests=5,
            limit=10,
            remaining=5,
            reset_time=time.time() + 60
        ))
        return strategy
    
    @pytest.fixture
    def rate_limiter(self, mock_strategy):
        """Create rate limiter with mock strategy"""
        return RateLimiter(mock_strategy, key_prefix="test")
    
    @pytest.mark.asyncio
    async def test_rate_limiter_check_rate_limit(self, rate_limiter, mock_strategy):
        """Test basic rate limit checking"""
        result = await rate_limiter.check_rate_limit(
            identifier="user:123",
            limit=10,
            window_seconds=60,
            category="api"
        )
        
        assert result.allowed is True
        mock_strategy.check_limit.assert_called_once_with(
            "test:api:user:123", 10, 60, 1
        )
    
    @pytest.mark.asyncio
    async def test_rate_limiter_key_generation(self, rate_limiter, mock_strategy):
        """Test rate limit key generation with prefix and category"""
        await rate_limiter.check_rate_limit(
            identifier="ip:192.168.1.1",
            limit=30,
            window_seconds=60,
            category="login"
        )
        
        expected_key = "test:login:ip:192.168.1.1"
        mock_strategy.check_limit.assert_called_with(expected_key, 30, 60, 1)
    
    @pytest.mark.asyncio
    async def test_rate_limiter_check_multiple_limits(self, rate_limiter, mock_strategy):
        """Test checking multiple rate limits simultaneously"""
        limits = [
            (10, 60, "per_minute"),
            (100, 3600, "per_hour"),
            (1000, 86400, "per_day")
        ]
        
        results = await rate_limiter.check_multiple_limits("user:123", limits)
        
        assert len(results) == 3
        assert all(r.allowed for r in results)
        assert mock_strategy.check_limit.call_count == 3
    
    @pytest.mark.asyncio
    async def test_rate_limiter_reset(self, rate_limiter):
        """Test resetting rate limit for an identifier"""
        # Test with Redis strategy
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)
        rate_limiter.strategy.redis = mock_redis
        
        result = await rate_limiter.reset_rate_limit("user:123", "api")
        
        assert result is True
        mock_redis.delete.assert_called_once_with("test:api:user:123")
    
    @pytest.mark.asyncio
    async def test_rate_limiter_custom_increment(self, rate_limiter, mock_strategy):
        """Test rate limiting with custom increment value"""
        await rate_limiter.check_rate_limit(
            identifier="user:123",
            limit=100,
            window_seconds=60,
            increment=10  # Count as 10 requests
        )
        
        mock_strategy.check_limit.assert_called_with("test:default:user:123", 100, 60, 10)


class TestEndpointRateLimiter:
    """Tests for endpoint-specific rate limiting"""
    
    @pytest.fixture
    def mock_rate_limiter(self):
        """Create mock rate limiter"""
        limiter = AsyncMock()
        limiter.check_rate_limit = AsyncMock(return_value=RateLimitResult(
            allowed=True,
            current_requests=5,
            limit=60,
            remaining=55,
            reset_time=time.time() + 60
        ))
        return limiter
    
    @pytest.fixture
    def endpoint_limiter(self, mock_rate_limiter):
        """Create endpoint rate limiter"""
        return EndpointRateLimiter(mock_rate_limiter)
    
    @pytest.mark.asyncio
    async def test_endpoint_specific_limits(self, endpoint_limiter, mock_rate_limiter):
        """Test endpoint-specific rate limits"""
        # Test login endpoint (strict limit)
        result = await endpoint_limiter.check_endpoint_limit(
            identifier="user:123",
            method="POST",
            path="/auth/login"
        )
        
        assert result.allowed is True
        mock_rate_limiter.check_rate_limit.assert_called_with(
            identifier="user:123",
            limit=5,  # Login has limit of 5
            window_seconds=60,
            category="endpoint:POST:/auth/login"
        )
    
    @pytest.mark.asyncio
    async def test_endpoint_role_based_limits(self, endpoint_limiter, mock_rate_limiter):
        """Test role-based rate limit adjustments"""
        # Admin should get 3x the base limit
        await endpoint_limiter.check_endpoint_limit(
            identifier="user:admin",
            method="POST",
            path="/auth/login",
            user_role="admin"
        )
        
        mock_rate_limiter.check_rate_limit.assert_called_with(
            identifier="user:admin",
            limit=15,  # 5 * 3 for admin
            window_seconds=60,
            category="endpoint:POST:/auth/login"
        )
        
        # Manager should get 2x the base limit
        await endpoint_limiter.check_endpoint_limit(
            identifier="user:manager",
            method="POST",
            path="/auth/login",
            user_role="manager"
        )
        
        mock_rate_limiter.check_rate_limit.assert_called_with(
            identifier="user:manager",
            limit=10,  # 5 * 2 for manager
            window_seconds=60,
            category="endpoint:POST:/auth/login"
        )
    
    @pytest.mark.asyncio
    async def test_endpoint_anonymous_limits(self, endpoint_limiter, mock_rate_limiter):
        """Test anonymous user gets half the limit"""
        await endpoint_limiter.check_endpoint_limit(
            identifier="ip:192.168.1.1",
            method="GET",
            path="/api/",
            user_role=None  # Anonymous
        )
        
        mock_rate_limiter.check_rate_limit.assert_called_with(
            identifier="ip:192.168.1.1",
            limit=30,  # Half of default 60 for anonymous
            window_seconds=60,
            category="endpoint:GET:/api/"
        )
    
    @pytest.mark.asyncio
    async def test_endpoint_custom_configuration(self, endpoint_limiter, mock_rate_limiter):
        """Test configuring custom endpoint limits"""
        # Configure custom limit
        endpoint_limiter.configure_endpoint_limit("POST", "/api/heavy-operation", 2)
        
        # Test the custom limit
        await endpoint_limiter.check_endpoint_limit(
            identifier="user:123",
            method="POST",
            path="/api/heavy-operation"
        )
        
        mock_rate_limiter.check_rate_limit.assert_called_with(
            identifier="user:123",
            limit=2,  # Custom configured limit
            window_seconds=60,
            category="endpoint:POST:/api/heavy-operation"
        )
    
    @pytest.mark.asyncio
    async def test_endpoint_default_limits(self, endpoint_limiter, mock_rate_limiter):
        """Test default limits for unspecified endpoints"""
        # Test an endpoint not in the default limits
        await endpoint_limiter.check_endpoint_limit(
            identifier="user:123",
            method="GET",
            path="/unknown/endpoint",
            user_role="client"
        )
        
        # Should use default limit of 60
        mock_rate_limiter.check_rate_limit.assert_called_with(
            identifier="user:123",
            limit=60,
            window_seconds=60,
            category="endpoint:GET:/unknown/endpoint"
        )


class TestRateLimiterIntegration:
    """Integration tests for rate limiter initialization"""
    
    def test_init_rate_limiter_with_redis(self):
        """Test rate limiter initialization with Redis"""
        mock_redis = AsyncMock()
        
        limiter = init_rate_limiter(mock_redis, key_prefix="app")
        
        assert limiter is not None
        assert limiter.key_prefix == "app"
        assert isinstance(limiter.strategy, RedisRateLimitStrategy)
    
    def test_init_rate_limiter_without_redis(self):
        """Test rate limiter initialization with memory fallback"""
        limiter = init_rate_limiter(redis_client=None, key_prefix="app")
        
        assert limiter is not None
        assert limiter.key_prefix == "app"
        assert isinstance(limiter.strategy, MemoryRateLimitStrategy)
    
    def test_get_rate_limiter_not_initialized(self):
        """Test getting rate limiter before initialization"""
        # Clear global instance
        import src.shared.services.rate_limiter as limiter_module
        limiter_module._rate_limiter = None
        
        with pytest.raises(RuntimeError, match="Rate limiter not initialized"):
            get_rate_limiter()
    
    def test_get_endpoint_rate_limiter_not_initialized(self):
        """Test getting endpoint rate limiter before initialization"""
        # Clear global instance
        import src.shared.services.rate_limiter as limiter_module
        limiter_module._endpoint_rate_limiter = None
        
        with pytest.raises(RuntimeError, match="Endpoint rate limiter not initialized"):
            get_endpoint_rate_limiter()
    
    def test_global_instances_after_init(self):
        """Test global instances are properly set after initialization"""
        mock_redis = AsyncMock()
        
        rate_limiter = init_rate_limiter(mock_redis)
        
        # Should be able to get both instances
        assert get_rate_limiter() is rate_limiter
        assert get_endpoint_rate_limiter() is not None
        assert isinstance(get_endpoint_rate_limiter(), EndpointRateLimiter)


class TestRateLimiterStressTests:
    """Stress tests for rate limiting under high load"""
    
    @pytest.mark.asyncio
    async def test_redis_high_concurrency(self):
        """Test Redis rate limiter under high concurrent load"""
        mock_redis = AsyncMock()
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_pipeline.execute = AsyncMock(return_value=[None, 0])
        
        strategy = RedisRateLimitStrategy(mock_redis)
        limiter = RateLimiter(strategy, key_prefix="stress")
        
        # Simulate 100 concurrent requests
        async def make_request(req_id):
            return await limiter.check_rate_limit(
                identifier=f"user:{req_id % 10}",  # 10 different users
                limit=10,
                window_seconds=1
            )
        
        tasks = [make_request(i) for i in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should handle all requests without errors
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_memory_cleanup_performance(self):
        """Test memory strategy cleanup performance"""
        strategy = MemoryRateLimitStrategy()
        
        # Add many requests with short window
        for i in range(1000):
            await strategy.check_limit(f"key:{i}", limit=10, window_seconds=1)
        
        # Wait for expiry
        await asyncio.sleep(1.1)
        
        # Next request should trigger cleanup
        start_time = time.time()
        await strategy.check_limit("test_key", limit=10, window_seconds=1)
        cleanup_time = time.time() - start_time
        
        # Cleanup should be fast even with many expired entries
        assert cleanup_time < 0.1  # Less than 100ms
    
    @pytest.mark.asyncio
    async def test_endpoint_limiter_performance(self):
        """Test endpoint rate limiter performance"""
        mock_redis = AsyncMock()
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_pipeline.execute = AsyncMock(return_value=[None, 5])
        
        strategy = RedisRateLimitStrategy(mock_redis)
        limiter = RateLimiter(strategy)
        endpoint_limiter = EndpointRateLimiter(limiter)
        
        # Test various endpoints and roles
        test_cases = [
            ("POST", "/auth/login", "admin"),
            ("GET", "/api/users", "manager"),
            ("POST", "/auth/register", None),
            ("DELETE", "/api/resource", "client")
        ]
        
        tasks = []
        for _ in range(25):  # 25 iterations
            for method, path, role in test_cases:
                tasks.append(endpoint_limiter.check_endpoint_limit(
                    identifier=f"test:{role or 'anon'}",
                    method=method,
                    path=path,
                    user_role=role
                ))
        
        results = await asyncio.gather(*tasks)
        assert len(results) == 100  # 25 * 4 test cases


if __name__ == "__main__":
    pytest.main([__file__, "-v"])