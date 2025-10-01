from typing import Dict, Any
from datetime import datetime
import psutil
from sqlalchemy import text
# Removed FastAPI dependency - this is core infrastructure only

from app.core.db import engine
from app.core.config import settings


class HealthChecker:
    """Health check utilities."""
    
    @staticmethod
    async def check_database() -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.fetchone()
            return {"status": "healthy", "latency_ms": 0}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    @staticmethod
    async def check_redis() -> Dict[str, Any]:
        """Check Redis connectivity."""
        if not settings.redis_url:
            return {"status": "not_configured"}

        try:
            from app.core.cache.redis_client import redis_client

            if redis_client.is_available():
                return {"status": "healthy"}
            else:
                return {"status": "unhealthy", "error": "Redis ping failed"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    @staticmethod
    async def check_system() -> Dict[str, Any]:
        """Check system resources."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "status": "healthy" if cpu_percent < 90 and memory.percent < 90 else "degraded"
            }
        except Exception as e:
            return {"status": "unknown", "error": str(e)}
    
    @staticmethod
    async def get_health_status() -> Dict[str, Any]:
        """Get overall health status."""
        database = await HealthChecker.check_database()
        redis = await HealthChecker.check_redis()
        system = await HealthChecker.check_system()
        
        # Determine overall status
        if database["status"] != "healthy":
            overall_status = "unhealthy"
        elif system.get("status") == "degraded":
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.app_version,
            "environment": settings.environment,
            "checks": {
                "database": database,
                "redis": redis,
                "system": system,
            }
        }
    
    @staticmethod
    async def get_readiness_status() -> Dict[str, Any]:
        """Get readiness status."""
        database = await HealthChecker.check_database()
        
        # Application is ready if database is healthy
        is_ready = database["status"] == "healthy"
        
        return {
            "ready": is_ready,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": database,
            }
        }


health_checker = HealthChecker()

# Health checker utility only - endpoints moved to interfaces/health.py