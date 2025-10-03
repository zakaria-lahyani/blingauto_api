from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal

from app.core.errors import ValidationError
from app.features.services.domain import Service, Category
from app.features.services.ports import (
    IServiceRepository,
    ICategoryRepository,
    ICacheService,
)


@dataclass
class ListServicesRequest:
    category_id: Optional[str] = None
    include_inactive: bool = False
    popular_only: bool = False
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None
    search_query: Optional[str] = None
    page: int = 1
    limit: int = 20


@dataclass
class ServiceSummary:
    id: str
    category_id: str
    category_name: str
    name: str
    description: str
    price: Decimal
    duration_minutes: int
    status: str
    is_popular: bool
    price_display: str
    duration_display: str


@dataclass
class ListServicesResponse:
    services: List[ServiceSummary]
    total_count: int
    page: int
    limit: int
    has_next: bool
    filters_applied: dict


class ListServicesUseCase:
    """Use case for listing services with filters."""
    
    def __init__(
        self,
        service_repository: IServiceRepository,
        category_repository: ICategoryRepository,
        cache_service: ICacheService,
    ):
        self._service_repository = service_repository
        self._category_repository = category_repository
        self._cache_service = cache_service
    
    async def execute(self, request: ListServicesRequest) -> ListServicesResponse:
        """Execute the list services use case."""

        # Step 1: Validate pagination parameters
        if request.page < 1:
            raise ValidationError("Page must be greater than 0")
        if request.limit < 1 or request.limit > 100:
            raise ValidationError("Limit must be between 1 and 100")

        # Step 2: Calculate offset
        offset = (request.page - 1) * request.limit

        # Step 3: Try to get from cache for common queries
        cached_services = None
        if (request.popular_only and not request.category_id and
            not request.search_query and request.page == 1):
            cached_services = await self._cache_service.get_popular_services()
        elif (request.category_id and not request.search_query and
              not request.popular_only and request.page == 1):
            cached_services = await self._cache_service.get_category_services(
                request.category_id
            )

        services = []

        if cached_services is not None:
            # Use cached data
            services = cached_services
            # Apply pagination to cached results
            services = services[offset:offset + request.limit]
        else:
            # Step 4: Query services based on filters
            if request.search_query:
                # Search services
                services = await self._service_repository.search_services(
                    request.search_query,
                    category_id=request.category_id,
                    limit=request.limit * 2,  # Get more for filtering
                )
            elif request.popular_only:
                # Get popular services
                services = await self._service_repository.list_popular(limit=50)
                if request.category_id:
                    services = [s for s in services if s.category_id == request.category_id]
            elif request.min_price is not None and request.max_price is not None:
                # Filter by price range
                services = await self._service_repository.list_by_price_range(
                    request.min_price,
                    request.max_price,
                    category_id=request.category_id,
                    limit=request.limit * 2,
                )
            elif request.min_duration is not None and request.max_duration is not None:
                # Filter by duration range
                services = await self._service_repository.list_by_duration_range(
                    request.min_duration,
                    request.max_duration,
                    category_id=request.category_id,
                    limit=request.limit * 2,
                )
            elif request.category_id:
                # List by category
                services = await self._service_repository.list_by_category(
                    request.category_id,
                    include_inactive=request.include_inactive,
                    offset=offset,
                    limit=request.limit,
                )
            else:
                # List all services
                services = await self._service_repository.list_all(
                    include_inactive=request.include_inactive,
                    offset=offset,
                    limit=request.limit,
                )
            
            # Step 5: Apply additional filters
            if not request.include_inactive:
                services = [s for s in services if s.is_active]
            
            if request.min_price is not None:
                services = [s for s in services if s.price >= request.min_price]
            if request.max_price is not None:
                services = [s for s in services if s.price <= request.max_price]
            
            if request.min_duration is not None:
                services = [s for s in services if s.duration_minutes >= request.min_duration]
            if request.max_duration is not None:
                services = [s for s in services if s.duration_minutes <= request.max_duration]
            
            # Apply pagination to filtered results
            services = services[offset:offset + request.limit]
        
        # Step 6: Get categories for service summaries
        category_map = {}
        for service in services:
            if service.category_id not in category_map:
                category = await self._category_repository.get_by_id(service.category_id)
                if category:
                    category_map[service.category_id] = category.name
        
        # Step 7: Convert to summary format
        service_summaries = [
            ServiceSummary(
                id=service.id,
                category_id=service.category_id,
                category_name=category_map.get(service.category_id, "Unknown"),
                name=service.name,
                description=service.description,
                price=service.price,
                duration_minutes=service.duration_minutes,
                status=service.status.value if hasattr(service.status, 'value') else service.status,
                is_popular=service.is_popular,
                price_display=service.price_display,
                duration_display=service.duration_display,
            )
            for service in services
        ]
        
        # Step 8: Get total count (simplified - would need proper counting)
        total_count = len(service_summaries)
        if len(service_summaries) == request.limit:
            # There might be more
            total_count = offset + len(service_summaries) + 1
        
        # Step 9: Cache results if appropriate
        if request.popular_only and not cached_services and request.page == 1:
            popular_services = self._service_repository.list_popular()
            self._cache_service.set_popular_services(popular_services)
        elif request.category_id and not cached_services and request.page == 1:
            category_services = self._service_repository.list_by_category(
                request.category_id, include_inactive=False
            )
            self._cache_service.set_category_services(
                request.category_id, category_services
            )
        
        # Step 10: Prepare response
        filters_applied = {
            "category": request.category_id is not None,
            "popular": request.popular_only,
            "price_range": request.min_price is not None or request.max_price is not None,
            "duration_range": request.min_duration is not None or request.max_duration is not None,
            "search": request.search_query is not None,
            "include_inactive": request.include_inactive,
        }
        
        has_next = len(service_summaries) == request.limit
        
        return ListServicesResponse(
            services=service_summaries,
            total_count=total_count,
            page=request.page,
            limit=request.limit,
            has_next=has_next,
            filters_applied=filters_applied,
        )