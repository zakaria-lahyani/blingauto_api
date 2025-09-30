"""
Scheduling API Module
Exports all scheduling-related routers for FastAPI integration.
"""

from .management_router import router as management_router
from .smart_booking_router import router as smart_booking_router
from .advanced_features_router import router as advanced_features_router

__all__ = [
    "management_router",
    "smart_booking_router", 
    "advanced_features_router"
]