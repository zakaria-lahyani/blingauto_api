"""
Services repositories - Fixed version with proper async implementation
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.future import select

from src.shared.database.base import BaseRepository
from src.features.services.domain.entities import ServiceCategory, Service
from src.features.services.domain.enums import ServiceStatus, CategoryStatus, ServiceSortBy, CategorySortBy
from .models import ServiceCategoryModel, ServiceModel


class ServiceCategoryRepository(BaseRepository[ServiceCategory, ServiceCategoryModel]):
    """Repository for service categories"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ServiceCategoryModel)
    
    async def create(self, category: ServiceCategory) -> ServiceCategory:
        """Create a new service category"""
        db_category = ServiceCategoryModel.from_entity(category)
        self.session.add(db_category)
        await self.session.flush()
        await self.session.refresh(db_category)
        return db_category.to_entity()
    
    async def get(self, category_id: UUID) -> Optional[ServiceCategory]:
        """Get category by ID"""
        stmt = select(ServiceCategoryModel).where(ServiceCategoryModel.id == category_id)
        result = await self.session.execute(stmt)
        db_category = result.scalar_one_or_none()
        return db_category.to_entity() if db_category else None
    
    async def get_by_id(self, category_id: UUID) -> Optional[ServiceCategory]:
        """Get category by ID - backwards compatibility"""
        return await self.get(category_id)
    
    async def get_by_name(self, name: str) -> Optional[ServiceCategory]:
        """Get category by name"""
        stmt = select(ServiceCategoryModel).where(ServiceCategoryModel.name == name)
        result = await self.session.execute(stmt)
        db_category = result.scalar_one_or_none()
        return db_category.to_entity() if db_category else None
    
    async def list(self, limit: int = 100, offset: int = 0) -> List[ServiceCategory]:
        """List categories"""
        stmt = select(ServiceCategoryModel).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        db_categories = result.scalars().all()
        return [category.to_entity() for category in db_categories]
    
    async def list_categories(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[CategoryStatus] = None,
        search: Optional[str] = None,
        sort_by: CategorySortBy = CategorySortBy.NAME,
        sort_desc: bool = False
    ) -> List[ServiceCategory]:
        """List categories with filtering and pagination"""
        stmt = select(ServiceCategoryModel)
        
        # Apply status filter
        if status:
            stmt = stmt.where(ServiceCategoryModel.status == status.value)
        
        # Apply search filter
        if search:
            stmt = stmt.where(
                or_(
                    ServiceCategoryModel.name.ilike(f"%{search}%"),
                    ServiceCategoryModel.description.ilike(f"%{search}%")
                )
            )
        
        # Apply sorting
        if sort_by == CategorySortBy.NAME:
            order_column = ServiceCategoryModel.name
        else:  # CategorySortBy.CREATED_AT
            order_column = ServiceCategoryModel.created_at
        
        if sort_desc:
            stmt = stmt.order_by(desc(order_column))
        else:
            stmt = stmt.order_by(asc(order_column))
        
        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        db_categories = result.scalars().all()
        return [category.to_entity() for category in db_categories]
    
    async def count_categories(
        self,
        status: Optional[CategoryStatus] = None,
        search: Optional[str] = None
    ) -> int:
        """Count categories with filtering"""
        stmt = select(func.count(ServiceCategoryModel.id))
        
        if status:
            stmt = stmt.where(ServiceCategoryModel.status == status.value)
        
        if search:
            stmt = stmt.where(
                or_(
                    ServiceCategoryModel.name.ilike(f"%{search}%"),
                    ServiceCategoryModel.description.ilike(f"%{search}%")
                )
            )
        
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def update(self, category: ServiceCategory) -> ServiceCategory:
        """Update an existing service category"""
        stmt = select(ServiceCategoryModel).where(ServiceCategoryModel.id == category.id)
        result = await self.session.execute(stmt)
        db_category = result.scalar_one_or_none()
        
        if not db_category:
            raise ValueError(f"Category with id {category.id} not found")
        
        db_category.update_from_entity(category)
        await self.session.flush()
        await self.session.refresh(db_category)
        return db_category.to_entity()
    
    async def delete(self, category_id: UUID) -> bool:
        """Delete a service category"""
        stmt = select(ServiceCategoryModel).where(ServiceCategoryModel.id == category_id)
        result = await self.session.execute(stmt)
        db_category = result.scalar_one_or_none()
        
        if not db_category:
            return False
        
        await self.session.delete(db_category)
        return True
    
    async def has_active_services(self, category_id: UUID) -> bool:
        """Check if category has active services"""
        stmt = select(func.count(ServiceModel.id)).where(
            and_(
                ServiceModel.category_id == category_id,
                ServiceModel.status == ServiceStatus.ACTIVE.value
            )
        )
        result = await self.session.execute(stmt)
        count = result.scalar() or 0
        return count > 0
    
    async def exists_by_name(self, name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if category name already exists"""
        stmt = select(ServiceCategoryModel).where(ServiceCategoryModel.name == name)
        
        if exclude_id:
            stmt = stmt.where(ServiceCategoryModel.id != exclude_id)
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None


class ServiceRepository(BaseRepository[Service, ServiceModel]):
    """Repository for services"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ServiceModel)
    
    async def create(self, service: Service) -> Service:
        """Create a new service"""
        db_service = ServiceModel.from_entity(service)
        self.session.add(db_service)
        await self.session.flush()
        await self.session.refresh(db_service)
        return db_service.to_entity()
    
    async def get(self, service_id: UUID) -> Optional[Service]:
        """Get service by ID"""
        stmt = select(ServiceModel).where(ServiceModel.id == service_id)
        result = await self.session.execute(stmt)
        db_service = result.scalar_one_or_none()
        return db_service.to_entity() if db_service else None
    
    async def get_by_id(self, service_id: UUID) -> Optional[Service]:
        """Get service by ID - backwards compatibility"""
        return await self.get(service_id)
    
    async def list(self, limit: int = 100, offset: int = 0) -> List[Service]:
        """List services"""
        stmt = select(ServiceModel).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        db_services = result.scalars().all()
        return [service.to_entity() for service in db_services]
    
    async def list_services(
        self,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[UUID] = None,
        status: Optional[ServiceStatus] = None,
        popular_only: bool = False,
        search: Optional[str] = None,
        sort_by: ServiceSortBy = ServiceSortBy.NAME,
        sort_desc: bool = False
    ) -> List[Service]:
        """List services with filtering and pagination"""
        stmt = select(ServiceModel)
        
        # Apply category filter
        if category_id:
            stmt = stmt.where(ServiceModel.category_id == category_id)
        
        # Apply status filter
        if status:
            stmt = stmt.where(ServiceModel.status == status.value)
        
        # Apply popular filter
        if popular_only:
            stmt = stmt.where(ServiceModel.popular == True)
        
        # Apply search filter
        if search:
            stmt = stmt.where(
                or_(
                    ServiceModel.name.ilike(f"%{search}%"),
                    ServiceModel.description.ilike(f"%{search}%")
                )
            )
        
        # Apply sorting
        if sort_by == ServiceSortBy.NAME:
            order_column = ServiceModel.name
        elif sort_by == ServiceSortBy.PRICE:
            order_column = ServiceModel.price
        elif sort_by == ServiceSortBy.DURATION:
            order_column = ServiceModel.duration
        elif sort_by == ServiceSortBy.POPULARITY:
            order_column = ServiceModel.popular
        else:  # ServiceSortBy.CREATED_AT
            order_column = ServiceModel.created_at
        
        if sort_desc:
            stmt = stmt.order_by(desc(order_column))
        else:
            stmt = stmt.order_by(asc(order_column))
        
        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        db_services = result.scalars().all()
        return [service.to_entity() for service in db_services]
    
    async def count_services(
        self,
        category_id: Optional[UUID] = None,
        status: Optional[ServiceStatus] = None,
        popular_only: bool = False,
        search: Optional[str] = None
    ) -> int:
        """Count services with filtering"""
        stmt = select(func.count(ServiceModel.id))
        
        if category_id:
            stmt = stmt.where(ServiceModel.category_id == category_id)
        
        if status:
            stmt = stmt.where(ServiceModel.status == status.value)
        
        if popular_only:
            stmt = stmt.where(ServiceModel.popular == True)
        
        if search:
            stmt = stmt.where(
                or_(
                    ServiceModel.name.ilike(f"%{search}%"),
                    ServiceModel.description.ilike(f"%{search}%")
                )
            )
        
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def get_popular_services(self, limit: int = 10) -> List[Service]:
        """Get popular services"""
        stmt = select(ServiceModel).where(
            and_(
                ServiceModel.popular == True,
                ServiceModel.status == ServiceStatus.ACTIVE.value
            )
        ).order_by(ServiceModel.name).limit(limit)
        
        result = await self.session.execute(stmt)
        db_services = result.scalars().all()
        return [service.to_entity() for service in db_services]
    
    async def get_services_by_category(
        self,
        category_id: UUID,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Service]:
        """Get services by category"""
        stmt = select(ServiceModel).where(ServiceModel.category_id == category_id)
        
        if active_only:
            stmt = stmt.where(ServiceModel.status == ServiceStatus.ACTIVE.value)
        
        stmt = stmt.order_by(ServiceModel.name).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        db_services = result.scalars().all()
        return [service.to_entity() for service in db_services]
    
    async def update(self, service: Service) -> Service:
        """Update an existing service"""
        stmt = select(ServiceModel).where(ServiceModel.id == service.id)
        result = await self.session.execute(stmt)
        db_service = result.scalar_one_or_none()
        
        if not db_service:
            raise ValueError(f"Service with id {service.id} not found")
        
        db_service.update_from_entity(service)
        await self.session.flush()
        await self.session.refresh(db_service)
        return db_service.to_entity()
    
    async def delete(self, service_id: UUID) -> bool:
        """Delete a service (soft delete by setting status to inactive)"""
        stmt = select(ServiceModel).where(ServiceModel.id == service_id)
        result = await self.session.execute(stmt)
        db_service = result.scalar_one_or_none()
        
        if not db_service:
            return False
        
        # Soft delete - mark as inactive instead of actual deletion
        db_service.status = ServiceStatus.INACTIVE.value
        await self.session.flush()
        return True
    
    async def hard_delete(self, service_id: UUID) -> bool:
        """Hard delete a service (actual deletion from database)"""
        stmt = select(ServiceModel).where(ServiceModel.id == service_id)
        result = await self.session.execute(stmt)
        db_service = result.scalar_one_or_none()
        
        if not db_service:
            return False
        
        await self.session.delete(db_service)
        return True