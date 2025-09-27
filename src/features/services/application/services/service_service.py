"""
Service business logic
"""
from typing import List, Optional, Tuple
from uuid import UUID
from decimal import Decimal

from src.features.services.domain.entities import Service, ServiceCategory
from src.features.services.domain.enums import ServiceStatus, ServiceSortBy, CategoryStatus
from src.features.services.infrastructure.database.repositories import ServiceRepository, ServiceCategoryRepository


class ServiceService:
    """Service for managing services"""
    
    def __init__(
        self,
        service_repository: ServiceRepository,
        category_repository: ServiceCategoryRepository
    ):
        self.service_repository = service_repository
        self.category_repository = category_repository
    
    async def create_service(
        self,
        name: str,
        price: Decimal,
        duration: int,
        category_id: UUID,
        description: Optional[str] = None,
        point_description: Optional[List[str]] = None
    ) -> Service:
        """Create a new service"""
        # Validate category exists and is active
        category = await self.category_repository.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with id {category_id} not found")
        
        if not category.is_active:
            raise ValueError("Cannot create service in inactive category")
        
        # Validate inputs
        name = name.strip()
        if len(name) == 0:
            raise ValueError("Service name cannot be empty")
        
        if len(name) > 100:
            raise ValueError("Service name cannot exceed 100 characters")
        
        if price <= 0:
            raise ValueError("Service price must be positive")
        
        if duration <= 0:
            raise ValueError("Service duration must be positive")
        
        # Clean point descriptions
        clean_points = []
        if point_description:
            for point in point_description:
                if isinstance(point, str) and point.strip():
                    clean_points.append(point.strip())
        
        # Create the service
        service = Service(
            name=name,
            price=price,
            duration=duration,
            category_id=category_id,
            description=description.strip() if description else None,
            point_description=clean_points,
            status=ServiceStatus.ACTIVE,
            popular=False
        )
        
        return await self.service_repository.create(service)
    
    async def get_service_by_id(self, service_id: UUID) -> Optional[Service]:
        """Get service by ID"""
        return await self.service_repository.get_by_id(service_id)
    
    async def list_services(
        self,
        page: int = 1,
        page_size: int = 20,
        category_id: Optional[UUID] = None,
        status: Optional[ServiceStatus] = None,
        popular_only: bool = False,
        search: Optional[str] = None,
        sort_by: ServiceSortBy = ServiceSortBy.NAME,
        sort_desc: bool = False
    ) -> Tuple[List[Service], int]:
        """List services with pagination and filtering"""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        if page_size > 100:
            page_size = 100
        
        skip = (page - 1) * page_size
        
        # Get services and total count
        services = await self.service_repository.list_services(
            skip=skip,
            limit=page_size,
            category_id=category_id,
            status=status,
            popular_only=popular_only,
            search=search,
            sort_by=sort_by,
            sort_desc=sort_desc
        )
        
        total_count = await self.service_repository.count_services(
            category_id=category_id,
            status=status,
            popular_only=popular_only,
            search=search
        )
        
        return services, total_count
    
    async def get_popular_services(self, limit: int = 10) -> List[Service]:
        """Get popular services"""
        if limit < 1:
            limit = 10
        if limit > 50:
            limit = 50
        
        return await self.service_repository.get_popular_services(limit)
    
    async def get_services_by_category(
        self,
        category_id: UUID,
        page: int = 1,
        page_size: int = 20,
        active_only: bool = True
    ) -> List[Service]:
        """Get services by category"""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        if page_size > 100:
            page_size = 100
        
        skip = (page - 1) * page_size
        
        return await self.service_repository.get_services_by_category(
            category_id=category_id,
            skip=skip,
            limit=page_size,
            active_only=active_only
        )
    
    async def update_service(
        self,
        service_id: UUID,
        name: Optional[str] = None,
        price: Optional[Decimal] = None,
        duration: Optional[int] = None,
        category_id: Optional[UUID] = None,
        description: Optional[str] = None,
        point_description: Optional[List[str]] = None
    ) -> Service:
        """Update an existing service"""
        # Get the existing service
        service = await self.service_repository.get_by_id(service_id)
        if not service:
            raise ValueError(f"Service with id {service_id} not found")
        
        # Validate and update name if provided
        if name is not None:
            name = name.strip()
            if len(name) == 0:
                raise ValueError("Service name cannot be empty")
            if len(name) > 100:
                raise ValueError("Service name cannot exceed 100 characters")
            service.update_name(name)
        
        # Validate and update price if provided
        if price is not None:
            if price <= 0:
                raise ValueError("Service price must be positive")
            service.update_price(price)
        
        # Validate and update duration if provided
        if duration is not None:
            if duration <= 0:
                raise ValueError("Service duration must be positive")
            service.update_duration(duration)
        
        # Validate and update category if provided
        if category_id is not None:
            category = await self.category_repository.get_by_id(category_id)
            if not category:
                raise ValueError(f"Category with id {category_id} not found")
            if not category.is_active:
                raise ValueError("Cannot assign service to inactive category")
            service.update_category(category_id)
        
        # Update description if provided
        if description is not None:
            service.update_description(description.strip() if description else None)
        
        # Update point description if provided
        if point_description is not None:
            clean_points = []
            for point in point_description:
                if isinstance(point, str) and point.strip():
                    clean_points.append(point.strip())
            service.update_point_description(clean_points)
        
        return await self.service_repository.update(service)
    
    async def activate_service(self, service_id: UUID) -> Service:
        """Activate a service"""
        service = await self.service_repository.get_by_id(service_id)
        if not service:
            raise ValueError(f"Service with id {service_id} not found")
        
        # Check if category is active
        category = await self.category_repository.get_by_id(service.category_id)
        if not category or not category.is_active:
            raise ValueError("Cannot activate service in inactive category")
        
        service.activate()
        return await self.service_repository.update(service)
    
    async def deactivate_service(self, service_id: UUID) -> Service:
        """Deactivate a service"""
        service = await self.service_repository.get_by_id(service_id)
        if not service:
            raise ValueError(f"Service with id {service_id} not found")
        
        service.deactivate()
        return await self.service_repository.update(service)
    
    async def mark_service_popular(self, service_id: UUID) -> Service:
        """Mark service as popular"""
        service = await self.service_repository.get_by_id(service_id)
        if not service:
            raise ValueError(f"Service with id {service_id} not found")
        
        service.mark_as_popular()
        return await self.service_repository.update(service)
    
    async def unmark_service_popular(self, service_id: UUID) -> Service:
        """Unmark service as popular"""
        service = await self.service_repository.get_by_id(service_id)
        if not service:
            raise ValueError(f"Service with id {service_id} not found")
        
        service.unmark_as_popular()
        return await self.service_repository.update(service)
    
    async def delete_service(self, service_id: UUID) -> bool:
        """Delete a service (soft delete)"""
        service = await self.service_repository.get_by_id(service_id)
        if not service:
            raise ValueError(f"Service with id {service_id} not found")
        
        return await self.service_repository.delete(service_id)
    
    async def search_services(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        category_id: Optional[UUID] = None,
        active_only: bool = True
    ) -> Tuple[List[Service], int]:
        """Search services by name and description"""
        if not query or len(query.strip()) == 0:
            return [], 0
        
        status = ServiceStatus.ACTIVE if active_only else None
        
        return await self.list_services(
            page=page,
            page_size=page_size,
            category_id=category_id,
            status=status,
            search=query.strip(),
            sort_by=ServiceSortBy.NAME
        )