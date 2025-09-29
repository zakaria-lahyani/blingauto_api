"""
Scheduling repositories
"""
import json
from datetime import datetime, time, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src.features.scheduling.domain.entities import (
    BusinessHours, Resource, TimeSlot, SchedulingConflict,
    AvailabilityRequest, BusinessConfiguration
)
from src.features.scheduling.domain.enums import (
    DayOfWeek, ResourceType, ResourceStatus, SlotStatus, ConflictType
)
from .models import (
    BusinessHoursModel, ResourceModel, TimeSlotModel, SchedulingConfigurationModel,
    ResourceScheduleModel, SchedulingConflictModel
)


class BusinessHoursRepository:
    """Repository for business hours management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_all(self) -> Dict[DayOfWeek, BusinessHours]:
        """Get all business hours"""
        stmt = select(BusinessHoursModel).order_by(BusinessHoursModel.day_of_week)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        business_hours = {}
        for model in models:
            day_of_week = DayOfWeek(model.day_of_week)
            break_periods = []
            if model.break_periods:
                break_data = json.loads(model.break_periods)
                break_periods = [
                    (time.fromisoformat(period['start']), time.fromisoformat(period['end']))
                    for period in break_data
                ]
            
            business_hours[day_of_week] = BusinessHours(
                day_of_week=day_of_week,
                open_time=model.open_time or time(0, 0),
                close_time=model.close_time or time(23, 59),
                is_closed=model.is_closed,
                break_periods=break_periods,
                id=model.id
            )
        
        return business_hours
    
    async def get_for_day(self, day_of_week: DayOfWeek) -> Optional[BusinessHours]:
        """Get business hours for specific day"""
        stmt = select(BusinessHoursModel).where(BusinessHoursModel.day_of_week == day_of_week.value)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        break_periods = []
        if model.break_periods:
            break_data = json.loads(model.break_periods)
            break_periods = [
                (time.fromisoformat(period['start']), time.fromisoformat(period['end']))
                for period in break_data
            ]
        
        return BusinessHours(
            day_of_week=day_of_week,
            open_time=model.open_time or time(0, 0),
            close_time=model.close_time or time(23, 59),
            is_closed=model.is_closed,
            break_periods=break_periods,
            id=model.id
        )
    
    async def create_or_update(self, business_hours: BusinessHours) -> BusinessHours:
        """Create or update business hours for a day"""
        # Check if exists
        stmt = select(BusinessHoursModel).where(
            BusinessHoursModel.day_of_week == business_hours.day_of_week.value
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        # Prepare break periods JSON
        break_periods_json = None
        if business_hours.break_periods:
            break_periods_json = json.dumps([
                {'start': period[0].isoformat(), 'end': period[1].isoformat()}
                for period in business_hours.break_periods
            ])
        
        if model:
            # Update existing
            model.open_time = business_hours.open_time
            model.close_time = business_hours.close_time
            model.is_closed = business_hours.is_closed
            model.break_periods = break_periods_json
            model.updated_at = datetime.utcnow()
        else:
            # Create new
            model = BusinessHoursModel(
                day_of_week=business_hours.day_of_week.value,
                open_time=business_hours.open_time,
                close_time=business_hours.close_time,
                is_closed=business_hours.is_closed,
                break_periods=break_periods_json
            )
            self.session.add(model)
        
        await self.session.commit()
        await self.session.refresh(model)
        
        business_hours.id = model.id
        return business_hours


class ResourceRepository:
    """Repository for resource management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, resource: Resource) -> Resource:
        """Create a new resource"""
        skills_json = json.dumps(list(resource.skills)) if resource.skills else None
        
        model = ResourceModel(
            name=resource.name,
            resource_type=resource.resource_type.value,
            capacity=resource.capacity,
            status=resource.status.value,
            skills=skills_json,
            hourly_rate=int(resource.hourly_rate * 100) if resource.hourly_rate else None
        )
        
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        
        resource.id = model.id
        return resource
    
    async def get_by_id(self, resource_id: UUID) -> Optional[Resource]:
        """Get resource by ID"""
        stmt = select(ResourceModel).where(ResourceModel.id == resource_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        skills = set()
        if model.skills:
            skills = set(json.loads(model.skills))
        
        return Resource(
            name=model.name,
            resource_type=ResourceType(model.resource_type),
            capacity=model.capacity,
            status=ResourceStatus(model.status),
            skills=skills,
            hourly_rate=model.hourly_rate / 100 if model.hourly_rate else None,
            id=model.id,
            created_at=model.created_at
        )
    
    async def get_available_resources(
        self,
        resource_type: Optional[ResourceType] = None,
        required_skills: Optional[set] = None
    ) -> List[Resource]:
        """Get available resources with optional filtering"""
        stmt = select(ResourceModel).where(ResourceModel.status == ResourceStatus.AVAILABLE.value)
        
        if resource_type:
            stmt = stmt.where(ResourceModel.resource_type == resource_type.value)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        resources = []
        for model in models:
            skills = set()
            if model.skills:
                skills = set(json.loads(model.skills))
            
            resource = Resource(
                name=model.name,
                resource_type=ResourceType(model.resource_type),
                capacity=model.capacity,
                status=ResourceStatus(model.status),
                skills=skills,
                hourly_rate=model.hourly_rate / 100 if model.hourly_rate else None,
                id=model.id,
                created_at=model.created_at
            )
            
            # Filter by required skills if specified
            if required_skills and not resource.can_handle_service(required_skills):
                continue
            
            resources.append(resource)
        
        return resources
    
    async def update_status(self, resource_id: UUID, status: ResourceStatus) -> bool:
        """Update resource status"""
        stmt = select(ResourceModel).where(ResourceModel.id == resource_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        model.status = status.value
        model.updated_at = datetime.utcnow()
        await self.session.commit()
        
        return True


class TimeSlotRepository:
    """Repository for time slot management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_available_slots(
        self,
        start_time: datetime,
        end_time: datetime,
        resource_ids: Optional[List[UUID]] = None,
        min_duration_minutes: Optional[int] = None
    ) -> List[TimeSlot]:
        """Get available time slots within date range"""
        stmt = select(TimeSlotModel).where(
            and_(
                TimeSlotModel.start_time >= start_time,
                TimeSlotModel.end_time <= end_time,
                TimeSlotModel.status == SlotStatus.AVAILABLE.value
            )
        )
        
        if resource_ids:
            stmt = stmt.where(TimeSlotModel.resource_id.in_(resource_ids))
        
        stmt = stmt.order_by(TimeSlotModel.start_time)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        slots = []
        for model in models:
            slot = TimeSlot(
                start_time=model.start_time,
                end_time=model.end_time,
                resource_id=model.resource_id,
                status=SlotStatus(model.status),
                booking_id=model.booking_id,
                blocked_reason=model.blocked_reason,
                id=model.id
            )
            
            # Filter by minimum duration if specified
            if min_duration_minutes and not slot.can_accommodate_duration(min_duration_minutes):
                continue
            
            slots.append(slot)
        
        return slots
    
    async def check_conflicts(
        self,
        start_time: datetime,
        end_time: datetime,
        resource_id: Optional[UUID] = None,
        exclude_booking_id: Optional[UUID] = None
    ) -> List[TimeSlot]:
        """Check for conflicting time slots"""
        stmt = select(TimeSlotModel).where(
            and_(
                or_(
                    and_(
                        TimeSlotModel.start_time < end_time,
                        TimeSlotModel.end_time > start_time
                    )
                ),
                TimeSlotModel.status.in_([SlotStatus.BOOKED.value, SlotStatus.BLOCKED.value])
            )
        )
        
        if resource_id:
            stmt = stmt.where(TimeSlotModel.resource_id == resource_id)
        
        if exclude_booking_id:
            stmt = stmt.where(TimeSlotModel.booking_id != exclude_booking_id)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        conflicts = []
        for model in models:
            conflicts.append(TimeSlot(
                start_time=model.start_time,
                end_time=model.end_time,
                resource_id=model.resource_id,
                status=SlotStatus(model.status),
                booking_id=model.booking_id,
                blocked_reason=model.blocked_reason,
                id=model.id
            ))
        
        return conflicts
    
    async def create_slot(self, time_slot: TimeSlot) -> TimeSlot:
        """Create a new time slot"""
        model = TimeSlotModel(
            start_time=time_slot.start_time,
            end_time=time_slot.end_time,
            resource_id=time_slot.resource_id,
            status=time_slot.status.value,
            booking_id=time_slot.booking_id,
            blocked_reason=time_slot.blocked_reason
        )
        
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        
        time_slot.id = model.id
        return time_slot
    
    async def update_slot_status(
        self,
        slot_id: UUID,
        status: SlotStatus,
        booking_id: Optional[UUID] = None
    ) -> bool:
        """Update time slot status"""
        stmt = select(TimeSlotModel).where(TimeSlotModel.id == slot_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        model.status = status.value
        if booking_id:
            model.booking_id = booking_id
        model.updated_at = datetime.utcnow()
        
        await self.session.commit()
        return True
    
    async def generate_slots_for_period(
        self,
        start_date: datetime,
        end_date: datetime,
        resource_id: UUID,
        slot_duration_minutes: int,
        business_hours: Dict[DayOfWeek, BusinessHours]
    ) -> List[TimeSlot]:
        """Generate time slots for a period based on business hours"""
        slots = []
        current_date = start_date.date()
        
        day_mapping = {
            0: DayOfWeek.MONDAY,
            1: DayOfWeek.TUESDAY,
            2: DayOfWeek.WEDNESDAY,
            3: DayOfWeek.THURSDAY,
            4: DayOfWeek.FRIDAY,
            5: DayOfWeek.SATURDAY,
            6: DayOfWeek.SUNDAY
        }
        
        while current_date <= end_date.date():
            day_of_week = day_mapping[current_date.weekday()]
            hours = business_hours.get(day_of_week)
            
            if hours and not hours.is_closed:
                # Generate slots for this day
                slot_start = datetime.combine(current_date, hours.open_time)
                day_end = datetime.combine(current_date, hours.close_time)
                
                while slot_start < day_end:
                    slot_end = slot_start + timedelta(minutes=slot_duration_minutes)
                    if slot_end > day_end:
                        break
                    
                    # Check if slot overlaps with break periods
                    overlaps_break = False
                    for break_start, break_end in hours.break_periods:
                        break_start_dt = datetime.combine(current_date, break_start)
                        break_end_dt = datetime.combine(current_date, break_end)
                        
                        if slot_start < break_end_dt and slot_end > break_start_dt:
                            overlaps_break = True
                            break
                    
                    if not overlaps_break:
                        slot = TimeSlot(
                            start_time=slot_start,
                            end_time=slot_end,
                            resource_id=resource_id,
                            status=SlotStatus.AVAILABLE
                        )
                        
                        # Save slot to database
                        created_slot = await self.create_slot(slot)
                        slots.append(created_slot)
                    
                    slot_start = slot_end
            
            current_date += timedelta(days=1)
        
        return slots


class SchedulingConflictRepository:
    """Repository for scheduling conflicts"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log_conflict(self, conflict: SchedulingConflict, customer_id: UUID) -> None:
        """Log a scheduling conflict"""
        model = SchedulingConflictModel(
            conflict_type=conflict.conflict_type.value,
            message=conflict.message,
            requested_time=conflict.requested_time,
            conflicting_booking_id=conflict.conflicting_booking_id,
            resource_id=conflict.resource_id,
            customer_id=customer_id
        )
        
        self.session.add(model)
        await self.session.commit()
    
    async def get_conflicts_for_customer(
        self,
        customer_id: UUID,
        start_date: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conflicts for a customer"""
        stmt = select(SchedulingConflictModel).where(
            SchedulingConflictModel.customer_id == customer_id
        )
        
        if start_date:
            stmt = stmt.where(SchedulingConflictModel.created_at >= start_date)
        
        stmt = stmt.order_by(SchedulingConflictModel.created_at.desc()).limit(limit)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        conflicts = []
        for model in models:
            conflicts.append({
                'id': model.id,
                'conflict_type': model.conflict_type,
                'message': model.message,
                'requested_time': model.requested_time,
                'created_at': model.created_at,
                'resolved': model.resolved
            })
        
        return conflicts