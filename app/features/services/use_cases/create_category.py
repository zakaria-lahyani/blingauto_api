from dataclasses import dataclass

from app.core.errors import ValidationError, BusinessRuleViolationError
from app.features.services.domain import Category, CategoryManagementPolicy
from app.features.services.ports import (
    ICategoryRepository,
    ICacheService,
    IEventService,
    IAuditService,
)


@dataclass
class CreateCategoryRequest:
    name: str
    description: str = ""
    display_order: int = 0
    created_by: str = ""


@dataclass
class CreateCategoryResponse:
    category_id: str
    name: str
    description: str
    status: str
    display_order: int


class CreateCategoryUseCase:
    """Use case for creating a new category."""
    
    def __init__(
        self,
        category_repository: ICategoryRepository,
        cache_service: ICacheService,
        event_service: IEventService,
        audit_service: IAuditService,
    ):
        self._category_repository = category_repository
        self._cache_service = cache_service
        self._event_service = event_service
        self._audit_service = audit_service
    
    async def execute(self, request: CreateCategoryRequest) -> CreateCategoryResponse:
        """Execute the create category use case."""

        # Step 1: Check if category name already exists
        existing_categories = await self._category_repository.list_all(include_inactive=True)

        CategoryManagementPolicy.validate_category_name_uniqueness(
            request.name,
            "",  # No category ID for new category
            existing_categories,
        )

        # Step 2: Create category entity
        category = Category.create(
            name=request.name,
            description=request.description,
            display_order=request.display_order,
        )

        # Step 3: Validate category with policy
        CategoryManagementPolicy.validate_category_creation(category)

        # Step 4: Save category to repository
        saved_category = await self._category_repository.create(category)

        # Step 5: Clear cache
        await self._cache_service.invalidate_services_cache()

        # Step 6: Publish domain event
        await self._event_service.publish_category_created(saved_category)

        # Step 7: Log audit event
        status_value = saved_category.status.value if hasattr(saved_category.status, 'value') else saved_category.status
        await self._audit_service.log_category_creation(
            saved_category,
            request.created_by,
            {"initial_status": status_value}
        )

        # Step 8: Prepare response
        return CreateCategoryResponse(
            category_id=saved_category.id,
            name=saved_category.name,
            description=saved_category.description,
            status=status_value,
            display_order=saved_category.display_order,
        )