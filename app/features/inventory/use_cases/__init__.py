"""Inventory use cases."""

# Product use cases
from .create_product import CreateProductUseCase, CreateProductRequest
from .update_product import UpdateProductUseCase, UpdateProductRequest
from .get_product import GetProductUseCase
from .list_products import ListProductsUseCase, ListProductsRequest
from .delete_product import DeleteProductUseCase

# Stock movement use cases
from .record_stock_in import RecordStockInUseCase, RecordStockInRequest
from .record_stock_out import RecordStockOutUseCase, RecordStockOutRequest
from .adjust_stock import AdjustStockUseCase, AdjustStockRequest
from .list_stock_movements import ListStockMovementsUseCase, ListStockMovementsRequest

# Supplier use cases
from .create_supplier import CreateSupplierUseCase, CreateSupplierRequest
from .update_supplier import UpdateSupplierUseCase, UpdateSupplierRequest
from .get_supplier import GetSupplierUseCase
from .list_suppliers import ListSuppliersUseCase, ListSuppliersRequest
from .delete_supplier import DeleteSupplierUseCase

# Alert use cases
from .get_low_stock_alerts import GetLowStockAlertsUseCase

__all__ = [
    # Product
    "CreateProductUseCase",
    "CreateProductRequest",
    "UpdateProductUseCase",
    "UpdateProductRequest",
    "GetProductUseCase",
    "ListProductsUseCase",
    "ListProductsRequest",
    "DeleteProductUseCase",
    # Stock movement
    "RecordStockInUseCase",
    "RecordStockInRequest",
    "RecordStockOutUseCase",
    "RecordStockOutRequest",
    "AdjustStockUseCase",
    "AdjustStockRequest",
    "ListStockMovementsUseCase",
    "ListStockMovementsRequest",
    # Supplier
    "CreateSupplierUseCase",
    "CreateSupplierRequest",
    "UpdateSupplierUseCase",
    "UpdateSupplierRequest",
    "GetSupplierUseCase",
    "ListSuppliersUseCase",
    "ListSuppliersRequest",
    "DeleteSupplierUseCase",
    # Alerts
    "GetLowStockAlertsUseCase",
]
