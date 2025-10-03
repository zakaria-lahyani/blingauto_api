# Cache Incident Analysis & Production-Ready Solutions

## Root Cause Analysis

### What Happened?

1. **Incorrect Dataclass Serialization (Primary Issue)**
   - **Location**: `app/features/auth/use_cases/manage_users.py:94`
   - **Problem**: Used `response.__dict__` to serialize a dataclass for caching
   - **Why it failed**: Python dataclasses' `__dict__` attribute doesn't always behave predictably, especially with default values and optional fields. The cached data was incomplete/malformed.
   - **Impact**: When cached data was retrieved and used to reconstruct `UserResponse(**cached_user)`, it was missing 7 required fields.

2. **No Cache Versioning**
   - **Problem**: After fixing the serialization bug, old corrupted data remained in Redis
   - **Impact**: The fix didn't take effect until cache was manually flushed
   - **Why it matters**: In production, you can't easily flush all cache without downtime

3. **Type Confusion (Secondary Issue)**
   - **Location**: `app/features/auth/api/router.py:382`
   - **Problem**: Tried to call `.value` on `current_user.role` which is already a string
   - **Root cause**: Inconsistent type handling - `AuthenticatedUser.role` is `str`, but code assumed it was an enum

### Why It Happened

1. **Lack of Type Safety**
   - Using `Dict[str, Any]` for cache data loses type information
   - No validation when deserializing from cache

2. **Missing Cache Invalidation Strategy**
   - No version tagging on cached data
   - No automatic invalidation when schema changes
   - No graceful degradation when cache read fails

3. **Silent Failures**
   - Cache operations catch all exceptions and return None
   - Errors are logged but don't propagate
   - Application continues with corrupt data

4. **Development-Production Parity**
   - Development uses same cache as before restart
   - No migration strategy for cache schema changes

## Production-Ready Solutions

### 1. Add Cache Versioning (CRITICAL)

**Why**: Prevents stale cache issues when code changes

```python
# Add to CacheServiceAdapter
CACHE_VERSION = "v2"  # Increment when UserResponse schema changes

async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
    try:
        import json
        key = f"user:{CACHE_VERSION}:{user_id}"  # Version in key
        data = self.redis.get(key)
        if data:
            cached = json.loads(data) if isinstance(data, (str, bytes)) else data
            # Validate cache structure
            required_fields = ['id', 'email', 'first_name', 'last_name', 'role',
                             'status', 'phone_number', 'email_verified',
                             'created_at', 'last_login_at']
            if all(field in cached for field in required_fields):
                return cached
            else:
                logger.warning(f"Invalid cache structure for user {user_id}, missing fields")
                self.redis.delete(key)  # Remove invalid cache
                return None
        return None
    except Exception as e:
        logger.error(f"Failed to get user from cache: {str(e)}")
        return None

async def set_user(self, user_id: str, user_data: Dict[str, Any], ttl: int = 300) -> bool:
    try:
        key = f"user:{CACHE_VERSION}:{user_id}"  # Version in key
        return self.redis.set(key, user_data, ttl=ttl)
    except Exception as e:
        logger.error(f"Failed to set user in cache: {str(e)}")
        return False
```

### 2. Implement Graceful Cache Degradation (HIGH PRIORITY)

**Why**: Application should work even when cache fails

```python
# In manage_users.py
async def execute(self, request: GetUserRequest) -> UserResponse:
    """Get user by ID with caching and graceful degradation."""

    # Try cache first (but don't fail if it's broken)
    try:
        cached_user = await self.cache_service.get_user(request.user_id)
        if cached_user:
            # Validate before using
            try:
                return UserResponse(**cached_user)
            except TypeError as e:
                # Cache data is corrupted, log and continue to DB
                logger.warning(
                    f"Corrupted cache data for user {request.user_id}: {e}. "
                    f"Fetching from database instead."
                )
                # Invalidate bad cache
                await self.cache_service.delete_user(request.user_id)
    except Exception as e:
        logger.error(f"Cache read error for user {request.user_id}: {e}")

    # Get from repository (always works)
    user = await self.user_repository.get_by_id(request.user_id)
    if not user:
        raise NotFoundError("User", request.user_id)

    response = UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        role=user.role.value,
        status=user.status.value,
        phone_number=user.phone_number,
        email_verified=user.email_verified,
        created_at=user.created_at.isoformat(),
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
    )

    # Try to cache (but don't fail if caching fails)
    try:
        await self.cache_service.set_user(
            user_id=user.id,
            user_data=asdict(response),
            ttl=300,
        )
    except Exception as e:
        logger.error(f"Failed to cache user {user.id}: {e}")

    return response
```

### 3. Add Cache Warming Strategy (MEDIUM PRIORITY)

**Why**: Prevents cache stampede after deployments

```python
# Create app/core/cache/warming.py
from typing import List
import asyncio
import logging

logger = logging.getLogger(__name__)

class CacheWarmer:
    """Warm cache with frequently accessed data after deployment."""

    async def warm_user_cache(self, user_ids: List[str]):
        """Pre-populate cache with user data."""
        from app.core.db import AsyncSessionLocal
        from app.features.auth.adapters.repositories import UserRepository
        from app.features.auth.adapters.services import CacheServiceAdapter
        from app.features.auth.use_cases.manage_users import GetUserUseCase, GetUserRequest

        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            cache_service = CacheServiceAdapter()
            use_case = GetUserUseCase(user_repo, cache_service)

            logger.info(f"Warming cache for {len(user_ids)} users...")

            tasks = []
            for user_id in user_ids:
                tasks.append(use_case.execute(GetUserRequest(user_id=user_id)))

            # Execute in parallel with limit
            chunk_size = 10
            for i in range(0, len(tasks), chunk_size):
                chunk = tasks[i:i + chunk_size]
                try:
                    await asyncio.gather(*chunk, return_exceptions=True)
                except Exception as e:
                    logger.error(f"Error warming cache chunk: {e}")

            logger.info("Cache warming completed")

    async def warm_on_startup(self):
        """Warm cache on application startup."""
        # Get most active users from last 24h
        from app.core.db import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                "SELECT id FROM users WHERE last_login_at > NOW() - INTERVAL '24 hours' LIMIT 100"
            )
            user_ids = [row[0] for row in result]

            if user_ids:
                await self.warm_user_cache(user_ids)

# Add to interfaces/http_api.py startup event
@app.on_event("startup")
async def warm_cache():
    """Warm cache on startup."""
    try:
        from app.core.cache.warming import CacheWarmer
        warmer = CacheWarmer()
        asyncio.create_task(warmer.warm_on_startup())
    except Exception as e:
        logger.error(f"Failed to warm cache: {e}")
```

### 4. Add Cache Monitoring & Metrics (MEDIUM PRIORITY)

**Why**: Detect cache issues before they impact users

```python
# Add to CacheServiceAdapter
from prometheus_client import Counter, Histogram
import time

# Metrics
cache_hits = Counter('cache_hits_total', 'Number of cache hits', ['cache_type'])
cache_misses = Counter('cache_misses_total', 'Number of cache misses', ['cache_type'])
cache_errors = Counter('cache_errors_total', 'Number of cache errors', ['cache_type', 'operation'])
cache_latency = Histogram('cache_operation_seconds', 'Cache operation latency', ['operation'])

async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
    start_time = time.time()
    try:
        # ... existing code ...
        if data:
            cache_hits.labels(cache_type='user').inc()
            return data
        cache_misses.labels(cache_type='user').inc()
        return None
    except Exception as e:
        cache_errors.labels(cache_type='user', operation='get').inc()
        logger.error(f"Failed to get user from cache: {str(e)}")
        return None
    finally:
        cache_latency.labels(operation='get_user').observe(time.time() - start_time)
```

### 5. Implement Cache Invalidation Patterns (HIGH PRIORITY)

**Why**: Ensure cache stays in sync with database

```python
# Pattern 1: Invalidate on write operations
# In UpdateUserRoleUseCase
async def execute(self, request: UpdateUserRoleRequest) -> UserResponse:
    # ... update user ...

    # Invalidate ALL related caches
    await self.cache_service.delete_user(user.id)
    # Also invalidate list caches that might include this user
    await self._invalidate_user_lists()

    return response

async def _invalidate_user_lists(self):
    """Invalidate all user list caches."""
    # This is expensive but safe - could use cache tagging instead
    pattern = "user:list:*"
    for key in self.cache_service.redis.scan_iter(match=pattern):
        self.cache_service.redis.delete(key)

# Pattern 2: Cache aside with write-through
async def update_user_cache(self, user_id: str):
    """Write-through: Update DB then immediately update cache."""
    # After DB update
    fresh_data = await self.user_repository.get_by_id(user_id)
    if fresh_data:
        response = self._build_response(fresh_data)
        await self.cache_service.set_user(user_id, asdict(response))
```

### 6. Add Health Checks for Cache (HIGH PRIORITY)

```python
# Add to app/interfaces/http_api.py health endpoint
@router.get("/health")
async def health_check():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "cache_integrity": await check_cache_integrity(),  # NEW
    }

    overall_healthy = all(check["status"] == "healthy" for check in checks.values())

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "checks": checks,
        ...
    }

async def check_cache_integrity():
    """Check if cache is working and data is valid."""
    try:
        from app.core.cache import redis_client

        # Test write
        test_key = "health:check:cache"
        test_data = {"test": "data", "timestamp": time.time()}
        redis_client.set(test_key, test_data, ttl=10)

        # Test read
        retrieved = redis_client.get(test_key)
        if retrieved != test_data:
            return {"status": "unhealthy", "message": "Cache data integrity check failed"}

        # Cleanup
        redis_client.delete(test_key)

        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}
```

### 7. Add Circuit Breaker for Cache (OPTIONAL - Advanced)

**Why**: Prevent cascading failures when cache is slow/down

```python
# Install: pip install pybreaker

from pybreaker import CircuitBreaker

cache_breaker = CircuitBreaker(
    fail_max=5,  # Open after 5 failures
    timeout_duration=60,  # Stay open for 60 seconds
    name='redis_cache'
)

@cache_breaker
async def get_user_cached(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user with circuit breaker protection."""
    return await cache_service.get_user(user_id)

# Usage
try:
    cached = await get_user_cached(user_id)
except CircuitBreakerError:
    logger.warning("Cache circuit breaker is open, skipping cache")
    cached = None  # Fall back to DB
```

## Deployment Checklist

### Before Deploying Cache Changes

- [ ] Increment `CACHE_VERSION` constant
- [ ] Test cache invalidation in staging
- [ ] Review all cache keys for version prefix
- [ ] Verify graceful degradation works (disable Redis and test)
- [ ] Add monitoring alerts for cache hit rate drop
- [ ] Document new cache keys in runbook

### During Deployment

- [ ] Deploy code with new cache version
- [ ] Monitor cache miss rate (should spike then normalize)
- [ ] Monitor error logs for cache issues
- [ ] Check cache warming task runs successfully

### After Deployment

- [ ] Verify old cache keys expire naturally (check Redis key count)
- [ ] Monitor cache hit rate returns to normal (may take 5-10 minutes)
- [ ] Clean up old cache keys manually if needed (optional):
  ```bash
  # For old version keys only
  docker exec blingauto-redis redis-cli -a "$REDIS_PASSWORD" --scan --pattern "user:v1:*" | \
    xargs docker exec blingauto-redis redis-cli -a "$REDIS_PASSWORD" DEL
  ```

## Testing Strategy

### Unit Tests

```python
# tests/test_cache_versioning.py
import pytest
from app.features.auth.use_cases.manage_users import GetUserUseCase

async def test_cache_handles_corrupt_data():
    """Test that corrupt cache data doesn't crash the app."""
    # Setup: Put bad data in cache
    await cache_service.redis.set("user:v2:test-id", "{invalid json")

    # Execute: Should handle gracefully
    result = await use_case.execute(GetUserRequest(user_id="test-id"))

    # Assert: Falls back to DB
    assert result is not None
    assert result.id == "test-id"

async def test_cache_version_isolation():
    """Test that different cache versions don't interfere."""
    # Setup: Put data in v1
    await redis.set("user:v1:test-id", old_format_data)

    # Execute: Get with v2
    result = await get_user_v2("test-id")

    # Assert: Doesn't use v1 data
    assert result is None or result uses v2 format
```

### Integration Tests

```python
async def test_cache_invalidation_on_update():
    """Test that updating user invalidates cache."""
    # Get user (caches it)
    user1 = await get_user_use_case.execute(GetUserRequest(user_id=user_id))

    # Update user role
    await update_role_use_case.execute(UpdateUserRoleRequest(...))

    # Get user again (should be fresh from DB, not cache)
    user2 = await get_user_use_case.execute(GetUserRequest(user_id=user_id))

    assert user2.role != user1.role
```

## Monitoring & Alerts

### Key Metrics to Track

1. **Cache Hit Rate**: Should be > 80% in steady state
2. **Cache Error Rate**: Should be < 0.1%
3. **Cache Latency**: p95 should be < 10ms
4. **Cache Size**: Monitor Redis memory usage

### Recommended Alerts

```yaml
# Prometheus alerts
- alert: CacheHitRateLow
  expr: rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) < 0.5
  for: 10m
  annotations:
    summary: "Cache hit rate is low (< 50%)"
    description: "This might indicate cache is not working or was recently flushed"

- alert: CacheErrorRateHigh
  expr: rate(cache_errors_total[5m]) > 10
  for: 5m
  annotations:
    summary: "High cache error rate"
    description: "Redis might be down or having issues"
```

## Long-term Improvements

1. **Use Pydantic for Cache Validation**: Serialize/deserialize through Pydantic models
2. **Implement Cache Tagging**: Tag cache entries with related entities for easier invalidation
3. **Consider Cache-Aside Pattern Library**: Use libraries like `aiocache` or `cachetools`
4. **Multi-level Caching**: Add in-memory L1 cache + Redis L2 cache
5. **Implement Distributed Cache Invalidation**: For multi-instance deployments

## Summary

The incident occurred due to:
1. ✅ **FIXED**: Improper dataclass serialization (`__dict__` → `asdict()`)
2. ✅ **FIXED**: Type confusion with role enum
3. ⚠️ **NEEDS FIX**: No cache versioning (critical for production)
4. ⚠️ **NEEDS FIX**: No graceful degradation (high priority)
5. ⚠️ **NEEDS FIX**: No cache monitoring (medium priority)

**Immediate actions for production readiness:**
1. Implement cache versioning (CRITICAL)
2. Add graceful degradation (HIGH)
3. Add cache integrity checks to health endpoint (HIGH)
4. Set up monitoring and alerts (MEDIUM)
