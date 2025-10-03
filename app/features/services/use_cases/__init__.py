from .create_category import CreateCategoryUseCase, CreateCategoryRequest, CreateCategoryResponse
from .create_service import CreateServiceUseCase, CreateServiceRequest, CreateServiceResponse
from .update_service_price import UpdateServicePriceUseCase, UpdateServicePriceRequest, UpdateServicePriceResponse
from .set_service_popular import SetServicePopularUseCase, SetServicePopularRequest, SetServicePopularResponse
from .list_services import ListServicesUseCase, ListServicesRequest, ListServicesResponse
from .list_categories import ListCategoriesUseCase, ListCategoriesRequest, ListCategoriesResponse
from .get_service import GetServiceUseCase, GetServiceRequest, GetServiceResponse

class DeactivateServiceUseCase:
    def __init__(self, **kwargs):
        # Stub implementation - accepts any dependencies
        pass

    async def execute(self, **kwargs):
        return None

class GetPopularServicesUseCase:
    """Use case for getting popular services."""

    def __init__(
        self,
        service_repository,
        category_repository,
        cache_service,
    ):
        self._service_repository = service_repository
        self._category_repository = category_repository
        self._cache_service = cache_service

    async def execute(
        self,
        limit: int = 10,
        requesting_user_id: str = None,
    ):
        """Execute get popular services use case."""
        # Get popular services from repository
        services = await self._service_repository.list_popular(limit=limit)

        # Get category names for the services
        category_names = {}
        for service in services:
            if service.category_id not in category_names:
                category = await self._category_repository.get_by_id(service.category_id)
                if category:
                    category_names[service.category_id] = category.name

        return {
            "services": services,
            "category_names": category_names,
        }

class SearchServicesUseCase:
    """Use case for searching services by name or description."""

    def __init__(
        self,
        service_repository,
        category_repository,
        cache_service,
    ):
        self._service_repository = service_repository
        self._category_repository = category_repository
        self._cache_service = cache_service

    async def execute(
        self,
        query: str,
        category_id: str = None,
        limit: int = 20,
        requesting_user_id: str = None,
    ):
        """Execute search services use case."""
        # Search services using repository
        services = await self._service_repository.search_services(
            query=query,
            category_id=category_id,
            limit=limit,
        )

        # Get category names for the services
        category_names = {}
        for service in services:
            if service.category_id not in category_names:
                category = await self._category_repository.get_by_id(service.category_id)
                if category:
                    category_names[service.category_id] = category.name

        return {
            "services": services,
            "category_names": category_names,
        }

__all__ = [
    # Use Cases
    "CreateCategoryUseCase",
    "CreateServiceUseCase",
    "UpdateServicePriceUseCase",
    "SetServicePopularUseCase",
    "ListServicesUseCase",
    "ListCategoriesUseCase",
    "GetServiceUseCase",
    "DeactivateServiceUseCase", 
    "GetPopularServicesUseCase",
    "SearchServicesUseCase",
    # Requests
    "CreateCategoryRequest",
    "CreateServiceRequest",
    "UpdateServicePriceRequest",
    "SetServicePopularRequest",
    "ListServicesRequest",
    # Responses
    "CreateCategoryResponse",
    "CreateServiceResponse",
    "UpdateServicePriceResponse",
    "SetServicePopularResponse",
    "ListServicesResponse",
]