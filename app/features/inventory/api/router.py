"""Inventory API router."""

from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.features.auth.domain import UserRole
from app.shared.auth import get_current_user, require_any_role
from app.features.inventory.api.schemas import *
from app.features.inventory.api.dependencies import *
from app.features.inventory.use_cases.create_product import CreateProductRequest
from app.features.inventory.use_cases.update_product import UpdateProductRequest
from app.features.inventory.use_cases.list_products import ListProductsRequest
from app.features.inventory.use_cases.record_stock_in import RecordStockInRequest
from app.features.inventory.use_cases.record_stock_out import RecordStockOutRequest
from app.features.inventory.use_cases.adjust_stock import AdjustStockRequest
from app.features.inventory.use_cases.list_stock_movements import (
    ListStockMovementsRequest,
)
from app.features.inventory.use_cases.create_supplier import CreateSupplierRequest
from app.features.inventory.use_cases.update_supplier import UpdateSupplierRequest
from app.features.inventory.use_cases.list_suppliers import ListSuppliersRequest

router = APIRouter()


# ============================================================================
# Product Endpoints
# ============================================================================


@router.post(
    "/products",
    response_model=ProductSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))
    ],
)
async def create_product(
    data: CreateProductSchema,
    use_case: Annotated[CreateProductUseCase, Depends(get_create_product_use_case)],
):
    """Create new product. **Auto-generates SKU** (PRD-00001)."""
    try:
        request = CreateProductRequest(
            name=data.name,
            description=data.description,
            category=data.category,
            unit=data.unit,
            minimum_quantity=data.minimum_quantity,
            reorder_point=data.reorder_point,
            maximum_quantity=data.maximum_quantity,
            unit_cost=data.unit_cost,
            unit_price=data.unit_price,
            supplier_id=data.supplier_id,
            supplier_sku=data.supplier_sku,
            initial_quantity=data.initial_quantity,
            notes=data.notes,
        )
        product = await use_case.execute(request)
        return ProductSchema(
            id=product.id,
            sku=product.sku,
            name=product.name,
            description=product.description,
            category=product.category,
            unit=product.unit,
            current_quantity=product.current_quantity,
            minimum_quantity=product.minimum_quantity,
            reorder_point=product.reorder_point,
            maximum_quantity=product.maximum_quantity,
            unit_cost=product.unit_cost,
            unit_price=product.unit_price,
            supplier_id=product.supplier_id,
            supplier_sku=product.supplier_sku,
            is_active=product.is_active,
            stock_status=product.get_stock_status(),
            stock_value=product.calculate_stock_value(),
            needs_reorder=product.needs_reorder(),
            notes=product.notes,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/products/{product_id}", response_model=ProductSchema)
async def get_product(
    product_id: str,
    use_case: Annotated[GetProductUseCase, Depends(get_get_product_use_case)],
):
    """Get product by ID."""
    try:
        product = await use_case.execute(product_id)
        return ProductSchema(
            id=product.id,
            sku=product.sku,
            name=product.name,
            description=product.description,
            category=product.category,
            unit=product.unit,
            current_quantity=product.current_quantity,
            minimum_quantity=product.minimum_quantity,
            reorder_point=product.reorder_point,
            maximum_quantity=product.maximum_quantity,
            unit_cost=product.unit_cost,
            unit_price=product.unit_price,
            supplier_id=product.supplier_id,
            supplier_sku=product.supplier_sku,
            is_active=product.is_active,
            stock_status=product.get_stock_status(),
            stock_value=product.calculate_stock_value(),
            needs_reorder=product.needs_reorder(),
            notes=product.notes,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/products", response_model=ProductListSchema)
async def list_products(
    use_case: Annotated[ListProductsUseCase, Depends(get_list_products_use_case)],
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List products with filters."""
    try:
        from app.features.inventory.domain.enums import ProductCategory

        request = ListProductsRequest(
            category=ProductCategory(category) if category else None,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )
        products = await use_case.execute(request)
        items = [
            ProductSchema(
                id=p.id,
                sku=p.sku,
                name=p.name,
                description=p.description,
                category=p.category,
                unit=p.unit,
                current_quantity=p.current_quantity,
                minimum_quantity=p.minimum_quantity,
                reorder_point=p.reorder_point,
                maximum_quantity=p.maximum_quantity,
                unit_cost=p.unit_cost,
                unit_price=p.unit_price,
                supplier_id=p.supplier_id,
                supplier_sku=p.supplier_sku,
                is_active=p.is_active,
                stock_status=p.get_stock_status(),
                stock_value=p.calculate_stock_value(),
                needs_reorder=p.needs_reorder(),
                notes=p.notes,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in products
        ]
        return ProductListSchema(
            items=items, total=len(items), limit=limit, offset=offset
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/products/{product_id}",
    response_model=ProductSchema,
    dependencies=[
        Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))
    ],
)
async def update_product(
    product_id: str,
    data: UpdateProductSchema,
    use_case: Annotated[UpdateProductUseCase, Depends(get_update_product_use_case)],
):
    """Update product."""
    try:
        request = UpdateProductRequest(product_id=product_id, **data.dict(exclude_unset=True))
        product = await use_case.execute(request)
        return ProductSchema(
            id=product.id,
            sku=product.sku,
            name=product.name,
            description=product.description,
            category=product.category,
            unit=product.unit,
            current_quantity=product.current_quantity,
            minimum_quantity=product.minimum_quantity,
            reorder_point=product.reorder_point,
            maximum_quantity=product.maximum_quantity,
            unit_cost=product.unit_cost,
            unit_price=product.unit_price,
            supplier_id=product.supplier_id,
            supplier_sku=product.supplier_sku,
            is_active=product.is_active,
            stock_status=product.get_stock_status(),
            stock_value=product.calculate_stock_value(),
            needs_reorder=product.needs_reorder(),
            notes=product.notes,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value))],
)
async def delete_product(
    product_id: str,
    use_case: Annotated[DeleteProductUseCase, Depends(get_delete_product_use_case)],
):
    """Delete product (soft delete). Admin only."""
    try:
        await use_case.execute(product_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Stock Movement Endpoints
# ============================================================================


@router.post(
    "/products/{product_id}/stock/in",
    response_model=StockMovementSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))
    ],
)
async def record_stock_in(
    product_id: str,
    data: RecordStockInSchema,
    use_case: Annotated[RecordStockInUseCase, Depends(get_record_stock_in_use_case)],
    current_user=Depends(get_current_user),
):
    """Record stock in (purchase, receiving). **Updates product quantity**."""
    try:
        request = RecordStockInRequest(
            product_id=product_id,
            quantity=data.quantity,
            unit_cost=data.unit_cost,
            performed_by_id=current_user["user_id"],
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            reason=data.reason,
            notes=data.notes,
        )
        movement = await use_case.execute(request)
        return StockMovementSchema.from_orm(movement)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/products/{product_id}/stock/out",
    response_model=StockMovementSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(
            require_any_role(
                UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.WASHER.value
            )
        )
    ],
)
async def record_stock_out(
    product_id: str,
    data: RecordStockOutSchema,
    use_case: Annotated[RecordStockOutUseCase, Depends(get_record_stock_out_use_case)],
    current_user=Depends(get_current_user),
):
    """Record stock out (usage). **Updates product quantity**."""
    try:
        request = RecordStockOutRequest(
            product_id=product_id,
            quantity=data.quantity,
            performed_by_id=current_user["user_id"],
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            reason=data.reason,
            notes=data.notes,
        )
        movement = await use_case.execute(request)
        return StockMovementSchema.from_orm(movement)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/products/{product_id}/stock/adjust",
    response_model=StockMovementSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))
    ],
)
async def adjust_stock(
    product_id: str,
    data: AdjustStockSchema,
    use_case: Annotated[AdjustStockUseCase, Depends(get_adjust_stock_use_case)],
    current_user=Depends(get_current_user),
):
    """Adjust stock (manual correction). **Requires reason**."""
    try:
        request = AdjustStockRequest(
            product_id=product_id,
            new_quantity=data.new_quantity,
            reason=data.reason,
            performed_by_id=current_user["user_id"],
            notes=data.notes,
        )
        movement = await use_case.execute(request)
        return StockMovementSchema.from_orm(movement)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/stock-movements", response_model=StockMovementListSchema)
async def list_stock_movements(
    use_case: Annotated[
        ListStockMovementsUseCase, Depends(get_list_stock_movements_use_case)
    ],
    product_id: Optional[str] = Query(None),
    movement_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List stock movements with filters."""
    try:
        from app.features.inventory.domain.enums import StockMovementType

        request = ListStockMovementsRequest(
            product_id=product_id,
            movement_type=StockMovementType(movement_type) if movement_type else None,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
        movements = await use_case.execute(request)
        items = [StockMovementSchema.from_orm(m) for m in movements]
        return StockMovementListSchema(
            items=items, total=len(items), limit=limit, offset=offset
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ============================================================================
# Supplier Endpoints
# ============================================================================


@router.post(
    "/suppliers",
    response_model=SupplierSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))
    ],
)
async def create_supplier(
    data: CreateSupplierSchema,
    use_case: Annotated[CreateSupplierUseCase, Depends(get_create_supplier_use_case)],
):
    """Create new supplier."""
    try:
        request = CreateSupplierRequest(**data.dict())
        supplier = await use_case.execute(request)
        return SupplierSchema.from_orm(supplier)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/suppliers/{supplier_id}", response_model=SupplierSchema)
async def get_supplier(
    supplier_id: str,
    use_case: Annotated[GetSupplierUseCase, Depends(get_get_supplier_use_case)],
):
    """Get supplier by ID."""
    try:
        supplier = await use_case.execute(supplier_id)
        return SupplierSchema.from_orm(supplier)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/suppliers", response_model=SupplierListSchema)
async def list_suppliers(
    use_case: Annotated[ListSuppliersUseCase, Depends(get_list_suppliers_use_case)],
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List suppliers with filters."""
    try:
        request = ListSuppliersRequest(
            is_active=is_active, limit=limit, offset=offset
        )
        suppliers = await use_case.execute(request)
        items = [SupplierSchema.from_orm(s) for s in suppliers]
        return SupplierListSchema(
            items=items, total=len(items), limit=limit, offset=offset
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/suppliers/{supplier_id}",
    response_model=SupplierSchema,
    dependencies=[
        Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))
    ],
)
async def update_supplier(
    supplier_id: str,
    data: UpdateSupplierSchema,
    use_case: Annotated[UpdateSupplierUseCase, Depends(get_update_supplier_use_case)],
):
    """Update supplier."""
    try:
        request = UpdateSupplierRequest(
            supplier_id=supplier_id, **data.dict(exclude_unset=True)
        )
        supplier = await use_case.execute(request)
        return SupplierSchema.from_orm(supplier)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/suppliers/{supplier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value))],
)
async def delete_supplier(
    supplier_id: str,
    use_case: Annotated[DeleteSupplierUseCase, Depends(get_delete_supplier_use_case)],
):
    """Delete supplier (soft delete). Admin only."""
    try:
        await use_case.execute(supplier_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Alert Endpoints
# ============================================================================


@router.get(
    "/alerts/low-stock",
    response_model=LowStockAlertsListSchema,
    dependencies=[
        Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))
    ],
)
async def get_low_stock_alerts(
    use_case: Annotated[
        GetLowStockAlertsUseCase, Depends(get_low_stock_alerts_use_case)
    ],
):
    """Get low stock alerts. Products at or below reorder point."""
    alerts = await use_case.execute()
    items = [LowStockAlertSchema.from_orm(a) for a in alerts]
    return LowStockAlertsListSchema(items=items, total=len(items))
