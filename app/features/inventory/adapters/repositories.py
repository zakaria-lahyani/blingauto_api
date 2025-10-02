"""Inventory repository implementations."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.inventory.domain.entities import Product, StockMovement, Supplier
from app.features.inventory.domain.enums import (
    ProductCategory,
    ProductUnit,
    StockMovementType,
)
from app.features.inventory.ports.repositories import (
    IProductRepository,
    IStockMovementRepository,
    ISupplierRepository,
)
from app.features.inventory.adapters.models import (
    ProductModel,
    StockMovementModel,
    SupplierModel,
)


class ProductRepository(IProductRepository):
    """Product repository implementation using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self._session = session

    async def create(self, product: Product) -> Product:
        """Create new product."""
        model = self._to_model(product)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def update(self, product: Product) -> Product:
        """Update existing product."""
        stmt = select(ProductModel).where(ProductModel.id == product.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise LookupError(f"Product {product.id} not found")

        # Update fields
        model.name = product.name
        model.description = product.description
        model.category = product.category.value
        model.unit = product.unit.value
        model.current_quantity = product.current_quantity
        model.minimum_quantity = product.minimum_quantity
        model.reorder_point = product.reorder_point
        model.maximum_quantity = product.maximum_quantity
        model.unit_cost = product.unit_cost
        model.unit_price = product.unit_price
        model.supplier_id = product.supplier_id
        model.supplier_sku = product.supplier_sku
        model.is_active = product.is_active
        model.notes = product.notes
        model.updated_at = datetime.now(timezone.utc)

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, product_id: str) -> Optional[Product]:
        """Get product by ID."""
        stmt = (
            select(ProductModel)
            .where(ProductModel.id == product_id)
            .where(ProductModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU."""
        stmt = (
            select(ProductModel)
            .where(ProductModel.sku == sku)
            .where(ProductModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_all(
        self,
        category: Optional[ProductCategory] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Product]:
        """List products with filters."""
        conditions = [ProductModel.deleted_at.is_(None)]

        if category:
            conditions.append(ProductModel.category == category.value)
        if is_active is not None:
            conditions.append(ProductModel.is_active == is_active)

        stmt = (
            select(ProductModel)
            .where(and_(*conditions))
            .order_by(ProductModel.name)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def list_low_stock(self) -> List[Product]:
        """List products with low stock."""
        stmt = (
            select(ProductModel)
            .where(
                and_(
                    ProductModel.deleted_at.is_(None),
                    ProductModel.is_active == True,
                    ProductModel.current_quantity <= ProductModel.reorder_point,
                )
            )
            .order_by(ProductModel.current_quantity)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def list_out_of_stock(self) -> List[Product]:
        """List products that are out of stock."""
        stmt = (
            select(ProductModel)
            .where(
                and_(
                    ProductModel.deleted_at.is_(None),
                    ProductModel.is_active == True,
                    ProductModel.current_quantity == 0,
                )
            )
            .order_by(ProductModel.name)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def get_next_product_count(self) -> int:
        """Get count of products for SKU generation."""
        stmt = select(func.count()).select_from(ProductModel)
        result = await self._session.execute(stmt)
        count = result.scalar() or 0
        return count

    async def delete(self, product_id: str) -> None:
        """Soft delete product."""
        stmt = select(ProductModel).where(ProductModel.id == product_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.deleted_at = datetime.now(timezone.utc)
            await self._session.flush()

    def _to_domain(self, model: ProductModel) -> Product:
        """Convert model to domain entity."""
        return Product(
            id=model.id,
            sku=model.sku,
            name=model.name,
            description=model.description,
            category=ProductCategory(model.category),
            unit=ProductUnit(model.unit),
            current_quantity=model.current_quantity,
            minimum_quantity=model.minimum_quantity,
            reorder_point=model.reorder_point,
            maximum_quantity=model.maximum_quantity,
            unit_cost=model.unit_cost,
            unit_price=model.unit_price,
            supplier_id=model.supplier_id,
            supplier_sku=model.supplier_sku,
            is_active=model.is_active,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, product: Product) -> ProductModel:
        """Convert domain entity to model."""
        return ProductModel(
            id=product.id,
            sku=product.sku,
            name=product.name,
            description=product.description,
            category=product.category.value,
            unit=product.unit.value,
            current_quantity=product.current_quantity,
            minimum_quantity=product.minimum_quantity,
            reorder_point=product.reorder_point,
            maximum_quantity=product.maximum_quantity,
            unit_cost=product.unit_cost,
            unit_price=product.unit_price,
            supplier_id=product.supplier_id,
            supplier_sku=product.supplier_sku,
            is_active=product.is_active,
            notes=product.notes,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )


class StockMovementRepository(IStockMovementRepository):
    """Stock movement repository implementation using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self._session = session

    async def create(self, movement: StockMovement) -> StockMovement:
        """Create stock movement."""
        model = self._to_model(movement)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, movement_id: str) -> Optional[StockMovement]:
        """Get movement by ID."""
        stmt = select(StockMovementModel).where(StockMovementModel.id == movement_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_product(
        self,
        product_id: str,
        movement_type: Optional[StockMovementType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[StockMovement]:
        """List movements for a product."""
        conditions = [StockMovementModel.product_id == product_id]

        if movement_type:
            conditions.append(StockMovementModel.movement_type == movement_type.value)

        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            conditions.append(StockMovementModel.movement_date >= start_datetime)

        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            conditions.append(StockMovementModel.movement_date <= end_datetime)

        stmt = (
            select(StockMovementModel)
            .where(and_(*conditions))
            .order_by(StockMovementModel.movement_date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def list_all(
        self,
        movement_type: Optional[StockMovementType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[StockMovement]:
        """List all movements with filters."""
        conditions = []

        if movement_type:
            conditions.append(StockMovementModel.movement_type == movement_type.value)

        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            conditions.append(StockMovementModel.movement_date >= start_datetime)

        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            conditions.append(StockMovementModel.movement_date <= end_datetime)

        stmt = select(StockMovementModel)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = (
            stmt.order_by(StockMovementModel.movement_date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def get_total_usage_by_product(
        self, product_id: str, start_date: date, end_date: date
    ) -> dict:
        """Get total usage (OUT movements) for a product in date range."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        stmt = select(
            func.sum(func.abs(StockMovementModel.quantity)).label("total_quantity"),
            func.sum(StockMovementModel.total_cost).label("total_cost"),
            func.count().label("movement_count"),
        ).where(
            and_(
                StockMovementModel.product_id == product_id,
                StockMovementModel.movement_type == StockMovementType.OUT.value,
                StockMovementModel.movement_date >= start_datetime,
                StockMovementModel.movement_date <= end_datetime,
            )
        )

        result = await self._session.execute(stmt)
        row = result.first()

        return {
            "total_quantity": row.total_quantity or Decimal("0"),
            "total_cost": row.total_cost or Decimal("0"),
            "movement_count": row.movement_count or 0,
        }

    def _to_domain(self, model: StockMovementModel) -> StockMovement:
        """Convert model to domain entity."""
        return StockMovement(
            id=model.id,
            product_id=model.product_id,
            movement_type=StockMovementType(model.movement_type),
            quantity=model.quantity,
            quantity_before=model.quantity_before,
            quantity_after=model.quantity_after,
            unit_cost=model.unit_cost,
            total_cost=model.total_cost,
            reference_type=model.reference_type,
            reference_id=model.reference_id,
            performed_by_id=model.performed_by_id,
            reason=model.reason,
            notes=model.notes,
            movement_date=model.movement_date,
            created_at=model.created_at,
        )

    def _to_model(self, movement: StockMovement) -> StockMovementModel:
        """Convert domain entity to model."""
        return StockMovementModel(
            id=movement.id,
            product_id=movement.product_id,
            movement_type=movement.movement_type.value,
            quantity=movement.quantity,
            quantity_before=movement.quantity_before,
            quantity_after=movement.quantity_after,
            unit_cost=movement.unit_cost,
            total_cost=movement.total_cost,
            reference_type=movement.reference_type,
            reference_id=movement.reference_id,
            performed_by_id=movement.performed_by_id,
            reason=movement.reason,
            notes=movement.notes,
            movement_date=movement.movement_date,
            created_at=movement.created_at,
        )


class SupplierRepository(ISupplierRepository):
    """Supplier repository implementation using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self._session = session

    async def create(self, supplier: Supplier) -> Supplier:
        """Create supplier."""
        model = self._to_model(supplier)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def update(self, supplier: Supplier) -> Supplier:
        """Update supplier."""
        stmt = select(SupplierModel).where(SupplierModel.id == supplier.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise LookupError(f"Supplier {supplier.id} not found")

        # Update fields
        model.name = supplier.name
        model.contact_person = supplier.contact_person
        model.email = supplier.email
        model.phone = supplier.phone
        model.address = supplier.address
        model.payment_terms = supplier.payment_terms
        model.is_active = supplier.is_active
        model.rating = supplier.rating
        model.notes = supplier.notes
        model.updated_at = datetime.now(timezone.utc)

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, supplier_id: str) -> Optional[Supplier]:
        """Get supplier by ID."""
        stmt = (
            select(SupplierModel)
            .where(SupplierModel.id == supplier_id)
            .where(SupplierModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_all(
        self, is_active: Optional[bool] = None, limit: int = 100, offset: int = 0
    ) -> List[Supplier]:
        """List suppliers with filters."""
        conditions = [SupplierModel.deleted_at.is_(None)]

        if is_active is not None:
            conditions.append(SupplierModel.is_active == is_active)

        stmt = (
            select(SupplierModel)
            .where(and_(*conditions))
            .order_by(SupplierModel.name)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def delete(self, supplier_id: str) -> None:
        """Soft delete supplier."""
        stmt = select(SupplierModel).where(SupplierModel.id == supplier_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.deleted_at = datetime.now(timezone.utc)
            await self._session.flush()

    def _to_domain(self, model: SupplierModel) -> Supplier:
        """Convert model to domain entity."""
        return Supplier(
            id=model.id,
            name=model.name,
            contact_person=model.contact_person,
            email=model.email,
            phone=model.phone,
            address=model.address,
            payment_terms=model.payment_terms,
            is_active=model.is_active,
            rating=model.rating,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, supplier: Supplier) -> SupplierModel:
        """Convert domain entity to model."""
        return SupplierModel(
            id=supplier.id,
            name=supplier.name,
            contact_person=supplier.contact_person,
            email=supplier.email,
            phone=supplier.phone,
            address=supplier.address,
            payment_terms=supplier.payment_terms,
            is_active=supplier.is_active,
            rating=supplier.rating,
            notes=supplier.notes,
            created_at=supplier.created_at,
            updated_at=supplier.updated_at,
        )
