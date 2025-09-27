"""
Service category business logic
"""
from typing import List, Optional, Tuple
from uuid import UUID
from decimal import Decimal

from src.features.services.domain.entities import ServiceCategory
from src.features.services.domain.enums import CategoryStatus, CategorySortBy
from src.features.services.infrastructure.database.repositories import ServiceCategoryRepository


class CategoryService:
    """Service for managing service categories"""
    
    def __init__(self, category_repository: ServiceCategoryRepository):
        self.category_repository = category_repository
    
    async def create_category(
        self,
        name: str,
        description: Optional[str] = None
    ) -> ServiceCategory:
        """Create a new service category"""
        # Validate name uniqueness
        if await self.category_repository.exists_by_name(name):
            raise ValueError(f"Category with name '{name}' already exists")
        
        # Validate name length
        if len(name.strip()) == 0:
            raise ValueError("Category name cannot be empty")
        
        if len(name) > 100:
            raise ValueError("Category name cannot exceed 100 characters")
        
        # Create the category
        category = ServiceCategory(
            name=name.strip(),
            description=description.strip() if description else None,
            status=CategoryStatus.ACTIVE
        )
        
        return await self.category_repository.create(category)
    
    async def get_category_by_id(self, category_id: UUID) -> Optional[ServiceCategory]:
        """Get category by ID"""
        return await self.category_repository.get_by_id(category_id)
    
    async def get_category_by_name(self, name: str) -> Optional[ServiceCategory]:
        """Get category by name"""
        return await self.category_repository.get_by_name(name)
    
    async def list_categories(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[CategoryStatus] = None,
        search: Optional[str] = None,
        sort_by: CategorySortBy = CategorySortBy.NAME,
        sort_desc: bool = False
    ) -> Tuple[List[ServiceCategory], int]:
        """List categories with pagination and filtering"""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        if page_size > 100:
            page_size = 100
        
        skip = (page - 1) * page_size
        
        # Get categories and total count
        categories = await self.category_repository.list_categories(
            skip=skip,
            limit=page_size,
            status=status,
            search=search,
            sort_by=sort_by,
            sort_desc=sort_desc
        )
        
        total_count = await self.category_repository.count_categories(
            status=status,
            search=search
        )
        
        return categories, total_count
    
    async def update_category(
        self,
        category_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> ServiceCategory:
        """Update an existing category"""
        # Get the existing category
        category = await self.category_repository.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with id {category_id} not found")
        
        # Validate and update name if provided
        if name is not None:
            name = name.strip()
            if len(name) == 0:
                raise ValueError("Category name cannot be empty")
            if len(name) > 100:
                raise ValueError("Category name cannot exceed 100 characters")
            
            # Check name uniqueness (excluding current category)
            if await self.category_repository.exists_by_name(name, exclude_id=category_id):
                raise ValueError(f"Category with name '{name}' already exists")
            
            category.update_name(name)
        
        # Update description if provided
        if description is not None:
            category.update_description(description.strip() if description else None)
        
        return await self.category_repository.update(category)
    
    async def activate_category(self, category_id: UUID) -> ServiceCategory:
        """Activate a category"""
        category = await self.category_repository.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with id {category_id} not found")
        
        category.activate()
        return await self.category_repository.update(category)
    
    async def deactivate_category(self, category_id: UUID) -> ServiceCategory:
        """Deactivate a category"""
        category = await self.category_repository.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with id {category_id} not found")
        
        category.deactivate()
        return await self.category_repository.update(category)
    
    async def delete_category(self, category_id: UUID) -> bool:
        """Delete a category (only if no active services)"""
        # Check if category exists
        category = await self.category_repository.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with id {category_id} not found")
        
        # Check if category has active services
        if await self.category_repository.has_active_services(category_id):
            raise ValueError("Cannot delete category with active services")
        
        return await self.category_repository.delete(category_id)
    
    async def get_active_categories(self) -> List[ServiceCategory]:
        """Get all active categories"""
        categories, _ = await self.list_categories(
            page=1,
            page_size=1000,  # Large limit to get all
            status=CategoryStatus.ACTIVE,
            sort_by=CategorySortBy.NAME
        )
        return categories