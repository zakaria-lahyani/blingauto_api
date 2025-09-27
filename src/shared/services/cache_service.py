"""
Distributed Cache Service

Provides distributed caching capabilities using Redis for:
- Session storage
- User data caching
- Rate limiting data
- Application state
"""
import asyncio
import json
import pickle
import time
import logging
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheProvider(ABC):
    """Abstract base class for cache providers"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[bytes]:
        """Get raw bytes value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: bytes, ttl: Optional[int] = None) -> bool:
        """Set raw bytes value in cache"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
    
    @abstractmethod
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Atomic increment operation"""
        pass


class RedisCacheProvider(CacheProvider):
    """Redis cache provider implementation"""
    
    def __init__(self, redis_url: str, max_connections: int = 20):
        self.redis_url = redis_url
        self.max_connections = max_connections
        self._redis = None
        self._connection_pool = None
    
    async def _get_redis(self):
        """Get Redis connection with connection pooling"""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                
                # Create connection pool
                self._connection_pool = redis.ConnectionPool.from_url(
                    self.redis_url,
                    max_connections=self.max_connections,
                    decode_responses=False  # We handle encoding ourselves
                )
                
                self._redis = redis.Redis(connection_pool=self._connection_pool)
                
                # Test connection
                await self._redis.ping()
                logger.info("Redis cache provider connected successfully")
                
            except ImportError:
                logger.error("redis package not installed. Install with: pip install redis[hiredis]")
                raise
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        
        return self._redis
    
    async def get(self, key: str) -> Optional[bytes]:
        """Get value from Redis"""
        try:
            redis_client = await self._get_redis()
            return await redis_client.get(key)
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: bytes, ttl: Optional[int] = None) -> bool:
        """Set value in Redis"""
        try:
            redis_client = await self._get_redis()
            if ttl:
                return await redis_client.setex(key, ttl, value)
            else:
                return await redis_client.set(key, value)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            redis_client = await self._get_redis()
            return await redis_client.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            redis_client = await self._get_redis()
            return await redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Atomic increment in Redis"""
        try:
            redis_client = await self._get_redis()
            pipeline = redis_client.pipeline()
            pipeline.incrby(key, amount)
            if ttl:
                pipeline.expire(key, ttl)
            results = await pipeline.execute()
            return results[0]
        except Exception as e:
            logger.error(f"Redis increment error for key {key}: {e}")
            return 0
    
    async def close(self):
        """Close Redis connection"""
        if self._connection_pool:
            await self._connection_pool.disconnect()


class InMemoryCacheProvider(CacheProvider):
    """In-memory cache provider (fallback for development)"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[bytes]:
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                # Check expiration
                if entry.get('expires') and datetime.utcnow() > entry['expires']:
                    del self._cache[key]
                    return None
                return entry['value']
            return None
    
    async def set(self, key: str, value: bytes, ttl: Optional[int] = None) -> bool:
        async with self._lock:
            entry = {'value': value}
            if ttl:
                entry['expires'] = datetime.utcnow() + timedelta(seconds=ttl)
            self._cache[key] = entry
            return True
    
    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                # Check expiration
                if entry.get('expires') and datetime.utcnow() > entry['expires']:
                    del self._cache[key]
                    return False
                return True
            return False
    
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        async with self._lock:
            current_value = 0
            if key in self._cache:
                entry = self._cache[key]
                # Check expiration
                if entry.get('expires') and datetime.utcnow() > entry['expires']:
                    del self._cache[key]
                else:
                    try:
                        current_value = int.from_bytes(entry['value'], 'big')
                    except:
                        current_value = 0
            
            new_value = current_value + amount
            entry = {'value': new_value.to_bytes(8, 'big')}
            if ttl:
                entry['expires'] = datetime.utcnow() + timedelta(seconds=ttl)
            self._cache[key] = entry
            return new_value


class CacheService:
    """
    High-level cache service with serialization and typed methods
    """
    
    def __init__(self, provider: CacheProvider, key_prefix: str = "carwash"):
        self.provider = provider
        self.key_prefix = key_prefix
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key"""
        return f"{self.key_prefix}:{key}"
    
    async def get_json(self, key: str, default: Any = None) -> Any:
        """Get JSON-serialized value from cache"""
        try:
            raw_value = await self.provider.get(self._make_key(key))
            if raw_value is None:
                return default
            return json.loads(raw_value.decode('utf-8'))
        except Exception as e:
            logger.error(f"Cache JSON get error for key {key}: {e}")
            return default
    
    async def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set JSON-serialized value in cache"""
        try:
            serialized = json.dumps(value, default=str).encode('utf-8')
            return await self.provider.set(self._make_key(key), serialized, ttl)
        except Exception as e:
            logger.error(f"Cache JSON set error for key {key}: {e}")
            return False
    
    async def get_pickle(self, key: str, default: Any = None) -> Any:
        """Get pickle-serialized value from cache"""
        try:
            raw_value = await self.provider.get(self._make_key(key))
            if raw_value is None:
                return default
            return pickle.loads(raw_value)
        except Exception as e:
            logger.error(f"Cache pickle get error for key {key}: {e}")
            return default
    
    async def set_pickle(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set pickle-serialized value in cache"""
        try:
            serialized = pickle.dumps(value)
            return await self.provider.set(self._make_key(key), serialized, ttl)
        except Exception as e:
            logger.error(f"Cache pickle set error for key {key}: {e}")
            return False
    
    async def get_string(self, key: str, default: str = None) -> Optional[str]:
        """Get string value from cache"""
        try:
            raw_value = await self.provider.get(self._make_key(key))
            if raw_value is None:
                return default
            return raw_value.decode('utf-8')
        except Exception as e:
            logger.error(f"Cache string get error for key {key}: {e}")
            return default
    
    async def set_string(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set string value in cache"""
        try:
            return await self.provider.set(self._make_key(key), value.encode('utf-8'), ttl)
        except Exception as e:
            logger.error(f"Cache string set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        return await self.provider.delete(self._make_key(key))
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self.provider.exists(self._make_key(key))
    
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Atomic increment operation"""
        return await self.provider.increment(self._make_key(key), amount, ttl)
    
    async def get_or_set(self, key: str, factory_func, ttl: Optional[int] = None, use_json: bool = True) -> Any:
        """Get value from cache or set it using factory function"""
        # Try to get from cache first
        if use_json:
            cached_value = await self.get_json(key)
        else:
            cached_value = await self.get_pickle(key)
        
        if cached_value is not None:
            return cached_value
        
        # Cache miss - generate value
        try:
            if asyncio.iscoroutinefunction(factory_func):
                value = await factory_func()
            else:
                value = factory_func()
            
            # Store in cache
            if use_json:
                await self.set_json(key, value, ttl)
            else:
                await self.set_pickle(key, value, ttl)
            
            return value
        except Exception as e:
            logger.error(f"Factory function failed for key {key}: {e}")
            return None


# Global cache service instance
_cache_service: Optional[CacheService] = None


def init_cache_service(redis_url: Optional[str] = None, key_prefix: str = "carwash") -> CacheService:
    """Initialize global cache service"""
    global _cache_service
    
    if redis_url:
        provider = RedisCacheProvider(redis_url)
        logger.info("Initialized Redis cache service")
    else:
        provider = InMemoryCacheProvider()
        logger.warning("Initialized in-memory cache service (not recommended for production)")
    
    _cache_service = CacheService(provider, key_prefix)
    return _cache_service


def get_cache_service() -> CacheService:
    """Get global cache service instance"""
    if _cache_service is None:
        raise RuntimeError("Cache service not initialized. Call init_cache_service() first.")
    return _cache_service


# Convenience functions
async def cache_get(key: str, default: Any = None, use_json: bool = True) -> Any:
    """Convenience function to get from cache"""
    cache = get_cache_service()
    if use_json:
        return await cache.get_json(key, default)
    else:
        return await cache.get_pickle(key, default)


async def cache_set(key: str, value: Any, ttl: Optional[int] = None, use_json: bool = True) -> bool:
    """Convenience function to set in cache"""
    cache = get_cache_service()
    if use_json:
        return await cache.set_json(key, value, ttl)
    else:
        return await cache.set_pickle(key, value, ttl)