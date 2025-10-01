"""Wash bay capacity management service implementation."""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.features.bookings.ports.capacity_service import IWashBayCapacityService


class WashBayCapacityService(IWashBayCapacityService):
    """
    Implementation of wash bay capacity management.

    Uses raw SQL queries to avoid cross-feature model imports.
    Queries wash_bays and bookings tables directly.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_available_wash_bay(
        self,
        scheduled_at: datetime,
        duration_minutes: int,
        vehicle_size: str
    ) -> Optional[str]:
        """
        Find an available wash bay for the given time slot and vehicle size.

        Algorithm:
        1. Get all active wash bays that can accommodate the vehicle size
        2. Check which ones don't have conflicting bookings
        3. Return the first available one
        """
        # Define vehicle size hierarchy: compact < standard < large < oversized
        size_hierarchy = {
            "compact": ["compact", "standard", "large", "oversized"],
            "standard": ["standard", "large", "oversized"],
            "large": ["large", "oversized"],
            "oversized": ["oversized"]
        }

        compatible_sizes = size_hierarchy.get(vehicle_size, ["oversized"])

        # Get all active wash bays that can accommodate the vehicle
        query = text("""
            SELECT id, bay_number, max_vehicle_size
            FROM wash_bays
            WHERE status = 'active'
              AND deleted_at IS NULL
              AND max_vehicle_size = ANY(:compatible_sizes)
            ORDER BY bay_number
        """)

        result = await self._session.execute(
            query,
            {"compatible_sizes": compatible_sizes}
        )
        wash_bays = result.fetchall()

        # Check each wash bay for availability
        for bay in wash_bays:
            is_available = await self.check_wash_bay_availability(
                bay.id,
                scheduled_at,
                duration_minutes
            )
            if is_available:
                return bay.id

        return None

    async def get_available_capacity(
        self,
        scheduled_at: datetime,
        duration_minutes: int
    ) -> int:
        """Get the number of available wash bays for the given time slot."""
        # Get all active wash bays
        query = text("""
            SELECT id
            FROM wash_bays
            WHERE status = 'active'
              AND deleted_at IS NULL
        """)

        result = await self._session.execute(query)
        wash_bays = result.fetchall()

        # Count available bays
        available_count = 0
        for bay in wash_bays:
            is_available = await self.check_wash_bay_availability(
                bay.id,
                scheduled_at,
                duration_minutes
            )
            if is_available:
                available_count += 1

        return available_count

    async def check_wash_bay_availability(
        self,
        wash_bay_id: str,
        scheduled_at: datetime,
        duration_minutes: int,
        exclude_booking_id: Optional[str] = None
    ) -> bool:
        """
        Check if a specific wash bay is available for the given time slot.

        A bay is unavailable if there's any booking that overlaps with the requested time.
        Overlap logic: (start1 < end2) AND (end1 > start2)
        """
        end_time = scheduled_at + timedelta(minutes=duration_minutes)

        # Build query to find conflicting bookings
        # We fetch bookings in a reasonable time window and check overlap in Python
        query = text("""
            SELECT id, scheduled_at, estimated_duration_minutes
            FROM bookings
            WHERE wash_bay_id = :wash_bay_id
              AND status IN ('pending', 'confirmed', 'in_progress')
              AND scheduled_at >= :min_time
              AND scheduled_at <= :max_time
              AND (:exclude_id IS NULL OR id != :exclude_id)
        """)

        result = await self._session.execute(
            query,
            {
                "wash_bay_id": wash_bay_id,
                "min_time": scheduled_at - timedelta(hours=24),
                "max_time": end_time + timedelta(hours=24),
                "exclude_id": exclude_booking_id
            }
        )
        bookings = result.fetchall()

        # Check for actual time overlap
        for booking in bookings:
            booking_end = booking.scheduled_at + timedelta(minutes=booking.estimated_duration_minutes)
            # Overlap check: (start1 < end2) AND (end1 > start2)
            if booking.scheduled_at < end_time and booking_end > scheduled_at:
                return False

        return True

    async def get_time_slot_capacity_info(
        self,
        scheduled_at: datetime,
        duration_minutes: int
    ) -> Dict[str, Any]:
        """Get detailed capacity information for a time slot."""
        # Get all active wash bays
        query = text("""
            SELECT id, bay_number, max_vehicle_size
            FROM wash_bays
            WHERE status = 'active'
              AND deleted_at IS NULL
            ORDER BY bay_number
        """)

        result = await self._session.execute(query)
        wash_bays = result.fetchall()

        total_bays = len(wash_bays)
        available_bays = 0
        bay_details = []

        for bay in wash_bays:
            is_available = await self.check_wash_bay_availability(
                bay.id,
                scheduled_at,
                duration_minutes
            )

            if is_available:
                available_bays += 1

            bay_details.append({
                "bay_id": bay.id,
                "bay_number": bay.bay_number,
                "max_vehicle_size": bay.max_vehicle_size,
                "is_available": is_available
            })

        return {
            "scheduled_at": scheduled_at.isoformat(),
            "duration_minutes": duration_minutes,
            "total_bays": total_bays,
            "available_bays": available_bays,
            "booked_bays": total_bays - available_bays,
            "utilization_percent": round((total_bays - available_bays) / total_bays * 100, 2) if total_bays > 0 else 0,
            "bay_details": bay_details
        }

    async def get_available_time_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int,
        slot_interval_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """Get all available time slots within a date range."""
        time_slots = []
        current_time = start_date

        while current_time <= end_date:
            capacity = await self.get_available_capacity(current_time, duration_minutes)

            if capacity > 0:
                time_slots.append({
                    "start_time": current_time.isoformat(),
                    "end_time": (current_time + timedelta(minutes=duration_minutes)).isoformat(),
                    "available_capacity": capacity,
                    "duration_minutes": duration_minutes
                })

            current_time += timedelta(minutes=slot_interval_minutes)

        return time_slots
