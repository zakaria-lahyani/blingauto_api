"""Walk-in API router."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.features.auth.domain.enums import UserRole
from app.core.auth import get_current_user, require_any_role
from app.features.walkins.api.schemas import (
    CreateWalkInSchema,
    AddServiceSchema,
    ApplyDiscountSchema,
    RecordPaymentSchema,
    CancelWalkInSchema,
    ListWalkInsQuerySchema,
    WalkInServiceSchema,
    WalkInServiceListSchema,
    DailyReportSchema,
    ErrorResponseSchema,
)
from app.features.walkins.api.dependencies import (
    get_create_walkin_use_case,
    get_add_service_use_case,
    get_remove_service_use_case,
    get_apply_discount_use_case,
    get_complete_walkin_use_case,
    get_record_payment_use_case,
    get_cancel_walkin_use_case,
    get_get_walkin_use_case,
    get_list_walkins_use_case,
    get_daily_report_use_case,
)
from app.features.walkins.use_cases.create_walkin import (
    CreateWalkInUseCase,
    CreateWalkInRequest,
)
from app.features.walkins.use_cases.add_service import (
    AddServiceUseCase,
    AddServiceRequest,
)
from app.features.walkins.use_cases.remove_service import RemoveServiceUseCase
from app.features.walkins.use_cases.apply_discount import (
    ApplyDiscountUseCase,
    ApplyDiscountRequest,
)
from app.features.walkins.use_cases.complete_walkin import CompleteWalkInUseCase
from app.features.walkins.use_cases.record_payment import (
    RecordPaymentUseCase,
    RecordPaymentRequest,
)
from app.features.walkins.use_cases.cancel_walkin import CancelWalkInUseCase
from app.features.walkins.use_cases.get_walkin import GetWalkInUseCase
from app.features.walkins.use_cases.list_walkins import (
    ListWalkInsUseCase,
    ListWalkInsRequest,
)
from app.features.walkins.use_cases.get_daily_report import GetDailyReportUseCase

router = APIRouter(prefix="/walkins", tags=["Walk-in Services"])


# ============================================================================
# Create Walk-in
# ============================================================================


@router.post(
    "/",
    response_model=WalkInServiceSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_any_role(
                UserRole.ADMIN.value,
                UserRole.MANAGER.value,
                UserRole.WASHER.value,
            )
        )
    ],
    responses={
        400: {"model": ErrorResponseSchema, "description": "Validation error"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
)
async def create_walkin(
    data: CreateWalkInSchema,
    use_case: Annotated[CreateWalkInUseCase, Depends(get_create_walkin_use_case)],
    current_user=Depends(get_current_user),
):
    """
    Create a new walk-in service.

    **Permissions**: Admin, Manager, Washer

    **Auto-generated**: Service number (WI-20251002-001)
    """
    try:
        request = CreateWalkInRequest(
            vehicle_make=data.vehicle_make,
            vehicle_model=data.vehicle_model,
            vehicle_color=data.vehicle_color,
            vehicle_size=data.vehicle_size,
            license_plate=data.license_plate,
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            created_by_id=current_user["user_id"],
            notes=data.notes,
        )

        walkin = await use_case.execute(request)

        return WalkInServiceSchema(
            id=walkin.id,
            service_number=walkin.service_number,
            vehicle_make=walkin.vehicle_make,
            vehicle_model=walkin.vehicle_model,
            vehicle_color=walkin.vehicle_color,
            vehicle_size=walkin.vehicle_size,
            license_plate=walkin.license_plate,
            customer_name=walkin.customer_name,
            customer_phone=walkin.customer_phone,
            status=walkin.status,
            payment_status=walkin.payment_status,
            services=[],
            total_amount=walkin.total_amount,
            discount_amount=walkin.discount_amount,
            discount_reason=walkin.discount_reason,
            final_amount=walkin.final_amount,
            paid_amount=walkin.paid_amount,
            started_at=walkin.started_at,
            completed_at=walkin.completed_at,
            cancelled_at=walkin.cancelled_at,
            created_by_id=walkin.created_by_id,
            completed_by_id=walkin.completed_by_id,
            cancelled_by_id=walkin.cancelled_by_id,
            notes=walkin.notes,
            cancellation_reason=walkin.cancellation_reason,
            created_at=walkin.created_at,
            updated_at=walkin.updated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# Get Walk-in
# ============================================================================


@router.get(
    "/{walkin_id}",
    response_model=WalkInServiceSchema,
    dependencies=[
        Depends(
            require_any_role(
                UserRole.ADMIN.value,
                UserRole.MANAGER.value,
                UserRole.WASHER.value,
            )
        )
    ],
    responses={
        404: {"model": ErrorResponseSchema, "description": "Walk-in not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
)
async def get_walkin(
    walkin_id: str,
    use_case: Annotated[GetWalkInUseCase, Depends(get_get_walkin_use_case)],
):
    """
    Get walk-in service by ID.

    **Permissions**: Admin, Manager, Washer
    """
    try:
        walkin = await use_case.execute(walkin_id)

        return WalkInServiceSchema(
            id=walkin.id,
            service_number=walkin.service_number,
            vehicle_make=walkin.vehicle_make,
            vehicle_model=walkin.vehicle_model,
            vehicle_color=walkin.vehicle_color,
            vehicle_size=walkin.vehicle_size,
            license_plate=walkin.license_plate,
            customer_name=walkin.customer_name,
            customer_phone=walkin.customer_phone,
            status=walkin.status,
            payment_status=walkin.payment_status,
            services=[
                {
                    "id": s.id,
                    "service_id": s.service_id,
                    "service_name": s.service_name,
                    "price": s.price,
                    "product_costs": s.product_costs,
                    "quantity": s.quantity,
                    "notes": s.notes,
                }
                for s in walkin.services
            ],
            total_amount=walkin.total_amount,
            discount_amount=walkin.discount_amount,
            discount_reason=walkin.discount_reason,
            final_amount=walkin.final_amount,
            paid_amount=walkin.paid_amount,
            started_at=walkin.started_at,
            completed_at=walkin.completed_at,
            cancelled_at=walkin.cancelled_at,
            created_by_id=walkin.created_by_id,
            completed_by_id=walkin.completed_by_id,
            cancelled_by_id=walkin.cancelled_by_id,
            notes=walkin.notes,
            cancellation_reason=walkin.cancellation_reason,
            created_at=walkin.created_at,
            updated_at=walkin.updated_at,
        )

    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# List Walk-ins
# ============================================================================


@router.get(
    "/",
    response_model=WalkInServiceListSchema,
    dependencies=[
        Depends(
            require_any_role(
                UserRole.ADMIN.value,
                UserRole.MANAGER.value,
                UserRole.WASHER.value,
            )
        )
    ],
)
async def list_walkins(
    use_case: Annotated[ListWalkInsUseCase, Depends(get_list_walkins_use_case)],
    status: str | None = Query(None),
    payment_status: str | None = Query(None),
    created_by_id: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    List walk-in services with filters.

    **Permissions**: Admin, Manager, Washer

    **Filters**:
    - status: Filter by walk-in status
    - payment_status: Filter by payment status
    - created_by_id: Filter by staff who created
    - start_date/end_date: Filter by date range
    """
    try:
        from app.features.walkins.domain.enums import WalkInStatus, PaymentStatus

        request = ListWalkInsRequest(
            status=WalkInStatus(status) if status else None,
            payment_status=PaymentStatus(payment_status) if payment_status else None,
            created_by_id=created_by_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

        walkins = await use_case.execute(request)

        items = [
            WalkInServiceSchema(
                id=w.id,
                service_number=w.service_number,
                vehicle_make=w.vehicle_make,
                vehicle_model=w.vehicle_model,
                vehicle_color=w.vehicle_color,
                vehicle_size=w.vehicle_size,
                license_plate=w.license_plate,
                customer_name=w.customer_name,
                customer_phone=w.customer_phone,
                status=w.status,
                payment_status=w.payment_status,
                services=[
                    {
                        "id": s.id,
                        "service_id": s.service_id,
                        "service_name": s.service_name,
                        "price": s.price,
                        "product_costs": s.product_costs,
                        "quantity": s.quantity,
                        "notes": s.notes,
                    }
                    for s in w.services
                ],
                total_amount=w.total_amount,
                discount_amount=w.discount_amount,
                discount_reason=w.discount_reason,
                final_amount=w.final_amount,
                paid_amount=w.paid_amount,
                started_at=w.started_at,
                completed_at=w.completed_at,
                cancelled_at=w.cancelled_at,
                created_by_id=w.created_by_id,
                completed_by_id=w.completed_by_id,
                cancelled_by_id=w.cancelled_by_id,
                notes=w.notes,
                cancellation_reason=w.cancellation_reason,
                created_at=w.created_at,
                updated_at=w.updated_at,
            )
            for w in walkins
        ]

        return WalkInServiceListSchema(
            items=items, total=len(items), limit=limit, offset=offset
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# Add Service to Walk-in
# ============================================================================


@router.post(
    "/{walkin_id}/services",
    response_model=WalkInServiceSchema,
    dependencies=[
        Depends(
            require_any_role(
                UserRole.ADMIN.value,
                UserRole.MANAGER.value,
                UserRole.WASHER.value,
            )
        )
    ],
    responses={
        400: {"model": ErrorResponseSchema, "description": "Validation error"},
        404: {"model": ErrorResponseSchema, "description": "Walk-in not found"},
    },
)
async def add_service(
    walkin_id: str,
    data: AddServiceSchema,
    use_case: Annotated[AddServiceUseCase, Depends(get_add_service_use_case)],
):
    """
    Add a service to walk-in.

    **Permissions**: Admin, Manager, Washer

    **Auto-calculated**: Total amount, final amount
    """
    try:
        request = AddServiceRequest(
            walkin_id=walkin_id,
            service_id=data.service_id,
            service_name=data.service_name,
            price=data.price,
            product_costs=data.product_costs,
            quantity=data.quantity,
            notes=data.notes,
        )

        walkin = await use_case.execute(request)

        return WalkInServiceSchema(
            id=walkin.id,
            service_number=walkin.service_number,
            vehicle_make=walkin.vehicle_make,
            vehicle_model=walkin.vehicle_model,
            vehicle_color=walkin.vehicle_color,
            vehicle_size=walkin.vehicle_size,
            license_plate=walkin.license_plate,
            customer_name=walkin.customer_name,
            customer_phone=walkin.customer_phone,
            status=walkin.status,
            payment_status=walkin.payment_status,
            services=[
                {
                    "id": s.id,
                    "service_id": s.service_id,
                    "service_name": s.service_name,
                    "price": s.price,
                    "product_costs": s.product_costs,
                    "quantity": s.quantity,
                    "notes": s.notes,
                }
                for s in walkin.services
            ],
            total_amount=walkin.total_amount,
            discount_amount=walkin.discount_amount,
            discount_reason=walkin.discount_reason,
            final_amount=walkin.final_amount,
            paid_amount=walkin.paid_amount,
            started_at=walkin.started_at,
            completed_at=walkin.completed_at,
            cancelled_at=walkin.cancelled_at,
            created_by_id=walkin.created_by_id,
            completed_by_id=walkin.completed_by_id,
            cancelled_by_id=walkin.cancelled_by_id,
            notes=walkin.notes,
            cancellation_reason=walkin.cancellation_reason,
            created_at=walkin.created_at,
            updated_at=walkin.updated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Remove Service from Walk-in
# ============================================================================


@router.delete(
    "/{walkin_id}/services/{service_item_id}",
    response_model=WalkInServiceSchema,
    dependencies=[
        Depends(
            require_any_role(
                UserRole.ADMIN.value,
                UserRole.MANAGER.value,
                UserRole.WASHER.value,
            )
        )
    ],
    responses={
        400: {"model": ErrorResponseSchema, "description": "Validation error"},
        404: {"model": ErrorResponseSchema, "description": "Not found"},
    },
)
async def remove_service(
    walkin_id: str,
    service_item_id: str,
    use_case: Annotated[RemoveServiceUseCase, Depends(get_remove_service_use_case)],
):
    """
    Remove a service from walk-in.

    **Permissions**: Admin, Manager, Washer

    **Auto-recalculated**: Total amount, final amount
    """
    try:
        walkin = await use_case.execute(walkin_id, service_item_id)

        return WalkInServiceSchema(
            id=walkin.id,
            service_number=walkin.service_number,
            vehicle_make=walkin.vehicle_make,
            vehicle_model=walkin.vehicle_model,
            vehicle_color=walkin.vehicle_color,
            vehicle_size=walkin.vehicle_size,
            license_plate=walkin.license_plate,
            customer_name=walkin.customer_name,
            customer_phone=walkin.customer_phone,
            status=walkin.status,
            payment_status=walkin.payment_status,
            services=[
                {
                    "id": s.id,
                    "service_id": s.service_id,
                    "service_name": s.service_name,
                    "price": s.price,
                    "product_costs": s.product_costs,
                    "quantity": s.quantity,
                    "notes": s.notes,
                }
                for s in walkin.services
            ],
            total_amount=walkin.total_amount,
            discount_amount=walkin.discount_amount,
            discount_reason=walkin.discount_reason,
            final_amount=walkin.final_amount,
            paid_amount=walkin.paid_amount,
            started_at=walkin.started_at,
            completed_at=walkin.completed_at,
            cancelled_at=walkin.cancelled_at,
            created_by_id=walkin.created_by_id,
            completed_by_id=walkin.completed_by_id,
            cancelled_by_id=walkin.cancelled_by_id,
            notes=walkin.notes,
            cancellation_reason=walkin.cancellation_reason,
            created_at=walkin.created_at,
            updated_at=walkin.updated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Apply Discount
# ============================================================================


@router.post(
    "/{walkin_id}/discount",
    response_model=WalkInServiceSchema,
    dependencies=[
        Depends(
            require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value)
        )  # Only Admin/Manager can apply discounts
    ],
    responses={
        400: {"model": ErrorResponseSchema, "description": "Validation error"},
        404: {"model": ErrorResponseSchema, "description": "Walk-in not found"},
    },
)
async def apply_discount(
    walkin_id: str,
    data: ApplyDiscountSchema,
    use_case: Annotated[ApplyDiscountUseCase, Depends(get_apply_discount_use_case)],
):
    """
    Apply discount to walk-in.

    **Permissions**: Admin, Manager only

    **Max discount**: 50%
    """
    try:
        request = ApplyDiscountRequest(
            walkin_id=walkin_id,
            discount_percent=data.discount_percent,
            discount_reason=data.discount_reason,
        )

        walkin = await use_case.execute(request)

        return WalkInServiceSchema(
            id=walkin.id,
            service_number=walkin.service_number,
            vehicle_make=walkin.vehicle_make,
            vehicle_model=walkin.vehicle_model,
            vehicle_color=walkin.vehicle_color,
            vehicle_size=walkin.vehicle_size,
            license_plate=walkin.license_plate,
            customer_name=walkin.customer_name,
            customer_phone=walkin.customer_phone,
            status=walkin.status,
            payment_status=walkin.payment_status,
            services=[
                {
                    "id": s.id,
                    "service_id": s.service_id,
                    "service_name": s.service_name,
                    "price": s.price,
                    "product_costs": s.product_costs,
                    "quantity": s.quantity,
                    "notes": s.notes,
                }
                for s in walkin.services
            ],
            total_amount=walkin.total_amount,
            discount_amount=walkin.discount_amount,
            discount_reason=walkin.discount_reason,
            final_amount=walkin.final_amount,
            paid_amount=walkin.paid_amount,
            started_at=walkin.started_at,
            completed_at=walkin.completed_at,
            cancelled_at=walkin.cancelled_at,
            created_by_id=walkin.created_by_id,
            completed_by_id=walkin.completed_by_id,
            cancelled_by_id=walkin.cancelled_by_id,
            notes=walkin.notes,
            cancellation_reason=walkin.cancellation_reason,
            created_at=walkin.created_at,
            updated_at=walkin.updated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Record Payment
# ============================================================================


@router.post(
    "/{walkin_id}/payments",
    response_model=WalkInServiceSchema,
    dependencies=[
        Depends(
            require_any_role(
                UserRole.ADMIN.value,
                UserRole.MANAGER.value,
                UserRole.WASHER.value,
            )
        )
    ],
    responses={
        400: {"model": ErrorResponseSchema, "description": "Validation error"},
        404: {"model": ErrorResponseSchema, "description": "Walk-in not found"},
    },
)
async def record_payment(
    walkin_id: str,
    data: RecordPaymentSchema,
    use_case: Annotated[RecordPaymentUseCase, Depends(get_record_payment_use_case)],
):
    """
    Record payment for walk-in.

    **Permissions**: Admin, Manager, Washer

    **Payment methods**: CASH, CARD, MOBILE_MONEY, BANK_TRANSFER

    **Auto-updated**: Payment status (PENDING → PARTIAL → PAID)
    """
    try:
        request = RecordPaymentRequest(
            walkin_id=walkin_id,
            amount=data.amount,
            payment_method=data.payment_method,
            transaction_reference=data.transaction_reference,
            notes=data.notes,
        )

        walkin = await use_case.execute(request)

        return WalkInServiceSchema(
            id=walkin.id,
            service_number=walkin.service_number,
            vehicle_make=walkin.vehicle_make,
            vehicle_model=walkin.vehicle_model,
            vehicle_color=walkin.vehicle_color,
            vehicle_size=walkin.vehicle_size,
            license_plate=walkin.license_plate,
            customer_name=walkin.customer_name,
            customer_phone=walkin.customer_phone,
            status=walkin.status,
            payment_status=walkin.payment_status,
            services=[
                {
                    "id": s.id,
                    "service_id": s.service_id,
                    "service_name": s.service_name,
                    "price": s.price,
                    "product_costs": s.product_costs,
                    "quantity": s.quantity,
                    "notes": s.notes,
                }
                for s in walkin.services
            ],
            total_amount=walkin.total_amount,
            discount_amount=walkin.discount_amount,
            discount_reason=walkin.discount_reason,
            final_amount=walkin.final_amount,
            paid_amount=walkin.paid_amount,
            started_at=walkin.started_at,
            completed_at=walkin.completed_at,
            cancelled_at=walkin.cancelled_at,
            created_by_id=walkin.created_by_id,
            completed_by_id=walkin.completed_by_id,
            cancelled_by_id=walkin.cancelled_by_id,
            notes=walkin.notes,
            cancellation_reason=walkin.cancellation_reason,
            created_at=walkin.created_at,
            updated_at=walkin.updated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Complete Walk-in
# ============================================================================


@router.post(
    "/{walkin_id}/complete",
    response_model=WalkInServiceSchema,
    dependencies=[
        Depends(
            require_any_role(
                UserRole.ADMIN.value,
                UserRole.MANAGER.value,
                UserRole.WASHER.value,
            )
        )
    ],
    responses={
        400: {"model": ErrorResponseSchema, "description": "Validation error"},
        404: {"model": ErrorResponseSchema, "description": "Walk-in not found"},
    },
)
async def complete_walkin(
    walkin_id: str,
    use_case: Annotated[CompleteWalkInUseCase, Depends(get_complete_walkin_use_case)],
    current_user=Depends(get_current_user),
):
    """
    Complete walk-in service.

    **Permissions**: Admin, Manager, Washer

    **Requirements**: Must have services and full payment

    **Auto-calculated**: Service duration
    """
    try:
        walkin = await use_case.execute(walkin_id, current_user["user_id"])

        return WalkInServiceSchema(
            id=walkin.id,
            service_number=walkin.service_number,
            vehicle_make=walkin.vehicle_make,
            vehicle_model=walkin.vehicle_model,
            vehicle_color=walkin.vehicle_color,
            vehicle_size=walkin.vehicle_size,
            license_plate=walkin.license_plate,
            customer_name=walkin.customer_name,
            customer_phone=walkin.customer_phone,
            status=walkin.status,
            payment_status=walkin.payment_status,
            services=[
                {
                    "id": s.id,
                    "service_id": s.service_id,
                    "service_name": s.service_name,
                    "price": s.price,
                    "product_costs": s.product_costs,
                    "quantity": s.quantity,
                    "notes": s.notes,
                }
                for s in walkin.services
            ],
            total_amount=walkin.total_amount,
            discount_amount=walkin.discount_amount,
            discount_reason=walkin.discount_reason,
            final_amount=walkin.final_amount,
            paid_amount=walkin.paid_amount,
            started_at=walkin.started_at,
            completed_at=walkin.completed_at,
            cancelled_at=walkin.cancelled_at,
            created_by_id=walkin.created_by_id,
            completed_by_id=walkin.completed_by_id,
            cancelled_by_id=walkin.cancelled_by_id,
            notes=walkin.notes,
            cancellation_reason=walkin.cancellation_reason,
            created_at=walkin.created_at,
            updated_at=walkin.updated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Cancel Walk-in
# ============================================================================


@router.post(
    "/{walkin_id}/cancel",
    response_model=WalkInServiceSchema,
    dependencies=[
        Depends(
            require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value)
        )  # Only Admin/Manager can cancel
    ],
    responses={
        400: {"model": ErrorResponseSchema, "description": "Validation error"},
        404: {"model": ErrorResponseSchema, "description": "Walk-in not found"},
    },
)
async def cancel_walkin(
    walkin_id: str,
    data: CancelWalkInSchema,
    use_case: Annotated[CancelWalkInUseCase, Depends(get_cancel_walkin_use_case)],
    current_user=Depends(get_current_user),
):
    """
    Cancel walk-in service.

    **Permissions**: Admin, Manager only

    **Requirements**: No payment made (process refund first if paid)
    """
    try:
        walkin = await use_case.execute(
            walkin_id, current_user["user_id"], data.reason
        )

        return WalkInServiceSchema(
            id=walkin.id,
            service_number=walkin.service_number,
            vehicle_make=walkin.vehicle_make,
            vehicle_model=walkin.vehicle_model,
            vehicle_color=walkin.vehicle_color,
            vehicle_size=walkin.vehicle_size,
            license_plate=walkin.license_plate,
            customer_name=walkin.customer_name,
            customer_phone=walkin.customer_phone,
            status=walkin.status,
            payment_status=walkin.payment_status,
            services=[
                {
                    "id": s.id,
                    "service_id": s.service_id,
                    "service_name": s.service_name,
                    "price": s.price,
                    "product_costs": s.product_costs,
                    "quantity": s.quantity,
                    "notes": s.notes,
                }
                for s in walkin.services
            ],
            total_amount=walkin.total_amount,
            discount_amount=walkin.discount_amount,
            discount_reason=walkin.discount_reason,
            final_amount=walkin.final_amount,
            paid_amount=walkin.paid_amount,
            started_at=walkin.started_at,
            completed_at=walkin.completed_at,
            cancelled_at=walkin.cancelled_at,
            created_by_id=walkin.created_by_id,
            completed_by_id=walkin.completed_by_id,
            cancelled_by_id=walkin.cancelled_by_id,
            notes=walkin.notes,
            cancellation_reason=walkin.cancellation_reason,
            created_at=walkin.created_at,
            updated_at=walkin.updated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Get Daily Report
# ============================================================================


@router.get(
    "/reports/daily/{report_date}",
    response_model=DailyReportSchema,
    dependencies=[
        Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))
    ],
    responses={
        400: {"model": ErrorResponseSchema, "description": "Validation error"},
    },
)
async def get_daily_report(
    report_date: date,
    use_case: Annotated[GetDailyReportUseCase, Depends(get_daily_report_use_case)],
):
    """
    Get daily walk-in report with statistics.

    **Permissions**: Admin, Manager

    **Statistics**: Revenue, costs, profit, service counts, average time
    """
    try:
        report = await use_case.execute(report_date)

        return DailyReportSchema(
            report_date=report.report_date,
            total_services=report.total_services,
            completed_services=report.completed_services,
            cancelled_services=report.cancelled_services,
            in_progress_services=report.in_progress_services,
            total_revenue=report.total_revenue,
            total_costs=report.total_costs,
            total_profit=report.total_profit,
            total_discounts=report.total_discounts,
            avg_service_time_minutes=report.avg_service_time_minutes,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
