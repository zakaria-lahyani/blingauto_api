"""Add expense tables

Revision ID: 007
Revises: 006
Create Date: 2025-10-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create expense and budget tables."""

    # Create expenses table
    op.create_table(
        "expenses",
        # Primary identification
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("expense_number", sa.String(50), nullable=False),
        # Expense details
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("payment_method", sa.String(20), nullable=True),
        # Dates
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("paid_date", sa.Date(), nullable=True),
        # User tracking
        sa.Column("created_by_id", sa.String(), nullable=False),
        sa.Column("approved_by_id", sa.String(), nullable=True),
        sa.Column("paid_by_id", sa.String(), nullable=True),
        # Vendor information
        sa.Column("vendor_name", sa.String(200), nullable=True),
        sa.Column("vendor_id", sa.String(), nullable=True),
        # Documentation
        sa.Column("receipt_url", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("approval_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        # Recurrence
        sa.Column("recurrence_type", sa.String(20), nullable=False),
        sa.Column("parent_expense_id", sa.String(), nullable=True),
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
        sa.UniqueConstraint("expense_number"),
    )

    # Create indexes for expenses
    op.create_index("ix_expenses_expense_number", "expenses", ["expense_number"], unique=True)
    op.create_index("ix_expenses_category", "expenses", ["category"], unique=False)
    op.create_index("ix_expenses_status", "expenses", ["status"], unique=False)
    op.create_index("ix_expenses_expense_date", "expenses", ["expense_date"], unique=False)
    op.create_index("ix_expenses_created_by", "expenses", ["created_by_id"], unique=False)
    op.create_index("ix_expenses_vendor", "expenses", ["vendor_id"], unique=False)
    op.create_index("ix_expenses_parent", "expenses", ["parent_expense_id"], unique=False)
    # Composite indexes for common queries
    op.create_index("ix_expenses_category_status", "expenses", ["category", "status"], unique=False)
    op.create_index("ix_expenses_status_date", "expenses", ["status", "expense_date"], unique=False)
    op.create_index("ix_expenses_category_date", "expenses", ["category", "expense_date"], unique=False)
    op.create_index("ix_expenses_status_due_date", "expenses", ["status", "due_date"], unique=False)

    # Create budgets table
    op.create_table(
        "budgets",
        # Primary identification
        sa.Column("id", sa.String(), nullable=False),
        # Budget identification
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        # Budget amounts
        sa.Column("budgeted_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("spent_amount", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        # Alert settings
        sa.Column("alert_threshold_percent", sa.Integer(), nullable=False, server_default="80"),
        # User tracking
        sa.Column("created_by_id", sa.String(), nullable=False),
        # Notes
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
    )

    # Create indexes for budgets
    op.create_index("ix_budgets_category", "budgets", ["category"], unique=False)
    op.create_index("ix_budgets_month", "budgets", ["month"], unique=False)
    op.create_index("ix_budgets_category_month", "budgets", ["category", "month"], unique=True)
    op.create_index("ix_budgets_created_by", "budgets", ["created_by_id"], unique=False)


def downgrade() -> None:
    """Drop expense and budget tables."""

    # Drop budget indexes
    op.drop_index("ix_budgets_created_by", table_name="budgets")
    op.drop_index("ix_budgets_category_month", table_name="budgets")
    op.drop_index("ix_budgets_month", table_name="budgets")
    op.drop_index("ix_budgets_category", table_name="budgets")

    # Drop expense indexes
    op.drop_index("ix_expenses_status_due_date", table_name="expenses")
    op.drop_index("ix_expenses_category_date", table_name="expenses")
    op.drop_index("ix_expenses_status_date", table_name="expenses")
    op.drop_index("ix_expenses_category_status", table_name="expenses")
    op.drop_index("ix_expenses_parent", table_name="expenses")
    op.drop_index("ix_expenses_vendor", table_name="expenses")
    op.drop_index("ix_expenses_created_by", table_name="expenses")
    op.drop_index("ix_expenses_expense_date", table_name="expenses")
    op.drop_index("ix_expenses_status", table_name="expenses")
    op.drop_index("ix_expenses_category", table_name="expenses")
    op.drop_index("ix_expenses_expense_number", table_name="expenses")

    # Drop tables
    op.drop_table("budgets")
    op.drop_table("expenses")
