from dataclasses import dataclass
from decimal import Decimal

from app.core.errors import ValidationError, BusinessRuleViolationError, NotFoundError
from app.features.services.domain import Service, ServiceManagementPolicy, CategoryStatus
from app.features.services.ports import (
    ICategoryRepository,
    IServiceRepository,
    ICacheService,
    IEventService,
    IAuditService,
)


@dataclass
class CreateServiceRequest:
    category_id: str
    name: str
    description: str
    price: Decimal
    duration_minutes: int
    is_popular: bool = False
    display_order: int = 0
    created_by: str = ""


@dataclass
class CreateServiceResponse:
    service_id: str
    category_id: str
    name: str
    description: str
    price: Decimal
    duration_minutes: int
    status: str
    is_popular: bool
    display_order: int
    price_display: str
    duration_display: str


class CreateServiceUseCase:
    """Use case for creating a new service."""
    
    def __init__(
        self,
        category_repository: ICategoryRepository,
        service_repository: IServiceRepository,
        cache_service: ICacheService,
        event_service: IEventService,
        audit_service: IAuditService,
    ):
        self._category_repository = category_repository
        self._service_repository = service_repository
        self._cache_service = cache_service
        self._event_service = event_service
        self._audit_service = audit_service
    
    async def execute(self, request: CreateServiceRequest) -> CreateServiceResponse:
        """Execute the create service use case."""

        # Step 1: Validate category exists and is active
        category = await self._category_repository.get_by_id(request.category_id)
        if not category:
            raise NotFoundError(f"Category {request.category_id} not found")

        # Handle both string and enum status
        category_status = category.status if isinstance(category.status, str) else category.status.value
        if category_status != CategoryStatus.ACTIVE.value:
            raise BusinessRuleViolationError("Cannot add services to inactive category")

        # Step 2: Validate service name uniqueness within category
        existing_services = await self._service_repository.list_by_category(
            request.category_id, include_inactive=True
        )
        
        ServiceManagementPolicy.validate_service_name_uniqueness_in_category(
            request.name,
            request.category_id,
            "",  # No service ID for new service
            existing_services,
        )
        
        # Step 3: Validate pricing rules (RG-SVC-004)
        ServiceManagementPolicy.validate_pricing_rules(request.price)
        
        # Step 4: Validate duration rules (RG-SVC-005)
        ServiceManagementPolicy.validate_duration_rules(request.duration_minutes)
        
        # Step 5: Create service entity
        service = Service.create(
            category_id=request.category_id,
            name=request.name,
            description=request.description,
            price=request.price,
            duration_minutes=request.duration_minutes,
            is_popular=request.is_popular,
            display_order=request.display_order,
        )
        
        # Step 6: Validate service with policy
        ServiceManagementPolicy.validate_service_creation(service)
        
        # Step 7: Validate popular service limits (RG-SVC-006)
        if request.is_popular:
            popular_services = await self._service_repository.list_popular()
            ServiceManagementPolicy.validate_popular_service_limits(
                service, popular_services
            )

        # Step 8: Save service to repository
        saved_service = await self._service_repository.create(service)
        
        # Step 9: Clear cache
        self._cache_service.delete_category_services(request.category_id)
        if saved_service.is_popular:
            self._cache_service.set_popular_services(None, ttl=0)  # Invalidate
        
        # Step 10: Publish domain event
        self._event_service.publish_service_created(saved_service)
        
        # Step 11: Log audit event
        status_value = saved_service.status.value if hasattr(saved_service.status, 'value') else saved_service.status
        self._audit_service.log_service_creation(
            saved_service,
            request.created_by,
            {
                "category_name": category.name,
                "initial_status": status_value,
                "is_popular": saved_service.is_popular,
            }
        )

        # Step 12: Prepare response
        return CreateServiceResponse(
            service_id=saved_service.id,
            category_id=saved_service.category_id,
            name=saved_service.name,
            description=saved_service.description,
            price=saved_service.price,
            duration_minutes=saved_service.duration_minutes,
            status=status_value,
            is_popular=saved_service.is_popular,
            display_order=saved_service.display_order,
            price_display=saved_service.price_display,
            duration_display=saved_service.duration_display,
        )