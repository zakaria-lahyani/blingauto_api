"""Add walk-in service tables

Revision ID: 005
Revises: 004
Create Date: 2025-10-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create walk-in service tables."""

    # Create walkin_services table
    op.create_table(
        "walkin_services",
        # Primary identification
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("service_number", sa.String(50), nullable=False),
        # Vehicle information
        sa.Column("vehicle_make", sa.String(100), nullable=False),
        sa.Column("vehicle_model", sa.String(100), nullable=False),
        sa.Column("vehicle_color", sa.String(50), nullable=False),
        sa.Column("vehicle_size", sa.String(20), nullable=False),
        sa.Column("license_plate", sa.String(20), nullable=True),
        # Customer information (optional)
        sa.Column("customer_name", sa.String(200), nullable=True),
        sa.Column("customer_phone", sa.String(20), nullable=True),
        # Status
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("payment_status", sa.String(20), nullable=False),
        # Pricing
        sa.Column(
            "total_amount",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "discount_amount",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("discount_reason", sa.String(200), nullable=True),
        sa.Column(
            "final_amount",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "paid_amount",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0.00",
        ),
        # Timing
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        # Tracking
        sa.Column("created_by_id", sa.String(), nullable=False),
        sa.Column("completed_by_id", sa.String(), nullable=True),
        sa.Column("cancelled_by_id", sa.String(), nullable=True),
        # Additional info
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        # Payment details (JSONB)
        sa.Column("payment_details", JSONB, nullable=True),
        # Timestamps
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
        sa.UniqueConstraint("service_number"),
    )

    # Create indexes for walkin_services
    op.create_index(
        "ix_walkin_services_service_number",
        "walkin_services",
        ["service_number"],
        unique=True,
    )
    op.create_index(
        "ix_walkin_services_license_plate",
        "walkin_services",
        ["license_plate"],
        unique=False,
    )
    op.create_index(
        "ix_walkin_services_customer_phone",
        "walkin_services",
        ["customer_phone"],
        unique=False,
    )
    op.create_index(
        "ix_walkin_services_status", "walkin_services", ["status"], unique=False
    )
    op.create_index(
        "ix_walkin_services_payment_status",
        "walkin_services",
        ["payment_status"],
        unique=False,
    )
    op.create_index(
        "ix_walkin_services_started_at",
        "walkin_services",
        ["started_at"],
        unique=False,
    )
    op.create_index(
        "ix_walkin_services_created_by_id",
        "walkin_services",
        ["created_by_id"],
        unique=False,
    )

    # Composite indexes for common queries
    op.create_index(
        "ix_walkin_services_status_created",
        "walkin_services",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_walkin_services_payment_status_created",
        "walkin_services",
        ["payment_status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_walkin_services_created_by_date",
        "walkin_services",
        ["created_by_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_walkin_services_started_date",
        "walkin_services",
        ["started_at"],
        unique=False,
    )

    # Create walkin_service_items table
    op.create_table(
        "walkin_service_items",
        # Primary identification
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("walkin_id", sa.String(), nullable=False),
        # Service reference
        sa.Column("service_id", sa.String(), nullable=False),
        sa.Column("service_name", sa.String(200), nullable=False),
        # Pricing
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "product_costs",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        # Additional info
        sa.Column("notes", sa.Text(), nullable=True),
        # Timestamps
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
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["walkin_id"],
            ["walkin_services.id"],
            ondelete="CASCADE",
        ),
    )

    # Create indexes for walkin_service_items
    op.create_index(
        "ix_walkin_service_items_walkin",
        "walkin_service_items",
        ["walkin_id"],
        unique=False,
    )
    op.create_index(
        "ix_walkin_service_items_service",
        "walkin_service_items",
        ["service_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop walk-in service tables."""

    # Drop indexes first
    op.drop_index("ix_walkin_service_items_service", table_name="walkin_service_items")
    op.drop_index("ix_walkin_service_items_walkin", table_name="walkin_service_items")

    op.drop_index(
        "ix_walkin_services_started_date", table_name="walkin_services"
    )
    op.drop_index(
        "ix_walkin_services_created_by_date", table_name="walkin_services"
    )
    op.drop_index(
        "ix_walkin_services_payment_status_created",
        table_name="walkin_services",
    )
    op.drop_index(
        "ix_walkin_services_status_created", table_name="walkin_services"
    )
    op.drop_index("ix_walkin_services_created_by_id", table_name="walkin_services")
    op.drop_index("ix_walkin_services_started_at", table_name="walkin_services")
    op.drop_index("ix_walkin_services_payment_status", table_name="walkin_services")
    op.drop_index("ix_walkin_services_status", table_name="walkin_services")
    op.drop_index("ix_walkin_services_customer_phone", table_name="walkin_services")
    op.drop_index("ix_walkin_services_license_plate", table_name="walkin_services")
    op.drop_index("ix_walkin_services_service_number", table_name="walkin_services")

    # Drop tables
    op.drop_table("walkin_service_items")
    op.drop_table("walkin_services")
