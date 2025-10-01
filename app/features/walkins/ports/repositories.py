"""Walk-in repository interfaces."""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Optional

from app.features.walkins.domain import (
    WalkInService,
    WalkInStatus,
    PaymentStatus,
)


class IWalkInRepository(ABC):
    """Interface for walk-in service repository."""

    @abstractmethod
    async def create(self, walkin: WalkInService) -> WalkInService:
        """Create a new walk-in service."""
        pass

    @abstractmethod
    async def get_by_id(self, walkin_id: str) -> Optional[WalkInService]:
        """Get walk-in service by ID."""
        pass

    @abstractmethod
    async def get_by_service_number(self, service_number: str) -> Optional[WalkInService]:
        """Get walk-in service by service number."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[WalkInStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        staff_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[WalkInService]:
        """List walk-in services with filters."""
        pass

    @abstractmethod
    async def update(self, walkin: WalkInService) -> WalkInService:
        """Update walk-in service."""
        pass

    @abstractmethod
    async def delete(self, walkin_id: str) -> bool:
        """Delete walk-in service."""
        pass

    @abstractmethod
    async def count(
        self,
        status: Optional[WalkInStatus] = None,
        staff_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """Count walk-in services with filters."""
        pass

    @abstractmethod
    async def get_daily_services(self, target_date: date) -> List[WalkInService]:
        """Get all services for a specific date."""
        pass

    @abstractmethod
    async def get_next_service_number(self, date_prefix: str) -> str:
        """Get next service number for the day."""
        pass
