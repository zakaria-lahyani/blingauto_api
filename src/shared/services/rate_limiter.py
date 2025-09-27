"""
Distributed Rate Limiting Service

Provides distributed rate limiting using Redis with:
- Sliding window algorithm
- Multiple rate limiting strategies
- Automatic cleanup
- Fallback to in-memory for development
"""
import time
import uuid
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    """Result of a rate limit check"""
    allowed: bool
    current_requests: int
    limit: int
    remaining: int
    reset_time: float
    retry_after: Optional[int] = None


class RateLimitStrategy(ABC):
    """Abstract base class for rate limiting strategies"""
    
    @abstractmethod
    async def check_limit(self, key: str, limit: int, window_seconds: int, increment: int = 1) -> RateLimitResult:
        """Check if request is within rate limit"""
        pass


class RedisRateLimitStrategy(RateLimitStrategy):
    """Redis-based sliding window rate limiting"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def check_limit(self, key: str, limit: int, window_seconds: int, increment: int = 1) -> RateLimitResult:
        """
        Sliding window rate limiting using Redis sorted sets
        
        Uses Redis sorted sets to track request timestamps within a sliding window.
        More accurate than fixed windows but requires more Redis operations.
        """
        now = time.time()
        window_start = now - window_seconds
        
        try:
            # Use Redis pipeline for atomic operations
            pipeline = self.redis.pipeline()
            
            # Remove expired entries
            pipeline.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            pipeline.zcard(key)
            
            # Execute first part to get current count
            results = await pipeline.execute()
            current_count = results[1]
            
            if current_count + increment <= limit:
                # Add new request(s) to the window
                pipeline = self.redis.pipeline()
                for i in range(increment):
                    # Use unique score to handle concurrent requests
                    score = now + (i * 0.000001)  # Microsecond precision
                    member = f"{now}:{uuid.uuid4()}"
                    pipeline.zadd(key, {member: score})
                
                # Set expiration to prevent memory leaks
                pipeline.expire(key, window_seconds + 60)  # Extra 60 seconds buffer
                
                await pipeline.execute()
                
                return RateLimitResult(
                    allowed=True,
                    current_requests=current_count + increment,
                    limit=limit,
                    remaining=limit - (current_count + increment),
                    reset_time=now + window_seconds
                )
            else:
                # Rate limit exceeded
                return RateLimitResult(
                    allowed=False,
                    current_requests=current_count,
                    limit=limit,
                    remaining=0,
                    reset_time=now + window_seconds,
                    retry_after=window_seconds
                )
                
        except Exception as e:
            logger.error(f"Redis rate limiting error for key {key}: {e}")
            # Fail open - allow request if Redis is down
            return RateLimitResult(
                allowed=True,
                current_requests=0,
                limit=limit,
                remaining=limit,
                reset_time=now + window_seconds
            )


class MemoryRateLimitStrategy(RateLimitStrategy):
    """In-memory rate limiting (fallback for development)"""
    
    def __init__(self):
        self._requests: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()
    
    async def check_limit(self, key: str, limit: int, window_seconds: int, increment: int = 1) -> RateLimitResult:
        """In-memory sliding window rate limiting"""
        now = time.time()
        window_start = now - window_seconds
        
        async with self._lock:
            # Get existing requests for this key
            if key not in self._requests:
                self._requests[key] = []
            
            requests = self._requests[key]
            
            # Remove expired requests
            recent_requests = [req_time for req_time in requests if req_time > window_start]
            self._requests[key] = recent_requests
            
            current_count = len(recent_requests)
            
            if current_count + increment <= limit:
                # Add new requests
                for i in range(increment):
                    recent_requests.append(now + (i * 0.000001))
                
                return RateLimitResult(
                    allowed=True,
                    current_requests=current_count + increment,
                    limit=limit,
                    remaining=limit - (current_count + increment),
                    reset_time=now + window_seconds
                )
            else:
                return RateLimitResult(
                    allowed=False,
                    current_requests=current_count,
                    limit=limit,
                    remaining=0,
                    reset_time=now + window_seconds,
                    retry_after=window_seconds
                )


class RateLimiter:
    """
    Main rate limiter service with multiple backends
    """
    
    def __init__(self, strategy: RateLimitStrategy, key_prefix: str = "rate_limit"):
        self.strategy = strategy
        self.key_prefix = key_prefix
    
    def _make_key(self, identifier: str, category: str = "default") -> str:
        """Create rate limit key"""
        return f"{self.key_prefix}:{category}:{identifier}"
    
    async def check_rate_limit(
        self, 
        identifier: str, 
        limit: int, 
        window_seconds: int,
        category: str = "default",
        increment: int = 1
    ) -> RateLimitResult:
        """
        Check rate limit for an identifier
        
        Args:
            identifier: Unique identifier (user_id, ip_address, etc.)
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds
            category: Category for grouping (e.g., 'login', 'api', 'user')
            increment: Number of requests to add (default: 1)
        """
        key = self._make_key(identifier, category)
        return await self.strategy.check_limit(key, limit, window_seconds, increment)
    
    async def check_multiple_limits(
        self, 
        identifier: str, 
        limits: List[Tuple[int, int, str]]  # (limit, window_seconds, category)
    ) -> List[RateLimitResult]:
        """
        Check multiple rate limits simultaneously
        
        Useful for checking different time windows or categories for the same identifier
        """
        tasks = []
        for limit, window_seconds, category in limits:
            task = self.check_rate_limit(identifier, limit, window_seconds, category, increment=0)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    async def reset_rate_limit(self, identifier: str, category: str = "default") -> bool:
        """Reset rate limit for an identifier (admin function)"""
        if hasattr(self.strategy, 'redis'):
            key = self._make_key(identifier, category)
            try:
                await self.strategy.redis.delete(key)
                return True
            except Exception as e:
                logger.error(f"Failed to reset rate limit for {key}: {e}")
                return False
        elif hasattr(self.strategy, '_requests'):
            key = self._make_key(identifier, category)
            if key in self.strategy._requests:
                del self.strategy._requests[key]
                return True
        
        return False


class EndpointRateLimiter:
    """
    Specialized rate limiter for API endpoints with different limits per endpoint
    """
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        
        # Default endpoint limits (requests per minute)
        self.endpoint_limits = {
            # Auth endpoints
            "POST:/auth/login": 5,
            "POST:/auth/register": 3,
            "POST:/auth/reset-password": 2,
            "POST:/auth/verify-email/request": 3,
            "POST:/auth/refresh": 10,
            
            # General API
            "GET:/api/": 60,
            "POST:/api/": 30,
            "PUT:/api/": 30,
            "DELETE:/api/": 20,
        }
    
    async def check_endpoint_limit(
        self, 
        identifier: str, 
        method: str, 
        path: str,
        user_role: Optional[str] = None
    ) -> RateLimitResult:
        """Check rate limit for specific endpoint"""
        
        # Create endpoint key
        endpoint_key = f"{method}:{path}"
        
        # Get base limit for endpoint
        base_limit = self.endpoint_limits.get(endpoint_key, 60)  # Default 60/min
        
        # Adjust limit based on user role
        if user_role:
            role_multipliers = {
                "admin": 3.0,
                "manager": 2.0,
                "washer": 1.5,
                "client": 1.0
            }
            multiplier = role_multipliers.get(user_role.lower(), 1.0)
            limit = int(base_limit * multiplier)
        else:
            # Anonymous users get half the limit
            limit = base_limit // 2
        
        return await self.rate_limiter.check_rate_limit(
            identifier=identifier,
            limit=limit,
            window_seconds=60,  # 1 minute window
            category=f"endpoint:{endpoint_key}"
        )
    
    def configure_endpoint_limit(self, method: str, path: str, limit: int):
        """Configure custom limit for an endpoint"""
        endpoint_key = f"{method}:{path}"
        self.endpoint_limits[endpoint_key] = limit


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None
_endpoint_rate_limiter: Optional[EndpointRateLimiter] = None


def init_rate_limiter(redis_client=None, key_prefix: str = "rate_limit") -> RateLimiter:
    """Initialize global rate limiter"""
    global _rate_limiter, _endpoint_rate_limiter
    
    if redis_client:
        strategy = RedisRateLimitStrategy(redis_client)
        logger.info("Initialized Redis-based rate limiter")
    else:
        strategy = MemoryRateLimitStrategy()
        logger.warning("Initialized in-memory rate limiter (not recommended for production)")
    
    _rate_limiter = RateLimiter(strategy, key_prefix)
    _endpoint_rate_limiter = EndpointRateLimiter(_rate_limiter)
    
    return _rate_limiter


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    if _rate_limiter is None:
        raise RuntimeError("Rate limiter not initialized. Call init_rate_limiter() first.")
    return _rate_limiter


def get_endpoint_rate_limiter() -> EndpointRateLimiter:
    """Get global endpoint rate limiter instance"""
    if _endpoint_rate_limiter is None:
        raise RuntimeError("Endpoint rate limiter not initialized. Call init_rate_limiter() first.")
    return _endpoint_rate_limiter


# Convenience functions
async def check_rate_limit(identifier: str, limit: int, window_seconds: int, category: str = "default") -> RateLimitResult:
    """Convenience function to check rate limit"""
    limiter = get_rate_limiter()
    return await limiter.check_rate_limit(identifier, limit, window_seconds, category)


async def check_endpoint_rate_limit(identifier: str, method: str, path: str, user_role: Optional[str] = None) -> RateLimitResult:
    """Convenience function to check endpoint rate limit"""
    limiter = get_endpoint_rate_limiter()
    return await limiter.check_endpoint_limit(identifier, method, path, user_role)