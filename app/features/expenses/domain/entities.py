"""Expense domain entities."""

from dataclasses import dataclass, field
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, List

from app.features.expenses.domain.enums import (
    ExpenseCategory,
    ExpenseStatus,
    PaymentMethod,
    RecurrenceType,
)


@dataclass
class Expense:
    """Expense entity - business spending record."""

    # Required fields
    id: str
    expense_number: str  # Auto-generated: EXP-20251002-001
    category: ExpenseCategory
    amount: Decimal
    description: str
    status: ExpenseStatus
    expense_date: date  # When expense occurred
    created_by_id: str  # Staff who created expense

    # Optional fields with defaults
    payment_method: Optional[PaymentMethod] = None
    due_date: Optional[date] = None  # Payment due date
    paid_date: Optional[date] = None  # Actual payment date
    approved_by_id: Optional[str] = None  # Manager/Admin who approved
    paid_by_id: Optional[str] = None  # Staff who processed payment
    vendor_name: Optional[str] = None
    vendor_id: Optional[str] = None  # Link to suppliers (string-based FK)
    receipt_url: Optional[str] = None  # Receipt/invoice file
    notes: Optional[str] = None
    approval_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    recurrence_type: RecurrenceType = RecurrenceType.ONE_TIME
    parent_expense_id: Optional[str] = None  # For recurring expense instances
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def approve(self, approved_by_id: str, approval_notes: Optional[str] = None) -> None:
        """Approve expense."""
        if self.status != ExpenseStatus.PENDING:
            raise ValueError(f"Cannot approve expense with status {self.status}")

        self.status = ExpenseStatus.APPROVED
        self.approved_by_id = approved_by_id
        self.approval_notes = approval_notes
        self.updated_at = datetime.now(timezone.utc)

    def reject(self, rejected_by_id: str, rejection_reason: str) -> None:
        """Reject expense."""
        if self.status != ExpenseStatus.PENDING:
            raise ValueError(f"Cannot reject expense with status {self.status}")

        if not rejection_reason or not rejection_reason.strip():
            raise ValueError("Rejection reason is required")

        self.status = ExpenseStatus.REJECTED
        self.approved_by_id = rejected_by_id  # Store who rejected
        self.rejection_reason = rejection_reason
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_paid(
        self, paid_by_id: str, payment_method: PaymentMethod, paid_date: date
    ) -> None:
        """Mark expense as paid."""
        if self.status != ExpenseStatus.APPROVED:
            raise ValueError(
                f"Cannot mark as paid - expense must be approved first (current: {self.status})"
            )

        self.status = ExpenseStatus.PAID
        self.paid_by_id = paid_by_id
        self.payment_method = payment_method
        self.paid_date = paid_date
        self.updated_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        """Cancel expense."""
        if self.status == ExpenseStatus.PAID:
            raise ValueError("Cannot cancel paid expense")

        self.status = ExpenseStatus.CANCELLED
        self.updated_at = datetime.now(timezone.utc)

    def is_overdue(self) -> bool:
        """Check if expense payment is overdue."""
        if self.status == ExpenseStatus.PAID or not self.due_date:
            return False

        return datetime.now().date() > self.due_date


@dataclass
class Budget:
    """Budget entity - monthly budget allocation per category."""

    # Required fields
    id: str
    category: ExpenseCategory
    month: date  # First day of month (2025-10-01)
    budgeted_amount: Decimal
    created_by_id: str

    # Optional fields with defaults
    spent_amount: Decimal = Decimal("0.00")
    alert_threshold_percent: Decimal = Decimal("80.00")  # Alert at 80% spent
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_remaining_amount(self) -> Decimal:
        """Calculate remaining budget."""
        return self.budgeted_amount - self.spent_amount

    def get_spent_percentage(self) -> Decimal:
        """Calculate percentage of budget spent."""
        if self.budgeted_amount == Decimal("0"):
            return Decimal("0")
        return (self.spent_amount / self.budgeted_amount) * Decimal("100")

    def is_over_budget(self) -> bool:
        """Check if spending exceeds budget."""
        return self.spent_amount > self.budgeted_amount

    def should_alert(self) -> bool:
        """Check if alert threshold reached."""
        return self.get_spent_percentage() >= self.alert_threshold_percent

    def add_expense(self, amount: Decimal) -> None:
        """Add expense to spent amount."""
        if amount < Decimal("0"):
            raise ValueError("Expense amount cannot be negative")

        self.spent_amount += amount
        self.updated_at = datetime.now(timezone.utc)

    def remove_expense(self, amount: Decimal) -> None:
        """Remove expense from spent amount (e.g., if expense cancelled)."""
        if amount < Decimal("0"):
            raise ValueError("Expense amount cannot be negative")

        self.spent_amount = max(Decimal("0"), self.spent_amount - amount)
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class ExpenseSummary:
    """Monthly expense summary by category."""

    category: ExpenseCategory
    month: date
    total_expenses: int  # Count
    total_amount: Decimal
    approved_amount: Decimal
    pending_amount: Decimal
    paid_amount: Decimal
    budgeted_amount: Decimal
    over_budget: bool
