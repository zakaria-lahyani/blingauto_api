"""
Services repositories
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from src.features.services.domain.entities import ServiceCategory, Service
from src.features.services.domain.enums import ServiceStatus, CategoryStatus, ServiceSortBy, CategorySortBy
from .models import ServiceCategoryModel, ServiceModel


class ServiceCategoryRepository:
    """Repository for service categories"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, category: ServiceCategory) -> ServiceCategory:
        """Create a new service category"""
        db_category = ServiceCategoryModel.from_entity(category)
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        return db_category.to_entity()
    
    async def get_by_id(self, category_id: UUID) -> Optional[ServiceCategory]:
        """Get category by ID"""
        db_category = self.db.query(ServiceCategoryModel).filter(
            ServiceCategoryModel.id == category_id
        ).first()
        return db_category.to_entity() if db_category else None
    
    async def get_by_name(self, name: str) -> Optional[ServiceCategory]:
        """Get category by name"""
        db_category = self.db.query(ServiceCategoryModel).filter(
            ServiceCategoryModel.name == name
        ).first()
        return db_category.to_entity() if db_category else None
    
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
        query = self.db.query(ServiceCategoryModel)
        
        # Apply status filter
        if status:
            query = query.filter(ServiceCategoryModel.status == status.value)
        
        # Apply search filter
        if search:
            query = query.filter(
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
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
        
        # Apply pagination
        db_categories = query.offset(skip).limit(limit).all()
        return [category.to_entity() for category in db_categories]
    
    async def count_categories(
        self,
        status: Optional[CategoryStatus] = None,
        search: Optional[str] = None
    ) -> int:
        """Count categories with filtering"""
        query = self.db.query(ServiceCategoryModel)
        
        if status:
            query = query.filter(ServiceCategoryModel.status == status.value)
        
        if search:
            query = query.filter(
                or_(
                    ServiceCategoryModel.name.ilike(f"%{search}%"),
                    ServiceCategoryModel.description.ilike(f"%{search}%")
                )
            )
        
        return query.count()
    
    async def update(self, category: ServiceCategory) -> ServiceCategory:
        """Update an existing service category"""
        db_category = self.db.query(ServiceCategoryModel).filter(
            ServiceCategoryModel.id == category.id
        ).first()
        
        if not db_category:
            raise ValueError(f"Category with id {category.id} not found")
        
        db_category.update_from_entity(category)
        self.db.commit()
        self.db.refresh(db_category)
        return db_category.to_entity()
    
    async def delete(self, category_id: UUID) -> bool:
        """Delete a service category"""
        db_category = self.db.query(ServiceCategoryModel).filter(
            ServiceCategoryModel.id == category_id
        ).first()
        
        if not db_category:
            return False
        
        self.db.delete(db_category)
        self.db.commit()
        return True
    
    async def has_active_services(self, category_id: UUID) -> bool:
        """Check if category has active services"""
        count = self.db.query(ServiceModel).filter(
            and_(
                ServiceModel.category_id == category_id,
                ServiceModel.status == ServiceStatus.ACTIVE.value
            )
        ).count()
        return count > 0
    
    async def exists_by_name(self, name: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if category name already exists"""
        query = self.db.query(ServiceCategoryModel).filter(
            ServiceCategoryModel.name == name
        )
        
        if exclude_id:
            query = query.filter(ServiceCategoryModel.id != exclude_id)
        
        return query.first() is not None


class ServiceRepository:
    """Repository for services"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, service: Service) -> Service:
        """Create a new service"""
        db_service = ServiceModel.from_entity(service)
        self.db.add(db_service)
        self.db.commit()
        self.db.refresh(db_service)
        return db_service.to_entity()
    
    async def get_by_id(self, service_id: UUID) -> Optional[Service]:
        """Get service by ID"""
        db_service = self.db.query(ServiceModel).filter(
            ServiceModel.id == service_id
        ).first()
        return db_service.to_entity() if db_service else None
    
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
        query = self.db.query(ServiceModel)
        
        # Apply category filter
        if category_id:
            query = query.filter(ServiceModel.category_id == category_id)
        
        # Apply status filter
        if status:
            query = query.filter(ServiceModel.status == status.value)
        
        # Apply popular filter
        if popular_only:
            query = query.filter(ServiceModel.popular == True)
        
        # Apply search filter
        if search:
            query = query.filter(
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
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
        
        # Apply pagination
        db_services = query.offset(skip).limit(limit).all()
        return [service.to_entity() for service in db_services]
    
    async def count_services(
        self,
        category_id: Optional[UUID] = None,
        status: Optional[ServiceStatus] = None,
        popular_only: bool = False,
        search: Optional[str] = None
    ) -> int:
        """Count services with filtering"""
        query = self.db.query(ServiceModel)
        
        if category_id:
            query = query.filter(ServiceModel.category_id == category_id)
        
        if status:
            query = query.filter(ServiceModel.status == status.value)
        
        if popular_only:
            query = query.filter(ServiceModel.popular == True)
        
        if search:
            query = query.filter(
                or_(
                    ServiceModel.name.ilike(f"%{search}%"),
                    ServiceModel.description.ilike(f"%{search}%")
                )
            )
        
        return query.count()
    
    async def get_popular_services(self, limit: int = 10) -> List[Service]:
        """Get popular services"""
        db_services = self.db.query(ServiceModel).filter(
            and_(
                ServiceModel.popular == True,
                ServiceModel.status == ServiceStatus.ACTIVE.value
            )
        ).order_by(ServiceModel.name).limit(limit).all()
        
        return [service.to_entity() for service in db_services]
    
    async def get_services_by_category(
        self,
        category_id: UUID,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Service]:
        """Get services by category"""
        query = self.db.query(ServiceModel).filter(
            ServiceModel.category_id == category_id
        )
        
        if active_only:
            query = query.filter(ServiceModel.status == ServiceStatus.ACTIVE.value)
        
        db_services = query.order_by(ServiceModel.name).offset(skip).limit(limit).all()
        return [service.to_entity() for service in db_services]
    
    async def update(self, service: Service) -> Service:
        """Update an existing service"""
        db_service = self.db.query(ServiceModel).filter(
            ServiceModel.id == service.id
        ).first()
        
        if not db_service:
            raise ValueError(f"Service with id {service.id} not found")
        
        db_service.update_from_entity(service)
        self.db.commit()
        self.db.refresh(db_service)
        return db_service.to_entity()
    
    async def delete(self, service_id: UUID) -> bool:
        """Delete a service (soft delete by setting status to inactive)"""
        db_service = self.db.query(ServiceModel).filter(
            ServiceModel.id == service_id
        ).first()
        
        if not db_service:
            return False
        
        # Soft delete - mark as inactive instead of actual deletion
        db_service.status = ServiceStatus.INACTIVE.value
        self.db.commit()
        return True
    
    async def hard_delete(self, service_id: UUID) -> bool:
        """Hard delete a service (actual deletion from database)"""
        db_service = self.db.query(ServiceModel).filter(
            ServiceModel.id == service_id
        ).first()
        
        if not db_service:
            return False
        
        self.db.delete(db_service)
        self.db.commit()
        return True