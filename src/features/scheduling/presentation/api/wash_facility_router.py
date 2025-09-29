"""
Wash facility management API router
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Set
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.database.session import get_db
from src.shared.auth import get_current_user, require_admin, require_manager_or_admin
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole
from src.features.scheduling.application.services.wash_facility_service import WashFacilityService
from src.features.scheduling.infrastructure.database.wash_facility_repositories import (
    WashBayRepository, MobileWashTeamRepository, WashFacilityConfigurationRepository, CapacityAllocationRepository
)
from src.features.scheduling.domain.wash_facility_entities import WashType
from .wash_facility_schemas import (
    CreateWashBayRequest, CreateMobileTeamRequest, UpdateWashBayRequest, UpdateMobileTeamRequest,
    UpdateFacilityConfigRequest, WashBayResponse, MobileTeamResponse, FacilityConfigResponse,
    CapacitySummaryResponse, FacilityOverviewResponse
)

router = APIRouter(prefix="/wash-facility")


def get_wash_facility_service(db: AsyncSession = Depends(get_db)) -> WashFacilityService:
    """Dependency to get wash facility service"""
    wash_bay_repo = WashBayRepository(db)
    mobile_team_repo = MobileWashTeamRepository(db)
    facility_config_repo = WashFacilityConfigurationRepository(db)
    capacity_allocation_repo = CapacityAllocationRepository(db)
    
    return WashFacilityService(
        wash_bay_repo=wash_bay_repo,
        mobile_team_repo=mobile_team_repo,
        facility_config_repo=facility_config_repo,
        capacity_allocation_repo=capacity_allocation_repo
    )


# ============= WASH BAY MANAGEMENT =============

@router.post("/wash-bays", response_model=WashBayResponse, status_code=status.HTTP_201_CREATED)
async def create_wash_bay(
    request: CreateWashBayRequest,
    current_user: AuthUser = Depends(require_manager_or_admin),
    facility_service: WashFacilityService = Depends(get_wash_facility_service)
):
    """Create a new wash bay (admin/manager only)"""
    try:
        wash_bay = await facility_service.create_wash_bay(
            name=request.name,
            bay_number=request.bay_number,
            equipment_types=request.equipment_types,
            max_vehicle_size=request.max_vehicle_size,
            has_covered_area=request.has_covered_area,
            has_power_supply=request.has_power_supply,
            notes=request.notes
        )
        
        return _wash_bay_to_response(wash_bay)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create wash bay"
        )


@router.get("/wash-bays", response_model=List[WashBayResponse])
async def list_wash_bays(
    active_only: bool = Query(True),
    current_user: AuthUser = Depends(require_manager_or_admin),
    facility_service: WashFacilityService = Depends(get_wash_facility_service)
):
    """List all wash bays (admin/manager only)"""
    try:
        wash_bays = await facility_service.get_all_wash_bays(active_only=active_only)
        return [_wash_bay_to_response(bay) for bay in wash_bays]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve wash bays"
        )


@router.get("/wash-bays/{bay_id}", response_model=WashBayResponse)
async def get_wash_bay(
    bay_id: UUID,
    current_user: AuthUser = Depends(require_manager_or_admin),
    facility_service: WashFacilityService = Depends(get_wash_facility_service)
):
    """Get a specific wash bay (admin/manager only)"""
    try:
        wash_bay = await facility_service.get_wash_bay(bay_id)
        
        if not wash_bay:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wash bay not found"
            )
        
        return _wash_bay_to_response(wash_bay)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve wash bay"
        )


@router.put("/wash-bays/{bay_id}", response_model=WashBayResponse)
async def update_wash_bay(
    bay_id: UUID,
    request: UpdateWashBayRequest,
    current_user: AuthUser = Depends(require_manager_or_admin),
    facility_service: WashFacilityService = Depends(get_wash_facility_service)
):
    """Update a wash bay (admin/manager only)"""
    try:
        wash_bay = await facility_service.get_wash_bay(bay_id)
        
        if not wash_bay:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wash bay not found"
            )
        
        # Update fields
        if request.name is not None:
            wash_bay.name = request.name
        if request.equipment_types is not None:
            wash_bay.equipment_types = request.equipment_types
        if request.max_vehicle_size is not None:
            wash_bay.max_vehicle_size = request.max_vehicle_size
        if request.has_covered_area is not None:
            wash_bay.has_covered_area = request.has_covered_area
        if request.has_power_supply is not None:
            wash_bay.has_power_supply = request.has_power_supply
        if request.notes is not None:
            wash_bay.notes = request.notes
        if request.is_active is not None:
            wash_bay.is_active = request.is_active
        
        updated_bay = await facility_service.update_wash_bay(wash_bay)
        return _wash_bay_to_response(updated_bay)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update wash bay"
        )


@router.delete("/wash-bays/{bay_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wash_bay(
    bay_id: UUID,
    current_user: AuthUser = Depends(require_admin),
    facility_service: WashFacilityService = Depends(get_wash_facility_service)
):
    """Delete a wash bay (admin only)"""
    try:
        success = await facility_service.delete_wash_bay(bay_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wash bay not found"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete wash bay"
        )


# ============= MOBILE TEAM MANAGEMENT =============

@router.post("/mobile-teams", response_model=MobileTeamResponse, status_code=status.HTTP_201_CREATED)
async def create_mobile_team(
    request: CreateMobileTeamRequest,
    current_user: AuthUser = Depends(require_manager_or_admin),
    facility_service: WashFacilityService = Depends(get_wash_facility_service)
):
    """Create a new mobile wash team (admin/manager only)"""
    try:
        mobile_team = await facility_service.create_mobile_wash_team(
            name=request.name,
            team_size=request.team_size,
            equipment_types=request.equipment_types,
            service_radius_km=request.service_radius_km,
            max_vehicles_per_day=request.max_vehicles_per_day,
            hourly_rate=request.hourly_rate,
            base_location=request.base_location,
            notes=request.notes
        )
        
        return _mobile_team_to_response(mobile_team)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create mobile team"
        )


@router.get("/mobile-teams", response_model=List[MobileTeamResponse])
async def list_mobile_teams(
    active_only: bool = Query(True),
    current_user: AuthUser = Depends(require_manager_or_admin),
    facility_service: WashFacilityService = Depends(get_wash_facility_service)
):
    """List all mobile teams (admin/manager only)"""
    try:
        mobile_teams = await facility_service.get_all_mobile_teams(active_only=active_only)
        return [_mobile_team_to_response(team) for team in mobile_teams]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve mobile teams"
        )


@router.get("/mobile-teams/{team_id}", response_model=MobileTeamResponse)
async def get_mobile_team(
    team_id: UUID,
    current_user: AuthUser = Depends(require_manager_or_admin),
    facility_service: WashFacilityService = Depends(get_wash_facility_service)
):
    """Get a specific mobile team (admin/manager only)"""
    try:
        mobile_team = await facility_service.get_mobile_team(team_id)
        
        if not mobile_team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mobile team not found"
            )
        
        return _mobile_team_to_response(mobile_team)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve mobile team"
        )


@router.put("/mobile-teams/{team_id}", response_model=MobileTeamResponse)
async def update_mobile_team(
    team_id: UUID,
    request: UpdateMobileTeamRequest,
    current_user: AuthUser = Depends(require_manager_or_admin),
    facility_service: WashFacilityService = Depends(get_wash_facility_service)
):
    """Update a mobile team (admin/manager only)"""
    try:
        mobile_team = await facility_service.get_mobile_team(team_id)
        
        if not mobile_team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mobile team not found"
            )
        
        # Update fields
        if request.name is not None:
            mobile_team.name = request.name
        if request.team_size is not None:
            mobile_team.team_size = request.team_size
        if request.equipment_types is not None:
            mobile_team.equipment_types = request.equipment_types
        if request.service_radius_km is not None:
            mobile_team.service_radius_km = request.service_radius_km
        if request.max_vehicles_per_day is not None:
            mobile_team.max_vehicles_per_day = request.max_vehicles_per_day
        if request.hourly_rate is not None:
            mobile_team.hourly_rate = request.hourly_rate
        if request.base_location is not None:
            mobile_team.base_location = request.base_location
        if request.notes is not None:
            mobile_team.notes = request.notes
        if request.is_active is not None:
            mobile_team.is_active = request.is_active
        
        updated_team = await facility_service.update_mobile_team(mobile_team)
        return _mobile_team_to_response(updated_team)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update mobile team"
        )


@router.delete("/mobile-teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mobile_team(
    team_id: UUID,
    current_user: AuthUser = Depends(require_admin),
    facility_service: WashFacilityService = Depends(get_wash_facility_service)
):
    """Delete a mobile team (admin only)"""
    try:
        success = await facility_service.delete_mobile_team(team_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mobile team not found"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete mobile team"
        )


# ============= FACILITY CONFIGURATION =============

@router.get("/configuration", response_model=FacilityConfigResponse)
async def get_facility_configuration(
    current_user: AuthUser = Depends(require_manager_or_admin),
    facility_service: WashFacilityService = Depends(get_wash_facility_service)
):
    """Get facility configuration (admin/manager only)"""
    try:
        configuration = await facility_service.get_facility_configuration()
        
        if not configuration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility configuration not found"
            )
        
        return _facility_config_to_response(configuration)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve facility configuration"
        )


@router.put("/configuration", response_model=FacilityConfigResponse)
async def update_facility_configuration(
    request: UpdateFacilityConfigRequest,
    current_user: AuthUser = Depends(require_manager_or_admin),
    facility_service: WashFacilityService = Depends(get_wash_facility_service)
):
    """Update facility configuration (admin/manager only)"""
    try:
        configuration = await facility_service.update_facility_configuration(
            facility_name=request.facility_name,
            operating_hours=request.operating_hours,
            default_service_duration_minutes=request.default_service_duration_minutes,
            buffer_between_services_minutes=request.buffer_between_services_minutes,
            max_advance_booking_days=request.max_advance_booking_days
        )
        
        return _facility_config_to_response(configuration)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update facility configuration"
        )


# ============= CAPACITY MANAGEMENT =============

@router.get("/capacity/summary/{date}", response_model=CapacitySummaryResponse)
async def get_capacity_summary(
    date: str,  # Format: YYYY-MM-DD
    current_user: AuthUser = Depends(require_manager_or_admin),
    facility_service: WashFacilityService = Depends(get_wash_facility_service)
):
    """Get capacity summary for a specific date (admin/manager only)"""
    try:
        # Parse date
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        summary = await facility_service.get_daily_capacity_summary(parsed_date)
        
        return CapacitySummaryResponse(
            date=date,
            stationary=summary.get("stationary", {"total_capacity": 0, "allocated": 0, "available": 0}),
            mobile=summary.get("mobile", {"total_capacity": 0, "allocated": 0, "available": 0})
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get capacity summary"
        )


@router.get("/overview", response_model=FacilityOverviewResponse)
async def get_facility_overview(
    current_user: AuthUser = Depends(require_manager_or_admin),
    facility_service: WashFacilityService = Depends(get_wash_facility_service)
):
    """Get facility capacity overview (admin/manager only)"""
    try:
        overview = await facility_service.get_facility_capacity_overview()
        return FacilityOverviewResponse(**overview)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get facility overview"
        )


# ============= HELPER FUNCTIONS =============

def _wash_bay_to_response(wash_bay) -> WashBayResponse:
    """Convert wash bay entity to response schema"""
    return WashBayResponse(
        id=wash_bay.id,
        name=wash_bay.name,
        bay_number=wash_bay.bay_number,
        is_active=wash_bay.is_active,
        equipment_types=list(wash_bay.equipment_types) if wash_bay.equipment_types else [],
        max_vehicle_size=wash_bay.max_vehicle_size,
        has_covered_area=wash_bay.has_covered_area,
        has_power_supply=wash_bay.has_power_supply,
        notes=wash_bay.notes,
        created_at=wash_bay.created_at
    )


def _mobile_team_to_response(mobile_team) -> MobileTeamResponse:
    """Convert mobile team entity to response schema"""
    return MobileTeamResponse(
        id=mobile_team.id,
        name=mobile_team.name,
        team_size=mobile_team.team_size,
        equipment_types=list(mobile_team.equipment_types) if mobile_team.equipment_types else [],
        service_radius_km=mobile_team.service_radius_km,
        max_vehicles_per_day=mobile_team.max_vehicles_per_day,
        hourly_rate=mobile_team.hourly_rate,
        is_active=mobile_team.is_active,
        base_location=mobile_team.base_location,
        notes=mobile_team.notes,
        created_at=mobile_team.created_at
    )


def _facility_config_to_response(configuration) -> FacilityConfigResponse:
    """Convert facility configuration entity to response schema"""
    return FacilityConfigResponse(
        id=configuration.id,
        facility_name=configuration.facility_name,
        total_wash_bays=configuration.total_wash_bays,
        total_mobile_teams=configuration.total_mobile_teams,
        operating_hours=configuration.operating_hours,
        default_service_duration_minutes=configuration.default_service_duration_minutes,
        buffer_between_services_minutes=configuration.buffer_between_services_minutes,
        max_advance_booking_days=configuration.max_advance_booking_days,
        created_at=configuration.created_at,
        updated_at=configuration.updated_at
    )