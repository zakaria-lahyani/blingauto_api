"""Expense repository interfaces."""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from app.features.expenses.domain.entities import Expense, Budget, ExpenseSummary
from app.features.expenses.domain.enums import ExpenseCategory, ExpenseStatus


class IExpenseRepository(ABC):
    """Expense repository interface."""

    @abstractmethod
    async def create(self, expense: Expense) -> Expense:
        """Create new expense."""
        pass

    @abstractmethod
    async def update(self, expense: Expense) -> Expense:
        """Update existing expense."""
        pass

    @abstractmethod
    async def get_by_id(self, expense_id: str) -> Optional[Expense]:
        """Get expense by ID."""
        pass

    @abstractmethod
    async def get_by_expense_number(self, expense_number: str) -> Optional[Expense]:
        """Get expense by expense number."""
        pass

    @abstractmethod
    async def list_all(
        self,
        category: Optional[ExpenseCategory] = None,
        status: Optional[ExpenseStatus] = None,
        created_by_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Expense]:
        """List expenses with filters."""
        pass

    @abstractmethod
    async def list_pending_approval(self, limit: int = 100) -> List[Expense]:
        """List expenses pending approval."""
        pass

    @abstractmethod
    async def list_overdue(self) -> List[Expense]:
        """List overdue expenses (unpaid past due date)."""
        pass

    @abstractmethod
    async def get_daily_count(self, expense_date: date) -> int:
        """Get count of expenses for a specific date (for number generation)."""
        pass

    @abstractmethod
    async def get_monthly_summary(self, month: date) -> List[ExpenseSummary]:
        """Get monthly expense summary by category."""
        pass

    @abstractmethod
    async def delete(self, expense_id: str) -> None:
        """Soft delete expense."""
        pass


class IBudgetRepository(ABC):
    """Budget repository interface."""

    @abstractmethod
    async def create(self, budget: Budget) -> Budget:
        """Create budget."""
        pass

    @abstractmethod
    async def update(self, budget: Budget) -> Budget:
        """Update budget."""
        pass

    @abstractmethod
    async def get_by_id(self, budget_id: str) -> Optional[Budget]:
        """Get budget by ID."""
        pass

    @abstractmethod
    async def get_by_category_and_month(
        self, category: ExpenseCategory, month: date
    ) -> Optional[Budget]:
        """Get budget for specific category and month."""
        pass

    @abstractmethod
    async def list_by_month(self, month: date) -> List[Budget]:
        """List all budgets for a specific month."""
        pass

    @abstractmethod
    async def list_over_budget(self, month: date) -> List[Budget]:
        """List budgets that are over budget for a month."""
        pass

    @abstractmethod
    async def delete(self, budget_id: str) -> None:
        """Delete budget."""
        pass
