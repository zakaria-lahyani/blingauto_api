"""
Public Services API router (without auth dependencies)
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from src.shared.database import get_db
from src.features.services.application.services import CategoryService, ServiceService
from src.features.services.infrastructure.database.repositories import ServiceCategoryRepository, ServiceRepository
from src.features.services.domain.enums import CategoryStatus, ServiceStatus
from src.features.services.presentation.api.schemas import (
    CategoryResponse, CategoryListResponse,
    ServiceResponse, ServiceListResponse,
    ServiceWithCategoryResponse, ServiceSearchResponse
)

router = APIRouter(prefix="/services", tags=["services"])


def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
    """Get category service instance"""
    category_repository = ServiceCategoryRepository(db)
    return CategoryService(category_repository)


def get_service_service(db: Session = Depends(get_db)) -> ServiceService:
    """Get service service instance"""
    service_repository = ServiceRepository(db)
    category_repository = ServiceCategoryRepository(db)
    return ServiceService(service_repository, category_repository)


# Public endpoints only for now
@router.get("/categories", response_model=CategoryListResponse)
async def list_categories(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[CategoryStatus] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("name"),
    sort_desc: bool = Query(False),
    category_service: CategoryService = Depends(get_category_service)
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
    category_service: CategoryService = Depends(get_category_service)
):
    """Get a specific category by ID"""
    category = await category_service.get_category_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return CategoryResponse.from_orm(category)


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
    service_service: ServiceService = Depends(get_service_service)
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
    service_service: ServiceService = Depends(get_service_service)
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
    service_service: ServiceService = Depends(get_service_service)
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
    service_service: ServiceService = Depends(get_service_service)
):
    """Get a specific service by ID"""
    service = await service_service.get_service_by_id(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return ServiceResponse.from_orm(service)