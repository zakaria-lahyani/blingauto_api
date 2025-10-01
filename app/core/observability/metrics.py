from typing import Dict, Any
from datetime import datetime
import time
from functools import wraps
import logging
import asyncio

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Simple metrics collection."""
    
    def __init__(self):
        self._metrics = {
            "requests": {},
            "durations": {},
            "errors": {},
        }
        self._start_time = time.time()
    
    def record_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """Record a request metric."""
        key = f"{method}:{endpoint}:{status_code}"
        
        if key not in self._metrics["requests"]:
            self._metrics["requests"][key] = 0
        self._metrics["requests"][key] += 1
        
        if endpoint not in self._metrics["durations"]:
            self._metrics["durations"][endpoint] = []
        self._metrics["durations"][endpoint].append(duration)
        
        # Keep only last 100 durations per endpoint
        if len(self._metrics["durations"][endpoint]) > 100:
            self._metrics["durations"][endpoint] = self._metrics["durations"][endpoint][-100:]
    
    def record_error(self, error_type: str):
        """Record an error."""
        if error_type not in self._metrics["errors"]:
            self._metrics["errors"][error_type] = 0
        self._metrics["errors"][error_type] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        uptime = time.time() - self._start_time
        
        # Calculate average durations
        avg_durations = {}
        for endpoint, durations in self._metrics["durations"].items():
            if durations:
                avg_durations[endpoint] = {
                    "avg_ms": sum(durations) / len(durations) * 1000,
                    "min_ms": min(durations) * 1000,
                    "max_ms": max(durations) * 1000,
                    "count": len(durations),
                }
        
        return {
            "uptime_seconds": uptime,
            "requests": self._metrics["requests"],
            "durations": avg_durations,
            "errors": self._metrics["errors"],
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def reset(self):
        """Reset metrics."""
        self._metrics = {
            "requests": {},
            "durations": {},
            "errors": {},
        }


def track_time(name: str):
    """Decorator to track execution time."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                logger.debug(f"{name} took {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(f"{name} failed after {duration:.3f}s: {str(e)}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                logger.debug(f"{name} took {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(f"{name} failed after {duration:.3f}s: {str(e)}")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Singleton instance
metrics_collector = MetricsCollector()