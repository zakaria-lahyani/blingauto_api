"""Add inventory tables

Revision ID: 006
Revises: 005
Create Date: 2025-10-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create inventory tables."""

    # Create products table
    op.create_table(
        "products",
        # Primary identification
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("sku", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # Categorization
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        # Stock levels
        sa.Column("current_quantity", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("minimum_quantity", sa.Numeric(10, 2), nullable=False),
        sa.Column("reorder_point", sa.Numeric(10, 2), nullable=False),
        sa.Column("maximum_quantity", sa.Numeric(10, 2), nullable=True),
        # Pricing
        sa.Column("unit_cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=True),
        # Supplier info
        sa.Column("supplier_id", sa.String(), nullable=True),
        sa.Column("supplier_sku", sa.String(100), nullable=True),
        # Status
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        # Metadata
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku"),
    )

    # Create indexes for products
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_index("ix_products_name", "products", ["name"], unique=False)
    op.create_index("ix_products_category_active", "products", ["category", "is_active"], unique=False)
    op.create_index("ix_products_supplier", "products", ["supplier_id"], unique=False)
    op.create_index("ix_products_current_quantity", "products", ["current_quantity"], unique=False)
    op.create_index("ix_products_reorder", "products", ["current_quantity", "reorder_point"], unique=False)

    # Create stock_movements table
    op.create_table(
        "stock_movements",
        # Primary identification
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("product_id", sa.String(), nullable=False),
        # Movement details
        sa.Column("movement_type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=False),
        # Audit trail
        sa.Column("quantity_before", sa.Numeric(10, 2), nullable=False),
        sa.Column("quantity_after", sa.Numeric(10, 2), nullable=False),
        # Cost tracking
        sa.Column("unit_cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_cost", sa.Numeric(10, 2), nullable=False),
        # Reference information
        sa.Column("reference_type", sa.String(50), nullable=True),
        sa.Column("reference_id", sa.String(), nullable=True),
        # User tracking
        sa.Column("performed_by_id", sa.String(), nullable=False),
        # Details
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("movement_date", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for stock_movements
    op.create_index("ix_stock_movements_product", "stock_movements", ["product_id"], unique=False)
    op.create_index("ix_stock_movements_type", "stock_movements", ["movement_type"], unique=False)
    op.create_index("ix_stock_movements_date", "stock_movements", ["movement_date"], unique=False)
    op.create_index("ix_stock_movements_product_date", "stock_movements", ["product_id", "movement_date"], unique=False)
    op.create_index("ix_stock_movements_type_date", "stock_movements", ["movement_type", "movement_date"], unique=False)
    op.create_index("ix_stock_movements_reference", "stock_movements", ["reference_type", "reference_id"], unique=False)
    op.create_index("ix_stock_movements_performed_by", "stock_movements", ["performed_by_id"], unique=False)

    # Create suppliers table
    op.create_table(
        "suppliers",
        # Primary identification
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        # Contact information
        sa.Column("contact_person", sa.String(200), nullable=True),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        # Payment terms
        sa.Column("payment_terms", sa.String(200), nullable=True),
        # Status
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        # Ratings and notes
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        # Metadata
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for suppliers
    op.create_index("ix_suppliers_name", "suppliers", ["name"], unique=False)
    op.create_index("ix_suppliers_email", "suppliers", ["email"], unique=False)
    op.create_index("ix_suppliers_phone", "suppliers", ["phone"], unique=False)
    op.create_index("ix_suppliers_active", "suppliers", ["is_active"], unique=False)
    op.create_index("ix_suppliers_rating", "suppliers", ["rating"], unique=False)


def downgrade() -> None:
    """Drop inventory tables."""

    # Drop indexes first
    op.drop_index("ix_suppliers_rating", table_name="suppliers")
    op.drop_index("ix_suppliers_active", table_name="suppliers")
    op.drop_index("ix_suppliers_phone", table_name="suppliers")
    op.drop_index("ix_suppliers_email", table_name="suppliers")
    op.drop_index("ix_suppliers_name", table_name="suppliers")

    op.drop_index("ix_stock_movements_performed_by", table_name="stock_movements")
    op.drop_index("ix_stock_movements_reference", table_name="stock_movements")
    op.drop_index("ix_stock_movements_type_date", table_name="stock_movements")
    op.drop_index("ix_stock_movements_product_date", table_name="stock_movements")
    op.drop_index("ix_stock_movements_date", table_name="stock_movements")
    op.drop_index("ix_stock_movements_type", table_name="stock_movements")
    op.drop_index("ix_stock_movements_product", table_name="stock_movements")

    op.drop_index("ix_products_reorder", table_name="products")
    op.drop_index("ix_products_current_quantity", table_name="products")
    op.drop_index("ix_products_supplier", table_name="products")
    op.drop_index("ix_products_category_active", table_name="products")
    op.drop_index("ix_products_name", table_name="products")
    op.drop_index("ix_products_sku", table_name="products")

    # Drop tables
    op.drop_table("suppliers")
    op.drop_table("stock_movements")
    op.drop_table("products")
