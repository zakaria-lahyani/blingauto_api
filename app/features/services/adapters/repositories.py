from typing import Optional, List
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.features.services.ports import (
    Category as CategoryDomain,
    Service as ServiceDomain,
    ICategoryRepository,
    IServiceRepository,
    IBookingRepository,
)
from app.features.services.adapters.models import Category as CategoryModel, Service as ServiceModel


class SqlCategoryRepository(ICategoryRepository):
    """SQLAlchemy implementation of category repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_domain(self, db_category: CategoryModel) -> CategoryDomain:
        """Convert database model to domain entity."""
        from app.features.services.domain.entities import CategoryStatus

        # Convert status string to enum if needed
        status = db_category.status
        if isinstance(status, str):
            status = CategoryStatus(status)

        return CategoryDomain(
            id=db_category.id,
            name=db_category.name,
            description=db_category.description,
            status=status,
            display_order=db_category.display_order,
            created_at=db_category.created_at,
            updated_at=db_category.updated_at
        )

    async def get_by_id(self, category_id: str) -> Optional[CategoryDomain]:
        """Get category by ID."""
        result = await self._session.execute(
            select(CategoryModel).where(CategoryModel.id == category_id)
        )
        db_category = result.scalar_one_or_none()

        if not db_category:
            return None

        return self._to_domain(db_category)

    async def get_by_name(self, name: str) -> Optional[CategoryDomain]:
        """Get category by name."""
        result = await self._session.execute(
            select(CategoryModel).where(CategoryModel.name == name)
        )
        db_category = result.scalar_one_or_none()

        if not db_category:
            return None

        return self._to_domain(db_category)

    async def create(self, category: CategoryDomain) -> CategoryDomain:
        """Create a new category."""
        # Convert domain entity to database model
        db_category = CategoryModel(
            id=category.id,
            name=category.name,
            description=category.description,
            status=category.status.value,
            display_order=category.display_order
        )

        # Save to database
        self._session.add(db_category)
        await self._session.commit()
        await self._session.refresh(db_category)

        # Convert back to domain entity
        return self._to_domain(db_category)

    async def update(self, category: CategoryDomain) -> CategoryDomain:
        """Update an existing category."""
        result = await self._session.execute(
            select(CategoryModel).where(CategoryModel.id == category.id)
        )
        db_category = result.scalar_one_or_none()

        if not db_category:
            raise ValueError(f"Category {category.id} not found")

        db_category.name = category.name
        db_category.description = category.description
        db_category.status = category.status.value if hasattr(category.status, 'value') else category.status
        db_category.display_order = category.display_order

        await self._session.commit()
        await self._session.refresh(db_category)

        return self._to_domain(db_category)

    async def delete(self, category_id: str) -> bool:
        """Delete a category."""
        from sqlalchemy import delete as sql_delete

        result = await self._session.execute(
            sql_delete(CategoryModel).where(CategoryModel.id == category_id)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def list_all(
        self,
        include_inactive: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> List[CategoryDomain]:
        """List all categories."""
        # Build query
        query = select(CategoryModel)

        if not include_inactive:
            query = query.where(CategoryModel.status == "ACTIVE")

        # Apply pagination
        query = query.offset(offset).limit(limit).order_by(CategoryModel.display_order)

        # Execute query
        result = await self._session.execute(query)
        db_categories = result.scalars().all()

        # Convert to domain entities
        return [self._to_domain(cat) for cat in db_categories]

    async def count(self, include_inactive: bool = False) -> int:
        """Count categories."""
        from sqlalchemy import func

        query = select(func.count()).select_from(CategoryModel)

        if not include_inactive:
            query = query.where(CategoryModel.status == "ACTIVE")

        result = await self._session.execute(query)
        return result.scalar_one()

    async def list_active(self) -> List[CategoryDomain]:
        """List active categories."""
        return await self.list_all(include_inactive=False)

    async def count_services_in_category(
        self,
        category_id: str,
        include_inactive: bool = False,
    ) -> int:
        """Count services in a category."""
        from sqlalchemy import func

        query = select(func.count()).select_from(ServiceModel).where(
            ServiceModel.category_id == category_id
        )

        if not include_inactive:
            query = query.where(ServiceModel.status == "ACTIVE")

        result = await self._session.execute(query)
        return result.scalar_one()

    async def exists_by_name(
        self,
        name: str,
        exclude_category_id: Optional[str] = None,
    ) -> bool:
        """Check if category exists by name."""
        from sqlalchemy import func

        query = select(func.count()).select_from(CategoryModel).where(
            CategoryModel.name == name
        )

        if exclude_category_id:
            query = query.where(CategoryModel.id != exclude_category_id)

        result = await self._session.execute(query)
        count = result.scalar_one()
        return count > 0


class SqlServiceRepository(IServiceRepository):
    """SQLAlchemy implementation of service repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_domain(self, db_service: ServiceModel) -> ServiceDomain:
        """Convert database model to domain entity."""
        from app.features.services.domain.entities import ServiceStatus

        # Convert status string to enum if needed
        status = db_service.status
        if isinstance(status, str):
            status = ServiceStatus(status)

        return ServiceDomain(
            id=db_service.id,
            category_id=db_service.category_id,
            name=db_service.name,
            description=db_service.description,
            price=db_service.price,
            duration_minutes=db_service.duration_minutes,
            status=status,
            is_popular=db_service.is_popular,
            display_order=db_service.display_order,
            created_at=db_service.created_at,
            updated_at=db_service.updated_at
        )

    async def get_by_id(self, service_id: str) -> Optional[ServiceDomain]:
        """Get service by ID."""
        result = await self._session.execute(
            select(ServiceModel).where(ServiceModel.id == service_id)
        )
        db_service = result.scalar_one_or_none()

        if not db_service:
            return None

        return self._to_domain(db_service)

    async def get_by_name_in_category(
        self,
        name: str,
        category_id: str,
    ) -> Optional[ServiceDomain]:
        """Get service by name within a category."""
        result = await self._session.execute(
            select(ServiceModel).where(
                ServiceModel.name == name,
                ServiceModel.category_id == category_id
            )
        )
        db_service = result.scalar_one_or_none()

        if not db_service:
            return None

        return self._to_domain(db_service)

    async def create(self, service: ServiceDomain) -> ServiceDomain:
        """Create a new service."""
        db_service = ServiceModel(
            id=service.id,
            category_id=service.category_id,
            name=service.name,
            description=service.description,
            price=service.price,
            duration_minutes=service.duration_minutes,
            status=service.status.value if hasattr(service.status, 'value') else service.status,
            is_popular=service.is_popular,
            display_order=service.display_order
        )

        self._session.add(db_service)
        await self._session.commit()
        await self._session.refresh(db_service)

        return self._to_domain(db_service)

    async def update(self, service: ServiceDomain) -> ServiceDomain:
        """Update an existing service."""
        result = await self._session.execute(
            select(ServiceModel).where(ServiceModel.id == service.id)
        )
        db_service = result.scalar_one_or_none()

        if not db_service:
            raise ValueError(f"Service {service.id} not found")

        db_service.name = service.name
        db_service.description = service.description
        db_service.price = service.price
        db_service.duration_minutes = service.duration_minutes
        db_service.status = service.status.value if hasattr(service.status, 'value') else service.status
        db_service.is_popular = service.is_popular
        db_service.display_order = service.display_order

        await self._session.commit()
        await self._session.refresh(db_service)

        return self._to_domain(db_service)

    async def delete(self, service_id: str) -> bool:
        """Delete a service."""
        from sqlalchemy import delete as sql_delete

        result = await self._session.execute(
            sql_delete(ServiceModel).where(ServiceModel.id == service_id)
        )
        await self._session.commit()
        return result.rowcount > 0
    
    async def list_by_category(
        self,
        category_id: str,
        include_inactive: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> List[ServiceDomain]:
        """List services in a category."""
        query = select(ServiceModel).where(ServiceModel.category_id == category_id)

        if not include_inactive:
            query = query.where(ServiceModel.status == "ACTIVE")

        query = query.offset(offset).limit(limit).order_by(ServiceModel.display_order)

        result = await self._session.execute(query)
        db_services = result.scalars().all()

        return [self._to_domain(svc) for svc in db_services]

    async def list_all(
        self,
        include_inactive: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> List[ServiceDomain]:
        """List all services."""
        query = select(ServiceModel)

        if not include_inactive:
            query = query.where(ServiceModel.status == "ACTIVE")

        query = query.offset(offset).limit(limit).order_by(ServiceModel.display_order)

        result = await self._session.execute(query)
        db_services = result.scalars().all()

        return [self._to_domain(svc) for svc in db_services]

    async def list_popular(self, limit: int = 10) -> List[ServiceDomain]:
        """List popular services."""
        query = select(ServiceModel).where(
            ServiceModel.is_popular == True,
            ServiceModel.status == "ACTIVE"
        ).limit(limit).order_by(ServiceModel.display_order)

        result = await self._session.execute(query)
        db_services = result.scalars().all()

        return [self._to_domain(svc) for svc in db_services]
    
    async def list_by_price_range(
        self,
        min_price: Decimal,
        max_price: Decimal,
        category_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[ServiceDomain]:
        """List services within a price range."""
        query = select(ServiceModel).where(
            ServiceModel.price >= min_price,
            ServiceModel.price <= max_price,
            ServiceModel.status == "ACTIVE"
        )

        if category_id:
            query = query.where(ServiceModel.category_id == category_id)

        query = query.limit(limit).order_by(ServiceModel.price)

        result = await self._session.execute(query)
        db_services = result.scalars().all()

        return [self._to_domain(svc) for svc in db_services]

    async def list_by_duration_range(
        self,
        min_duration: int,
        max_duration: int,
        category_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[ServiceDomain]:
        """List services within a duration range."""
        query = select(ServiceModel).where(
            ServiceModel.duration_minutes >= min_duration,
            ServiceModel.duration_minutes <= max_duration,
            ServiceModel.status == "ACTIVE"
        )

        if category_id:
            query = query.where(ServiceModel.category_id == category_id)

        query = query.limit(limit).order_by(ServiceModel.duration_minutes)

        result = await self._session.execute(query)
        db_services = result.scalars().all()

        return [self._to_domain(svc) for svc in db_services]

    async def count_by_category(
        self,
        category_id: str,
        include_inactive: bool = False,
    ) -> int:
        """Count services in a category."""
        from sqlalchemy import func

        query = select(func.count()).select_from(ServiceModel).where(
            ServiceModel.category_id == category_id
        )

        if not include_inactive:
            query = query.where(ServiceModel.status == "ACTIVE")

        result = await self._session.execute(query)
        return result.scalar_one()

    async def count_popular_in_category(self, category_id: str) -> int:
        """Count popular services in a category."""
        from sqlalchemy import func

        result = await self._session.execute(
            select(func.count()).select_from(ServiceModel).where(
                ServiceModel.category_id == category_id,
                ServiceModel.is_popular == True,
                ServiceModel.status == "ACTIVE"
            )
        )
        return result.scalar_one()

    async def exists_by_name_in_category(
        self,
        name: str,
        category_id: str,
        exclude_service_id: Optional[str] = None,
    ) -> bool:
        """Check if service exists by name in category."""
        from sqlalchemy import func

        query = select(func.count()).select_from(ServiceModel).where(
            ServiceModel.name == name,
            ServiceModel.category_id == category_id
        )

        if exclude_service_id:
            query = query.where(ServiceModel.id != exclude_service_id)

        result = await self._session.execute(query)
        count = result.scalar_one()
        return count > 0

    async def get_multiple_by_ids(self, service_ids: List[str]) -> List[ServiceDomain]:
        """Get multiple services by their IDs."""
        result = await self._session.execute(
            select(ServiceModel).where(ServiceModel.id.in_(service_ids))
        )
        db_services = result.scalars().all()
        return [self._to_domain(svc) for svc in db_services]

    async def search_services(
        self,
        query: str,
        category_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[ServiceDomain]:
        """Search services by name or description."""
        search_pattern = f"%{query}%"
        sql_query = select(ServiceModel).where(
            (ServiceModel.name.ilike(search_pattern)) |
            (ServiceModel.description.ilike(search_pattern))
        ).where(ServiceModel.status == "ACTIVE")

        if category_id:
            sql_query = sql_query.where(ServiceModel.category_id == category_id)

        sql_query = sql_query.limit(limit).order_by(ServiceModel.name)

        result = await self._session.execute(sql_query)
        db_services = result.scalars().all()

        return [self._to_domain(svc) for svc in db_services]


class SqlBookingRepository(IBookingRepository):
    """SQLAlchemy implementation of booking repository for service statistics."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def count_bookings_for_service(
        self,
        service_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> int:
        """Count bookings for a service."""
        # Query bookings that include this service
        # For now return 0 as bookings table may not exist yet
        return 0
    
    def get_service_revenue(
        self,
        service_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Decimal:
        """Get total revenue for a service."""
        # Sum up revenue from bookings
        return Decimal("0.00")
    
    def get_popular_services_by_bookings(
        self,
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[dict]:
        """Get most popular services by booking count."""
        # Query with GROUP BY and ORDER BY count
        return []