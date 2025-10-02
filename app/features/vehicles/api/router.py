"""Vehicles API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime

from .schemas import (
    CreateVehicleSchema,
    UpdateVehicleSchema,
    VehicleResponseSchema,
    VehicleListResponseSchema,
    SetDefaultVehicleSchema,
)
from .dependencies import (
    get_current_user,
    get_create_vehicle_use_case,
    get_list_vehicles_use_case,
    get_get_vehicle_use_case,
    get_update_vehicle_use_case,
    get_delete_vehicle_use_case,
    get_set_default_vehicle_use_case,
)

router = APIRouter()


@router.get("/", response_model=VehicleListResponseSchema)
async def list_vehicles(
    current_user = get_current_user,
    use_case = Depends(get_list_vehicles_use_case)
):
    """List all vehicles for the current user."""
    try:
        from app.features.vehicles.use_cases.list_vehicles import ListVehiclesRequest
        request = ListVehiclesRequest(customer_id=current_user.id)
        response = await use_case.execute(request)
        return VehicleListResponseSchema(
            vehicles=response.vehicles,
            total_count=response.total_count,
            page=response.page,
            limit=response.limit,
            has_next=response.has_next
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/", response_model=VehicleResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle_data: CreateVehicleSchema,
    current_user = get_current_user,
    use_case = Depends(get_create_vehicle_use_case)
):
    """Create a new vehicle for the current user."""
    try:
        from app.features.vehicles.use_cases.create_vehicle import CreateVehicleRequest
        request = CreateVehicleRequest(
            customer_id=current_user.id,
            **vehicle_data.dict()
        )
        response = await use_case.execute(request)
        # Convert CreateVehicleResponse to VehicleResponseSchema
        return VehicleResponseSchema(
            id=response.vehicle_id,
            customer_id=current_user.id,
            make=response.make,
            model=response.model,
            year=response.year,
            color=response.color,
            license_plate=response.license_plate,
            is_default=response.is_default,
            is_deleted=False,
            display_name=response.display_name,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            deleted_at=None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{vehicle_id}", response_model=VehicleResponseSchema)
async def get_vehicle(
    vehicle_id: str,
    current_user = get_current_user,
    use_case = Depends(get_get_vehicle_use_case)
):
    """Get a specific vehicle by ID."""
    try:
        from app.features.vehicles.use_cases.get_vehicle import GetVehicleRequest
        request = GetVehicleRequest(
            vehicle_id=vehicle_id,
            requested_by=current_user.id
        )
        response = await use_case.execute(request)
        # Convert GetVehicleResponse to VehicleResponseSchema
        return VehicleResponseSchema(
            id=response.id,
            customer_id=response.customer_id,
            make=response.make,
            model=response.model,
            year=response.year,
            color=response.color,
            license_plate=response.license_plate,
            is_default=response.is_default,
            is_deleted=response.is_deleted,
            display_name=response.display_name,
            created_at=datetime.fromisoformat(response.created_at),
            updated_at=datetime.fromisoformat(response.updated_at),
            deleted_at=datetime.fromisoformat(response.deleted_at) if response.deleted_at else None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )


@router.put("/{vehicle_id}", response_model=VehicleResponseSchema)
async def update_vehicle(
    vehicle_id: str,
    vehicle_data: UpdateVehicleSchema,
    current_user = get_current_user,
    use_case = Depends(get_update_vehicle_use_case)
):
    """Update a specific vehicle."""
    try:
        from app.features.vehicles.use_cases.update_vehicle import UpdateVehicleRequest
        request = UpdateVehicleRequest(
            vehicle_id=vehicle_id,
            updated_by=current_user.id,
            **vehicle_data.dict(exclude_unset=True)
        )
        response = await use_case.execute(request)
        # Convert UpdateVehicleResponse to VehicleResponseSchema
        return VehicleResponseSchema(
            id=response.vehicle_id,
            customer_id=current_user.id,
            make=response.make,
            model=response.model,
            year=response.year,
            color=response.color,
            license_plate=response.license_plate,
            is_default=response.is_default,
            is_deleted=False,
            display_name=response.display_name,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            deleted_at=None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: str,
    current_user = get_current_user,
    use_case = Depends(get_delete_vehicle_use_case)
):
    """Soft delete a specific vehicle."""
    try:
        from app.features.vehicles.use_cases.delete_vehicle import DeleteVehicleRequest
        request = DeleteVehicleRequest(
            vehicle_id=vehicle_id,
            deleted_by=current_user.id
        )
        await use_case.execute(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{vehicle_id}/default", response_model=VehicleResponseSchema)
async def set_default_vehicle(
    vehicle_id: str,
    current_user = get_current_user,
    use_case = Depends(get_set_default_vehicle_use_case)
):
    """Set a vehicle as the default for the user."""
    try:
        from app.features.vehicles.use_cases.set_default_vehicle import SetDefaultVehicleRequest
        request = SetDefaultVehicleRequest(
            vehicle_id=vehicle_id,
            customer_id=current_user.id,
            changed_by=current_user.id
        )
        response = await use_case.execute(request)
        # Convert SetDefaultVehicleResponse to VehicleResponseSchema  
        return VehicleResponseSchema(
            id=response.vehicle_id,
            customer_id=current_user.id,
            make=response.make,
            model=response.model,
            year=response.year,
            color=response.color,
            license_plate=response.license_plate,
            is_default=True,
            is_deleted=False,
            display_name=response.display_name,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            deleted_at=None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )