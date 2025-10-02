"""Expense database models."""

from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Numeric,
    Date,
    Text,
    Index,
)

from app.core.db.base import Base


class ExpenseModel(Base):
    """Expense database model."""

    __tablename__ = "expenses"

    # Primary identification
    id = Column(String, primary_key=True)
    expense_number = Column(String(50), unique=True, nullable=False, index=True)

    # Categorization and amount
    category = Column(String(50), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(Text, nullable=False)

    # Status workflow
    status = Column(String(20), nullable=False, index=True)
    payment_method = Column(String(30), nullable=True)

    # Dates
    expense_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=True)
    paid_date = Column(Date, nullable=True)

    # Tracking
    created_by_id = Column(String, nullable=False, index=True)
    approved_by_id = Column(String, nullable=True)
    paid_by_id = Column(String, nullable=True)

    # Vendor/Supplier (string-based FK)
    vendor_name = Column(String(200), nullable=True)
    vendor_id = Column(String, nullable=True, index=True)

    # Documentation
    receipt_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    # Approval workflow
    approval_notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Recurrence
    recurrence_type = Column(String(20), nullable=False, default="ONE_TIME")
    parent_expense_id = Column(String, nullable=True, index=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # Indexes for performance (composite indexes only, single-column indexes are defined on the columns)
    __table_args__ = (
        Index("ix_expenses_category_status", "category", "status"),
        Index("ix_expenses_status_date", "status", "expense_date"),
    )


class BudgetModel(Base):
    """Budget database model."""

    __tablename__ = "budgets"

    # Primary identification
    id = Column(String, primary_key=True)
    category = Column(String(50), nullable=False, index=True)
    month = Column(Date, nullable=False, index=True)  # First day of month

    # Amounts
    budgeted_amount = Column(Numeric(10, 2), nullable=False)
    spent_amount = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    # Alert configuration
    alert_threshold_percent = Column(
        Numeric(5, 2), nullable=False, default=Decimal("80.00")
    )

    # Tracking
    created_by_id = Column(String, nullable=False)
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Indexes for performance (single-column indexes are defined on the columns)
    __table_args__ = (
        Index("ix_budgets_category_month", "category", "month", unique=True),
    )
