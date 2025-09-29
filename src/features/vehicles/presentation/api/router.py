"""
Vehicle API router
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.simple_database import get_db
from src.shared.auth import get_current_user, get_current_active_user
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole
from src.features.vehicles.application.services.vehicle_service import VehicleApplicationService
from src.features.vehicles.infrastructure.database.repositories import VehicleRepository
from src.features.vehicles.domain.enums import VehicleStatus
from .schemas import (
    CreateVehicleRequest, UpdateVehicleRequest, VehicleResponse, VehicleSummaryResponse,
    VehicleListResponse, VehicleAnalyticsResponse, VehicleFilters,
    SetDefaultVehicleRequest, SuccessResponse
)

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


# Authentication dependencies now imported from shared module


def get_vehicle_service(db: AsyncSession = Depends(get_db)) -> VehicleApplicationService:
    """Dependency to get vehicle service"""
    vehicle_repo = VehicleRepository(db)
    return VehicleApplicationService(vehicle_repo)


@router.post("/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    request: CreateVehicleRequest,
    current_user: AuthUser = Depends(get_current_user),
    vehicle_service: VehicleApplicationService = Depends(get_vehicle_service)
):
    """Create a new vehicle"""
    try:
        vehicle = await vehicle_service.create_vehicle(
            user_id=current_user.id,
            make=request.make,
            model=request.model,
            year=request.year,
            license_plate=request.license_plate,
            color=request.color,
            is_default=request.is_default
        )
        
        return _vehicle_to_response(vehicle)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create vehicle"
        )


@router.get("/", response_model=VehicleListResponse)
async def list_vehicles(
    filters: VehicleFilters = Depends(),
    current_user: AuthUser = Depends(get_current_user),
    vehicle_service: VehicleApplicationService = Depends(get_vehicle_service)
):
    """List user's vehicles with optional filtering"""
    try:
        vehicles = await vehicle_service.get_user_vehicles(
            user_id=current_user.id,
            status=filters.status,
            search=filters.search,
            include_inactive=filters.include_inactive
        )
        
        default_vehicle = await vehicle_service.get_default_vehicle(current_user.id)
        default_vehicle_id = default_vehicle.id if default_vehicle else None
        
        vehicle_summaries = [_vehicle_to_summary_response(vehicle) for vehicle in vehicles]
        
        return VehicleListResponse(
            vehicles=vehicle_summaries,
            total=len(vehicle_summaries),
            default_vehicle_id=default_vehicle_id
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vehicles"
        )


@router.get("/default", response_model=VehicleResponse)
async def get_default_vehicle(
    current_user: AuthUser = Depends(get_current_user),
    vehicle_service: VehicleApplicationService = Depends(get_vehicle_service)
):
    """Get user's default vehicle"""
    try:
        vehicle = await vehicle_service.get_default_vehicle(current_user.id)
        
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No default vehicle found"
            )
        
        return _vehicle_to_response(vehicle)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve default vehicle"
        )


@router.get("/search", response_model=List[VehicleSummaryResponse])
async def search_vehicles(
    q: str = Query(..., min_length=2, max_length=100),
    current_user: AuthUser = Depends(get_current_user),
    vehicle_service: VehicleApplicationService = Depends(get_vehicle_service)
):
    """Search user's vehicles"""
    try:
        vehicles = await vehicle_service.search_vehicles(
            user_id=current_user.id,
            search_term=q
        )
        
        return [_vehicle_to_summary_response(vehicle) for vehicle in vehicles]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search vehicles"
        )


@router.get("/analytics", response_model=VehicleAnalyticsResponse)
async def get_vehicle_analytics(
    current_user: AuthUser = Depends(get_current_user),
    vehicle_service: VehicleApplicationService = Depends(get_vehicle_service)
):
    """Get vehicle analytics for the user"""
    try:
        analytics = await vehicle_service.get_vehicle_analytics(current_user.id)
        return VehicleAnalyticsResponse(**analytics)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analytics"
        )


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: UUID,
    current_user: AuthUser = Depends(get_current_user),
    vehicle_service: VehicleApplicationService = Depends(get_vehicle_service)
):
    """Get a specific vehicle"""
    try:
        vehicle = await vehicle_service.get_vehicle(vehicle_id, current_user.id)
        
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
        
        return _vehicle_to_response(vehicle)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vehicle"
        )


@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: UUID,
    request: UpdateVehicleRequest,
    current_user: AuthUser = Depends(get_current_user),
    vehicle_service: VehicleApplicationService = Depends(get_vehicle_service)
):
    """Update a vehicle"""
    try:
        vehicle = await vehicle_service.update_vehicle(
            vehicle_id=vehicle_id,
            user_id=current_user.id,
            make=request.make,
            model=request.model,
            year=request.year,
            license_plate=request.license_plate,
            color=request.color
        )
        
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
        
        return _vehicle_to_response(vehicle)
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update vehicle"
        )


@router.patch("/{vehicle_id}/set-default", response_model=SuccessResponse)
async def set_default_vehicle(
    vehicle_id: UUID,
    current_user: AuthUser = Depends(get_current_user),
    vehicle_service: VehicleApplicationService = Depends(get_vehicle_service)
):
    """Set a vehicle as the default"""
    try:
        success = await vehicle_service.set_default_vehicle(vehicle_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
        
        return SuccessResponse(message="Vehicle set as default successfully")
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set default vehicle"
        )


@router.patch("/{vehicle_id}/activate", response_model=SuccessResponse)
async def activate_vehicle(
    vehicle_id: UUID,
    current_user: AuthUser = Depends(get_current_user),
    vehicle_service: VehicleApplicationService = Depends(get_vehicle_service)
):
    """Activate a vehicle"""
    try:
        success = await vehicle_service.activate_vehicle(vehicle_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
        
        return SuccessResponse(message="Vehicle activated successfully")
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate vehicle"
        )


@router.patch("/{vehicle_id}/deactivate", response_model=SuccessResponse)
async def deactivate_vehicle(
    vehicle_id: UUID,
    current_user: AuthUser = Depends(get_current_user),
    vehicle_service: VehicleApplicationService = Depends(get_vehicle_service)
):
    """Deactivate a vehicle"""
    try:
        success = await vehicle_service.deactivate_vehicle(vehicle_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
        
        return SuccessResponse(message="Vehicle deactivated successfully")
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate vehicle"
        )


@router.delete("/{vehicle_id}", response_model=SuccessResponse)
async def delete_vehicle(
    vehicle_id: UUID,
    current_user: AuthUser = Depends(get_current_user),
    vehicle_service: VehicleApplicationService = Depends(get_vehicle_service)
):
    """Delete a vehicle (soft delete)"""
    try:
        success = await vehicle_service.delete_vehicle(vehicle_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
        
        return SuccessResponse(message="Vehicle deleted successfully")
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete vehicle"
        )


def _vehicle_to_response(vehicle) -> VehicleResponse:
    """Convert vehicle entity to response schema"""
    return VehicleResponse(
        id=vehicle.id,
        user_id=vehicle.user_id,
        make=vehicle.make,
        model=vehicle.model,
        year=vehicle.year,
        license_plate=vehicle.license_plate,
        color=vehicle.color,
        status=vehicle.status,
        is_default=vehicle.is_default,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
        display_name=vehicle.display_name
    )


def _vehicle_to_summary_response(vehicle) -> VehicleSummaryResponse:
    """Convert vehicle entity to summary response schema"""
    return VehicleSummaryResponse(
        id=vehicle.id,
        make=vehicle.make,
        model=vehicle.model,
        year=vehicle.year,
        license_plate=vehicle.license_plate,
        color=vehicle.color,
        status=vehicle.status,
        is_default=vehicle.is_default,
        display_name=vehicle.display_name
    )