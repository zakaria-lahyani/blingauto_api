"""
Mobile Teams API Router

Implements RG-FAC-003, RG-FAC-004: Mobile team management endpoints.
RBAC: Admin and Manager can create/update/delete, Washer can view.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from .schemas import (
    CreateMobileTeamSchema,
    UpdateMobileTeamSchema,
    MobileTeamSchema,
    ListMobileTeamsSchema,
    DeleteMobileTeamSchema,
    LocationSchema
)
from .dependencies import (
    get_create_mobile_team_use_case,
    get_list_mobile_teams_use_case,
    get_update_mobile_team_use_case,
    get_delete_mobile_team_use_case
)
from ..use_cases import (
    CreateMobileTeamUseCase,
    CreateMobileTeamRequest,
    ListMobileTeamsUseCase,
    ListMobileTeamsRequest,
    UpdateMobileTeamUseCase,
    UpdateMobileTeamRequest,
    DeleteMobileTeamUseCase,
    DeleteMobileTeamRequest
)
from ..domain.entities import ResourceStatus
from app.core.errors import ValidationError, BusinessRuleViolationError, NotFoundError
from app.shared.auth import get_current_user, CurrentUser, require_any_role
from app.features.auth.domain import UserRole

router = APIRouter()


@router.post(
    "/",
    response_model=MobileTeamSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create Mobile Team",
    description="Create a new mobile team. Requires Admin or Manager role.",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))]
)
async def create_mobile_team(
    data: CreateMobileTeamSchema,
    current_user: CurrentUser,
    use_case: CreateMobileTeamUseCase = Depends(get_create_mobile_team_use_case)
):
    """
    Create a new mobile team with specified configuration.

    **Business Rules (RG-FAC-003)**:
    - Team name must be unique
    - Base location required for distance calculations
    - Service radius defaults to 50km
    - Daily capacity defaults to 8 vehicles

    **RG-FAC-004**: Service radius used for location-based assignments

    **RBAC**: Admin, Manager only
    """
    try:
        request = CreateMobileTeamRequest(
            team_name=data.team_name,
            base_latitude=data.base_latitude,
            base_longitude=data.base_longitude,
            service_radius_km=data.service_radius_km,
            daily_capacity=data.daily_capacity,
            equipment_types=data.equipment_types
        )

        response = await use_case.execute(request)

        return MobileTeamSchema(
            id=response.id,
            team_name=response.team_name,
            base_location=LocationSchema(
                latitude=response.base_location["latitude"],
                longitude=response.base_location["longitude"]
            ),
            service_radius_km=response.service_radius_km,
            daily_capacity=response.daily_capacity,
            equipment_types=response.equipment_types,
            status=response.status,
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
    response_model=ListMobileTeamsSchema,
    summary="List Mobile Teams",
    description="List all mobile teams with optional filtering. Requires Admin, Manager, or Washer role.",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.WASHER.value))]
)
async def list_mobile_teams(
    current_user: CurrentUser,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    include_inactive: bool = Query(False, description="Include inactive/deleted teams"),
    use_case: ListMobileTeamsUseCase = Depends(get_list_mobile_teams_use_case)
):
    """
    List all mobile teams with optional filtering.

    **Query Parameters**:
    - `status`: Filter by status (active, inactive)
    - `include_inactive`: Include soft-deleted teams

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
                    detail=f"Invalid status: {status_filter}. Must be one of: active, inactive"
                )

        request = ListMobileTeamsRequest(
            status=status_enum,
            include_inactive=include_inactive
        )

        response = await use_case.execute(request)

        # Convert to API schema
        mobile_team_schemas = []
        for team_dto in response.mobile_teams:
            mobile_team_schemas.append(MobileTeamSchema(
                id=team_dto.id,
                team_name=team_dto.team_name,
                base_location=LocationSchema(
                    latitude=team_dto.base_location["latitude"],
                    longitude=team_dto.base_location["longitude"]
                ),
                service_radius_km=team_dto.service_radius_km,
                daily_capacity=team_dto.daily_capacity,
                equipment_types=team_dto.equipment_types,
                status=team_dto.status,
                created_at=team_dto.created_at,
                updated_at=team_dto.updated_at
            ))

        return ListMobileTeamsSchema(
            mobile_teams=mobile_team_schemas,
            total_count=response.total_count,
            active_count=response.active_count,
            inactive_count=response.inactive_count
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.patch(
    "/{team_id}",
    response_model=MobileTeamSchema,
    summary="Update Mobile Team",
    description="Update mobile team configuration. Requires Admin or Manager role.",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))]
)
async def update_mobile_team(
    team_id: str,
    data: UpdateMobileTeamSchema,
    current_user: CurrentUser,
    use_case: UpdateMobileTeamUseCase = Depends(get_update_mobile_team_use_case)
):
    """
    Update mobile team configuration.

    **Business Rules (RG-FAC-003)**:
    - Team name must remain unique if changed
    - Can update service radius and daily capacity
    - Can update base location (RG-FAC-004)

    **RBAC**: Admin, Manager only
    """
    try:
        request = UpdateMobileTeamRequest(
            team_id=team_id,
            team_name=data.team_name,
            base_latitude=data.base_latitude,
            base_longitude=data.base_longitude,
            service_radius_km=data.service_radius_km,
            daily_capacity=data.daily_capacity,
            equipment_types=data.equipment_types,
            status=data.status
        )

        response = await use_case.execute(request)

        return MobileTeamSchema(
            id=response.id,
            team_name=response.team_name,
            base_location=LocationSchema(
                latitude=response.base_location["latitude"],
                longitude=response.base_location["longitude"]
            ),
            service_radius_km=response.service_radius_km,
            daily_capacity=response.daily_capacity,
            equipment_types=response.equipment_types,
            status=response.status,
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
    "/{team_id}",
    response_model=DeleteMobileTeamSchema,
    summary="Delete Mobile Team",
    description="Soft delete a mobile team. Requires Admin role.",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value))]
)
async def delete_mobile_team(
    team_id: str,
    current_user: CurrentUser,
    use_case: DeleteMobileTeamUseCase = Depends(get_delete_mobile_team_use_case)
):
    """
    Soft delete a mobile team (marks as deleted, preserves history).

    **Business Rules**:
    - Soft delete only (data preserved for history)
    - Cannot delete if active bookings exist (future validation)

    **RBAC**: Admin only
    """
    try:
        request = DeleteMobileTeamRequest(team_id=team_id)
        response = await use_case.execute(request)

        return DeleteMobileTeamSchema(
            id=response.id,
            team_name=response.team_name,
            deleted=response.deleted,
            message=response.message
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message}
        )
