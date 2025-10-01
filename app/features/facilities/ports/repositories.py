"""
Facilities repository interfaces (ports).

Defines contracts for data persistence following clean architecture.
Domain layer depends on these interfaces, adapters implement them.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..domain.entities import WashBay, MobileTeam, ResourceStatus


class IWashBayRepository(ABC):
    """
    Repository interface for WashBay entity.

    Implements persistence for RG-FAC-001: Wash bay configuration.
    """

    @abstractmethod
    async def create(self, wash_bay: WashBay) -> WashBay:
        """
        Create a new wash bay.

        Args:
            wash_bay: WashBay entity to persist

        Returns:
            Created WashBay with generated ID

        Raises:
            ValidationError: If bay_number already exists
        """
        pass

    @abstractmethod
    async def get_by_id(self, wash_bay_id: str) -> Optional[WashBay]:
        """
        Retrieve wash bay by ID.

        Args:
            wash_bay_id: UUID of the wash bay

        Returns:
            WashBay if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_bay_number(self, bay_number: str) -> Optional[WashBay]:
        """
        Retrieve wash bay by bay number.

        Args:
            bay_number: Unique bay number

        Returns:
            WashBay if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_all(
        self,
        status: Optional[ResourceStatus] = None,
        include_inactive: bool = False
    ) -> List[WashBay]:
        """
        List all wash bays with optional filtering.

        Args:
            status: Filter by status (ACTIVE, INACTIVE, MAINTENANCE)
            include_inactive: Include inactive bays in results

        Returns:
            List of WashBay entities
        """
        pass

    @abstractmethod
    async def update(self, wash_bay: WashBay) -> WashBay:
        """
        Update an existing wash bay.

        Args:
            wash_bay: WashBay entity with updated values

        Returns:
            Updated WashBay entity

        Raises:
            NotFoundError: If wash bay doesn't exist
        """
        pass

    @abstractmethod
    async def delete(self, wash_bay_id: str) -> bool:
        """
        Soft delete a wash bay.

        Args:
            wash_bay_id: UUID of the wash bay

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def count_by_status(self, status: ResourceStatus) -> int:
        """
        Count wash bays by status.

        Args:
            status: ResourceStatus to count

        Returns:
            Number of wash bays with given status
        """
        pass


class IMobileTeamRepository(ABC):
    """
    Repository interface for MobileTeam entity.

    Implements persistence for RG-FAC-003: Mobile team configuration.
    """

    @abstractmethod
    async def create(self, mobile_team: MobileTeam) -> MobileTeam:
        """
        Create a new mobile team.

        Args:
            mobile_team: MobileTeam entity to persist

        Returns:
            Created MobileTeam with generated ID

        Raises:
            ValidationError: If team_name already exists
        """
        pass

    @abstractmethod
    async def get_by_id(self, team_id: str) -> Optional[MobileTeam]:
        """
        Retrieve mobile team by ID.

        Args:
            team_id: UUID of the mobile team

        Returns:
            MobileTeam if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_name(self, team_name: str) -> Optional[MobileTeam]:
        """
        Retrieve mobile team by name.

        Args:
            team_name: Unique team name

        Returns:
            MobileTeam if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_all(
        self,
        status: Optional[ResourceStatus] = None,
        include_inactive: bool = False
    ) -> List[MobileTeam]:
        """
        List all mobile teams with optional filtering.

        Args:
            status: Filter by status (ACTIVE, INACTIVE, MAINTENANCE)
            include_inactive: Include inactive teams in results

        Returns:
            List of MobileTeam entities
        """
        pass

    @abstractmethod
    async def update(self, mobile_team: MobileTeam) -> MobileTeam:
        """
        Update an existing mobile team.

        Args:
            mobile_team: MobileTeam entity with updated values

        Returns:
            Updated MobileTeam entity

        Raises:
            NotFoundError: If mobile team doesn't exist
        """
        pass

    @abstractmethod
    async def delete(self, team_id: str) -> bool:
        """
        Soft delete a mobile team.

        Args:
            team_id: UUID of the mobile team

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def count_by_status(self, status: ResourceStatus) -> int:
        """
        Count mobile teams by status.

        Args:
            status: ResourceStatus to count

        Returns:
            Number of mobile teams with given status
        """
        pass

    @abstractmethod
    async def get_teams_within_radius(
        self,
        latitude: float,
        longitude: float,
        max_radius_km: float
    ) -> List[MobileTeam]:
        """
        Find mobile teams that can service a location.

        Implements RG-FAC-004: Service radius calculations.

        Args:
            latitude: Customer latitude
            longitude: Customer longitude
            max_radius_km: Maximum distance to search

        Returns:
            List of mobile teams within service range
        """
        pass
