"""Capacity management service port."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any


class IWashBayCapacityService(ABC):
    """Interface for wash bay capacity management."""

    @abstractmethod
    async def find_available_wash_bay(
        self,
        scheduled_at: datetime,
        duration_minutes: int,
        vehicle_size: str
    ) -> Optional[str]:
        """
        Find an available wash bay for the given time slot and vehicle size.

        Args:
            scheduled_at: Start time of the booking
            duration_minutes: Duration of the service
            vehicle_size: Size of the vehicle (compact, standard, large, oversized)

        Returns:
            wash_bay_id if available, None otherwise
        """
        pass

    @abstractmethod
    async def get_available_capacity(
        self,
        scheduled_at: datetime,
        duration_minutes: int
    ) -> int:
        """
        Get the number of available wash bays for the given time slot.

        Args:
            scheduled_at: Start time to check
            duration_minutes: Duration of the service

        Returns:
            Number of available wash bays
        """
        pass

    @abstractmethod
    async def check_wash_bay_availability(
        self,
        wash_bay_id: str,
        scheduled_at: datetime,
        duration_minutes: int,
        exclude_booking_id: Optional[str] = None
    ) -> bool:
        """
        Check if a specific wash bay is available for the given time slot.

        Args:
            wash_bay_id: ID of the wash bay to check
            scheduled_at: Start time of the booking
            duration_minutes: Duration of the service
            exclude_booking_id: Optional booking ID to exclude from check (for rescheduling)

        Returns:
            True if available, False otherwise
        """
        pass

    @abstractmethod
    async def get_time_slot_capacity_info(
        self,
        scheduled_at: datetime,
        duration_minutes: int
    ) -> Dict[str, Any]:
        """
        Get detailed capacity information for a time slot.

        Args:
            scheduled_at: Start time to check
            duration_minutes: Duration of the service

        Returns:
            Dictionary with capacity info (total_bays, available_bays, booked_bays, bay_details)
        """
        pass

    @abstractmethod
    async def get_available_time_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int,
        slot_interval_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get all available time slots within a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            duration_minutes: Duration needed
            slot_interval_minutes: Interval between slots (default 30 minutes)

        Returns:
            List of available time slots with capacity info
        """
        pass
