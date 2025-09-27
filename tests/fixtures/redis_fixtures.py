"""
Redis Test Fixtures

Shared fixtures for testing Redis-based services including cache and rate limiting.
Provides both real Redis connections (for integration tests) and mocked Redis (for unit tests).
"""
import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator, Optional
import logging

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def redis_url():
    """Get Redis URL from environment or use default"""
    return os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")  # Use database 1 for tests


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def real_redis_client(redis_url):
    """
    Create real Redis client for integration tests.
    Skip if Redis is not available.
    """
    try:
        import redis.asyncio as redis
        
        client = redis.from_url(redis_url, decode_responses=False)
        
        # Test connection
        await client.ping()
        
        # Flush test database before tests
        await client.flushdb()
        
        yield client
        
        # Cleanup after tests
        await client.flushdb()
        await client.close()
        
    except ImportError:
        pytest.skip("redis package not installed")
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")


@pytest.fixture
async def mock_redis_client():
    """Create mock Redis client for unit tests"""
    mock_redis = AsyncMock()
    
    # Setup common Redis methods
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.setex = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.exists = AsyncMock(return_value=0)
    mock_redis.expire = AsyncMock(return_value=True)
    mock_redis.ttl = AsyncMock(return_value=-1)
    mock_redis.flushdb = AsyncMock(return_value=True)
    mock_redis.close = AsyncMock()
    
    # Setup sorted set operations for rate limiting
    mock_redis.zadd = AsyncMock(return_value=1)
    mock_redis.zremrangebyscore = AsyncMock(return_value=0)
    mock_redis.zcard = AsyncMock(return_value=0)
    mock_redis.zrange = AsyncMock(return_value=[])
    
    # Setup pipeline
    mock_pipeline = AsyncMock()
    mock_pipeline.execute = AsyncMock(return_value=[])
    mock_redis.pipeline = MagicMock(return_value=mock_pipeline)
    
    # Setup increment operations
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.incrby = AsyncMock(return_value=1)
    
    return mock_redis


@pytest.fixture
async def redis_cache_service(mock_redis_client):
    """Create cache service with mocked Redis"""
    from src.shared.services.cache_service import CacheService, RedisCacheProvider
    
    provider = RedisCacheProvider("redis://localhost:6379/1")
    provider._redis = mock_redis_client
    
    return CacheService(provider, key_prefix="test")


@pytest.fixture
async def redis_rate_limiter(mock_redis_client):
    """Create rate limiter with mocked Redis"""
    from src.shared.services.rate_limiter import RateLimiter, RedisRateLimitStrategy
    
    strategy = RedisRateLimitStrategy(mock_redis_client)
    return RateLimiter(strategy, key_prefix="test")


@pytest.fixture
async def memory_cache_service():
    """Create cache service with in-memory provider"""
    from src.shared.services.cache_service import CacheService, InMemoryCacheProvider
    
    provider = InMemoryCacheProvider()
    return CacheService(provider, key_prefix="test")


@pytest.fixture
async def memory_rate_limiter():
    """Create rate limiter with in-memory strategy"""
    from src.shared.services.rate_limiter import RateLimiter, MemoryRateLimitStrategy
    
    strategy = MemoryRateLimitStrategy()
    return RateLimiter(strategy, key_prefix="test")


@pytest.fixture
def redis_test_data():
    """Common test data for Redis tests"""
    return {
        "users": [
            {"id": "user:1", "name": "Alice", "role": "admin"},
            {"id": "user:2", "name": "Bob", "role": "manager"},
            {"id": "user:3", "name": "Charlie", "role": "client"},
        ],
        "cache_keys": [
            "test:user:1",
            "test:user:email:alice@example.com",
            "test:session:abc123",
        ],
        "rate_limit_keys": [
            "rate_limit:api:user:1",
            "rate_limit:login:ip:192.168.1.1",
            "rate_limit:endpoint:POST:/auth/login:user:2",
        ]
    }


@pytest.fixture
async def populated_redis(real_redis_client, redis_test_data):
    """Populate Redis with test data"""
    if real_redis_client is None:
        pytest.skip("Redis not available")
    
    # Add test data
    for user in redis_test_data["users"]:
        await real_redis_client.set(user["id"], str(user))
    
    yield real_redis_client
    
    # Cleanup handled by real_redis_client fixture


class RedisTestHelper:
    """Helper class for Redis testing utilities"""
    
    @staticmethod
    async def is_redis_available(redis_url: str) -> bool:
        """Check if Redis is available for testing"""
        try:
            import redis.asyncio as redis
            client = redis.from_url(redis_url)
            await client.ping()
            await client.close()
            return True
        except:
            return False
    
    @staticmethod
    async def clean_test_data(client, prefix: str = "test:"):
        """Clean test data with specific prefix"""
        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor, match=f"{prefix}*", count=100)
            if keys:
                await client.delete(*keys)
            if cursor == 0:
                break
    
    @staticmethod
    def create_mock_pipeline():
        """Create a mock Redis pipeline"""
        pipeline = AsyncMock()
        pipeline.execute = AsyncMock(return_value=[])
        pipeline.zadd = AsyncMock()
        pipeline.zremrangebyscore = AsyncMock()
        pipeline.zcard = AsyncMock()
        pipeline.expire = AsyncMock()
        pipeline.set = AsyncMock()
        pipeline.get = AsyncMock()
        pipeline.delete = AsyncMock()
        return pipeline
    
    @staticmethod
    async def wait_for_expiry(seconds: float):
        """Wait for cache/rate limit expiry"""
        await asyncio.sleep(seconds)


@pytest.fixture
def redis_helper():
    """Provide Redis test helper"""
    return RedisTestHelper()


# Markers for test organization
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", 
        "redis: mark test as requiring Redis connection"
    )
    config.addinivalue_line(
        "markers",
        "redis_integration: mark test as Redis integration test"
    )
    config.addinivalue_line(
        "markers",
        "redis_unit: mark test as Redis unit test (mocked)"
    )


# Skip Redis tests if Redis is not available
def pytest_collection_modifyitems(config, items):
    """Skip Redis tests if Redis is not available"""
    if config.getoption("--no-redis", default=False):
        skip_redis = pytest.mark.skip(reason="--no-redis flag provided")
        for item in items:
            if "redis" in item.keywords:
                item.add_marker(skip_redis)


# Custom assertions for Redis tests
class RedisAssertions:
    """Custom assertions for Redis-related tests"""
    
    @staticmethod
    async def assert_key_exists(client, key: str):
        """Assert that a key exists in Redis"""
        exists = await client.exists(key)
        assert exists > 0, f"Key '{key}' does not exist in Redis"
    
    @staticmethod
    async def assert_key_not_exists(client, key: str):
        """Assert that a key does not exist in Redis"""
        exists = await client.exists(key)
        assert exists == 0, f"Key '{key}' exists in Redis but shouldn't"
    
    @staticmethod
    async def assert_ttl_set(client, key: str, min_ttl: int = 1):
        """Assert that a key has TTL set"""
        ttl = await client.ttl(key)
        assert ttl >= min_ttl, f"Key '{key}' has TTL {ttl}, expected at least {min_ttl}"
    
    @staticmethod
    async def assert_value_equals(client, key: str, expected_value):
        """Assert that a key has the expected value"""
        actual = await client.get(key)
        if isinstance(expected_value, str):
            actual = actual.decode('utf-8') if actual else None
        assert actual == expected_value, f"Key '{key}' has value {actual}, expected {expected_value}"
    
    @staticmethod
    async def assert_sorted_set_size(client, key: str, expected_size: int):
        """Assert sorted set has expected size"""
        size = await client.zcard(key)
        assert size == expected_size, f"Sorted set '{key}' has {size} members, expected {expected_size}"


@pytest.fixture
def redis_assertions():
    """Provide Redis assertions helper"""
    return RedisAssertions()


# Performance testing utilities
class RedisPerformanceMonitor:
    """Monitor Redis operation performance"""
    
    def __init__(self):
        self.operations = []
    
    async def measure_operation(self, operation_name: str, operation_func, *args, **kwargs):
        """Measure time taken for a Redis operation"""
        import time
        start = time.time()
        result = await operation_func(*args, **kwargs)
        duration = time.time() - start
        
        self.operations.append({
            "name": operation_name,
            "duration": duration,
            "args": args,
            "kwargs": kwargs
        })
        
        return result
    
    def get_stats(self):
        """Get performance statistics"""
        if not self.operations:
            return {}
        
        durations = [op["duration"] for op in self.operations]
        return {
            "total_operations": len(self.operations),
            "total_time": sum(durations),
            "average_time": sum(durations) / len(durations),
            "min_time": min(durations),
            "max_time": max(durations),
            "operations": self.operations
        }
    
    def assert_performance(self, max_avg_time: float = 0.01):
        """Assert that average operation time is below threshold"""
        stats = self.get_stats()
        if stats:
            assert stats["average_time"] < max_avg_time, \
                f"Average operation time {stats['average_time']:.4f}s exceeds threshold {max_avg_time}s"


@pytest.fixture
def redis_performance_monitor():
    """Provide Redis performance monitor"""
    return RedisPerformanceMonitor()


if __name__ == "__main__":
    # Quick test to check if Redis is available
    async def check_redis():
        helper = RedisTestHelper()
        redis_url = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")
        is_available = await helper.is_redis_available(redis_url)
        
        if is_available:
            print(f"✅ Redis is available at {redis_url}")
        else:
            print(f"❌ Redis is not available at {redis_url}")
            print("   To run Redis tests, ensure Redis is running")
            print("   Docker: docker run -d -p 6379:6379 redis:7-alpine")
        
        return is_available
    
    asyncio.run(check_redis())