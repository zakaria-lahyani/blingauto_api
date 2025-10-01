"""Expense API schemas - Request/Response DTOs."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.features.expenses.domain.enums import (
    ExpenseCategory,
    ExpenseStatus,
    PaymentMethod,
    RecurrenceType,
)


# ============================================================================
# Expense Schemas
# ============================================================================

class CreateExpenseSchema(BaseModel):
    """Schema for creating an expense."""

    category: ExpenseCategory
    amount: Decimal = Field(gt=0, decimal_places=2)
    description: str = Field(min_length=1, max_length=500)
    payment_method: Optional[PaymentMethod] = None
    expense_date: date
    due_date: Optional[date] = None
    vendor_name: Optional[str] = Field(None, max_length=200)
    vendor_id: Optional[str] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None
    recurrence_type: RecurrenceType = RecurrenceType.ONE_TIME
    parent_expense_id: Optional[str] = None

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: Optional[date], info) -> Optional[date]:
        """Validate due date is after expense date."""
        if v and "expense_date" in info.data:
            if v < info.data["expense_date"]:
                raise ValueError("Due date must be on or after expense date")
        return v


class UpdateExpenseSchema(BaseModel):
    """Schema for updating an expense."""

    category: Optional[ExpenseCategory] = None
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    payment_method: Optional[PaymentMethod] = None
    expense_date: Optional[date] = None
    due_date: Optional[date] = None
    vendor_name: Optional[str] = Field(None, max_length=200)
    vendor_id: Optional[str] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None


class ApproveExpenseSchema(BaseModel):
    """Schema for approving an expense."""

    approval_notes: Optional[str] = Field(None, max_length=1000)


class RejectExpenseSchema(BaseModel):
    """Schema for rejecting an expense."""

    rejection_reason: str = Field(min_length=1, max_length=1000)


class MarkExpenseAsPaidSchema(BaseModel):
    """Schema for marking expense as paid."""

    paid_date: date
    payment_method: PaymentMethod
    notes: Optional[str] = Field(None, max_length=1000)


class ExpenseSchema(BaseModel):
    """Schema for expense response."""

    id: str
    expense_number: str
    category: ExpenseCategory
    amount: Decimal
    description: str
    status: ExpenseStatus
    payment_method: Optional[PaymentMethod]
    expense_date: date
    due_date: Optional[date]
    paid_date: Optional[date]
    created_by_id: str
    approved_by_id: Optional[str]
    paid_by_id: Optional[str]
    vendor_name: Optional[str]
    vendor_id: Optional[str]
    receipt_url: Optional[str]
    notes: Optional[str]
    approval_notes: Optional[str]
    rejection_reason: Optional[str]
    recurrence_type: RecurrenceType
    parent_expense_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpenseListSchema(BaseModel):
    """Schema for expense list response."""

    items: List[ExpenseSchema]
    total: int


# ============================================================================
# Budget Schemas
# ============================================================================

class CreateBudgetSchema(BaseModel):
    """Schema for creating a budget."""

    category: ExpenseCategory
    month: date
    budgeted_amount: Decimal = Field(gt=0, decimal_places=2)
    alert_threshold_percent: int = Field(default=80, ge=0, le=100)
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("month")
    @classmethod
    def validate_month(cls, v: date) -> date:
        """Ensure month is first day of month."""
        return v.replace(day=1)


class UpdateBudgetSchema(BaseModel):
    """Schema for updating a budget."""

    budgeted_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    alert_threshold_percent: Optional[int] = Field(None, ge=0, le=100)
    notes: Optional[str] = Field(None, max_length=1000)


class BudgetSchema(BaseModel):
    """Schema for budget response."""

    id: str
    category: ExpenseCategory
    month: date
    budgeted_amount: Decimal
    spent_amount: Decimal
    remaining_amount: Decimal
    utilization_percent: int
    is_over_budget: bool
    alert_threshold_percent: int
    created_by_id: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BudgetListSchema(BaseModel):
    """Schema for budget list response."""

    items: List[BudgetSchema]
    total: int


# ============================================================================
# Report Schemas
# ============================================================================

class ExpenseSummarySchema(BaseModel):
    """Schema for expense summary response."""

    category: ExpenseCategory
    month: date
    total_expenses: int
    total_amount: Decimal
    approved_amount: Decimal
    pending_amount: Decimal
    paid_amount: Decimal
    budgeted_amount: Decimal
    over_budget: bool
    utilization_percent: int

    class Config:
        from_attributes = True


class MonthlySummarySchema(BaseModel):
    """Schema for monthly summary response."""

    month: date
    summaries: List[ExpenseSummarySchema]
    total_expenses: int
    total_amount: Decimal
    total_approved: Decimal
    total_pending: Decimal
    total_paid: Decimal
    total_budgeted: Decimal


# ============================================================================
# Query Schemas
# ============================================================================

class ExpenseQuerySchema(BaseModel):
    """Schema for expense query parameters."""

    category: Optional[ExpenseCategory] = None
    status: Optional[ExpenseStatus] = None
    created_by_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: Optional[date], info) -> Optional[date]:
        """Validate end date is after start date."""
        if v and "start_date" in info.data and info.data["start_date"]:
            if v < info.data["start_date"]:
                raise ValueError("End date must be on or after start date")
        return v


class BudgetQuerySchema(BaseModel):
    """Schema for budget query parameters."""

    category: Optional[ExpenseCategory] = None
    month: Optional[date] = None
    over_budget_only: bool = False

    @field_validator("month")
    @classmethod
    def validate_month(cls, v: Optional[date]) -> Optional[date]:
        """Ensure month is first day of month."""
        if v:
            return v.replace(day=1)
        return v
