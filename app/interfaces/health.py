"""
Health check endpoints for the application.
According to TO_REFACTORE_ARCHITECTURE.md line 64.
"""

from datetime import datetime
from fastapi import APIRouter
from typing import Dict, Any

from app.core.observability.health import health_checker

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    Returns overall system health status.
    """
    try:
        return await health_checker.get_health_status()
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint.
    Returns whether the application is ready to serve traffic.
    """
    try:
        return await health_checker.get_readiness_status()
    except Exception as e:
        return {
            "ready": False,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }