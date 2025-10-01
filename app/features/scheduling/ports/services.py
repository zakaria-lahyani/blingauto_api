"""
Scheduling ports for external services.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any

from ..domain.entities import Location


class IDistanceCalculationService(ABC):
    """Port for distance calculation service."""
    
    @abstractmethod
    async def calculate_distance(
        self,
        origin: Location,
        destination: Location
    ) -> Decimal:
        """Calculate distance between two locations in kilometers."""
        pass
    
    @abstractmethod
    async def calculate_travel_time(
        self,
        origin: Location,
        destination: Location
    ) -> int:
        """Calculate travel time between locations in minutes."""
        pass


class INotificationService(ABC):
    """Port for notification service."""
    
    @abstractmethod
    async def notify_booking_scheduled(
        self,
        customer_id: str,
        booking_details: Dict[str, Any]
    ) -> bool:
        """Notify customer of scheduled booking."""
        pass
    
    @abstractmethod
    async def notify_booking_cancelled(
        self,
        customer_id: str,
        booking_id: str,
        reason: str
    ) -> bool:
        """Notify customer of cancelled booking."""
        pass
    
    @abstractmethod
    async def notify_staff_assignment(
        self,
        staff_id: str,
        booking_details: Dict[str, Any]
    ) -> bool:
        """Notify staff of booking assignment."""
        pass


class IOptimizationService(ABC):
    """Port for route and schedule optimization."""
    
    @abstractmethod
    async def optimize_daily_routes(
        self,
        team_id: str,
        date: datetime,
        bookings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Optimize route for mobile team's daily bookings."""
        pass
    
    @abstractmethod
    async def suggest_optimal_time_slots(
        self,
        resource_id: str,
        preferred_time: datetime,
        duration_minutes: int,
        num_suggestions: int = 5
    ) -> List[datetime]:
        """Suggest optimal time slots based on various factors."""
        pass