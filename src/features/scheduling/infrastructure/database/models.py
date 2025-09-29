"""
Scheduling database models
"""
from datetime import time, datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Time, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID, ARRAY
from sqlalchemy.orm import relationship
from uuid import uuid4
from typing import List, Set, Optional, Dict
import json

from src.shared.database import Base
from src.shared.utils.timestamp import db_utc_timestamp
from src.features.scheduling.domain.entities import (
    BusinessHours, Resource, TimeSlot, SchedulingConflict
)
from src.features.scheduling.domain.wash_facility_entities import (
    WashBay, MobileWashTeam, WashFacilityConfiguration, CapacityAllocation, WashType
)
from src.features.scheduling.domain.enums import (
    DayOfWeek, ResourceType, ResourceStatus, SlotStatus, ConflictType
)


class BusinessHoursModel(Base):
    """Business hours database model"""
    __tablename__ = "business_hours"
    
    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4)
    day_of_week = Column(String(10), nullable=False, index=True)  # monday, tuesday, etc.
    open_time = Column(Time, nullable=True)  # NULL if closed
    close_time = Column(Time, nullable=True)  # NULL if closed
    is_closed = Column(Boolean, nullable=False, default=False, index=True)
    break_periods = Column(Text, nullable=True)  # JSON array of break periods
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), onupdate=db_utc_timestamp())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_business_hours_day', 'day_of_week'),
        Index('idx_business_hours_open_close', 'open_time', 'close_time'),
    )
    
    def to_entity(self) -> BusinessHours:
        """Convert model to domain entity"""
        # Parse break periods from JSON
        break_periods = []
        if self.break_periods:
            try:
                break_data = json.loads(self.break_periods)
                for period in break_data:
                    start_time = time.fromisoformat(period['start'])
                    end_time = time.fromisoformat(period['end'])
                    break_periods.append((start_time, end_time))
            except (json.JSONDecodeError, KeyError, ValueError):
                break_periods = []
        
        return BusinessHours(
            id=self.id,
            day_of_week=DayOfWeek(self.day_of_week),
            open_time=self.open_time if not self.is_closed else time(9, 0),
            close_time=self.close_time if not self.is_closed else time(17, 0),
            is_closed=self.is_closed,
            break_periods=break_periods
        )
    
    @classmethod
    def from_entity(cls, entity: BusinessHours) -> "BusinessHoursModel":
        """Create model from domain entity"""
        # Serialize break periods to JSON
        break_periods_json = None
        if entity.break_periods:
            break_data = []
            for start_time, end_time in entity.break_periods:
                break_data.append({
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                })
            break_periods_json = json.dumps(break_data)
        
        return cls(
            id=entity.id,
            day_of_week=entity.day_of_week.value,
            open_time=entity.open_time if not entity.is_closed else None,
            close_time=entity.close_time if not entity.is_closed else None,
            is_closed=entity.is_closed,
            break_periods=break_periods_json,
            created_at=None,
            updated_at=None
        )
    
    def update_from_entity(self, entity: BusinessHours) -> None:
        """Update model from domain entity"""
        # Serialize break periods to JSON
        break_periods_json = None
        if entity.break_periods:
            break_data = []
            for start_time, end_time in entity.break_periods:
                break_data.append({
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                })
            break_periods_json = json.dumps(break_data)
        
        self.day_of_week = entity.day_of_week.value
        self.open_time = entity.open_time if not entity.is_closed else None
        self.close_time = entity.close_time if not entity.is_closed else None
        self.is_closed = entity.is_closed
        self.break_periods = break_periods_json
        self.updated_at = None


class ResourceModel(Base):
    """Resource database model"""
    __tablename__ = "scheduling_resources"
    
    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(20), nullable=False, index=True)  # wash_bay, staff_member, etc.
    capacity = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="available", index=True)
    skills = Column(Text, nullable=True)  # JSON array of skills
    hourly_rate = Column(Integer, nullable=True)  # In cents
    resource_metadata = Column(Text, nullable=True)  # JSON for additional resource data
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), onupdate=db_utc_timestamp())
    
    # Relationships
    time_slots = relationship("TimeSlotModel", back_populates="resource")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_resource_type_status', 'resource_type', 'status'),
        Index('idx_resource_name', 'name'),
    )
    
    def to_entity(self) -> Resource:
        """Convert model to domain entity"""
        # Parse skills from JSON
        skills = set()
        if self.skills:
            try:
                skills_data = json.loads(self.skills)
                skills = set(skills_data) if isinstance(skills_data, list) else set()
            except (json.JSONDecodeError, TypeError):
                skills = set()
        
        # Convert hourly rate from cents to float
        hourly_rate = None
        if self.hourly_rate is not None:
            hourly_rate = self.hourly_rate / 100.0
        
        return Resource(
            id=self.id,
            name=self.name,
            resource_type=ResourceType(self.resource_type),
            capacity=self.capacity,
            status=ResourceStatus(self.status),
            skills=skills,
            hourly_rate=hourly_rate,
            created_at=self.created_at
        )
    
    @classmethod
    def from_entity(cls, entity: Resource) -> "ResourceModel":
        """Create model from domain entity"""
        # Serialize skills to JSON
        skills_json = None
        if entity.skills:
            skills_json = json.dumps(list(entity.skills))
        
        # Convert hourly rate to cents
        hourly_rate_cents = None
        if entity.hourly_rate is not None:
            hourly_rate_cents = int(entity.hourly_rate * 100)
        
        return cls(
            id=entity.id,
            name=entity.name,
            resource_type=entity.resource_type.value,
            capacity=entity.capacity,
            status=entity.status.value,
            skills=skills_json,
            hourly_rate=hourly_rate_cents,
            created_at=entity.created_at,
            updated_at=None
        )
    
    def update_from_entity(self, entity: Resource) -> None:
        """Update model from domain entity"""
        # Serialize skills to JSON
        skills_json = None
        if entity.skills:
            skills_json = json.dumps(list(entity.skills))
        
        # Convert hourly rate to cents
        hourly_rate_cents = None
        if entity.hourly_rate is not None:
            hourly_rate_cents = int(entity.hourly_rate * 100)
        
        self.name = entity.name
        self.resource_type = entity.resource_type.value
        self.capacity = entity.capacity
        self.status = entity.status.value
        self.skills = skills_json
        self.hourly_rate = hourly_rate_cents
        self.updated_at = None


class TimeSlotModel(Base):
    """Time slot database model"""
    __tablename__ = "time_slots"
    
    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    resource_id = Column(PostgreSQL_UUID(as_uuid=True), ForeignKey("scheduling_resources.id"), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="available", index=True)
    booking_id = Column(PostgreSQL_UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=True, index=True)
    blocked_reason = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), onupdate=db_utc_timestamp())
    
    # Relationships
    resource = relationship("ResourceModel", back_populates="time_slots")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_timeslot_start_end', 'start_time', 'end_time'),
        Index('idx_timeslot_resource_status', 'resource_id', 'status'),
        Index('idx_timeslot_booking', 'booking_id'),
        Index('idx_timeslot_status_time', 'status', 'start_time'),
    )
    
    def to_entity(self) -> TimeSlot:
        """Convert model to domain entity"""
        return TimeSlot(
            id=self.id,
            start_time=self.start_time,
            end_time=self.end_time,
            resource_id=self.resource_id,
            status=SlotStatus(self.status),
            booking_id=self.booking_id,
            blocked_reason=self.blocked_reason
        )
    
    @classmethod
    def from_entity(cls, entity: TimeSlot) -> "TimeSlotModel":
        """Create model from domain entity"""
        return cls(
            id=entity.id,
            start_time=entity.start_time,
            end_time=entity.end_time,
            resource_id=entity.resource_id,
            status=entity.status.value,
            booking_id=entity.booking_id,
            blocked_reason=entity.blocked_reason,
            created_at=None,
            updated_at=None
        )
    
    def update_from_entity(self, entity: TimeSlot) -> None:
        """Update model from domain entity"""
        self.start_time = entity.start_time
        self.end_time = entity.end_time
        self.resource_id = entity.resource_id
        self.status = entity.status.value
        self.booking_id = entity.booking_id
        self.blocked_reason = entity.blocked_reason
        self.updated_at = None


class SchedulingConfigurationModel(Base):
    """Scheduling configuration database model"""
    __tablename__ = "scheduling_configuration"
    
    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4)
    key = Column(String(50), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=False)  # JSON value
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), onupdate=db_utc_timestamp())


class ResourceScheduleModel(Base):
    """Resource-specific schedule overrides"""
    __tablename__ = "resource_schedules"
    
    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4)
    resource_id = Column(PostgreSQL_UUID(as_uuid=True), ForeignKey("scheduling_resources.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)  # Specific date for override
    start_time = Column(Time, nullable=True)  # NULL if not available
    end_time = Column(Time, nullable=True)  # NULL if not available
    is_available = Column(Boolean, nullable=False, default=True, index=True)
    reason = Column(String(200), nullable=True)  # maintenance, vacation, etc.
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), onupdate=db_utc_timestamp())
    
    # Relationships
    resource = relationship("ResourceModel")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_resource_schedule_date', 'resource_id', 'date'),
        Index('idx_resource_schedule_available', 'is_available', 'date'),
    )


class SchedulingConflictModel(Base):
    """Scheduling conflicts log"""
    __tablename__ = "scheduling_conflicts"
    
    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4)
    conflict_type = Column(String(30), nullable=False, index=True)
    message = Column(String(500), nullable=False)
    requested_time = Column(DateTime, nullable=False, index=True)
    conflicting_booking_id = Column(PostgreSQL_UUID(as_uuid=True), nullable=True, index=True)
    resource_id = Column(PostgreSQL_UUID(as_uuid=True), nullable=True, index=True)
    customer_id = Column(PostgreSQL_UUID(as_uuid=True), nullable=False, index=True)
    resolved = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), index=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_conflict_type_time', 'conflict_type', 'requested_time'),
        Index('idx_conflict_customer', 'customer_id', 'created_at'),
        Index('idx_conflict_resolved', 'resolved', 'created_at'),
    )
    
    def to_entity(self) -> SchedulingConflict:
        """Convert model to domain entity"""
        return SchedulingConflict(
            conflict_type=ConflictType(self.conflict_type),
            message=self.message,
            requested_time=self.requested_time,
            conflicting_booking_id=self.conflicting_booking_id,
            resource_id=self.resource_id
        )
    
    @classmethod
    def from_entity(cls, entity: SchedulingConflict, customer_id) -> "SchedulingConflictModel":
        """Create model from domain entity"""
        return cls(
            conflict_type=entity.conflict_type.value,
            message=entity.message,
            requested_time=entity.requested_time,
            conflicting_booking_id=entity.conflicting_booking_id,
            resource_id=entity.resource_id,
            customer_id=customer_id,
            resolved=False,
            created_at=None
        )
    
    def update_from_entity(self, entity: SchedulingConflict) -> None:
        """Update model from domain entity"""
        self.conflict_type = entity.conflict_type.value
        self.message = entity.message
        self.requested_time = entity.requested_time
        self.conflicting_booking_id = entity.conflicting_booking_id
        self.resource_id = entity.resource_id


class WashBayModel(Base):
    """Wash bay database model"""
    __tablename__ = "wash_bays"
    
    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, index=True)
    bay_number = Column(Integer, nullable=False, unique=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    equipment_types = Column(Text, nullable=True)  # JSON array of equipment
    max_vehicle_size = Column(String(20), nullable=False, default="standard")  # compact, standard, large, oversized
    has_covered_area = Column(Boolean, nullable=False, default=True)
    has_power_supply = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), onupdate=db_utc_timestamp())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_wash_bay_active', 'is_active'),
        Index('idx_wash_bay_number', 'bay_number'),
        Index('idx_wash_bay_size', 'max_vehicle_size'),
    )
    
    def to_entity(self) -> WashBay:
        """Convert model to domain entity"""
        # Parse equipment types from JSON
        equipment_types = set()
        if self.equipment_types:
            try:
                equipment_data = json.loads(self.equipment_types)
                equipment_types = set(equipment_data) if isinstance(equipment_data, list) else set()
            except (json.JSONDecodeError, TypeError):
                equipment_types = set()
        
        return WashBay(
            id=self.id,
            name=self.name,
            bay_number=self.bay_number,
            is_active=self.is_active,
            equipment_types=equipment_types,
            max_vehicle_size=self.max_vehicle_size,
            has_covered_area=self.has_covered_area,
            has_power_supply=self.has_power_supply,
            notes=self.notes,
            created_at=self.created_at
        )
    
    @classmethod
    def from_entity(cls, entity: WashBay) -> "WashBayModel":
        """Create model from domain entity"""
        # Serialize equipment types to JSON
        equipment_json = None
        if entity.equipment_types:
            equipment_json = json.dumps(list(entity.equipment_types))
        
        return cls(
            id=entity.id,
            name=entity.name,
            bay_number=entity.bay_number,
            is_active=entity.is_active,
            equipment_types=equipment_json,
            max_vehicle_size=entity.max_vehicle_size,
            has_covered_area=entity.has_covered_area,
            has_power_supply=entity.has_power_supply,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=None
        )
    
    def update_from_entity(self, entity: WashBay) -> None:
        """Update model from domain entity"""
        # Serialize equipment types to JSON
        equipment_json = None
        if entity.equipment_types:
            equipment_json = json.dumps(list(entity.equipment_types))
        
        self.name = entity.name
        self.bay_number = entity.bay_number
        self.is_active = entity.is_active
        self.equipment_types = equipment_json
        self.max_vehicle_size = entity.max_vehicle_size
        self.has_covered_area = entity.has_covered_area
        self.has_power_supply = entity.has_power_supply
        self.notes = entity.notes
        self.updated_at = None


class MobileWashTeamModel(Base):
    """Mobile wash team database model"""
    __tablename__ = "mobile_wash_teams"
    
    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, index=True)
    team_size = Column(Integer, nullable=False, default=2)
    equipment_types = Column(Text, nullable=True)  # JSON array of equipment
    service_radius_km = Column(Integer, nullable=False, default=50)  # In kilometers
    max_vehicles_per_day = Column(Integer, nullable=False, default=8)
    hourly_rate = Column(Integer, nullable=True)  # In cents
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    base_location = Column(Text, nullable=True)  # JSON with lat/lng
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), onupdate=db_utc_timestamp())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_mobile_team_active', 'is_active'),
        Index('idx_mobile_team_radius', 'service_radius_km'),
    )
    
    def to_entity(self) -> MobileWashTeam:
        """Convert model to domain entity"""
        # Parse equipment types from JSON
        equipment_types = set()
        if self.equipment_types:
            try:
                equipment_data = json.loads(self.equipment_types)
                equipment_types = set(equipment_data) if isinstance(equipment_data, list) else set()
            except (json.JSONDecodeError, TypeError):
                equipment_types = set()
        
        # Parse base location from JSON
        base_location = {}
        if self.base_location:
            try:
                base_location = json.loads(self.base_location)
            except (json.JSONDecodeError, TypeError):
                base_location = {}
        
        # Convert hourly rate from cents to float
        hourly_rate = None
        if self.hourly_rate is not None:
            hourly_rate = self.hourly_rate / 100.0
        
        return MobileWashTeam(
            id=self.id,
            name=self.name,
            team_size=self.team_size,
            equipment_types=equipment_types,
            service_radius_km=float(self.service_radius_km),
            max_vehicles_per_day=self.max_vehicles_per_day,
            hourly_rate=hourly_rate,
            is_active=self.is_active,
            base_location=base_location,
            notes=self.notes,
            created_at=self.created_at
        )
    
    @classmethod
    def from_entity(cls, entity: MobileWashTeam) -> "MobileWashTeamModel":
        """Create model from domain entity"""
        # Serialize equipment types to JSON
        equipment_json = None
        if entity.equipment_types:
            equipment_json = json.dumps(list(entity.equipment_types))
        
        # Serialize base location to JSON
        base_location_json = None
        if entity.base_location:
            base_location_json = json.dumps(entity.base_location)
        
        # Convert hourly rate to cents
        hourly_rate_cents = None
        if entity.hourly_rate is not None:
            hourly_rate_cents = int(entity.hourly_rate * 100)
        
        return cls(
            id=entity.id,
            name=entity.name,
            team_size=entity.team_size,
            equipment_types=equipment_json,
            service_radius_km=int(entity.service_radius_km),
            max_vehicles_per_day=entity.max_vehicles_per_day,
            hourly_rate=hourly_rate_cents,
            is_active=entity.is_active,
            base_location=base_location_json,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=None
        )
    
    def update_from_entity(self, entity: MobileWashTeam) -> None:
        """Update model from domain entity"""
        # Serialize equipment types to JSON
        equipment_json = None
        if entity.equipment_types:
            equipment_json = json.dumps(list(entity.equipment_types))
        
        # Serialize base location to JSON
        base_location_json = None
        if entity.base_location:
            base_location_json = json.dumps(entity.base_location)
        
        # Convert hourly rate to cents
        hourly_rate_cents = None
        if entity.hourly_rate is not None:
            hourly_rate_cents = int(entity.hourly_rate * 100)
        
        self.name = entity.name
        self.team_size = entity.team_size
        self.equipment_types = equipment_json
        self.service_radius_km = int(entity.service_radius_km)
        self.max_vehicles_per_day = entity.max_vehicles_per_day
        self.hourly_rate = hourly_rate_cents
        self.is_active = entity.is_active
        self.base_location = base_location_json
        self.notes = entity.notes
        self.updated_at = None


class WashFacilityConfigurationModel(Base):
    """Wash facility configuration database model"""
    __tablename__ = "wash_facility_configuration"
    
    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4)
    facility_name = Column(String(200), nullable=False, index=True)
    total_wash_bays = Column(Integer, nullable=False, default=0)
    total_mobile_teams = Column(Integer, nullable=False, default=0)
    operating_hours = Column(Text, nullable=True)  # JSON with operating hours
    default_service_duration_minutes = Column(Integer, nullable=False, default=60)
    buffer_between_services_minutes = Column(Integer, nullable=False, default=15)
    max_advance_booking_days = Column(Integer, nullable=False, default=30)
    settings = Column(Text, nullable=True)  # JSON for additional settings
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), onupdate=db_utc_timestamp())
    
    def to_entity(self) -> WashFacilityConfiguration:
        """Convert model to domain entity"""
        # Parse operating hours from JSON
        operating_hours = {}
        if self.operating_hours:
            try:
                operating_hours = json.loads(self.operating_hours)
            except (json.JSONDecodeError, TypeError):
                operating_hours = {}
        
        return WashFacilityConfiguration(
            id=self.id,
            facility_name=self.facility_name,
            total_wash_bays=self.total_wash_bays,
            total_mobile_teams=self.total_mobile_teams,
            operating_hours=operating_hours,
            default_service_duration_minutes=self.default_service_duration_minutes,
            buffer_between_services_minutes=self.buffer_between_services_minutes,
            max_advance_booking_days=self.max_advance_booking_days,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    @classmethod
    def from_entity(cls, entity: WashFacilityConfiguration) -> "WashFacilityConfigurationModel":
        """Create model from domain entity"""
        # Serialize operating hours to JSON
        operating_hours_json = None
        if entity.operating_hours:
            operating_hours_json = json.dumps(entity.operating_hours)
        
        return cls(
            id=entity.id,
            facility_name=entity.facility_name,
            total_wash_bays=entity.total_wash_bays,
            total_mobile_teams=entity.total_mobile_teams,
            operating_hours=operating_hours_json,
            default_service_duration_minutes=entity.default_service_duration_minutes,
            buffer_between_services_minutes=entity.buffer_between_services_minutes,
            max_advance_booking_days=entity.max_advance_booking_days,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    def update_from_entity(self, entity: WashFacilityConfiguration) -> None:
        """Update model from domain entity"""
        # Serialize operating hours to JSON
        operating_hours_json = None
        if entity.operating_hours:
            operating_hours_json = json.dumps(entity.operating_hours)
        
        self.facility_name = entity.facility_name
        self.total_wash_bays = entity.total_wash_bays
        self.total_mobile_teams = entity.total_mobile_teams
        self.operating_hours = operating_hours_json
        self.default_service_duration_minutes = entity.default_service_duration_minutes
        self.buffer_between_services_minutes = entity.buffer_between_services_minutes
        self.max_advance_booking_days = entity.max_advance_booking_days
        self.updated_at = entity.updated_at


class CapacityAllocationModel(Base):
    """Capacity allocation tracking database model"""
    __tablename__ = "capacity_allocations"
    
    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4)
    date = Column(DateTime, nullable=False, index=True)
    wash_type = Column(String(20), nullable=False, index=True)  # stationary, mobile
    resource_id = Column(PostgreSQL_UUID(as_uuid=True), nullable=False, index=True)
    resource_name = Column(String(100), nullable=False)
    allocated_slots = Column(Integer, nullable=False, default=0)
    max_capacity = Column(Integer, nullable=False, default=1)
    bookings = Column(Text, nullable=True)  # JSON array of booking IDs
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), onupdate=db_utc_timestamp())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_capacity_date_type', 'date', 'wash_type'),
        Index('idx_capacity_resource', 'resource_id', 'date'),
        Index('idx_capacity_allocation', 'allocated_slots', 'max_capacity'),
    )
    
    def to_entity(self) -> CapacityAllocation:
        """Convert model to domain entity"""
        from uuid import UUID
        
        # Parse bookings from JSON
        bookings = []
        if self.bookings:
            try:
                booking_data = json.loads(self.bookings)
                bookings = [UUID(booking_id) for booking_id in booking_data] if isinstance(booking_data, list) else []
            except (json.JSONDecodeError, TypeError, ValueError):
                bookings = []
        
        return CapacityAllocation(
            date=self.date,
            wash_type=WashType(self.wash_type),
            resource_id=self.resource_id,
            resource_name=self.resource_name,
            allocated_slots=self.allocated_slots,
            max_capacity=self.max_capacity,
            bookings=bookings
        )
    
    @classmethod
    def from_entity(cls, entity: CapacityAllocation) -> "CapacityAllocationModel":
        """Create model from domain entity"""
        # Serialize bookings to JSON
        bookings_json = None
        if entity.bookings:
            bookings_json = json.dumps([str(booking_id) for booking_id in entity.bookings])
        
        return cls(
            date=entity.date,
            wash_type=entity.wash_type.value,
            resource_id=entity.resource_id,
            resource_name=entity.resource_name,
            allocated_slots=entity.allocated_slots,
            max_capacity=entity.max_capacity,
            bookings=bookings_json,
            created_at=None,
            updated_at=None
        )
    
    def update_from_entity(self, entity: CapacityAllocation) -> None:
        """Update model from domain entity"""
        # Serialize bookings to JSON
        bookings_json = None
        if entity.bookings:
            bookings_json = json.dumps([str(booking_id) for booking_id in entity.bookings])
        
        self.date = entity.date
        self.wash_type = entity.wash_type.value
        self.resource_id = entity.resource_id
        self.resource_name = entity.resource_name
        self.allocated_slots = entity.allocated_slots
        self.max_capacity = entity.max_capacity
        self.bookings = bookings_json
        self.updated_at = None