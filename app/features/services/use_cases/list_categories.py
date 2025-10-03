"""List categories use case."""

from dataclasses import dataclass
from typing import List

from app.features.services.domain import Category
from app.features.services.ports import ICategoryRepository, ICacheService


@dataclass
class ListCategoriesRequest:
    include_inactive: bool = False
    requesting_user_id: str = ""


@dataclass
class CategorySummary:
    id: str
    name: str
    description: str
    status: str
    display_order: int
    service_count: int


@dataclass
class ListCategoriesResponse:
    categories: List[CategorySummary]
    total_count: int


class ListCategoriesUseCase:
    """Use case for listing service categories."""
    
    def __init__(
        self,
        category_repository: ICategoryRepository,
        cache_service: ICacheService,
    ):
        self._category_repository = category_repository
        self._cache_service = cache_service
    
    async def execute(self, request: ListCategoriesRequest) -> ListCategoriesResponse:
        """Execute the list categories use case."""

        # Get categories from repository
        categories = await self._category_repository.list_all(
            include_inactive=request.include_inactive
        )

        # Convert to summary format
        category_summaries = [
            CategorySummary(
                id=cat.id,
                name=cat.name,
                description=cat.description,
                status=cat.status.value if hasattr(cat.status, 'value') else cat.status,
                display_order=cat.display_order,
                service_count=0,
            )
            for cat in categories
        ]

        return ListCategoriesResponse(
            categories=category_summaries,
            total_count=len(category_summaries),
        )