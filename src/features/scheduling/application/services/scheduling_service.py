"""
Core scheduling service for availability discovery and conflict detection
"""
from datetime import datetime, timedelta, time
from typing import List, Optional, Set, Dict, Tuple
from uuid import UUID

from src.features.scheduling.domain.entities import (
    AvailabilityRequest, AvailabilityResponse, TimeSlot, SchedulingConflict,
    BusinessConfiguration, Resource, SchedulingPreferences, BusinessHours
)
from src.features.scheduling.domain.enums import (
    ConflictType, SlotStatus, ResourceStatus, DayOfWeek, SuggestionStrategy
)
from src.features.scheduling.infrastructure.database.repositories import (
    BusinessHoursRepository, ResourceRepository, TimeSlotRepository, SchedulingConflictRepository
)
from src.features.scheduling.infrastructure.database.wash_facility_repositories import (
    WashBayRepository, MobileWashTeamRepository, WashFacilityConfigurationRepository, CapacityAllocationRepository
)
from src.features.scheduling.domain.wash_facility_entities import WashType, WashBay, MobileWashTeam
from src.features.services.infrastructure.database.repositories import ServiceRepository


class SchedulingService:
    """Core scheduling service for time slot discovery and conflict detection"""
    
    def __init__(
        self,
        business_hours_repo: BusinessHoursRepository,
        resource_repo: ResourceRepository,
        time_slot_repo: TimeSlotRepository,
        conflict_repo: SchedulingConflictRepository,
        service_repo: ServiceRepository,
        wash_bay_repo: Optional[WashBayRepository] = None,
        mobile_team_repo: Optional[MobileWashTeamRepository] = None,
        facility_config_repo: Optional[WashFacilityConfigurationRepository] = None,
        capacity_allocation_repo: Optional[CapacityAllocationRepository] = None
    ):
        self.business_hours_repo = business_hours_repo
        self.resource_repo = resource_repo
        self.time_slot_repo = time_slot_repo
        self.conflict_repo = conflict_repo
        self.service_repo = service_repo
        
        # Wash facility repositories for capacity-based scheduling
        self.wash_bay_repo = wash_bay_repo
        self.mobile_team_repo = mobile_team_repo
        self.facility_config_repo = facility_config_repo
        self.capacity_allocation_repo = capacity_allocation_repo
        
        # Default configuration - could be loaded from database
        self.default_config = BusinessConfiguration(
            business_hours={},  # Will be loaded from repository
            slot_duration_minutes=30,
            buffer_between_bookings=15,
            max_advance_booking_days=90,
            min_advance_booking_hours=2
        )
    
    async def find_available_slots(
        self,
        request: AvailabilityRequest,
        customer_id: UUID,
        preferences: Optional[SchedulingPreferences] = None,
        wash_type: Optional[WashType] = None,
        vehicle_size: str = "standard",
        customer_location: Optional[Dict[str, float]] = None
    ) -> AvailabilityResponse:
        """Find available time slots based on request criteria with capacity-based allocation"""
        
        # Load business configuration
        business_hours = await self.business_hours_repo.get_all()
        self.default_config.business_hours = business_hours
        
        # If wash facility repositories are available, use capacity-based scheduling
        if wash_type and self._has_wash_facility_repos():
            return await self._find_available_slots_with_capacity(
                request=request,
                customer_id=customer_id,
                wash_type=wash_type,
                vehicle_size=vehicle_size,
                customer_location=customer_location,
                preferences=preferences
            )
        
        # Fallback to traditional resource-based scheduling
        available_resources = await self.resource_repo.get_available_resources(
            required_skills=request.required_skills
        )
        
        if not available_resources:
            return AvailabilityResponse(
                available_slots=[],
                conflicts=[SchedulingConflict(
                    conflict_type=ConflictType.RESOURCE_UNAVAILABLE,
                    message="No resources available with required skills",
                    requested_time=request.start_date
                )],
                suggested_times=[],
                total_available_slots=0,
                search_period=(request.start_date, request.end_date)
            )
        
        # Filter by preferred resources if specified
        if request.preferred_resources:
            preferred_available = [
                r for r in available_resources 
                if r.id in request.preferred_resources
            ]
            if preferred_available:
                available_resources = preferred_available
        
        # Find available slots for each resource
        all_available_slots = []
        conflicts = []
        
        for resource in available_resources:
            resource_slots, resource_conflicts = await self._find_slots_for_resource(
                resource=resource,
                request=request,
                business_hours=business_hours,
                preferences=preferences
            )
            
            all_available_slots.extend(resource_slots)
            conflicts.extend(resource_conflicts)
        
        # Remove duplicates and sort by start time
        unique_slots = self._deduplicate_slots(all_available_slots)
        unique_slots.sort(key=lambda slot: slot.start_time)
        
        # Generate suggested times based on strategy
        suggested_times = await self._generate_suggestions(
            available_slots=unique_slots,
            preferences=preferences,
            request=request
        )
        
        # Log conflicts for analytics
        for conflict in conflicts:
            await self.conflict_repo.log_conflict(conflict, customer_id)
        
        return AvailabilityResponse(
            available_slots=unique_slots,
            conflicts=conflicts,
            suggested_times=suggested_times,
            total_available_slots=len(unique_slots),
            search_period=(request.start_date, request.end_date)
        )
    
    async def check_booking_conflicts(
        self,
        start_time: datetime,
        duration_minutes: int,
        service_ids: List[UUID],
        customer_id: UUID,
        exclude_booking_id: Optional[UUID] = None
    ) -> List[SchedulingConflict]:
        """Check for conflicts when booking a specific time slot"""
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        conflicts = []
        
        # Load business configuration
        business_hours = await self.business_hours_repo.get_all()
        config = BusinessConfiguration(business_hours=business_hours)
        
        # Check business hours
        if not config.is_business_open_at(start_time):
            conflicts.append(SchedulingConflict(
                conflict_type=ConflictType.OUTSIDE_BUSINESS_HOURS,
                message=f"Requested time {start_time.strftime('%Y-%m-%d %H:%M')} is outside business hours",
                requested_time=start_time
            ))
        
        # Check if booking end time is within business hours
        business_hours_for_date = config.get_business_hours_for_date(start_time)
        if business_hours_for_date and not business_hours_for_date.is_closed:
            end_time_only = end_time.time()
            if end_time_only > business_hours_for_date.close_time:
                conflicts.append(SchedulingConflict(
                    conflict_type=ConflictType.OUTSIDE_BUSINESS_HOURS,
                    message=f"Booking would extend past business hours (closes at {business_hours_for_date.close_time})",
                    requested_time=start_time
                ))
        
        # Check minimum advance booking time
        now = datetime.utcnow()
        hours_in_advance = (start_time - now).total_seconds() / 3600
        if hours_in_advance < config.min_advance_booking_hours:
            conflicts.append(SchedulingConflict(
                conflict_type=ConflictType.INSUFFICIENT_DURATION,
                message=f"Booking requires at least {config.min_advance_booking_hours} hours advance notice",
                requested_time=start_time
            ))
        
        # Check maximum advance booking time
        days_in_advance = (start_time - now).days
        if days_in_advance > config.max_advance_booking_days:
            conflicts.append(SchedulingConflict(
                conflict_type=ConflictType.OUTSIDE_BUSINESS_HOURS,
                message=f"Cannot book more than {config.max_advance_booking_days} days in advance",
                requested_time=start_time
            ))
        
        # Get required skills for services
        required_skills = await self._get_required_skills_for_services(service_ids)
        
        # Get available resources that can handle the services
        available_resources = await self.resource_repo.get_available_resources(
            required_skills=required_skills
        )
        
        if not available_resources:
            conflicts.append(SchedulingConflict(
                conflict_type=ConflictType.RESOURCE_UNAVAILABLE,
                message="No resources available with required skills for selected services",
                requested_time=start_time
            ))
            return conflicts
        
        # Check for double booking conflicts
        for resource in available_resources:
            conflicting_slots = await self.time_slot_repo.check_conflicts(
                start_time=start_time,
                end_time=end_time,
                resource_id=resource.id,
                exclude_booking_id=exclude_booking_id
            )
            
            for conflicting_slot in conflicting_slots:
                conflicts.append(SchedulingConflict(
                    conflict_type=ConflictType.DOUBLE_BOOKING,
                    message=f"Time slot conflicts with existing booking on {resource.name}",
                    requested_time=start_time,
                    conflicting_booking_id=conflicting_slot.booking_id,
                    resource_id=resource.id
                ))
        
        return conflicts
    
    async def _find_slots_for_resource(
        self,
        resource: Resource,
        request: AvailabilityRequest,
        business_hours: Dict[DayOfWeek, BusinessHours],
        preferences: Optional[SchedulingPreferences] = None
    ) -> Tuple[List[TimeSlot], List[SchedulingConflict]]:
        """Find available slots for a specific resource"""
        
        # Get existing slots for this resource in the time period
        existing_slots = await self.time_slot_repo.get_available_slots(
            start_time=request.start_date,
            end_time=request.end_date,
            resource_ids=[resource.id],
            min_duration_minutes=request.duration_minutes
        )
        
        # If no existing slots, generate them
        if not existing_slots:
            existing_slots = await self.time_slot_repo.generate_slots_for_period(
                start_date=request.start_date,
                end_date=request.end_date,
                resource_id=resource.id,
                slot_duration_minutes=self.default_config.slot_duration_minutes,
                business_hours=business_hours
            )
        
        # Filter slots based on preferences
        filtered_slots = []
        conflicts = []
        
        for slot in existing_slots:
            # Check if slot meets duration requirements
            if not slot.can_accommodate_duration(request.duration_minutes):
                continue
            
            # Check if slot is available
            if not slot.is_available():
                continue
            
            # Apply preference filters
            if preferences:
                # Check preferred days
                if not preferences.matches_preferred_day(slot.start_time):
                    continue
                
                # Check preferred times
                if not preferences.matches_preferred_time(slot.start_time.time()):
                    continue
                
                # Check avoid times
                if preferences.should_avoid_time(slot.start_time.time()):
                    continue
            
            # Check against excluded times
            slot_conflicts_with_exclusions = False
            for exclude_start, exclude_end in request.exclude_times:
                if slot.start_time < exclude_end and slot.end_time > exclude_start:
                    slot_conflicts_with_exclusions = True
                    break
            
            if slot_conflicts_with_exclusions:
                continue
            
            filtered_slots.append(slot)
        
        return filtered_slots, conflicts
    
    async def _generate_suggestions(
        self,
        available_slots: List[TimeSlot],
        preferences: Optional[SchedulingPreferences],
        request: AvailabilityRequest
    ) -> List[datetime]:
        """Generate suggested appointment times based on strategy"""
        
        if not available_slots:
            return []
        
        strategy = preferences.strategy if preferences else SuggestionStrategy.EARLIEST_AVAILABLE
        suggestions = []
        
        if strategy == SuggestionStrategy.EARLIEST_AVAILABLE:
            # Return earliest slots
            suggestions = [slot.start_time for slot in available_slots[:5]]
        
        elif strategy == SuggestionStrategy.CLOSEST_TO_REQUESTED:
            # Find slots closest to requested start time
            slots_with_distance = [
                (slot, abs((slot.start_time - request.start_date).total_seconds()))
                for slot in available_slots
            ]
            slots_with_distance.sort(key=lambda x: x[1])
            suggestions = [slot[0].start_time for slot in slots_with_distance[:5]]
        
        elif strategy == SuggestionStrategy.MINIMIZE_GAPS:
            # Prefer slots that minimize gaps in schedule
            # This is a simplified implementation
            suggestions = [slot.start_time for slot in available_slots[:5]]
        
        elif strategy == SuggestionStrategy.LOAD_BALANCING:
            # Distribute load across different time periods
            # Group by hour and pick from different hours
            hour_groups = {}
            for slot in available_slots:
                hour = slot.start_time.hour
                if hour not in hour_groups:
                    hour_groups[hour] = []
                hour_groups[hour].append(slot)
            
            # Pick one from each hour group
            for hour_slots in hour_groups.values():
                if len(suggestions) < 5:
                    suggestions.append(hour_slots[0].start_time)
        
        else:  # CUSTOMER_PREFERENCE or fallback
            # Apply customer preferences more heavily
            if preferences:
                preferred_slots = []
                for slot in available_slots:
                    if (preferences.matches_preferred_day(slot.start_time) and
                        preferences.matches_preferred_time(slot.start_time.time())):
                        preferred_slots.append(slot)
                
                if preferred_slots:
                    suggestions = [slot.start_time for slot in preferred_slots[:5]]
                else:
                    suggestions = [slot.start_time for slot in available_slots[:5]]
            else:
                suggestions = [slot.start_time for slot in available_slots[:5]]
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    async def _get_required_skills_for_services(self, service_ids: List[UUID]) -> Set[str]:
        """Get required skills for a list of services"""
        required_skills = set()
        
        for service_id in service_ids:
            service = await self.service_repo.get_by_id(service_id)
            if service and hasattr(service, 'required_skills'):
                # Assuming service has required_skills field
                # This would need to be added to the service entity
                required_skills.update(service.required_skills or set())
        
        return required_skills
    
    def _deduplicate_slots(self, slots: List[TimeSlot]) -> List[TimeSlot]:
        """Remove duplicate time slots"""
        seen_times = set()
        unique_slots = []
        
        for slot in slots:
            slot_key = (slot.start_time, slot.end_time)
            if slot_key not in seen_times:
                seen_times.add(slot_key)
                unique_slots.append(slot)
        
        return unique_slots
    
    async def reserve_time_slot(
        self,
        start_time: datetime,
        duration_minutes: int,
        resource_id: UUID,
        booking_id: UUID
    ) -> bool:
        """Reserve a time slot for a booking"""
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Check for conflicts one more time
        conflicts = await self.time_slot_repo.check_conflicts(
            start_time=start_time,
            end_time=end_time,
            resource_id=resource_id
        )
        
        if conflicts:
            return False
        
        # Create or update time slot
        slot = TimeSlot(
            start_time=start_time,
            end_time=end_time,
            resource_id=resource_id,
            status=SlotStatus.BOOKED,
            booking_id=booking_id
        )
        
        await self.time_slot_repo.create_slot(slot)
        return True
    
    async def release_time_slot(self, booking_id: UUID) -> bool:
        """Release a time slot when booking is cancelled"""
        
        # Find slots associated with this booking
        # This would require adding a method to find slots by booking_id
        # For now, we'll mark it as available
        
        # This is a simplified implementation
        # In practice, you'd find the specific slot and update its status
        return True
    
    def _has_wash_facility_repos(self) -> bool:
        """Check if wash facility repositories are available"""
        return all([
            self.wash_bay_repo is not None,
            self.mobile_team_repo is not None,
            self.facility_config_repo is not None,
            self.capacity_allocation_repo is not None
        ])
    
    async def _find_available_slots_with_capacity(
        self,
        request: AvailabilityRequest,
        customer_id: UUID,
        wash_type: WashType,
        vehicle_size: str = "standard",
        customer_location: Optional[Dict[str, float]] = None,
        preferences: Optional[SchedulingPreferences] = None
    ) -> AvailabilityResponse:
        """Find available slots using capacity-based allocation"""
        
        # Get available resources based on wash type
        if wash_type == WashType.STATIONARY:
            suitable_resources = await self.wash_bay_repo.get_available_for_vehicle_size(vehicle_size)
        elif wash_type == WashType.MOBILE:
            all_teams = await self.mobile_team_repo.get_all(active_only=True)
            suitable_resources = []
            for team in all_teams:
                if customer_location and not team.can_service_location(customer_location):
                    continue
                suitable_resources.append(team)
        else:
            suitable_resources = []
        
        if not suitable_resources:
            return AvailabilityResponse(
                available_slots=[],
                conflicts=[SchedulingConflict(
                    conflict_type=ConflictType.RESOURCE_UNAVAILABLE,
                    message=f"No {wash_type.value} resources available",
                    requested_time=request.start_date
                )],
                suggested_times=[],
                total_available_slots=0,
                search_period=(request.start_date, request.end_date)
            )
        
        # Generate time slots based on business hours and check capacity
        all_available_slots = []
        conflicts = []
        
        current_date = request.start_date.date()
        end_date = request.end_date.date()
        
        while current_date <= end_date:
            # Get business hours for this day
            day_of_week = DayOfWeek(current_date.weekday())
            business_hours_today = self.default_config.business_hours.get(day_of_week)
            
            if not business_hours_today or business_hours_today.is_closed:
                current_date += timedelta(days=1)
                continue
            
            # Generate slots for this day
            day_slots = await self._generate_slots_for_day_with_capacity(
                date=current_date,
                business_hours=business_hours_today,
                suitable_resources=suitable_resources,
                wash_type=wash_type,
                request=request
            )
            
            all_available_slots.extend(day_slots)
            current_date += timedelta(days=1)
        
        # Apply preferences if provided
        if preferences:
            filtered_slots = []
            for slot in all_available_slots:
                if preferences.matches_preferred_day(slot.start_time) and \
                   preferences.matches_preferred_time(slot.start_time.time()) and \
                   not preferences.should_avoid_time(slot.start_time.time()):
                    filtered_slots.append(slot)
            all_available_slots = filtered_slots
        
        # Generate suggestions based on strategy
        suggested_times = await self._generate_suggestions(
            available_slots=all_available_slots,
            preferences=preferences,
            request=request
        )
        
        return AvailabilityResponse(
            available_slots=all_available_slots,
            conflicts=conflicts,
            suggested_times=suggested_times,
            total_available_slots=len(all_available_slots),
            search_period=(request.start_date, request.end_date)
        )
    
    async def _generate_slots_for_day_with_capacity(
        self,
        date: datetime.date,
        business_hours: BusinessHours,
        suitable_resources: List,
        wash_type: WashType,
        request: AvailabilityRequest
    ) -> List[TimeSlot]:
        """Generate available time slots for a day with capacity checking"""
        
        slots = []
        slot_duration = self.default_config.slot_duration_minutes
        buffer_time = self.default_config.buffer_between_bookings
        
        # Convert business hours to datetime objects for this date
        start_datetime = datetime.combine(date, business_hours.open_time)
        end_datetime = datetime.combine(date, business_hours.close_time)
        
        current_time = start_datetime
        
        while current_time + timedelta(minutes=request.duration_minutes) <= end_datetime:
            # Check if this time is during a break period
            is_break_time = False
            for break_start, break_end in business_hours.break_periods:
                break_start_dt = datetime.combine(date, break_start)
                break_end_dt = datetime.combine(date, break_end)
                
                if current_time < break_end_dt and current_time + timedelta(minutes=request.duration_minutes) > break_start_dt:
                    is_break_time = True
                    break
            
            if is_break_time:
                current_time += timedelta(minutes=slot_duration)
                continue
            
            # Check capacity for each suitable resource
            for resource in suitable_resources:
                allocation = await self.capacity_allocation_repo.get_allocation_for_date_and_resource(
                    date=datetime.combine(date, time.min),
                    resource_id=resource.id,
                    wash_type=wash_type
                )
                
                # If no allocation exists or has available capacity
                if not allocation or allocation.is_available():
                    slot = TimeSlot(
                        start_time=current_time,
                        end_time=current_time + timedelta(minutes=request.duration_minutes),
                        resource_id=resource.id,
                        status=SlotStatus.AVAILABLE
                    )
                    slots.append(slot)
                    break  # Only need one available resource per time slot
            
            current_time += timedelta(minutes=slot_duration)
        
        return slots
    
    async def reserve_capacity_slot(
        self,
        start_time: datetime,
        wash_type: WashType,
        resource_id: UUID,
        resource_name: str,
        booking_id: UUID
    ) -> bool:
        """Reserve capacity for a booking"""
        if not self._has_wash_facility_repos():
            return await self.reserve_time_slot(
                start_time=start_time,
                duration_minutes=60,  # Default duration
                resource_id=resource_id,
                booking_id=booking_id
            )
        
        # Allocate capacity using wash facility service
        return await self.capacity_allocation_repo.create_or_update_allocation(
            allocation=None  # This should be implemented properly
        )
    
    async def release_capacity_slot(
        self,
        start_time: datetime,
        wash_type: WashType,
        resource_id: UUID,
        booking_id: UUID
    ) -> bool:
        """Release capacity for a cancelled booking"""
        if not self._has_wash_facility_repos():
            return await self.release_time_slot(booking_id)
        
        # Release capacity using wash facility service
        date = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        allocation = await self.capacity_allocation_repo.get_allocation_for_date_and_resource(
            date=date,
            resource_id=resource_id,
            wash_type=wash_type
        )
        
        if allocation and allocation.release_slot(booking_id):
            await self.capacity_allocation_repo.create_or_update_allocation(allocation)
            return True
        
        return False