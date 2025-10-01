from typing import Optional, Tuple
from datetime import datetime, timedelta

from app.core.cache.redis_client import redis_client
from app.core.config import settings


class RateLimiter:
    """Rate limiter using Redis for distributed rate limiting."""

    def __init__(self):
        self.redis = redis_client.client

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, Optional[int]]:
        """
        Check if request is within rate limit.
        
        Returns:
            (allowed, remaining_requests, reset_time_seconds)
        """
        if not settings.rate_limit_enabled or not self.redis:
            return True, max_requests, None

        try:
            # Use sliding window with Redis
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=window_seconds)
            
            # Clean old entries
            self.redis.zremrangebyscore(
                key,
                0,
                window_start.timestamp(),
            )
            
            # Count requests in window
            request_count = self.redis.zcard(key)
            
            if request_count < max_requests:
                # Add current request
                self.redis.zadd(key, {str(now.timestamp()): now.timestamp()})
                self.redis.expire(key, window_seconds)
                
                remaining = max_requests - request_count - 1
                return True, remaining, None
            else:
                # Get oldest request time for reset calculation
                oldest = self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    reset_time = int(oldest[0][1]) + window_seconds
                else:
                    reset_time = int(now.timestamp()) + window_seconds
                
                return False, 0, reset_time
        except:
            # Allow request if Redis fails
            return True, max_requests, None

    def check_ip_rate_limit(self, ip: str) -> Tuple[bool, int, Optional[int]]:
        """Check rate limit for IP address."""
        key = f"rate_limit:ip:{ip}"
        return self.check_rate_limit(
            key,
            settings.rate_limit_requests_per_minute,
            60,
        )

    def check_user_rate_limit(self, user_id: str) -> Tuple[bool, int, Optional[int]]:
        """Check rate limit for user."""
        key = f"rate_limit:user:{user_id}"
        return self.check_rate_limit(
            key,
            settings.rate_limit_requests_per_minute * 2,  # Higher limit for authenticated users
            60,
        )

    def check_endpoint_rate_limit(
        self,
        endpoint: str,
        identifier: str,
        max_requests: int = 10,
        window_seconds: int = 60,
    ) -> Tuple[bool, int, Optional[int]]:
        """Check rate limit for specific endpoint."""
        key = f"rate_limit:endpoint:{endpoint}:{identifier}"
        return self.check_rate_limit(key, max_requests, window_seconds)


# Singleton instance
rate_limiter = RateLimiter()