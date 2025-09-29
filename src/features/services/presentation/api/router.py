"""
Services API router
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.database.session import get_db
from src.shared.auth import require_manager_or_admin, get_optional_user
from src.features.auth.domain.entities import AuthUser
from src.features.services.application.services import CategoryService, ServiceService
from src.features.services.infrastructure.database.repositories import ServiceCategoryRepository, ServiceRepository
from src.features.services.domain.enums import CategoryStatus, ServiceStatus
from .schemas import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryListResponse,
    ServiceCreate, ServiceUpdate, ServiceResponse, ServiceListResponse,
    ServiceWithCategoryResponse, ServiceSearchResponse,
    CategoryListParams, ServiceListParams, ServiceSearchParams,
    CategoryStatusUpdate, ServiceStatusUpdate, ServicePopularUpdate,
    MessageResponse
)

router = APIRouter(prefix="/services", tags=["Services"])


def get_category_service(db: AsyncSession = Depends(get_db)) -> CategoryService:
    """Get category service instance"""
    category_repository = ServiceCategoryRepository(db)
    return CategoryService(category_repository)


def get_service_service(db: AsyncSession = Depends(get_db)) -> ServiceService:
    """Get service service instance"""
    service_repository = ServiceRepository(db)
    category_repository = ServiceCategoryRepository(db)
    return ServiceService(service_repository, category_repository)


# Category endpoints
@router.get("/categories", response_model=CategoryListResponse)
async def list_categories(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[CategoryStatus] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("name"),
    sort_desc: bool = Query(False),
    category_service: CategoryService = Depends(get_category_service),
    current_user: Optional[AuthUser] = Depends(get_optional_user)
):
    """List service categories with pagination and filtering"""
    try:
        from src.features.services.domain.enums import CategorySortBy
        sort_by_enum = CategorySortBy(sort_by) if sort_by in ["name", "created_at"] else CategorySortBy.NAME
        
        categories, total = await category_service.list_categories(
            page=page,
            page_size=size,
            status=status,
            search=search,
            sort_by=sort_by_enum,
            sort_desc=sort_desc
        )
        
        pages = (total + size - 1) // size if total > 0 else 1
        
        return CategoryListResponse(
            categories=[CategoryResponse.from_orm(cat) for cat in categories],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    category_service: CategoryService = Depends(get_category_service),
    current_user: Optional[AuthUser] = Depends(get_optional_user)
):
    """Get a specific category by ID"""
    category = await category_service.get_category_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return CategoryResponse.from_orm(category)


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    category_service: CategoryService = Depends(get_category_service),
    current_user: AuthUser = Depends(require_manager_or_admin)
):
    """Create a new service category (Manager/Admin only)"""
    try:
        category = await category_service.create_category(
            name=category_data.name,
            description=category_data.description
        )
        return CategoryResponse.from_orm(category)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create category")


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    category_service: CategoryService = Depends(get_category_service),
    current_user: AuthUser = Depends(require_manager_or_admin)
):
    """Update a service category (Manager/Admin only)"""
    try:
        category = await category_service.update_category(
            category_id=category_id,
            name=category_data.name,
            description=category_data.description
        )
        return CategoryResponse.from_orm(category)
    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e) else 400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update category")


@router.patch("/categories/{category_id}/status", response_model=CategoryResponse)
async def update_category_status(
    category_id: UUID,
    status_data: CategoryStatusUpdate,
    category_service: CategoryService = Depends(get_category_service),
    current_user: AuthUser = Depends(require_manager_or_admin)
):
    """Update category status (Manager/Admin only)"""
    try:
        if status_data.status == CategoryStatus.ACTIVE:
            category = await category_service.activate_category(category_id)
        else:
            category = await category_service.deactivate_category(category_id)
        
        return CategoryResponse.from_orm(category)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update category status")


@router.delete("/categories/{category_id}", response_model=MessageResponse)
async def delete_category(
    category_id: UUID,
    category_service: CategoryService = Depends(get_category_service),
    current_user: AuthUser = Depends(require_manager_or_admin)
):
    """Delete a service category (Manager/Admin only)"""
    try:
        success = await category_service.delete_category(category_id)
        if not success:
            raise HTTPException(status_code=404, detail="Category not found")
        
        return MessageResponse(message="Category deleted successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete category")


# Service endpoints
@router.get("/", response_model=ServiceListResponse)
async def list_services(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category_id: Optional[UUID] = Query(None),
    status: Optional[ServiceStatus] = Query(None),
    popular_only: bool = Query(False),
    search: Optional[str] = Query(None),
    sort_by: str = Query("name"),
    sort_desc: bool = Query(False),
    service_service: ServiceService = Depends(get_service_service),
    current_user: Optional[AuthUser] = Depends(get_optional_user)
):
    """List services with pagination and filtering"""
    try:
        from src.features.services.domain.enums import ServiceSortBy
        sort_by_enum = ServiceSortBy(sort_by) if sort_by in ["name", "price", "duration", "created_at", "popularity"] else ServiceSortBy.NAME
        
        services, total = await service_service.list_services(
            page=page,
            page_size=size,
            category_id=category_id,
            status=status,
            popular_only=popular_only,
            search=search,
            sort_by=sort_by_enum,
            sort_desc=sort_desc
        )
        
        pages = (total + size - 1) // size if total > 0 else 1
        
        return ServiceListResponse(
            services=[ServiceResponse.from_orm(service) for service in services],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/popular", response_model=List[ServiceResponse])
async def get_popular_services(
    limit: int = Query(10, ge=1, le=50),
    service_service: ServiceService = Depends(get_service_service),
    current_user: Optional[AuthUser] = Depends(get_optional_user)
):
    """Get popular services"""
    try:
        services = await service_service.get_popular_services(limit)
        return [ServiceResponse.from_orm(service) for service in services]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=ServiceSearchResponse)
async def search_services(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category_id: Optional[UUID] = Query(None),
    active_only: bool = Query(True),
    service_service: ServiceService = Depends(get_service_service),
    current_user: Optional[AuthUser] = Depends(get_optional_user)
):
    """Search services by name and description"""
    try:
        services, total = await service_service.search_services(
            query=q,
            page=page,
            page_size=size,
            category_id=category_id,
            active_only=active_only
        )
        
        pages = (total + size - 1) // size if total > 0 else 1
        
        # For search results, we might want to include category name
        # This would require modifying the service to include category info
        return ServiceSearchResponse(
            services=[ServiceWithCategoryResponse(
                **service.dict(),
                category_name="Unknown"  # TODO: Add category name lookup
            ) for service in [ServiceResponse.from_orm(s) for s in services]],
            total=total,
            page=page,
            size=size,
            pages=pages,
            query=q
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: UUID,
    service_service: ServiceService = Depends(get_service_service),
    current_user: Optional[AuthUser] = Depends(get_optional_user)
):
    """Get a specific service by ID"""
    service = await service_service.get_service_by_id(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return ServiceResponse.from_orm(service)


@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    service_service: ServiceService = Depends(get_service_service),
    current_user: AuthUser = Depends(require_manager_or_admin)
):
    """Create a new service (Manager/Admin only)"""
    try:
        service = await service_service.create_service(
            name=service_data.name,
            price=service_data.price,
            duration=service_data.duration,
            category_id=service_data.category_id,
            description=service_data.description,
            point_description=service_data.point_description
        )
        return ServiceResponse.from_orm(service)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create service")


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: UUID,
    service_data: ServiceUpdate,
    service_service: ServiceService = Depends(get_service_service),
    current_user: AuthUser = Depends(require_manager_or_admin)
):
    """Update a service (Manager/Admin only)"""
    try:
        service = await service_service.update_service(
            service_id=service_id,
            name=service_data.name,
            price=service_data.price,
            duration=service_data.duration,
            category_id=service_data.category_id,
            description=service_data.description,
            point_description=service_data.point_description
        )
        return ServiceResponse.from_orm(service)
    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e) else 400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update service")


@router.patch("/{service_id}/status", response_model=ServiceResponse)
async def update_service_status(
    service_id: UUID,
    status_data: ServiceStatusUpdate,
    service_service: ServiceService = Depends(get_service_service),
    current_user: AuthUser = Depends(require_manager_or_admin)
):
    """Update service status (Manager/Admin only)"""
    try:
        if status_data.status == ServiceStatus.ACTIVE:
            service = await service_service.activate_service(service_id)
        else:
            service = await service_service.deactivate_service(service_id)
        
        return ServiceResponse.from_orm(service)
    except ValueError as e:
        raise HTTPException(status_code=404 if "not found" in str(e) else 400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update service status")


@router.patch("/{service_id}/mark-popular", response_model=ServiceResponse)
async def mark_service_popular(
    service_id: UUID,
    service_service: ServiceService = Depends(get_service_service),
    current_user: AuthUser = Depends(require_manager_or_admin)
):
    """Mark service as popular (Manager/Admin only)"""
    try:
        service = await service_service.mark_service_popular(service_id)
        return ServiceResponse.from_orm(service)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to mark service as popular")


@router.patch("/{service_id}/unmark-popular", response_model=ServiceResponse)
async def unmark_service_popular(
    service_id: UUID,
    service_service: ServiceService = Depends(get_service_service),
    current_user: AuthUser = Depends(require_manager_or_admin)
):
    """Unmark service as popular (Manager/Admin only)"""
    try:
        service = await service_service.unmark_service_popular(service_id)
        return ServiceResponse.from_orm(service)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to unmark service as popular")


@router.delete("/{service_id}", response_model=MessageResponse)
async def delete_service(
    service_id: UUID,
    service_service: ServiceService = Depends(get_service_service),
    current_user: AuthUser = Depends(require_manager_or_admin)
):
    """Delete a service (Manager/Admin only)"""
    try:
        success = await service_service.delete_service(service_id)
        if not success:
            raise HTTPException(status_code=404, detail="Service not found")
        
        return MessageResponse(message="Service deleted successfully")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete service")