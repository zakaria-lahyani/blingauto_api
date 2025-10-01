"""
Scheduling ports for repositories.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ..domain.entities import WashBay, MobileTeam, TimeSlot, SchedulingConstraints


class IWashBayRepository(ABC):
    """Port for wash bay repository."""
    
    @abstractmethod
    async def get_by_id(self, bay_id: str) -> Optional[WashBay]:
        """Get wash bay by ID."""
        pass
    
    @abstractmethod
    async def get_all_active(self) -> List[WashBay]:
        """Get all active wash bays."""
        pass
    
    @abstractmethod
    async def create(self, wash_bay: WashBay) -> WashBay:
        """Create new wash bay."""
        pass
    
    @abstractmethod
    async def update(self, wash_bay: WashBay) -> WashBay:
        """Update wash bay."""
        pass
    
    @abstractmethod
    async def delete(self, bay_id: str) -> bool:
        """Delete wash bay."""
        pass


class IMobileTeamRepository(ABC):
    """Port for mobile team repository."""
    
    @abstractmethod
    async def get_by_id(self, team_id: str) -> Optional[MobileTeam]:
        """Get mobile team by ID."""
        pass
    
    @abstractmethod
    async def get_all_active(self) -> List[MobileTeam]:
        """Get all active mobile teams."""
        pass
    
    @abstractmethod
    async def create(self, mobile_team: MobileTeam) -> MobileTeam:
        """Create new mobile team."""
        pass
    
    @abstractmethod
    async def update(self, mobile_team: MobileTeam) -> MobileTeam:
        """Update mobile team."""
        pass
    
    @abstractmethod
    async def delete(self, team_id: str) -> bool:
        """Delete mobile team."""
        pass


class ITimeSlotRepository(ABC):
    """Port for time slot repository."""
    
    @abstractmethod
    async def get_bookings_for_resource(
        self,
        resource_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[TimeSlot]:
        """Get all bookings for a resource in a date range."""
        pass
    
    @abstractmethod
    async def get_bookings_for_date(
        self,
        date: datetime
    ) -> List[TimeSlot]:
        """Get all bookings for a specific date."""
        pass
    
    @abstractmethod
    async def create_booking(self, time_slot: TimeSlot) -> TimeSlot:
        """Create a new booking slot."""
        pass
    
    @abstractmethod
    async def update_booking(self, time_slot: TimeSlot) -> TimeSlot:
        """Update booking slot."""
        pass
    
    @abstractmethod
    async def cancel_booking(self, booking_id: str) -> bool:
        """Cancel a booking."""
        pass


class ISchedulingConstraintsRepository(ABC):
    """Port for scheduling constraints repository."""
    
    @abstractmethod
    async def get_current_constraints(self) -> SchedulingConstraints:
        """Get current scheduling constraints."""
        pass
    
    @abstractmethod
    async def update_constraints(self, constraints: SchedulingConstraints) -> SchedulingConstraints:
        """Update scheduling constraints."""
        pass