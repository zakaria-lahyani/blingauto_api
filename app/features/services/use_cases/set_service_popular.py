from dataclasses import dataclass

from app.core.errors import NotFoundError, BusinessRuleViolationError
from app.features.services.domain import ServiceManagementPolicy, ServiceStatus
from app.features.services.ports import (
    IServiceRepository,
    ICacheService,
    IEventService,
    IAuditService,
)


@dataclass
class SetServicePopularRequest:
    service_id: str
    is_popular: bool
    updated_by: str


@dataclass
class SetServicePopularResponse:
    service_id: str
    name: str
    is_popular: bool
    category_popular_count: int
    message: str


class SetServicePopularUseCase:
    """Use case for setting service as popular (RG-SVC-006)."""
    
    def __init__(
        self,
        service_repository: IServiceRepository,
        cache_service: ICacheService,
        event_service: IEventService,
        audit_service: IAuditService,
    ):
        self._service_repository = service_repository
        self._cache_service = cache_service
        self._event_service = event_service
        self._audit_service = audit_service
    
    async def execute(self, request: SetServicePopularRequest) -> SetServicePopularResponse:
        """Execute the set service popular use case."""
        
        # Step 1: Get existing service
        service = await self._service_repository.get_by_id(request.service_id)
        if not service:
            raise NotFoundError(f"Service {request.service_id} not found")
        
        # Step 2: Check if already in desired state
        if service.is_popular == request.is_popular:
            return SetServicePopularResponse(
                service_id=service.id,
                name=service.name,
                is_popular=service.is_popular,
                category_popular_count=await self._service_repository.count_popular_in_category(
                    service.category_id
                ),
                message=f"Service is already {'popular' if service.is_popular else 'not popular'}",
            )
        
        # Step 3: Validate service can be marked popular
        if request.is_popular:
            if service.status != ServiceStatus.ACTIVE:
                raise BusinessRuleViolationError("Only active services can be marked as popular")
            
            # Get all popular services to check limits
            all_popular_services = await self._service_repository.list_popular()
            
            # Validate popular service limits per category
            ServiceManagementPolicy.validate_popular_service_limits(
                service, all_popular_services, max_popular_per_category=3
            )
        
        # Step 4: Update service popularity
        service.set_popular(request.is_popular)
        
        # Step 5: Save updated service
        updated_service = await self._service_repository.update(service)
        
        # Step 6: Clear cache
        await self._cache_service.delete_service(service.id)
        await self._cache_service.delete_category_services(service.category_id)
        # Invalidate popular services cache
        await self._cache_service.set_popular_services([], ttl=0)
        
        # Step 7: Publish domain event
        await self._event_service.publish_service_marked_popular(
            updated_service, request.is_popular
        )
        
        # Step 8: Log audit event
        await self._audit_service.log_service_update(
            updated_service,
            request.updated_by,
            {
                "popularity_changed": True,
                "old_popular": not request.is_popular,
                "new_popular": request.is_popular,
            },
            {
                "action": "set_popular" if request.is_popular else "unset_popular",
            }
        )
        
        # Step 9: Get updated category popular count
        category_popular_count = await self._service_repository.count_popular_in_category(
            service.category_id
        )
        
        # Step 10: Prepare response
        action = "marked as popular" if request.is_popular else "removed from popular"
        message = f"Service '{updated_service.name}' has been {action}"
        
        return SetServicePopularResponse(
            service_id=updated_service.id,
            name=updated_service.name,
            is_popular=updated_service.is_popular,
            category_popular_count=category_popular_count,
            message=message,
        )