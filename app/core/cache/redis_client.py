from typing import Optional, Any, Union
import json
import redis
from redis import ConnectionPool
from datetime import timedelta

from app.core.config import settings


class RedisClient:
    """Redis client wrapper with connection pooling and common operations."""

    _instance: Optional["RedisClient"] = None
    _pool: Optional[ConnectionPool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._client: Optional[redis.Redis] = None
            if settings.redis_url:
                self._setup_connection()

    def _setup_connection(self):
        """Setup Redis connection with connection pooling."""
        if not self._pool:
            self._pool = redis.ConnectionPool.from_url(
                settings.redis_url,
                max_connections=settings.redis_max_connections,
                decode_responses=True,
            )
        self._client = redis.Redis(connection_pool=self._pool)

    @property
    def client(self) -> Optional[redis.Redis]:
        """Get Redis client instance."""
        return self._client

    def is_available(self) -> bool:
        """Check if Redis is available."""
        if not self._client:
            return False
        try:
            return self._client.ping()
        except:
            return False

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._client:
            return None
        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except:
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        """Set value in cache with optional TTL."""
        if not self._client:
            return False
        try:
            serialized = json.dumps(value)
            if ttl is None:
                ttl = settings.redis_ttl
            elif isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            return self._client.setex(key, ttl, serialized)
        except:
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self._client:
            return False
        try:
            return bool(self._client.delete(key))
        except:
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._client:
            return False
        try:
            return bool(self._client.exists(key))
        except:
            return False

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter."""
        if not self._client:
            return None
        try:
            return self._client.incr(key, amount)
        except:
            return None

    def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set TTL on existing key."""
        if not self._client:
            return False
        try:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            return self._client.expire(key, ttl)
        except:
            return False

    def flush_all(self) -> bool:
        """Flush all keys (use with caution)."""
        if not self._client:
            return False
        try:
            self._client.flushall()
            return True
        except:
            return False

    def scan_iter(self, match: str = None, count: int = 100):
        """Iterate over keys matching a pattern."""
        if not self._client:
            return iter([])
        try:
            return self._client.scan_iter(match=match, count=count)
        except:
            return iter([])


# Singleton instance
redis_client = RedisClient()