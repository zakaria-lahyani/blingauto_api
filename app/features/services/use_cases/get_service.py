"""Get service use case."""

from dataclasses import dataclass

from app.core.errors import NotFoundError
from app.features.services.domain import Service
from app.features.services.ports import IServiceRepository, ICacheService


@dataclass
class GetServiceRequest:
    service_id: str
    requesting_user_id: str


@dataclass
class GetServiceResponse:
    id: str
    category_id: str
    name: str
    description: str
    price: float
    duration_minutes: int
    status: str
    is_popular: bool
    display_order: int
    price_display: str
    duration_display: str


class GetServiceUseCase:
    """Use case for getting a specific service."""
    
    def __init__(
        self,
        service_repository: IServiceRepository,
        cache_service: ICacheService,
    ):
        self._service_repository = service_repository
        self._cache_service = cache_service
    
    def execute(self, request: GetServiceRequest) -> GetServiceResponse:
        """Execute the get service use case."""
        
        # Try to get from cache first
        service = self._cache_service.get_service(request.service_id)
        
        if not service:
            # Get from repository if not cached
            service = self._service_repository.get_by_id(request.service_id)
            if not service:
                raise NotFoundError(f"Service {request.service_id} not found")
            
            # Cache the service for future requests
            self._cache_service.set_service(service, ttl=3600)
        
        return GetServiceResponse(
            id=service.id,
            category_id=service.category_id,
            name=service.name,
            description=service.description,
            price=float(service.price),
            duration_minutes=service.duration_minutes,
            status=service.status.value,
            is_popular=service.is_popular,
            display_order=service.display_order,
            price_display=service.price_display,
            duration_display=service.duration_display,
        )