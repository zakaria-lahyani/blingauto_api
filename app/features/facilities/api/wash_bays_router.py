"""
Wash Bays API Router

Implements RG-FAC-001, RG-FAC-002: Wash bay management endpoints.
RBAC: Admin and Manager can create/update/delete, Washer can view.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from .schemas import (
    CreateWashBaySchema,
    UpdateWashBaySchema,
    WashBaySchema,
    ListWashBaysSchema,
    DeleteWashBaySchema
)
from .dependencies import (
    get_create_wash_bay_use_case,
    get_list_wash_bays_use_case,
    get_update_wash_bay_use_case,
    get_delete_wash_bay_use_case
)
from ..use_cases import (
    CreateWashBayUseCase,
    CreateWashBayRequest,
    ListWashBaysUseCase,
    ListWashBaysRequest,
    UpdateWashBayUseCase,
    UpdateWashBayRequest,
    DeleteWashBayUseCase,
    DeleteWashBayRequest
)
from ..domain.entities import ResourceStatus
from app.core.errors import ValidationError, BusinessRuleViolationError, NotFoundError
from app.shared.auth import get_current_user, CurrentUser, require_any_role
from app.features.auth.domain import UserRole

router = APIRouter()


@router.post(
    "/",
    response_model=WashBaySchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create Wash Bay",
    description="Create a new wash bay. Requires Admin or Manager role.",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))]
)
async def create_wash_bay(
    data: CreateWashBaySchema,
    current_user: CurrentUser,
    use_case: CreateWashBayUseCase = Depends(get_create_wash_bay_use_case)
):
    """
    Create a new wash bay with specified configuration.

    **Business Rules (RG-FAC-001)**:
    - Bay number must be unique
    - Max vehicle size defines capacity
    - Equipment types list available equipment
    - Location is optional

    **RBAC**: Admin, Manager only
    """
    try:
        request = CreateWashBayRequest(
            bay_number=data.bay_number,
            max_vehicle_size=data.max_vehicle_size,
            equipment_types=data.equipment_types,
            latitude=data.latitude,
            longitude=data.longitude
        )

        response = await use_case.execute(request)

        # Convert to API schema
        location_schema = None
        if response.location:
            location_schema = {
                "latitude": response.location["latitude"],
                "longitude": response.location["longitude"]
            }

        return WashBaySchema(
            id=response.id,
            bay_number=response.bay_number,
            max_vehicle_size=response.max_vehicle_size,
            equipment_types=response.equipment_types,
            status=response.status,
            location=location_schema,
            created_at=response.created_at,
            updated_at=response.created_at
        )

    except BusinessRuleViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": e.code, "message": e.message}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message}
        )


@router.get(
    "/",
    response_model=ListWashBaysSchema,
    summary="List Wash Bays",
    description="List all wash bays with optional filtering. Requires Admin, Manager, or Washer role.",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.WASHER.value))]
)
async def list_wash_bays(
    current_user: CurrentUser,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    include_inactive: bool = Query(False, description="Include inactive/deleted bays"),
    use_case: ListWashBaysUseCase = Depends(get_list_wash_bays_use_case)
):
    """
    List all wash bays with optional filtering.

    **Query Parameters**:
    - `status`: Filter by status (active, inactive, maintenance)
    - `include_inactive`: Include soft-deleted bays

    **RBAC**: Admin, Manager, Washer can view
    """
    try:
        # Parse status filter
        status_enum = None
        if status_filter:
            try:
                status_enum = ResourceStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}. Must be one of: active, inactive, maintenance"
                )

        request = ListWashBaysRequest(
            status=status_enum,
            include_inactive=include_inactive
        )

        response = await use_case.execute(request)

        # Convert to API schema
        wash_bay_schemas = []
        for bay_dto in response.wash_bays:
            location_schema = None
            if bay_dto.location:
                location_schema = {
                    "latitude": bay_dto.location["latitude"],
                    "longitude": bay_dto.location["longitude"]
                }

            wash_bay_schemas.append(WashBaySchema(
                id=bay_dto.id,
                bay_number=bay_dto.bay_number,
                max_vehicle_size=bay_dto.max_vehicle_size,
                equipment_types=bay_dto.equipment_types,
                status=bay_dto.status,
                location=location_schema,
                created_at=bay_dto.created_at,
                updated_at=bay_dto.updated_at
            ))

        return ListWashBaysSchema(
            wash_bays=wash_bay_schemas,
            total_count=response.total_count,
            active_count=response.active_count,
            inactive_count=response.inactive_count,
            maintenance_count=response.maintenance_count
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.patch(
    "/{wash_bay_id}",
    response_model=WashBaySchema,
    summary="Update Wash Bay",
    description="Update wash bay configuration. Requires Admin or Manager role.",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))]
)
async def update_wash_bay(
    wash_bay_id: str,
    data: UpdateWashBaySchema,
    current_user: CurrentUser,
    use_case: UpdateWashBayUseCase = Depends(get_update_wash_bay_use_case)
):
    """
    Update wash bay configuration.

    **Business Rules (RG-FAC-001)**:
    - Bay number must remain unique if changed
    - Can update equipment types
    - Can change status (active, maintenance, inactive)

    **RBAC**: Admin, Manager only
    """
    try:
        request = UpdateWashBayRequest(
            wash_bay_id=wash_bay_id,
            bay_number=data.bay_number,
            max_vehicle_size=data.max_vehicle_size,
            equipment_types=data.equipment_types,
            status=data.status,
            latitude=data.latitude,
            longitude=data.longitude
        )

        response = await use_case.execute(request)

        # Convert to API schema
        location_schema = None
        if response.location:
            location_schema = {
                "latitude": response.location["latitude"],
                "longitude": response.location["longitude"]
            }

        return WashBaySchema(
            id=response.id,
            bay_number=response.bay_number,
            max_vehicle_size=response.max_vehicle_size,
            equipment_types=response.equipment_types,
            status=response.status,
            location=location_schema,
            created_at=response.updated_at,  # Use updated_at since created_at not in response
            updated_at=response.updated_at
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message}
        )


@router.delete(
    "/{wash_bay_id}",
    response_model=DeleteWashBaySchema,
    summary="Delete Wash Bay",
    description="Soft delete a wash bay. Requires Admin role.",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value))]
)
async def delete_wash_bay(
    wash_bay_id: str,
    current_user: CurrentUser,
    use_case: DeleteWashBayUseCase = Depends(get_delete_wash_bay_use_case)
):
    """
    Soft delete a wash bay (marks as deleted, preserves history).

    **Business Rules**:
    - Soft delete only (data preserved for history)
    - Cannot delete if active bookings exist (future validation)

    **RBAC**: Admin only
    """
    try:
        request = DeleteWashBayRequest(wash_bay_id=wash_bay_id)
        response = await use_case.execute(request)

        return DeleteWashBaySchema(
            id=response.id,
            bay_number=response.bay_number,
            deleted=response.deleted,
            message=response.message
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message}
        )
