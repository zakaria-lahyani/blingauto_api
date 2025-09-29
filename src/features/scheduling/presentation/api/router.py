"""
Scheduling API router
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.simple_database import get_db
from src.shared.auth import get_current_user, get_current_active_user, require_admin
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole
from src.features.scheduling.application.services.scheduling_service import SchedulingService
from src.features.scheduling.infrastructure.database.repositories import (
    BusinessHoursRepository, ResourceRepository, TimeSlotRepository, SchedulingConflictRepository
)
from src.features.services.infrastructure.database.repositories import ServiceRepository
from src.features.scheduling.domain.entities import (
    AvailabilityRequest as DomainAvailabilityRequest,
    SchedulingPreferences, BusinessHours, Resource
)
from src.features.scheduling.domain.enums import (
    DayOfWeek, ResourceType, ResourceStatus, SuggestionStrategy
)
from .schemas import (
    AvailabilityRequest, AvailabilityResponse, ConflictCheckRequest, ConflictCheckResponse,
    TimeSuggestionRequest, TimeSuggestionResponse, BusinessHoursRequest, BusinessHoursSchema,
    CreateResourceRequest, UpdateResourceRequest, ResourceSchema, SchedulingPreferencesRequest,
    BusinessConfigurationSchema, UpdateBusinessConfigurationRequest, ResourceAvailabilityRequest,
    ResourceAvailabilityResponse, SuccessResponse, TimeSlotSchema, ConflictSchema
)

router = APIRouter(prefix="/scheduling", tags=["Scheduling"])


# Authentication dependencies now imported from shared module


def get_scheduling_service(db: AsyncSession = Depends(get_db)) -> SchedulingService:
    """Dependency to get scheduling service"""
    business_hours_repo = BusinessHoursRepository(db)
    resource_repo = ResourceRepository(db)
    time_slot_repo = TimeSlotRepository(db)
    conflict_repo = SchedulingConflictRepository(db)
    service_repo = ServiceRepository(db)
    
    return SchedulingService(
        business_hours_repo=business_hours_repo,
        resource_repo=resource_repo,
        time_slot_repo=time_slot_repo,
        conflict_repo=conflict_repo,
        service_repo=service_repo
    )


# ============= AVAILABILITY ENDPOINTS =============

@router.post("/availability", response_model=AvailabilityResponse)
async def check_availability(
    request: AvailabilityRequest,
    preferences: Optional[SchedulingPreferencesRequest] = None,
    current_user: AuthUser = Depends(get_current_active_user),
    scheduling_service: SchedulingService = Depends(get_scheduling_service)
):
    """Check availability for booking appointments"""
    try:
        # Convert request to domain object
        exclude_times = []
        for exclude in request.exclude_times:
            exclude_times.append((
                datetime.fromisoformat(exclude['start']),
                datetime.fromisoformat(exclude['end'])
            ))
        
        # Get required skills from services
        required_skills = set()  # Would be populated from service lookup
        
        domain_request = DomainAvailabilityRequest(
            start_date=request.start_date,
            end_date=request.end_date,
            duration_minutes=request.duration_minutes,
            required_skills=required_skills,
            preferred_resources=request.preferred_resources,
            exclude_times=exclude_times
        )
        
        # Convert preferences if provided
        domain_preferences = None
        if preferences:
            preferred_times = []
            for time_range in preferences.preferred_times:
                preferred_times.append((
                    datetime.strptime(time_range['start'], '%H:%M').time(),
                    datetime.strptime(time_range['end'], '%H:%M').time()
                ))
            
            avoid_times = []
            for time_range in preferences.avoid_times:
                avoid_times.append((
                    datetime.strptime(time_range['start'], '%H:%M').time(),
                    datetime.strptime(time_range['end'], '%H:%M').time()
                ))
            
            domain_preferences = SchedulingPreferences(
                preferred_days=preferences.preferred_days,
                preferred_times=preferred_times,
                avoid_times=avoid_times,
                preferred_resources=preferences.preferred_resources,
                buffer_time=preferences.buffer_time,
                strategy=preferences.strategy
            )
        
        # Get availability
        availability = await scheduling_service.find_available_slots(
            request=domain_request,
            customer_id=current_user.id,
            preferences=domain_preferences
        )
        
        # Convert response
        available_slots = [
            TimeSlotSchema(
                id=slot.id,
                start_time=slot.start_time,
                end_time=slot.end_time,
                resource_id=slot.resource_id,
                status=slot.status.value,
                booking_id=slot.booking_id,
                duration_minutes=slot.duration_minutes
            )
            for slot in availability.available_slots
        ]
        
        conflicts = [
            ConflictSchema(
                conflict_type=conflict.conflict_type,
                message=conflict.message,
                requested_time=conflict.requested_time,
                conflicting_booking_id=conflict.conflicting_booking_id,
                resource_id=conflict.resource_id,
                suggested_alternatives=conflict.suggested_alternatives
            )
            for conflict in availability.conflicts
        ]
        
        return AvailabilityResponse(
            available_slots=available_slots,
            conflicts=conflicts,
            suggested_times=availability.suggested_times,
            total_available_slots=availability.total_available_slots,
            search_period={
                'start': availability.search_period[0].isoformat(),
                'end': availability.search_period[1].isoformat()
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check availability"
        )


@router.post("/conflicts/check", response_model=ConflictCheckResponse)
async def check_conflicts(
    request: ConflictCheckRequest,
    current_user: AuthUser = Depends(get_current_active_user),
    scheduling_service: SchedulingService = Depends(get_scheduling_service)
):
    """Check for scheduling conflicts at a specific time"""
    try:
        conflicts = await scheduling_service.check_booking_conflicts(
            start_time=request.start_time,
            duration_minutes=request.duration_minutes,
            service_ids=request.service_ids,
            customer_id=current_user.id,
            exclude_booking_id=request.exclude_booking_id
        )
        
        conflicts_schema = [
            ConflictSchema(
                conflict_type=conflict.conflict_type,
                message=conflict.message,
                requested_time=conflict.requested_time,
                conflicting_booking_id=conflict.conflicting_booking_id,
                resource_id=conflict.resource_id,
                suggested_alternatives=conflict.suggested_alternatives
            )
            for conflict in conflicts
        ]
        
        return ConflictCheckResponse(
            has_conflicts=len(conflicts) > 0,
            conflicts=conflicts_schema,
            is_bookable=len(conflicts) == 0,
            suggested_alternatives=[]  # Would be populated from conflict resolution
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check conflicts"
        )


@router.post("/suggestions", response_model=TimeSuggestionResponse)
async def get_time_suggestions(
    request: TimeSuggestionRequest,
    current_user: AuthUser = Depends(get_current_active_user),
    scheduling_service: SchedulingService = Depends(get_scheduling_service)
):
    """Get suggested appointment times"""
    try:
        # Set search period if no preferred date
        if request.preferred_date:
            start_date = request.preferred_date.replace(hour=0, minute=0, second=0)
            end_date = request.preferred_date.replace(hour=23, minute=59, second=59)
        else:
            start_date = datetime.utcnow()
            end_date = start_date.replace(hour=23, minute=59, second=59)
        
        # Create availability request
        domain_request = DomainAvailabilityRequest(
            start_date=start_date,
            end_date=end_date,
            duration_minutes=request.duration_minutes,
            required_skills=set()  # Would be populated from service lookup
        )
        
        # Convert preferences
        domain_preferences = None
        if request.preferences:
            domain_preferences = SchedulingPreferences(
                strategy=request.preferences.strategy,
                buffer_time=request.preferences.buffer_time
            )
        
        # Get suggestions
        availability = await scheduling_service.find_available_slots(
            request=domain_request,
            customer_id=current_user.id,
            preferences=domain_preferences
        )
        
        # Format suggestions
        suggestions = []
        for i, suggested_time in enumerate(availability.suggested_times[:request.max_suggestions]):
            suggestions.append({
                'time': suggested_time.isoformat(),
                'resource_name': f'Available Resource',  # Would lookup actual resource name
                'confidence': max(0.5, 1.0 - (i * 0.1))  # Simple confidence calculation
            })
        
        return TimeSuggestionResponse(
            suggestions=suggestions,
            total_suggestions=len(suggestions),
            search_period={
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            preferences_applied=request.preferences is not None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestions"
        )


# ============= BUSINESS HOURS ENDPOINTS =============

@router.get("/business-hours", response_model=List[BusinessHoursSchema])
async def get_business_hours(
    scheduling_service: SchedulingService = Depends(get_scheduling_service)
):
    """Get business hours for all days"""
    try:
        business_hours = await scheduling_service.business_hours_repo.get_all()
        
        result = []
        for day_of_week, hours in business_hours.items():
            break_periods = [
                {'start': period[0].strftime('%H:%M'), 'end': period[1].strftime('%H:%M')}
                for period in hours.break_periods
            ]
            
            result.append(BusinessHoursSchema(
                day_of_week=day_of_week,
                open_time=hours.open_time,
                close_time=hours.close_time,
                is_closed=hours.is_closed,
                break_periods=break_periods
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get business hours"
        )


@router.put("/business-hours", response_model=SuccessResponse)
async def update_business_hours(
    hours_list: List[BusinessHoursRequest],
    current_user: AuthUser = Depends(require_admin),
    scheduling_service: SchedulingService = Depends(get_scheduling_service)
):
    """Update business hours (admin only)"""
    try:
        for hours_request in hours_list:
            # Convert break periods
            break_periods = []
            for period in hours_request.break_periods:
                break_periods.append((
                    datetime.strptime(period['start'], '%H:%M').time(),
                    datetime.strptime(period['end'], '%H:%M').time()
                ))
            
            # Create domain object
            business_hours = BusinessHours(
                day_of_week=hours_request.day_of_week,
                open_time=hours_request.open_time,
                close_time=hours_request.close_time,
                is_closed=hours_request.is_closed,
                break_periods=break_periods
            )
            
            # Save
            await scheduling_service.business_hours_repo.create_or_update(business_hours)
        
        return SuccessResponse(
            message="Business hours updated successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update business hours"
        )


# ============= RESOURCE ENDPOINTS =============

@router.get("/resources", response_model=List[ResourceSchema])
async def list_resources(
    resource_type: Optional[ResourceType] = Query(None),
    status: Optional[ResourceStatus] = Query(None),
    current_user: AuthUser = Depends(get_current_active_user),
    scheduling_service: SchedulingService = Depends(get_scheduling_service)
):
    """List available resources"""
    try:
        resources = await scheduling_service.resource_repo.get_available_resources(
            resource_type=resource_type
        )
        
        if status:
            resources = [r for r in resources if r.status == status]
        
        return [
            ResourceSchema(
                id=resource.id,
                name=resource.name,
                resource_type=resource.resource_type,
                capacity=resource.capacity,
                status=resource.status,
                skills=resource.skills,
                hourly_rate=resource.hourly_rate,
                created_at=resource.created_at
            )
            for resource in resources
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list resources"
        )


@router.post("/resources", response_model=ResourceSchema)
async def create_resource(
    request: CreateResourceRequest,
    current_user: AuthUser = Depends(require_admin),
    scheduling_service: SchedulingService = Depends(get_scheduling_service)
):
    """Create a new resource (admin only)"""
    try:
        resource = Resource(
            name=request.name,
            resource_type=request.resource_type,
            capacity=request.capacity,
            skills=request.skills,
            hourly_rate=request.hourly_rate
        )
        
        created_resource = await scheduling_service.resource_repo.create(resource)
        
        return ResourceSchema(
            id=created_resource.id,
            name=created_resource.name,
            resource_type=created_resource.resource_type,
            capacity=created_resource.capacity,
            status=created_resource.status,
            skills=created_resource.skills,
            hourly_rate=created_resource.hourly_rate,
            created_at=created_resource.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create resource"
        )


@router.put("/resources/{resource_id}/status", response_model=SuccessResponse)
async def update_resource_status(
    resource_id: UUID,
    status: ResourceStatus,
    current_user: AuthUser = Depends(require_admin),
    scheduling_service: SchedulingService = Depends(get_scheduling_service)
):
    """Update resource status (admin only)"""
    try:
        success = await scheduling_service.resource_repo.update_status(resource_id, status)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        
        return SuccessResponse(
            message=f"Resource status updated to {status.value}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update resource status"
        )


# Include wash facility sub-router
from .wash_facility_router import router as wash_facility_router
router.include_router(wash_facility_router)