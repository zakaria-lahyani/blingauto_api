"""
SQLAlchemy repository implementations for facilities feature.

Implements repository interfaces from ports layer using SQLAlchemy.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.entities import WashBay, MobileTeam, Location, VehicleSize, ResourceStatus
from ..ports.repositories import IWashBayRepository, IMobileTeamRepository
from .models import WashBayModel, MobileTeamModel
from app.core.errors import ValidationError


class SQLAlchemyWashBayRepository(IWashBayRepository):
    """
    SQLAlchemy implementation of wash bay repository.

    Converts between domain entities and database models.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def create(self, wash_bay: WashBay) -> WashBay:
        """Create a new wash bay in the database."""
        model = self._to_model(wash_bay)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, wash_bay_id: str) -> Optional[WashBay]:
        """Retrieve wash bay by ID."""
        stmt = select(WashBayModel).where(
            and_(
                WashBayModel.id == wash_bay_id,
                WashBayModel.deleted_at.is_(None)
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_bay_number(self, bay_number: str) -> Optional[WashBay]:
        """Retrieve wash bay by bay number."""
        stmt = select(WashBayModel).where(
            and_(
                WashBayModel.bay_number == bay_number,
                WashBayModel.deleted_at.is_(None)
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_all(
        self,
        status: Optional[ResourceStatus] = None,
        include_inactive: bool = False
    ) -> List[WashBay]:
        """List all wash bays with optional filtering."""
        conditions = []

        if not include_inactive:
            conditions.append(WashBayModel.deleted_at.is_(None))

        if status:
            conditions.append(WashBayModel.status == status.value)

        stmt = select(WashBayModel)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(WashBayModel.bay_number)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def update(self, wash_bay: WashBay) -> WashBay:
        """Update an existing wash bay."""
        stmt = select(WashBayModel).where(
            and_(
                WashBayModel.id == wash_bay.id,
                WashBayModel.deleted_at.is_(None)
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValidationError(
                message=f"Wash bay with ID '{wash_bay.id}' not found",
                code="WASH_BAY_NOT_FOUND"
            )

        # Update model fields
        model.bay_number = wash_bay.bay_number
        model.max_vehicle_size = wash_bay.max_vehicle_size.value
        model.equipment_types = wash_bay.equipment_types
        model.status = wash_bay.status.value
        model.updated_at = datetime.now(timezone.utc)

        if wash_bay.location:
            model.location_latitude = wash_bay.location.latitude
            model.location_longitude = wash_bay.location.longitude
        else:
            model.location_latitude = None
            model.location_longitude = None

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def delete(self, wash_bay_id: str) -> bool:
        """Soft delete a wash bay."""
        stmt = select(WashBayModel).where(
            and_(
                WashBayModel.id == wash_bay_id,
                WashBayModel.deleted_at.is_(None)
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        model.deleted_at = datetime.now(timezone.utc)
        model.status = ResourceStatus.INACTIVE.value
        await self._session.flush()
        return True

    async def count_by_status(self, status: ResourceStatus) -> int:
        """Count wash bays by status."""
        stmt = select(func.count(WashBayModel.id)).where(
            and_(
                WashBayModel.status == status.value,
                WashBayModel.deleted_at.is_(None)
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    def _to_domain(self, model: WashBayModel) -> WashBay:
        """Convert database model to domain entity."""
        location = None
        if model.location_latitude and model.location_longitude:
            location = Location(
                latitude=Decimal(str(model.location_latitude)),
                longitude=Decimal(str(model.location_longitude))
            )

        return WashBay(
            id=model.id,
            bay_number=model.bay_number,
            max_vehicle_size=VehicleSize(model.max_vehicle_size),
            equipment_types=model.equipment_types or [],
            status=ResourceStatus(model.status),
            location=location,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, entity: WashBay) -> WashBayModel:
        """Convert domain entity to database model."""
        model = WashBayModel(
            id=entity.id,
            bay_number=entity.bay_number,
            max_vehicle_size=entity.max_vehicle_size.value,
            equipment_types=entity.equipment_types,
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

        if entity.location:
            model.location_latitude = entity.location.latitude
            model.location_longitude = entity.location.longitude

        return model


class SQLAlchemyMobileTeamRepository(IMobileTeamRepository):
    """
    SQLAlchemy implementation of mobile team repository.

    Converts between domain entities and database models.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def create(self, mobile_team: MobileTeam) -> MobileTeam:
        """Create a new mobile team in the database."""
        model = self._to_model(mobile_team)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, team_id: str) -> Optional[MobileTeam]:
        """Retrieve mobile team by ID."""
        stmt = select(MobileTeamModel).where(
            and_(
                MobileTeamModel.id == team_id,
                MobileTeamModel.deleted_at.is_(None)
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_name(self, team_name: str) -> Optional[MobileTeam]:
        """Retrieve mobile team by name."""
        stmt = select(MobileTeamModel).where(
            and_(
                MobileTeamModel.team_name == team_name,
                MobileTeamModel.deleted_at.is_(None)
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_all(
        self,
        status: Optional[ResourceStatus] = None,
        include_inactive: bool = False
    ) -> List[MobileTeam]:
        """List all mobile teams with optional filtering."""
        conditions = []

        if not include_inactive:
            conditions.append(MobileTeamModel.deleted_at.is_(None))

        if status:
            conditions.append(MobileTeamModel.status == status.value)

        stmt = select(MobileTeamModel)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(MobileTeamModel.team_name)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def update(self, mobile_team: MobileTeam) -> MobileTeam:
        """Update an existing mobile team."""
        stmt = select(MobileTeamModel).where(
            and_(
                MobileTeamModel.id == mobile_team.id,
                MobileTeamModel.deleted_at.is_(None)
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValidationError(
                message=f"Mobile team with ID '{mobile_team.id}' not found",
                code="MOBILE_TEAM_NOT_FOUND"
            )

        # Update model fields
        model.team_name = mobile_team.team_name
        model.base_latitude = mobile_team.base_location.latitude
        model.base_longitude = mobile_team.base_location.longitude
        model.service_radius_km = mobile_team.service_radius_km
        model.daily_capacity = mobile_team.daily_capacity
        model.equipment_types = mobile_team.equipment_types
        model.status = mobile_team.status.value
        model.updated_at = datetime.now(timezone.utc)

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def delete(self, team_id: str) -> bool:
        """Soft delete a mobile team."""
        stmt = select(MobileTeamModel).where(
            and_(
                MobileTeamModel.id == team_id,
                MobileTeamModel.deleted_at.is_(None)
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        model.deleted_at = datetime.now(timezone.utc)
        model.status = ResourceStatus.INACTIVE.value
        await self._session.flush()
        return True

    async def count_by_status(self, status: ResourceStatus) -> int:
        """Count mobile teams by status."""
        stmt = select(func.count(MobileTeamModel.id)).where(
            and_(
                MobileTeamModel.status == status.value,
                MobileTeamModel.deleted_at.is_(None)
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def get_teams_within_radius(
        self,
        latitude: float,
        longitude: float,
        max_radius_km: float
    ) -> List[MobileTeam]:
        """
        Find mobile teams that can service a location.

        Implements RG-FAC-004: Service radius calculations.

        Note: This is a simplified implementation. For production,
        consider using PostGIS for accurate geospatial queries.
        """
        # Get all active teams
        stmt = select(MobileTeamModel).where(
            and_(
                MobileTeamModel.status == ResourceStatus.ACTIVE.value,
                MobileTeamModel.deleted_at.is_(None)
            )
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        # Filter by distance in Python (for simplicity)
        # In production, use PostGIS ST_Distance_Sphere for database-level filtering
        customer_location = Location(
            latitude=Decimal(str(latitude)),
            longitude=Decimal(str(longitude))
        )

        teams_within_radius = []
        for model in models:
            team = self._to_domain(model)
            if team.can_service_location(customer_location):
                teams_within_radius.append(team)

        return teams_within_radius

    def _to_domain(self, model: MobileTeamModel) -> MobileTeam:
        """Convert database model to domain entity."""
        base_location = Location(
            latitude=Decimal(str(model.base_latitude)),
            longitude=Decimal(str(model.base_longitude))
        )

        return MobileTeam(
            id=model.id,
            team_name=model.team_name,
            base_location=base_location,
            service_radius_km=Decimal(str(model.service_radius_km)),
            daily_capacity=model.daily_capacity,
            equipment_types=model.equipment_types or [],
            status=ResourceStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, entity: MobileTeam) -> MobileTeamModel:
        """Convert domain entity to database model."""
        return MobileTeamModel(
            id=entity.id,
            team_name=entity.team_name,
            base_latitude=entity.base_location.latitude,
            base_longitude=entity.base_location.longitude,
            service_radius_km=entity.service_radius_km,
            daily_capacity=entity.daily_capacity,
            equipment_types=entity.equipment_types,
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
