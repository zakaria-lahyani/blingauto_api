"""Inventory API dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.features.inventory.adapters.repositories import (
    ProductRepository,
    StockMovementRepository,
    SupplierRepository,
)
from app.features.inventory.use_cases.create_product import CreateProductUseCase
from app.features.inventory.use_cases.update_product import UpdateProductUseCase
from app.features.inventory.use_cases.get_product import GetProductUseCase
from app.features.inventory.use_cases.list_products import ListProductsUseCase
from app.features.inventory.use_cases.delete_product import DeleteProductUseCase
from app.features.inventory.use_cases.record_stock_in import RecordStockInUseCase
from app.features.inventory.use_cases.record_stock_out import RecordStockOutUseCase
from app.features.inventory.use_cases.adjust_stock import AdjustStockUseCase
from app.features.inventory.use_cases.list_stock_movements import (
    ListStockMovementsUseCase,
)
from app.features.inventory.use_cases.create_supplier import CreateSupplierUseCase
from app.features.inventory.use_cases.update_supplier import UpdateSupplierUseCase
from app.features.inventory.use_cases.get_supplier import GetSupplierUseCase
from app.features.inventory.use_cases.list_suppliers import ListSuppliersUseCase
from app.features.inventory.use_cases.delete_supplier import DeleteSupplierUseCase
from app.features.inventory.use_cases.get_low_stock_alerts import (
    GetLowStockAlertsUseCase,
)


# ============================================================================
# Repository Dependencies
# ============================================================================


def get_product_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> ProductRepository:
    """Get product repository."""
    return ProductRepository(session)


def get_stock_movement_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> StockMovementRepository:
    """Get stock movement repository."""
    return StockMovementRepository(session)


def get_supplier_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> SupplierRepository:
    """Get supplier repository."""
    return SupplierRepository(session)


# ============================================================================
# Product Use Case Dependencies
# ============================================================================


def get_create_product_use_case(
    repository: Annotated[ProductRepository, Depends(get_product_repository)]
) -> CreateProductUseCase:
    """Get create product use case."""
    return CreateProductUseCase(repository)


def get_update_product_use_case(
    repository: Annotated[ProductRepository, Depends(get_product_repository)]
) -> UpdateProductUseCase:
    """Get update product use case."""
    return UpdateProductUseCase(repository)


def get_get_product_use_case(
    repository: Annotated[ProductRepository, Depends(get_product_repository)]
) -> GetProductUseCase:
    """Get get product use case."""
    return GetProductUseCase(repository)


def get_list_products_use_case(
    repository: Annotated[ProductRepository, Depends(get_product_repository)]
) -> ListProductsUseCase:
    """Get list products use case."""
    return ListProductsUseCase(repository)


def get_delete_product_use_case(
    repository: Annotated[ProductRepository, Depends(get_product_repository)]
) -> DeleteProductUseCase:
    """Get delete product use case."""
    return DeleteProductUseCase(repository)


# ============================================================================
# Stock Movement Use Case Dependencies
# ============================================================================


def get_record_stock_in_use_case(
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
    movement_repo: Annotated[
        StockMovementRepository, Depends(get_stock_movement_repository)
    ],
) -> RecordStockInUseCase:
    """Get record stock in use case."""
    return RecordStockInUseCase(product_repo, movement_repo)


def get_record_stock_out_use_case(
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
    movement_repo: Annotated[
        StockMovementRepository, Depends(get_stock_movement_repository)
    ],
) -> RecordStockOutUseCase:
    """Get record stock out use case."""
    return RecordStockOutUseCase(product_repo, movement_repo)


def get_adjust_stock_use_case(
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
    movement_repo: Annotated[
        StockMovementRepository, Depends(get_stock_movement_repository)
    ],
) -> AdjustStockUseCase:
    """Get adjust stock use case."""
    return AdjustStockUseCase(product_repo, movement_repo)


def get_list_stock_movements_use_case(
    repository: Annotated[
        StockMovementRepository, Depends(get_stock_movement_repository)
    ]
) -> ListStockMovementsUseCase:
    """Get list stock movements use case."""
    return ListStockMovementsUseCase(repository)


# ============================================================================
# Supplier Use Case Dependencies
# ============================================================================


def get_create_supplier_use_case(
    repository: Annotated[SupplierRepository, Depends(get_supplier_repository)]
) -> CreateSupplierUseCase:
    """Get create supplier use case."""
    return CreateSupplierUseCase(repository)


def get_update_supplier_use_case(
    repository: Annotated[SupplierRepository, Depends(get_supplier_repository)]
) -> UpdateSupplierUseCase:
    """Get update supplier use case."""
    return UpdateSupplierUseCase(repository)


def get_get_supplier_use_case(
    repository: Annotated[SupplierRepository, Depends(get_supplier_repository)]
) -> GetSupplierUseCase:
    """Get get supplier use case."""
    return GetSupplierUseCase(repository)


def get_list_suppliers_use_case(
    repository: Annotated[SupplierRepository, Depends(get_supplier_repository)]
) -> ListSuppliersUseCase:
    """Get list suppliers use case."""
    return ListSuppliersUseCase(repository)


def get_delete_supplier_use_case(
    repository: Annotated[SupplierRepository, Depends(get_supplier_repository)]
) -> DeleteSupplierUseCase:
    """Get delete supplier use case."""
    return DeleteSupplierUseCase(repository)


# ============================================================================
# Alert Use Case Dependencies
# ============================================================================


def get_low_stock_alerts_use_case(
    repository: Annotated[ProductRepository, Depends(get_product_repository)]
) -> GetLowStockAlertsUseCase:
    """Get low stock alerts use case."""
    return GetLowStockAlertsUseCase(repository)
