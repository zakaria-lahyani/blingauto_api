"""
Wash facility management repositories
"""
import json
from datetime import datetime, date
from typing import List, Optional, Dict, Set
from uuid import UUID

from sqlalchemy import and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.features.scheduling.domain.wash_facility_entities import (
    WashBay, MobileWashTeam, WashFacilityConfiguration, CapacityAllocation, WashType
)
from .models import (
    WashBayModel, MobileWashTeamModel, WashFacilityConfigurationModel, CapacityAllocationModel
)


class WashBayRepository:
    """Repository for wash bay management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, wash_bay: WashBay) -> WashBay:
        """Create a new wash bay"""
        equipment_json = json.dumps(list(wash_bay.equipment_types)) if wash_bay.equipment_types else None
        
        model = WashBayModel(
            name=wash_bay.name,
            bay_number=wash_bay.bay_number,
            is_active=wash_bay.is_active,
            equipment_types=equipment_json,
            max_vehicle_size=wash_bay.max_vehicle_size,
            has_covered_area=wash_bay.has_covered_area,
            has_power_supply=wash_bay.has_power_supply,
            notes=wash_bay.notes
        )
        
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        
        wash_bay.id = model.id
        return wash_bay
    
    async def get_by_id(self, bay_id: UUID) -> Optional[WashBay]:
        """Get wash bay by ID"""
        stmt = select(WashBayModel).where(WashBayModel.id == bay_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        equipment_types = set()
        if model.equipment_types:
            equipment_types = set(json.loads(model.equipment_types))
        
        return WashBay(
            name=model.name,
            bay_number=model.bay_number,
            is_active=model.is_active,
            equipment_types=equipment_types,
            max_vehicle_size=model.max_vehicle_size,
            has_covered_area=model.has_covered_area,
            has_power_supply=model.has_power_supply,
            notes=model.notes,
            id=model.id,
            created_at=model.created_at
        )
    
    async def get_all(self, active_only: bool = False) -> List[WashBay]:
        """Get all wash bays"""
        stmt = select(WashBayModel).order_by(WashBayModel.bay_number)
        
        if active_only:
            stmt = stmt.where(WashBayModel.is_active == True)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        wash_bays = []
        for model in models:
            equipment_types = set()
            if model.equipment_types:
                equipment_types = set(json.loads(model.equipment_types))
            
            wash_bays.append(WashBay(
                name=model.name,
                bay_number=model.bay_number,
                is_active=model.is_active,
                equipment_types=equipment_types,
                max_vehicle_size=model.max_vehicle_size,
                has_covered_area=model.has_covered_area,
                has_power_supply=model.has_power_supply,
                notes=model.notes,
                id=model.id,
                created_at=model.created_at
            ))
        
        return wash_bays
    
    async def update(self, wash_bay: WashBay) -> WashBay:
        """Update wash bay"""
        stmt = select(WashBayModel).where(WashBayModel.id == wash_bay.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError("Wash bay not found")
        
        equipment_json = json.dumps(list(wash_bay.equipment_types)) if wash_bay.equipment_types else None
        
        model.name = wash_bay.name
        model.is_active = wash_bay.is_active
        model.equipment_types = equipment_json
        model.max_vehicle_size = wash_bay.max_vehicle_size
        model.has_covered_area = wash_bay.has_covered_area
        model.has_power_supply = wash_bay.has_power_supply
        model.notes = wash_bay.notes
        model.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(model)
        
        return wash_bay
    
    async def delete(self, bay_id: UUID) -> bool:
        """Delete wash bay"""
        stmt = select(WashBayModel).where(WashBayModel.id == bay_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self.session.delete(model)
        await self.session.commit()
        return True
    
    async def get_available_for_vehicle_size(self, vehicle_size: str) -> List[WashBay]:
        """Get wash bays that can accommodate vehicle size"""
        size_hierarchy = ["compact", "standard", "large", "oversized"]
        vehicle_index = size_hierarchy.index(vehicle_size)
        suitable_sizes = size_hierarchy[vehicle_index:]
        
        stmt = select(WashBayModel).where(
            and_(
                WashBayModel.is_active == True,
                WashBayModel.max_vehicle_size.in_(suitable_sizes)
            )
        ).order_by(WashBayModel.bay_number)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        wash_bays = []
        for model in models:
            equipment_types = set()
            if model.equipment_types:
                equipment_types = set(json.loads(model.equipment_types))
            
            wash_bays.append(WashBay(
                name=model.name,
                bay_number=model.bay_number,
                is_active=model.is_active,
                equipment_types=equipment_types,
                max_vehicle_size=model.max_vehicle_size,
                has_covered_area=model.has_covered_area,
                has_power_supply=model.has_power_supply,
                notes=model.notes,
                id=model.id,
                created_at=model.created_at
            ))
        
        return wash_bays


class MobileWashTeamRepository:
    """Repository for mobile wash team management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, mobile_team: MobileWashTeam) -> MobileWashTeam:
        """Create a new mobile team"""
        equipment_json = json.dumps(list(mobile_team.equipment_types)) if mobile_team.equipment_types else None
        location_json = json.dumps(mobile_team.base_location) if mobile_team.base_location else None
        
        model = MobileWashTeamModel(
            name=mobile_team.name,
            team_size=mobile_team.team_size,
            equipment_types=equipment_json,
            service_radius_km=int(mobile_team.service_radius_km),
            max_vehicles_per_day=mobile_team.max_vehicles_per_day,
            hourly_rate=int(mobile_team.hourly_rate * 100) if mobile_team.hourly_rate else None,
            is_active=mobile_team.is_active,
            base_location=location_json,
            notes=mobile_team.notes
        )
        
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        
        mobile_team.id = model.id
        return mobile_team
    
    async def get_by_id(self, team_id: UUID) -> Optional[MobileWashTeam]:
        """Get mobile team by ID"""
        stmt = select(MobileWashTeamModel).where(MobileWashTeamModel.id == team_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        equipment_types = set()
        if model.equipment_types:
            equipment_types = set(json.loads(model.equipment_types))
        
        base_location = {}
        if model.base_location:
            base_location = json.loads(model.base_location)
        
        return MobileWashTeam(
            name=model.name,
            team_size=model.team_size,
            equipment_types=equipment_types,
            service_radius_km=float(model.service_radius_km),
            max_vehicles_per_day=model.max_vehicles_per_day,
            hourly_rate=model.hourly_rate / 100 if model.hourly_rate else None,
            is_active=model.is_active,
            base_location=base_location,
            notes=model.notes,
            id=model.id,
            created_at=model.created_at
        )
    
    async def get_all(self, active_only: bool = False) -> List[MobileWashTeam]:
        """Get all mobile teams"""
        stmt = select(MobileWashTeamModel).order_by(MobileWashTeamModel.name)
        
        if active_only:
            stmt = stmt.where(MobileWashTeamModel.is_active == True)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        teams = []
        for model in models:
            equipment_types = set()
            if model.equipment_types:
                equipment_types = set(json.loads(model.equipment_types))
            
            base_location = {}
            if model.base_location:
                base_location = json.loads(model.base_location)
            
            teams.append(MobileWashTeam(
                name=model.name,
                team_size=model.team_size,
                equipment_types=equipment_types,
                service_radius_km=float(model.service_radius_km),
                max_vehicles_per_day=model.max_vehicles_per_day,
                hourly_rate=model.hourly_rate / 100 if model.hourly_rate else None,
                is_active=model.is_active,
                base_location=base_location,
                notes=model.notes,
                id=model.id,
                created_at=model.created_at
            ))
        
        return teams
    
    async def update(self, mobile_team: MobileWashTeam) -> MobileWashTeam:
        """Update mobile team"""
        stmt = select(MobileWashTeamModel).where(MobileWashTeamModel.id == mobile_team.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError("Mobile team not found")
        
        equipment_json = json.dumps(list(mobile_team.equipment_types)) if mobile_team.equipment_types else None
        location_json = json.dumps(mobile_team.base_location) if mobile_team.base_location else None
        
        model.name = mobile_team.name
        model.team_size = mobile_team.team_size
        model.equipment_types = equipment_json
        model.service_radius_km = int(mobile_team.service_radius_km)
        model.max_vehicles_per_day = mobile_team.max_vehicles_per_day
        model.hourly_rate = int(mobile_team.hourly_rate * 100) if mobile_team.hourly_rate else None
        model.is_active = mobile_team.is_active
        model.base_location = location_json
        model.notes = mobile_team.notes
        model.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(model)
        
        return mobile_team
    
    async def delete(self, team_id: UUID) -> bool:
        """Delete mobile team"""
        stmt = select(MobileWashTeamModel).where(MobileWashTeamModel.id == team_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self.session.delete(model)
        await self.session.commit()
        return True


class WashFacilityConfigurationRepository:
    """Repository for wash facility configuration"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_current_configuration(self) -> Optional[WashFacilityConfiguration]:
        """Get current facility configuration"""
        stmt = select(WashFacilityConfigurationModel).order_by(WashFacilityConfigurationModel.created_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        operating_hours = {}
        if model.operating_hours:
            operating_hours = json.loads(model.operating_hours)
        
        return WashFacilityConfiguration(
            facility_name=model.facility_name,
            total_wash_bays=model.total_wash_bays,
            total_mobile_teams=model.total_mobile_teams,
            operating_hours=operating_hours,
            default_service_duration_minutes=model.default_service_duration_minutes,
            buffer_between_services_minutes=model.buffer_between_services_minutes,
            max_advance_booking_days=model.max_advance_booking_days,
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    async def create_or_update(self, configuration: WashFacilityConfiguration) -> WashFacilityConfiguration:
        """Create or update facility configuration"""
        operating_hours_json = json.dumps(configuration.operating_hours) if configuration.operating_hours else None
        
        if configuration.id:
            # Update existing
            stmt = select(WashFacilityConfigurationModel).where(WashFacilityConfigurationModel.id == configuration.id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                model.facility_name = configuration.facility_name
                model.total_wash_bays = configuration.total_wash_bays
                model.total_mobile_teams = configuration.total_mobile_teams
                model.operating_hours = operating_hours_json
                model.default_service_duration_minutes = configuration.default_service_duration_minutes
                model.buffer_between_services_minutes = configuration.buffer_between_services_minutes
                model.max_advance_booking_days = configuration.max_advance_booking_days
                model.updated_at = datetime.utcnow()
            else:
                raise ValueError("Configuration not found")
        else:
            # Create new
            model = WashFacilityConfigurationModel(
                facility_name=configuration.facility_name,
                total_wash_bays=configuration.total_wash_bays,
                total_mobile_teams=configuration.total_mobile_teams,
                operating_hours=operating_hours_json,
                default_service_duration_minutes=configuration.default_service_duration_minutes,
                buffer_between_services_minutes=configuration.buffer_between_services_minutes,
                max_advance_booking_days=configuration.max_advance_booking_days
            )
            self.session.add(model)
        
        await self.session.commit()
        await self.session.refresh(model)
        
        configuration.id = model.id
        return configuration


class CapacityAllocationRepository:
    """Repository for capacity allocation tracking"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_allocation_for_date_and_resource(
        self,
        date: datetime,
        resource_id: UUID,
        wash_type: WashType
    ) -> Optional[CapacityAllocation]:
        """Get capacity allocation for specific date and resource"""
        stmt = select(CapacityAllocationModel).where(
            and_(
                func.date(CapacityAllocationModel.date) == date.date(),
                CapacityAllocationModel.resource_id == resource_id,
                CapacityAllocationModel.wash_type == wash_type.value
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        bookings = []
        if model.bookings:
            bookings = json.loads(model.bookings)
        
        return CapacityAllocation(
            date=model.date,
            wash_type=WashType(model.wash_type),
            resource_id=model.resource_id,
            resource_name=model.resource_name,
            allocated_slots=model.allocated_slots,
            max_capacity=model.max_capacity,
            bookings=bookings
        )
    
    async def create_or_update_allocation(self, allocation: CapacityAllocation) -> CapacityAllocation:
        """Create or update capacity allocation"""
        stmt = select(CapacityAllocationModel).where(
            and_(
                func.date(CapacityAllocationModel.date) == allocation.date.date(),
                CapacityAllocationModel.resource_id == allocation.resource_id,
                CapacityAllocationModel.wash_type == allocation.wash_type.value
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        bookings_json = json.dumps([str(b) for b in allocation.bookings]) if allocation.bookings else None
        
        if model:
            # Update existing
            model.allocated_slots = allocation.allocated_slots
            model.max_capacity = allocation.max_capacity
            model.bookings = bookings_json
            model.updated_at = datetime.utcnow()
        else:
            # Create new
            model = CapacityAllocationModel(
                date=allocation.date,
                wash_type=allocation.wash_type.value,
                resource_id=allocation.resource_id,
                resource_name=allocation.resource_name,
                allocated_slots=allocation.allocated_slots,
                max_capacity=allocation.max_capacity,
                bookings=bookings_json
            )
            self.session.add(model)
        
        await self.session.commit()
        await self.session.refresh(model)
        
        return allocation
    
    async def get_daily_capacity_summary(self, date: datetime) -> Dict[str, Dict]:
        """Get daily capacity summary for all resources"""
        stmt = select(CapacityAllocationModel).where(
            func.date(CapacityAllocationModel.date) == date.date()
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        summary = {
            "stationary": {"total_capacity": 0, "allocated": 0, "available": 0},
            "mobile": {"total_capacity": 0, "allocated": 0, "available": 0}
        }
        
        for model in models:
            wash_type = model.wash_type
            summary[wash_type]["total_capacity"] += model.max_capacity
            summary[wash_type]["allocated"] += model.allocated_slots
            summary[wash_type]["available"] += (model.max_capacity - model.allocated_slots)
        
        return summary