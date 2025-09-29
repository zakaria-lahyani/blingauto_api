"""
Vehicle repositories
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func

from src.shared.database.base import BaseRepository
from src.features.vehicles.domain.entities import Vehicle
from src.features.vehicles.domain.enums import VehicleStatus
from .models import VehicleModel


class VehicleRepository(BaseRepository[Vehicle, VehicleModel]):
    """Repository for vehicle data access"""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, VehicleModel)
        self.db_session = db_session  # Keep for backwards compatibility
    
    async def create(self, vehicle: Vehicle) -> Vehicle:
        """Create a new vehicle"""
        # Check if this should be the default vehicle (if no other vehicles exist for user)
        existing_count = await self._count_user_vehicles(vehicle.user_id, VehicleStatus.ACTIVE)
        if existing_count == 0:
            vehicle.is_default = True
        
        # If setting as default, unset other defaults for this user
        if vehicle.is_default:
            await self._unset_other_defaults(vehicle.user_id, vehicle.id)
        
        # Check for license plate uniqueness for this user
        if await self._license_plate_exists(vehicle.license_plate, vehicle.user_id, exclude_id=vehicle.id):
            raise ValueError(f"License plate {vehicle.license_plate} already exists for this user")
        
        vehicle_model = VehicleModel(
            id=vehicle.id,
            user_id=vehicle.user_id,
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            color=vehicle.color,
            license_plate=vehicle.license_plate,
            is_default=vehicle.is_default,
            status=vehicle.status.value,
            created_at=vehicle.created_at,
            updated_at=vehicle.updated_at
        )
        
        self.db_session.add(vehicle_model)
        await self.db_session.flush()
        
        return self._model_to_entity(vehicle_model)
    
    async def get(self, vehicle_id: UUID) -> Optional[Vehicle]:
        """Get vehicle by ID - base repository interface"""
        return await self.get_by_id(vehicle_id)
    
    async def list(self, limit: int = 100, offset: int = 0) -> List[Vehicle]:
        """List all vehicles - base repository interface"""
        stmt = select(VehicleModel).where(
            VehicleModel.status != VehicleStatus.DELETED.value
        ).limit(limit).offset(offset)
        result = await self.db_session.execute(stmt)
        vehicle_models = result.scalars().all()
        return [self._model_to_entity(model) for model in vehicle_models]
    
    async def get_by_id(self, vehicle_id: UUID) -> Optional[Vehicle]:
        """Get vehicle by ID"""
        stmt = select(VehicleModel).where(
            and_(
                VehicleModel.id == vehicle_id,
                VehicleModel.status != VehicleStatus.DELETED.value
            )
        )
        result = await self.db_session.execute(stmt)
        vehicle_model = result.scalar_one_or_none()
        
        return self._model_to_entity(vehicle_model) if vehicle_model else None
    
    async def get_by_license_plate(self, license_plate: str, user_id: UUID) -> Optional[Vehicle]:
        """Get vehicle by license plate for specific user"""
        stmt = select(VehicleModel).where(
            and_(
                VehicleModel.license_plate == license_plate.upper(),
                VehicleModel.user_id == user_id,
                VehicleModel.status != VehicleStatus.DELETED.value
            )
        )
        result = await self.db_session.execute(stmt)
        vehicle_model = result.scalar_one_or_none()
        
        return self._model_to_entity(vehicle_model) if vehicle_model else None
    
    async def list_by_user(
        self,
        user_id: UUID,
        status: Optional[VehicleStatus] = None,
        search: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[Vehicle]:
        """List vehicles by user with optional filtering"""
        conditions = [VehicleModel.user_id == user_id]
        
        # Status filtering
        if not include_inactive:
            if status:
                conditions.append(VehicleModel.status == status.value)
            else:
                conditions.append(VehicleModel.status == VehicleStatus.ACTIVE.value)
        else:
            conditions.append(VehicleModel.status != VehicleStatus.DELETED.value)
        
        # Search filtering
        if search:
            search_term = f"%{search.lower()}%"
            search_conditions = or_(
                func.lower(VehicleModel.make).like(search_term),
                func.lower(VehicleModel.model).like(search_term),
                func.lower(VehicleModel.color).like(search_term),
                func.lower(VehicleModel.license_plate).like(search_term)
            )
            conditions.append(search_conditions)
        
        stmt = select(VehicleModel).where(and_(*conditions)).order_by(
            VehicleModel.is_default.desc(),
            VehicleModel.created_at.desc()
        )
        
        result = await self.db_session.execute(stmt)
        vehicle_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in vehicle_models]
    
    async def get_default_vehicle(self, user_id: UUID) -> Optional[Vehicle]:
        """Get the default vehicle for a user"""
        stmt = select(VehicleModel).where(
            and_(
                VehicleModel.user_id == user_id,
                VehicleModel.is_default == True,
                VehicleModel.status == VehicleStatus.ACTIVE.value
            )
        )
        result = await self.db_session.execute(stmt)
        vehicle_model = result.scalar_one_or_none()
        
        return self._model_to_entity(vehicle_model) if vehicle_model else None
    
    async def update(self, vehicle: Vehicle) -> Vehicle:
        """Update an existing vehicle"""
        # If setting as default, unset other defaults for this user
        if vehicle.is_default:
            await self._unset_other_defaults(vehicle.user_id, vehicle.id)
        
        # Check for license plate uniqueness for this user
        if await self._license_plate_exists(vehicle.license_plate, vehicle.user_id, exclude_id=vehicle.id):
            raise ValueError(f"License plate {vehicle.license_plate} already exists for this user")
        
        stmt = update(VehicleModel).where(VehicleModel.id == vehicle.id).values(
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            color=vehicle.color,
            license_plate=vehicle.license_plate,
            is_default=vehicle.is_default,
            status=vehicle.status.value,
            updated_at=vehicle.updated_at
        )
        
        await self.db_session.execute(stmt)
        await self.db_session.flush()
        
        return await self.get_by_id(vehicle.id)
    
    async def delete(self, vehicle_id: UUID) -> bool:
        """Soft delete a vehicle"""
        stmt = update(VehicleModel).where(VehicleModel.id == vehicle_id).values(
            status=VehicleStatus.DELETED.value,
            is_default=False,
            updated_at=func.now()
        )
        
        result = await self.db_session.execute(stmt)
        return result.rowcount > 0
    
    async def set_default_vehicle(self, vehicle_id: UUID, user_id: UUID) -> bool:
        """Set a vehicle as the default for a user"""
        # First unset all defaults for this user
        await self._unset_other_defaults(user_id)
        
        # Then set the specified vehicle as default
        stmt = update(VehicleModel).where(
            and_(
                VehicleModel.id == vehicle_id,
                VehicleModel.user_id == user_id,
                VehicleModel.status == VehicleStatus.ACTIVE.value
            )
        ).values(
            is_default=True,
            updated_at=func.now()
        )
        
        result = await self.db_session.execute(stmt)
        return result.rowcount > 0
    
    async def get_vehicle_count_by_user(self, user_id: UUID) -> int:
        """Get total count of active vehicles for a user"""
        return await self._count_user_vehicles(user_id, VehicleStatus.ACTIVE)
    
    async def _count_user_vehicles(self, user_id: UUID, status: VehicleStatus) -> int:
        """Count vehicles for a user with specific status"""
        stmt = select(func.count(VehicleModel.id)).where(
            and_(
                VehicleModel.user_id == user_id,
                VehicleModel.status == status.value
            )
        )
        result = await self.db_session.execute(stmt)
        return result.scalar() or 0
    
    async def _unset_other_defaults(self, user_id: UUID, exclude_id: Optional[UUID] = None) -> None:
        """Unset default flag for all other vehicles of a user"""
        conditions = [
            VehicleModel.user_id == user_id,
            VehicleModel.is_default == True
        ]
        
        if exclude_id:
            conditions.append(VehicleModel.id != exclude_id)
        
        stmt = update(VehicleModel).where(and_(*conditions)).values(
            is_default=False,
            updated_at=func.now()
        )
        
        await self.db_session.execute(stmt)
    
    async def _license_plate_exists(self, license_plate: str, user_id: UUID, exclude_id: Optional[UUID] = None) -> bool:
        """Check if license plate exists for this user"""
        conditions = [
            VehicleModel.license_plate == license_plate.upper(),
            VehicleModel.user_id == user_id,
            VehicleModel.status != VehicleStatus.DELETED.value
        ]
        
        if exclude_id:
            conditions.append(VehicleModel.id != exclude_id)
        
        stmt = select(func.count(VehicleModel.id)).where(and_(*conditions))
        result = await self.db_session.execute(stmt)
        count = result.scalar() or 0
        return count > 0
    
    def _model_to_entity(self, model: VehicleModel) -> Vehicle:
        """Convert database model to domain entity"""
        from src.features.vehicles.domain.enums import VehicleStatus
        
        return Vehicle(
            id=model.id,
            user_id=model.user_id,
            make=model.make,
            model=model.model,
            year=model.year,
            color=model.color,
            license_plate=model.license_plate,
            is_default=model.is_default,
            status=VehicleStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at
        )