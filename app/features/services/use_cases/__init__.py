from .create_category import CreateCategoryUseCase, CreateCategoryRequest, CreateCategoryResponse
from .create_service import CreateServiceUseCase, CreateServiceRequest, CreateServiceResponse
from .update_service_price import UpdateServicePriceUseCase, UpdateServicePriceRequest, UpdateServicePriceResponse
from .set_service_popular import SetServicePopularUseCase, SetServicePopularRequest, SetServicePopularResponse
from .list_services import ListServicesUseCase, ListServicesRequest, ListServicesResponse
from .list_categories import ListCategoriesUseCase, ListCategoriesRequest, ListCategoriesResponse
from .get_service import GetServiceUseCase, GetServiceRequest, GetServiceResponse

class DeactivateServiceUseCase:
    async def execute(self, **kwargs):
        return None

class GetPopularServicesUseCase:
    async def execute(self, **kwargs):
        return {"services": [], "category_names": {}}

class SearchServicesUseCase:
    async def execute(self, **kwargs):
        return {"services": [], "category_names": {}}

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