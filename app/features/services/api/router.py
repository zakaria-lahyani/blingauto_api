from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status, Request
from fastapi.responses import JSONResponse
import logging

from app.shared.auth import get_current_user as get_auth_user, require_any_role
from app.shared.auth.contracts import AuthenticatedUser
from app.features.auth.api.dependencies import CurrentUser, AdminUser
from app.features.services.use_cases import (
    CreateCategoryUseCase,
    CreateServiceUseCase,
    UpdateServicePriceUseCase,
    SetServicePopularUseCase,
    ListCategoriesUseCase,
    ListServicesUseCase,
    GetServiceUseCase,
    DeactivateServiceUseCase,
    GetPopularServicesUseCase,
    SearchServicesUseCase,
)
from app.features.services.api.dependencies import (
    get_create_category_use_case,
    get_create_service_use_case,
    get_list_categories_use_case,
    get_list_services_use_case,
    get_get_service_use_case,
    get_update_service_price_use_case,
    get_set_service_popular_use_case,
    get_deactivate_service_use_case,
    get_popular_services_use_case,
    get_search_services_use_case,
)
from app.features.services.api.schemas import (
    CreateCategorySchema,
    CreateServiceSchema,
    UpdateServicePriceSchema,
    SetServicePopularSchema,
    CategoryResponseSchema,
    ServiceResponseSchema,
    ServiceListResponseSchema,
    CategoryListResponseSchema,
    PopularServicesResponseSchema,
    CreateCategoryResponseSchema,
    CreateServiceResponseSchema,
    UpdateServicePriceResponseSchema,
    SetServicePopularResponseSchema,
    ServiceSummarySchema,
)
from app.core.errors.exceptions import (
    ValidationError,
    NotFoundError,
    BusinessRuleViolationError,
)

router = APIRouter()

logger = logging.getLogger(__name__)

# Auth dependency helpers - use shared auth
require_manager_or_admin = require_any_role("admin", "manager")
require_admin_role = require_any_role("admin")


@router.post("/categories", response_model=CreateCategoryResponseSchema)
async def create_category(
    category_data: CreateCategorySchema,
    current_user: AuthenticatedUser = Depends(require_admin_role),
    use_case: CreateCategoryUseCase = Depends(get_create_category_use_case),
):
    """Create a new service category. Admin only."""
    try:
        from app.features.services.use_cases.create_category import CreateCategoryRequest

        use_case_request = CreateCategoryRequest(
            name=category_data.name,
            description=category_data.description,
            display_order=category_data.display_order,
            created_by=current_user.id,
        )
        result = await use_case.execute(use_case_request)
        
        return CreateCategoryResponseSchema(
            category_id=result.category_id,
            name=result.name,
            description=result.description,
            status=result.status,
            display_order=result.display_order,
        )

    except ValidationError as e:
        logger.error(f"Validation error in create_category: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BusinessRuleViolationError as e:
        logger.error(f"Business rule violation in create_category: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in create_category: {type(e).__name__}: {e}", exc_info=True)
        raise


@router.get("/categories", response_model=CategoryListResponseSchema)
async def list_categories(
    include_inactive: bool = Query(False, description="Include inactive categories"),
    current_user: AuthenticatedUser = Depends(require_any_role("admin", "manager", "client", "washer")),
    use_case: ListCategoriesUseCase = Depends(get_list_categories_use_case),
):
    """List all service categories."""
    try:
        from app.features.services.use_cases.list_categories import ListCategoriesRequest

        logger.info(f"Current user type: {type(current_user)}, value: {current_user}")
        logger.info(f"Listing categories: include_inactive={include_inactive}, user={current_user.id}")

        request = ListCategoriesRequest(
            include_inactive=include_inactive,
            requesting_user_id=current_user.id,
        )

        logger.info("Executing list categories use case")
        result = await use_case.execute(request)
        logger.info(f"Got {len(result.categories)} categories from use case")

        categories = [
            CategoryResponseSchema(
                id=cat.id,
                name=cat.name,
                description=cat.description,
                status=cat.status,
                display_order=cat.display_order,
                service_count=cat.service_count,
            )
            for cat in result.categories
        ]

        logger.info(f"Returning {len(categories)} categories")
        return CategoryListResponseSchema(
            categories=categories,
            total_count=result.total_count,
        )

    except Exception as e:
        logger.error(f"Error listing categories: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve categories: {str(e)}"
        )


@router.post("/categories/{category_id}/services", response_model=CreateServiceResponseSchema)
async def create_service(
    category_id: str,
    *,
    service_data: CreateServiceSchema,
    current_user: AuthenticatedUser = Depends(require_manager_or_admin),
    use_case: CreateServiceUseCase = Depends(get_create_service_use_case),
):
    """Create a new service in a category. Manager or Admin only."""
    try:
        from app.features.services.use_cases.create_service import CreateServiceRequest
        
        request = CreateServiceRequest(
            category_id=category_id,
            name=service_data.name,
            description=service_data.description,
            price=service_data.price,
            duration_minutes=service_data.duration_minutes,
            is_popular=service_data.is_popular,
            display_order=service_data.display_order,
            created_by=current_user.id,
        )
        response = await use_case.execute(request)

        # The use case returns CreateServiceResponse, just return it directly
        return CreateServiceResponseSchema(
            service_id=response.service_id,
            category_id=response.category_id,
            name=response.name,
            description=response.description,
            price=response.price,
            duration_minutes=response.duration_minutes,
            status=response.status,
            is_popular=response.is_popular,
            display_order=response.display_order,
            price_display=response.price_display,
            duration_display=response.duration_display,
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.get("/", response_model=ServiceListResponseSchema)
async def list_services(
    category_id: Optional[str] = Query(None, description="Filter by category"),
    include_inactive: bool = Query(False, description="Include inactive services"),
    is_popular: bool = Query(False, description="Filter popular services only"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price filter"),
    min_duration: Optional[int] = Query(None, ge=0, description="Minimum duration (minutes)"),
    max_duration: Optional[int] = Query(None, ge=0, description="Maximum duration (minutes)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: AuthenticatedUser = CurrentUser,
    use_case: ListServicesUseCase = Depends(get_list_services_use_case),
):
    """List services with optional filters and pagination."""
    try:
        from app.features.services.use_cases.list_services import ListServicesRequest

        request = ListServicesRequest(
            category_id=category_id,
            include_inactive=include_inactive,
            popular_only=is_popular,
            min_price=min_price,
            max_price=max_price,
            min_duration=min_duration,
            max_duration=max_duration,
            search_query=search,
            page=page,
            limit=limit,
        )

        result = await use_case.execute(request)

        services = [
            ServiceSummarySchema(
                id=srv.id,
                category_id=srv.category_id,
                category_name=srv.category_name,
                name=srv.name,
                description=srv.description,
                price=srv.price,
                duration_minutes=srv.duration_minutes,
                status=srv.status,
                is_popular=srv.is_popular,
                price_display=srv.price_display,
                duration_display=srv.duration_display,
            )
            for srv in result.services
        ]

        return ServiceListResponseSchema(
            services=services,
            total_count=result.total_count,
            page=page,
            limit=limit,
            has_next=result.has_next,
            filters_applied=result.filters_applied,
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/popular", response_model=PopularServicesResponseSchema)
async def get_popular_services(
    limit: int = Query(10, ge=1, le=50, description="Number of popular services"),
    current_user: AuthenticatedUser = CurrentUser,
    use_case: GetPopularServicesUseCase = Depends(get_popular_services_use_case),
):
    """Get popular services."""
    try:
        result = await use_case.execute(
            limit=limit,
            requesting_user_id=current_user.id,
        )
        
        services = [
            ServiceSummarySchema(
                id=srv.id,
                category_id=srv.category_id,
                category_name=result.get("category_names", {}).get(srv.category_id, "Unknown"),
                name=srv.name,
                description=srv.description,
                price=srv.price,
                duration_minutes=srv.duration_minutes,
                status=srv.status.value,
                is_popular=srv.is_popular,
                price_display=srv.price_display,
                duration_display=srv.duration_display,
            )
            for srv in result["services"]
        ]
        
        return PopularServicesResponseSchema(
            services=services,
            total_count=len(services),
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve popular services"
        )


@router.get("/search", response_model=ServiceListResponseSchema)
async def search_services(
    q: str = Query(..., min_length=2, description="Search query"),
    category_id: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=50, description="Maximum results"),
    current_user: AuthenticatedUser = CurrentUser,
    use_case: SearchServicesUseCase = Depends(get_search_services_use_case),
):
    """Search services by name or description."""
    try:
        result = await use_case.execute(
            query=q,
            category_id=category_id,
            limit=limit,
            requesting_user_id=current_user.id,
        )
        
        services = [
            ServiceSummarySchema(
                id=srv.id,
                category_id=srv.category_id,
                category_name=result.get("category_names", {}).get(srv.category_id, "Unknown"),
                name=srv.name,
                description=srv.description,
                price=srv.price,
                duration_minutes=srv.duration_minutes,
                status=srv.status.value,
                is_popular=srv.is_popular,
                price_display=srv.price_display,
                duration_display=srv.duration_display,
            )
            for srv in result["services"]
        ]
        
        return ServiceListResponseSchema(
            services=services,
            total_count=len(services),
            page=1,
            limit=limit,
            has_next=False,
            filters_applied={"search_query": q, "category_id": category_id},
        )
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{service_id}", response_model=ServiceResponseSchema)
async def get_service(
    service_id: str,
    current_user: AuthenticatedUser = CurrentUser,
    use_case: GetServiceUseCase = Depends(get_get_service_use_case),
):
    """Get a specific service by ID."""
    try:
        from app.features.services.use_cases.get_service import GetServiceRequest

        request = GetServiceRequest(
            service_id=service_id,
            requesting_user_id=current_user.id,
        )
        service = await use_case.execute(request)

        return ServiceResponseSchema(
            id=service.id,
            category_id=service.category_id,
            name=service.name,
            description=service.description,
            price=service.price,
            duration_minutes=service.duration_minutes,
            status=service.status,
            is_popular=service.is_popular,
            display_order=service.display_order,
            price_display=service.price_display,
            duration_display=service.duration_display,
        )
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.patch("/{service_id}/price", response_model=UpdateServicePriceResponseSchema)
async def update_service_price(
    service_id: str,
    *,
    price_data: UpdateServicePriceSchema,
    current_user: AuthenticatedUser = Depends(require_manager_or_admin),
    use_case: UpdateServicePriceUseCase = Depends(get_update_service_price_use_case),
):
    """Update service price. Manager or Admin only."""
    try:
        from app.features.services.use_cases.update_service_price import UpdateServicePriceRequest

        request = UpdateServicePriceRequest(
            service_id=service_id,
            new_price=price_data.new_price,
            notify_customers=price_data.notify_customers,
            updated_by=current_user.id,
        )
        result = await use_case.execute(request)

        return UpdateServicePriceResponseSchema(
            service_id=result.service_id,
            old_price=result.old_price,
            new_price=result.new_price,
            price_change_percent=result.price_change_percent,
            affected_future_bookings=result.affected_future_bookings,
            customers_notified=result.customers_notified,
            price_display=result.price_display,
        )
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.patch("/{service_id}/popular", response_model=SetServicePopularResponseSchema)
async def set_service_popular(
    service_id: str,
    *,
    popular_data: SetServicePopularSchema,
    current_user: AuthenticatedUser = Depends(require_manager_or_admin),
    use_case: SetServicePopularUseCase = Depends(get_set_service_popular_use_case),
):
    """Set or unset service as popular. Manager or Admin only."""
    try:
        from app.features.services.use_cases.set_service_popular import SetServicePopularRequest

        request = SetServicePopularRequest(
            service_id=service_id,
            is_popular=popular_data.is_popular,
            updated_by=current_user.id,
        )
        result = await use_case.execute(request)

        return SetServicePopularResponseSchema(
            service_id=result.service_id,
            name=result.name,
            is_popular=result.is_popular,
            category_popular_count=result.category_popular_count,
            message=result.message,
        )
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.delete("/{service_id}")
async def deactivate_service(
    service_id: str,
    reason: str = Query(..., min_length=10, description="Reason for deactivation"),
    current_user: AuthenticatedUser = Depends(require_admin_role),
    use_case: DeactivateServiceUseCase = Depends(get_deactivate_service_use_case),
):
    """Deactivate a service. Admin only."""
    try:
        await use_case.execute(
            service_id=service_id,
            reason=reason,
            deactivated_by=current_user.id,
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Service deactivated successfully"}
        )
    
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
# Alias for backward compatibility
service_router = router
