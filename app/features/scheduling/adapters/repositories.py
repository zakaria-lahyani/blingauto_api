"""
Scheduling repository adapters.
Implementation of scheduling repository ports using SQLAlchemy.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from ..domain.entities import (
    WashBay as WashBayEntity, MobileTeam as MobileTeamEntity,
    TimeSlot as TimeSlotEntity, SchedulingConstraints as ConstraintsEntity,
    Location, VehicleSize, ResourceStatus, ResourceType
)
from app.features.scheduling.adapters.models import (
    TimeSlot, SchedulingConstraints
)
# Import facilities models (WashBay and MobileTeam belong to facilities feature)
from app.features.facilities.adapters.models import (
    WashBayModel as WashBay, MobileTeamModel as MobileTeam
)
from ..ports.repositories import (
    IWashBayRepository, IMobileTeamRepository,
    ITimeSlotRepository, ISchedulingConstraintsRepository
)


class WashBayRepository(IWashBayRepository):
    """SQLAlchemy implementation of wash bay repository."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_by_id(self, bay_id: str) -> Optional[WashBayEntity]:
        """Get wash bay by ID."""
        bay_model = self.db.query(WashBay).filter(WashBay.id == bay_id).first()
        if not bay_model:
            return None
        
        return self._model_to_entity(bay_model)
    
    async def get_all_active(self) -> List[WashBayEntity]:
        """Get all active wash bays."""
        bay_models = self.db.query(WashBay).filter(
            WashBay.status == ResourceStatus.ACTIVE.value
        ).all()
        
        return [self._model_to_entity(bay) for bay in bay_models]
    
    async def create(self, wash_bay: WashBayEntity) -> WashBayEntity:
        """Create new wash bay."""
        bay_model = WashBay(
            id=wash_bay.id,
            bay_number=wash_bay.bay_number,
            max_vehicle_size=wash_bay.max_vehicle_size.value,
            equipment_types=wash_bay.equipment_types,
            status=wash_bay.status.value,
            location_latitude=wash_bay.location.latitude if wash_bay.location else None,
            location_longitude=wash_bay.location.longitude if wash_bay.location else None
        )
        
        self.db.add(bay_model)
        self.db.commit()
        self.db.refresh(bay_model)
        
        return self._model_to_entity(bay_model)
    
    async def update(self, wash_bay: WashBayEntity) -> WashBayEntity:
        """Update wash bay."""
        bay_model = self.db.query(WashBay).filter(WashBay.id == wash_bay.id).first()
        if not bay_model:
            raise ValueError(f"Wash bay {wash_bay.id} not found")
        
        bay_model.bay_number = wash_bay.bay_number
        bay_model.max_vehicle_size = wash_bay.max_vehicle_size.value
        bay_model.equipment_types = wash_bay.equipment_types
        bay_model.status = wash_bay.status.value
        bay_model.location_latitude = wash_bay.location.latitude if wash_bay.location else None
        bay_model.location_longitude = wash_bay.location.longitude if wash_bay.location else None
        bay_model.updated_at = wash_bay.updated_at
        
        self.db.commit()
        self.db.refresh(bay_model)
        
        return self._model_to_entity(bay_model)
    
    async def delete(self, bay_id: str) -> bool:
        """Delete wash bay."""
        bay_model = self.db.query(WashBay).filter(WashBay.id == bay_id).first()
        if not bay_model:
            return False
        
        self.db.delete(bay_model)
        self.db.commit()
        return True
    
    def _model_to_entity(self, model: WashBay) -> WashBayEntity:
        """Convert model to entity."""
        location = None
        if model.location_latitude and model.location_longitude:
            location = Location(
                latitude=Decimal(str(model.location_latitude)),
                longitude=Decimal(str(model.location_longitude))
            )
        
        return WashBayEntity(
            id=model.id,
            bay_number=model.bay_number,
            max_vehicle_size=VehicleSize(model.max_vehicle_size),
            equipment_types=model.equipment_types or [],
            status=ResourceStatus(model.status),
            location=location,
            created_at=model.created_at,
            updated_at=model.updated_at
        )


class MobileTeamRepository(IMobileTeamRepository):
    """SQLAlchemy implementation of mobile team repository."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_by_id(self, team_id: str) -> Optional[MobileTeamEntity]:
        """Get mobile team by ID."""
        team_model = self.db.query(MobileTeam).filter(MobileTeam.id == team_id).first()
        if not team_model:
            return None
        
        return self._model_to_entity(team_model)
    
    async def get_all_active(self) -> List[MobileTeamEntity]:
        """Get all active mobile teams."""
        team_models = self.db.query(MobileTeam).filter(
            MobileTeam.status == ResourceStatus.ACTIVE.value
        ).all()
        
        return [self._model_to_entity(team) for team in team_models]
    
    async def create(self, mobile_team: MobileTeamEntity) -> MobileTeamEntity:
        """Create new mobile team."""
        team_model = MobileTeam(
            id=mobile_team.id,
            team_name=mobile_team.team_name,
            base_location_latitude=mobile_team.base_location.latitude,
            base_location_longitude=mobile_team.base_location.longitude,
            service_radius_km=mobile_team.service_radius_km,
            daily_capacity=mobile_team.daily_capacity,
            equipment_types=mobile_team.equipment_types,
            status=mobile_team.status.value
        )
        
        self.db.add(team_model)
        self.db.commit()
        self.db.refresh(team_model)
        
        return self._model_to_entity(team_model)
    
    async def update(self, mobile_team: MobileTeamEntity) -> MobileTeamEntity:
        """Update mobile team."""
        team_model = self.db.query(MobileTeam).filter(MobileTeam.id == mobile_team.id).first()
        if not team_model:
            raise ValueError(f"Mobile team {mobile_team.id} not found")
        
        team_model.team_name = mobile_team.team_name
        team_model.base_location_latitude = mobile_team.base_location.latitude
        team_model.base_location_longitude = mobile_team.base_location.longitude
        team_model.service_radius_km = mobile_team.service_radius_km
        team_model.daily_capacity = mobile_team.daily_capacity
        team_model.equipment_types = mobile_team.equipment_types
        team_model.status = mobile_team.status.value
        team_model.updated_at = mobile_team.updated_at
        
        self.db.commit()
        self.db.refresh(team_model)
        
        return self._model_to_entity(team_model)
    
    async def delete(self, team_id: str) -> bool:
        """Delete mobile team."""
        team_model = self.db.query(MobileTeam).filter(MobileTeam.id == team_id).first()
        if not team_model:
            return False
        
        self.db.delete(team_model)
        self.db.commit()
        return True
    
    def _model_to_entity(self, model: MobileTeam) -> MobileTeamEntity:
        """Convert model to entity."""
        base_location = Location(
            latitude=Decimal(str(model.base_location_latitude)),
            longitude=Decimal(str(model.base_location_longitude))
        )
        
        return MobileTeamEntity(
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


class TimeSlotRepository(ITimeSlotRepository):
    """SQLAlchemy implementation of time slot repository."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_bookings_for_resource(
        self,
        resource_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[TimeSlotEntity]:
        """Get all bookings for a resource in a date range."""
        slot_models = self.db.query(TimeSlot).filter(
            TimeSlot.resource_id == resource_id,
            TimeSlot.start_time >= start_date,
            TimeSlot.end_time <= end_date,
            TimeSlot.is_available == False  # Only booked slots
        ).all()
        
        return [self._model_to_entity(slot) for slot in slot_models]
    
    async def get_bookings_for_date(self, date: datetime) -> List[TimeSlotEntity]:
        """Get all bookings for a specific date."""
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start.replace(hour=23, minute=59, second=59)
        
        slot_models = self.db.query(TimeSlot).filter(
            TimeSlot.start_time >= day_start,
            TimeSlot.start_time <= day_end,
            TimeSlot.is_available == False  # Only booked slots
        ).all()
        
        return [self._model_to_entity(slot) for slot in slot_models]
    
    async def create_booking(self, time_slot: TimeSlotEntity) -> TimeSlotEntity:
        """Create a new booking slot."""
        slot_model = TimeSlot(
            id=time_slot.id if hasattr(time_slot, 'id') else None,
            start_time=time_slot.start_time,
            end_time=time_slot.end_time,
            resource_id=time_slot.resource_id,
            resource_type=time_slot.resource_type.value,
            is_available=time_slot.is_available,
            booking_id=time_slot.booking_id,
            buffer_minutes=time_slot.buffer_minutes
        )
        
        # Set the correct foreign key based on resource type
        if time_slot.resource_type == ResourceType.WASH_BAY:
            slot_model.wash_bay_id = time_slot.resource_id
        else:
            slot_model.mobile_team_id = time_slot.resource_id
        
        self.db.add(slot_model)
        self.db.commit()
        self.db.refresh(slot_model)
        
        return self._model_to_entity(slot_model)
    
    async def update_booking(self, time_slot: TimeSlotEntity) -> TimeSlotEntity:
        """Update booking slot."""
        slot_model = self.db.query(TimeSlot).filter(
            TimeSlot.id == getattr(time_slot, 'id', None)
        ).first()
        
        if not slot_model:
            raise ValueError(f"Time slot not found")
        
        slot_model.start_time = time_slot.start_time
        slot_model.end_time = time_slot.end_time
        slot_model.is_available = time_slot.is_available
        slot_model.booking_id = time_slot.booking_id
        slot_model.buffer_minutes = time_slot.buffer_minutes
        
        self.db.commit()
        self.db.refresh(slot_model)
        
        return self._model_to_entity(slot_model)
    
    async def cancel_booking(self, booking_id: str) -> bool:
        """Cancel a booking."""
        slot_models = self.db.query(TimeSlot).filter(
            TimeSlot.booking_id == booking_id
        ).all()
        
        if not slot_models:
            return False
        
        for slot_model in slot_models:
            slot_model.is_available = True
            slot_model.booking_id = None
        
        self.db.commit()
        return True
    
    def _model_to_entity(self, model: TimeSlot) -> TimeSlotEntity:
        """Convert model to entity."""
        return TimeSlotEntity(
            start_time=model.start_time,
            end_time=model.end_time,
            resource_id=model.resource_id,
            resource_type=ResourceType(model.resource_type),
            is_available=model.is_available,
            booking_id=model.booking_id,
            buffer_minutes=model.buffer_minutes
        )


class SchedulingConstraintsRepository(ISchedulingConstraintsRepository):
    """SQLAlchemy implementation of scheduling constraints repository."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_current_constraints(self) -> ConstraintsEntity:
        """Get current scheduling constraints."""
        constraints_model = self.db.query(SchedulingConstraints).filter(
            SchedulingConstraints.is_active == True
        ).first()
        
        if not constraints_model:
            # Return default constraints if none found
            return ConstraintsEntity()
        
        return self._model_to_entity(constraints_model)
    
    async def update_constraints(self, constraints: ConstraintsEntity) -> ConstraintsEntity:
        """Update scheduling constraints."""
        # Deactivate current constraints
        self.db.query(SchedulingConstraints).update({"is_active": False})
        
        # Create new active constraints
        constraints_model = SchedulingConstraints(
            is_active=True,
            min_advance_hours=constraints.min_advance_hours,
            max_advance_days=constraints.max_advance_days,
            slot_duration_minutes=constraints.slot_duration_minutes,
            buffer_minutes=constraints.buffer_minutes,
            business_hours=self._business_hours_to_dict(constraints.business_hours)
        )
        
        self.db.add(constraints_model)
        self.db.commit()
        self.db.refresh(constraints_model)
        
        return self._model_to_entity(constraints_model)
    
    def _model_to_entity(self, model: SchedulingConstraints) -> ConstraintsEntity:
        """Convert model to entity."""
        business_hours = self._business_hours_from_dict(model.business_hours or {})
        
        return ConstraintsEntity(
            min_advance_hours=model.min_advance_hours,
            max_advance_days=model.max_advance_days,
            slot_duration_minutes=model.slot_duration_minutes,
            buffer_minutes=model.buffer_minutes,
            business_hours=business_hours
        )
    
    def _business_hours_to_dict(self, business_hours):
        """Convert business hours to dictionary for JSON storage."""
        if not business_hours:
            return {}
        
        result = {}
        for day, hours in business_hours.items():
            result[day.value] = {
                "open_time": hours.open_time.isoformat() if hours.open_time else None,
                "close_time": hours.close_time.isoformat() if hours.close_time else None,
                "is_closed": hours.is_closed,
                "break_periods": [
                    [start.isoformat(), end.isoformat()]
                    for start, end in hours.break_periods
                ]
            }
        return result
    
    def _business_hours_from_dict(self, data):
        """Convert dictionary to business hours."""
        # This would need proper implementation with BusinessHours entities
        # For now, return empty dict
        return {}