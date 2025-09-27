"""
Tests for Redis-based Cache Service

Tests the distributed cache implementation with Redis backend,
including connection handling, serialization, TTL, and fallback scenarios.
"""
import pytest
import asyncio
import json
import pickle
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Any

from src.shared.services.cache_service import (
    CacheService,
    RedisCacheProvider,
    InMemoryCacheProvider,
    init_cache_service,
    get_cache_service
)


class TestRedisCacheProvider:
    """Tests for Redis cache provider implementation"""
    
    @pytest.fixture
    async def mock_redis(self):
        """Mock Redis client for testing"""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.setex = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.exists = AsyncMock(return_value=1)
        mock_redis.incrby = AsyncMock(return_value=5)
        mock_redis.expire = AsyncMock(return_value=True)
        mock_redis.pipeline = MagicMock(return_value=mock_redis)
        mock_redis.execute = AsyncMock(return_value=[5])
        return mock_redis
    
    @pytest.fixture
    async def redis_provider(self, mock_redis):
        """Create Redis cache provider with mock client"""
        provider = RedisCacheProvider("redis://localhost:6379/0")
        provider._redis = mock_redis
        return provider
    
    @pytest.mark.asyncio
    async def test_redis_provider_get_success(self, redis_provider, mock_redis):
        """Test successful get operation from Redis"""
        test_value = b"test_value"
        mock_redis.get.return_value = test_value
        
        result = await redis_provider.get("test_key")
        
        assert result == test_value
        mock_redis.get.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_redis_provider_get_miss(self, redis_provider, mock_redis):
        """Test cache miss returns None"""
        mock_redis.get.return_value = None
        
        result = await redis_provider.get("missing_key")
        
        assert result is None
        mock_redis.get.assert_called_once_with("missing_key")
    
    @pytest.mark.asyncio
    async def test_redis_provider_set_with_ttl(self, redis_provider, mock_redis):
        """Test setting value with TTL"""
        test_value = b"test_value"
        ttl = 300  # 5 minutes
        
        result = await redis_provider.set("test_key", test_value, ttl=ttl)
        
        assert result is True
        mock_redis.setex.assert_called_once_with("test_key", ttl, test_value)
    
    @pytest.mark.asyncio
    async def test_redis_provider_set_without_ttl(self, redis_provider, mock_redis):
        """Test setting value without TTL"""
        test_value = b"test_value"
        
        result = await redis_provider.set("test_key", test_value)
        
        assert result is True
        mock_redis.set.assert_called_once_with("test_key", test_value)
    
    @pytest.mark.asyncio
    async def test_redis_provider_delete_existing(self, redis_provider, mock_redis):
        """Test deleting existing key"""
        mock_redis.delete.return_value = 1
        
        result = await redis_provider.delete("test_key")
        
        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_redis_provider_delete_missing(self, redis_provider, mock_redis):
        """Test deleting non-existent key"""
        mock_redis.delete.return_value = 0
        
        result = await redis_provider.delete("missing_key")
        
        assert result is False
        mock_redis.delete.assert_called_once_with("missing_key")
    
    @pytest.mark.asyncio
    async def test_redis_provider_exists_true(self, redis_provider, mock_redis):
        """Test checking if key exists (positive case)"""
        mock_redis.exists.return_value = 1
        
        result = await redis_provider.exists("test_key")
        
        assert result is True
        mock_redis.exists.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_redis_provider_exists_false(self, redis_provider, mock_redis):
        """Test checking if key doesn't exist"""
        mock_redis.exists.return_value = 0
        
        result = await redis_provider.exists("missing_key")
        
        assert result is False
        mock_redis.exists.assert_called_once_with("missing_key")
    
    @pytest.mark.asyncio
    async def test_redis_provider_increment(self, redis_provider, mock_redis):
        """Test atomic increment operation"""
        mock_redis.execute.return_value = [10]
        
        result = await redis_provider.increment("counter_key", amount=5, ttl=60)
        
        assert result == 10
        mock_redis.incrby.assert_called_once_with("counter_key", 5)
        mock_redis.expire.assert_called_once_with("counter_key", 60)
    
    @pytest.mark.asyncio
    async def test_redis_provider_connection_error(self, redis_provider, mock_redis):
        """Test handling of Redis connection errors"""
        mock_redis.get.side_effect = Exception("Connection refused")
        
        result = await redis_provider.get("test_key")
        
        assert result is None  # Should return None on error
    
    @pytest.mark.asyncio
    async def test_redis_provider_connection_pooling(self):
        """Test Redis connection pool configuration"""
        provider = RedisCacheProvider("redis://localhost:6379/0", max_connections=50)
        
        assert provider.redis_url == "redis://localhost:6379/0"
        assert provider.max_connections == 50
        assert provider._redis is None  # Lazy initialization


class TestInMemoryCacheProvider:
    """Tests for in-memory cache provider (fallback implementation)"""
    
    @pytest.fixture
    def memory_provider(self):
        """Create in-memory cache provider"""
        return InMemoryCacheProvider()
    
    @pytest.mark.asyncio
    async def test_memory_provider_basic_operations(self, memory_provider):
        """Test basic get/set/delete operations"""
        test_value = b"test_value"
        
        # Test set
        result = await memory_provider.set("key1", test_value)
        assert result is True
        
        # Test get
        result = await memory_provider.get("key1")
        assert result == test_value
        
        # Test exists
        result = await memory_provider.exists("key1")
        assert result is True
        
        # Test delete
        result = await memory_provider.delete("key1")
        assert result is True
        
        # Test get after delete
        result = await memory_provider.get("key1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_memory_provider_ttl_expiration(self, memory_provider):
        """Test TTL expiration for in-memory cache"""
        test_value = b"test_value"
        
        # Set with very short TTL
        await memory_provider.set("key1", test_value, ttl=1)
        
        # Should exist immediately
        result = await memory_provider.get("key1")
        assert result == test_value
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        result = await memory_provider.get("key1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_memory_provider_increment(self, memory_provider):
        """Test atomic increment operation"""
        # First increment (creates key)
        result = await memory_provider.increment("counter", amount=5)
        assert result == 5
        
        # Second increment
        result = await memory_provider.increment("counter", amount=3)
        assert result == 8
        
        # Increment with TTL
        result = await memory_provider.increment("counter2", amount=10, ttl=60)
        assert result == 10
    
    @pytest.mark.asyncio
    async def test_memory_provider_concurrent_access(self, memory_provider):
        """Test thread-safe concurrent access"""
        async def increment_task():
            for _ in range(100):
                await memory_provider.increment("shared_counter", amount=1)
        
        # Run multiple concurrent tasks
        tasks = [increment_task() for _ in range(10)]
        await asyncio.gather(*tasks)
        
        # Should have exactly 1000 increments
        result = await memory_provider.get("shared_counter")
        value = int.from_bytes(result, 'big')
        assert value == 1000


class TestCacheService:
    """Tests for high-level cache service"""
    
    @pytest.fixture
    def mock_provider(self):
        """Create mock cache provider"""
        provider = AsyncMock()
        provider.get = AsyncMock(return_value=None)
        provider.set = AsyncMock(return_value=True)
        provider.delete = AsyncMock(return_value=True)
        provider.exists = AsyncMock(return_value=False)
        provider.increment = AsyncMock(return_value=1)
        return provider
    
    @pytest.fixture
    def cache_service(self, mock_provider):
        """Create cache service with mock provider"""
        return CacheService(mock_provider, key_prefix="test")
    
    @pytest.mark.asyncio
    async def test_cache_service_json_operations(self, cache_service, mock_provider):
        """Test JSON serialization/deserialization"""
        test_data = {"name": "John", "age": 30, "active": True}
        
        # Test set_json
        await cache_service.set_json("user:1", test_data, ttl=300)
        
        # Verify JSON serialization
        call_args = mock_provider.set.call_args
        assert call_args[0][0] == "test:user:1"  # Key with prefix
        assert json.loads(call_args[0][1].decode('utf-8')) == test_data
        assert call_args[0][2] == 300  # TTL
        
        # Test get_json
        mock_provider.get.return_value = json.dumps(test_data).encode('utf-8')
        result = await cache_service.get_json("user:1")
        
        assert result == test_data
        mock_provider.get.assert_called_with("test:user:1")
    
    @pytest.mark.asyncio
    async def test_cache_service_pickle_operations(self, cache_service, mock_provider):
        """Test pickle serialization for complex objects"""
        class CustomObject:
            def __init__(self, value):
                self.value = value
                self.timestamp = datetime.now()
        
        test_obj = CustomObject(42)
        
        # Test set_pickle
        await cache_service.set_pickle("obj:1", test_obj, ttl=600)
        
        # Verify pickle serialization
        call_args = mock_provider.set.call_args
        assert call_args[0][0] == "test:obj:1"
        assert pickle.loads(call_args[0][1]).value == 42
        
        # Test get_pickle
        mock_provider.get.return_value = pickle.dumps(test_obj)
        result = await cache_service.get_pickle("obj:1")
        
        assert result.value == 42
        assert isinstance(result.timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_cache_service_string_operations(self, cache_service, mock_provider):
        """Test string operations"""
        test_string = "Hello, Redis!"
        
        # Test set_string
        await cache_service.set_string("msg:1", test_string)
        
        call_args = mock_provider.set.call_args
        assert call_args[0][0] == "test:msg:1"
        assert call_args[0][1] == test_string.encode('utf-8')
        
        # Test get_string
        mock_provider.get.return_value = test_string.encode('utf-8')
        result = await cache_service.get_string("msg:1")
        
        assert result == test_string
    
    @pytest.mark.asyncio
    async def test_cache_service_key_prefixing(self, cache_service, mock_provider):
        """Test automatic key prefixing"""
        await cache_service.delete("test_key")
        mock_provider.delete.assert_called_with("test:test_key")
        
        await cache_service.exists("another_key")
        mock_provider.exists.assert_called_with("test:another_key")
        
        await cache_service.increment("counter", amount=5)
        mock_provider.increment.assert_called_with("test:counter", 5, None)
    
    @pytest.mark.asyncio
    async def test_cache_service_get_or_set(self, cache_service, mock_provider):
        """Test get_or_set pattern with factory function"""
        # Test cache hit
        cached_data = {"cached": True}
        mock_provider.get.return_value = json.dumps(cached_data).encode('utf-8')
        
        factory_func = Mock(return_value={"new": True})
        result = await cache_service.get_or_set("key1", factory_func, ttl=300)
        
        assert result == cached_data
        factory_func.assert_not_called()  # Should not call factory on cache hit
        
        # Test cache miss
        mock_provider.get.return_value = None
        factory_data = {"generated": True}
        factory_func = Mock(return_value=factory_data)
        
        result = await cache_service.get_or_set("key2", factory_func, ttl=300)
        
        assert result == factory_data
        factory_func.assert_called_once()
        
        # Verify set was called with factory result
        set_calls = mock_provider.set.call_args_list
        last_call = set_calls[-1]
        assert json.loads(last_call[0][1].decode('utf-8')) == factory_data
    
    @pytest.mark.asyncio
    async def test_cache_service_get_or_set_async_factory(self, cache_service, mock_provider):
        """Test get_or_set with async factory function"""
        mock_provider.get.return_value = None
        
        async def async_factory():
            await asyncio.sleep(0.1)  # Simulate async work
            return {"async": True}
        
        result = await cache_service.get_or_set("async_key", async_factory, ttl=300)
        
        assert result == {"async": True}
    
    @pytest.mark.asyncio
    async def test_cache_service_error_handling(self, cache_service, mock_provider):
        """Test graceful error handling"""
        # Test JSON decode error
        mock_provider.get.return_value = b"invalid json"
        result = await cache_service.get_json("bad_json", default={"default": True})
        assert result == {"default": True}
        
        # Test pickle decode error
        mock_provider.get.return_value = b"invalid pickle"
        result = await cache_service.get_pickle("bad_pickle", default="fallback")
        assert result == "fallback"
        
        # Test provider error
        mock_provider.set.side_effect = Exception("Redis error")
        result = await cache_service.set_json("error_key", {"data": True})
        assert result is False


class TestCacheServiceIntegration:
    """Integration tests for cache service initialization"""
    
    @pytest.mark.asyncio
    async def test_init_cache_service_with_redis(self):
        """Test cache service initialization with Redis URL"""
        with patch('src.shared.services.cache_service.RedisCacheProvider') as MockRedisProvider:
            mock_provider = AsyncMock()
            MockRedisProvider.return_value = mock_provider
            
            service = init_cache_service(redis_url="redis://localhost:6379/0", key_prefix="app")
            
            assert service is not None
            assert service.key_prefix == "app"
            MockRedisProvider.assert_called_once_with("redis://localhost:6379/0")
    
    @pytest.mark.asyncio
    async def test_init_cache_service_fallback_memory(self):
        """Test cache service initialization with in-memory fallback"""
        service = init_cache_service(redis_url=None, key_prefix="app")
        
        assert service is not None
        assert service.key_prefix == "app"
        assert isinstance(service.provider, InMemoryCacheProvider)
    
    def test_get_cache_service_not_initialized(self):
        """Test getting cache service before initialization"""
        # Clear global instance
        import src.shared.services.cache_service as cache_module
        cache_module._cache_service = None
        
        with pytest.raises(RuntimeError, match="Cache service not initialized"):
            get_cache_service()
    
    def test_get_cache_service_after_init(self):
        """Test getting cache service after initialization"""
        service = init_cache_service(redis_url=None)
        retrieved_service = get_cache_service()
        
        assert retrieved_service is service


class TestRedisCachePerformance:
    """Performance and stress tests for Redis cache"""
    
    @pytest.fixture
    async def redis_cache(self, mock_redis):
        """Create Redis cache service for performance testing"""
        provider = RedisCacheProvider("redis://localhost:6379/0")
        provider._redis = mock_redis
        return CacheService(provider, key_prefix="perf")
    
    @pytest.mark.asyncio
    async def test_redis_cache_bulk_operations(self, redis_cache, mock_redis):
        """Test bulk cache operations performance"""
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        
        # Simulate bulk write
        tasks = []
        for i in range(100):
            tasks.append(redis_cache.set_json(f"bulk:{i}", {"id": i, "data": f"value_{i}"}))
        
        results = await asyncio.gather(*tasks)
        assert all(results)
        assert mock_redis.set.call_count == 100
    
    @pytest.mark.asyncio
    async def test_redis_cache_concurrent_reads(self, redis_cache, mock_redis):
        """Test concurrent read operations"""
        test_data = {"test": "data"}
        mock_redis.get.return_value = json.dumps(test_data).encode('utf-8')
        
        # Simulate concurrent reads
        tasks = []
        for i in range(50):
            tasks.append(redis_cache.get_json(f"read:{i % 10}"))  # 10 unique keys
        
        results = await asyncio.gather(*tasks)
        assert len(results) == 50
        assert all(r == test_data for r in results)
    
    @pytest.mark.asyncio
    async def test_redis_cache_mixed_operations(self, redis_cache, mock_redis):
        """Test mixed read/write/delete operations"""
        mock_redis.get.return_value = b"value"
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 1
        
        async def mixed_ops(op_id):
            if op_id % 3 == 0:
                return await redis_cache.set_string(f"key:{op_id}", f"value:{op_id}")
            elif op_id % 3 == 1:
                return await redis_cache.get_string(f"key:{op_id}")
            else:
                return await redis_cache.delete(f"key:{op_id}")
        
        tasks = [mixed_ops(i) for i in range(30)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 30
        # Verify call distribution
        assert mock_redis.set.call_count == 10
        assert mock_redis.get.call_count == 10
        assert mock_redis.delete.call_count == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])