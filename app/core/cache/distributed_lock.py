from typing import Optional
from contextlib import contextmanager
import uuid
import time

from app.core.cache.redis_client import redis_client


class DistributedLock:
    """Distributed lock implementation using Redis."""

    def __init__(
        self,
        key: str,
        timeout: int = 10,
        blocking: bool = True,
        blocking_timeout: int = 5,
    ):
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.blocking = blocking
        self.blocking_timeout = blocking_timeout
        self.token = str(uuid.uuid4())
        self.redis = redis_client.client

    def acquire(self) -> bool:
        """Acquire the lock."""
        if not self.redis:
            return True  # If Redis is not available, allow operation

        if self.blocking:
            start_time = time.time()
            while True:
                if self._try_acquire():
                    return True
                if time.time() - start_time >= self.blocking_timeout:
                    return False
                time.sleep(0.1)
        else:
            return self._try_acquire()

    def _try_acquire(self) -> bool:
        """Try to acquire the lock once."""
        if not self.redis:
            return True
        
        try:
            # SET NX EX - atomic operation
            result = self.redis.set(
                self.key,
                self.token,
                nx=True,
                ex=self.timeout,
            )
            return bool(result)
        except:
            return True  # Allow operation if Redis fails

    def release(self) -> bool:
        """Release the lock if we own it."""
        if not self.redis:
            return True

        try:
            # Use Lua script for atomic check-and-delete
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            result = self.redis.eval(lua_script, 1, self.key, self.token)
            return bool(result)
        except:
            return False

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(f"Could not acquire lock for {self.key}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


@contextmanager
def distributed_lock(
    key: str,
    timeout: int = 10,
    blocking: bool = True,
    blocking_timeout: int = 5,
):
    """Context manager for distributed locking."""
    lock = DistributedLock(key, timeout, blocking, blocking_timeout)
    try:
        if not lock.acquire():
            raise RuntimeError(f"Could not acquire lock for {key}")
        yield lock
    finally:
        lock.release()