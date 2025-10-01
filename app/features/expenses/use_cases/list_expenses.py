"""List expenses use case."""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from app.features.expenses.domain.entities import Expense
from app.features.expenses.domain.enums import ExpenseCategory, ExpenseStatus
from app.features.expenses.ports.repositories import IExpenseRepository


@dataclass
class ListExpensesRequest:
    """Request to list expenses."""

    category: Optional[ExpenseCategory] = None
    status: Optional[ExpenseStatus] = None
    created_by_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: int = 100
    offset: int = 0


class ListExpensesUseCase:
    """Use case for listing expenses with filters."""

    def __init__(self, repository: IExpenseRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: ListExpensesRequest) -> List[Expense]:
        """List expenses."""
        if request.limit < 1 or request.limit > 200:
            raise ValueError("Limit must be between 1 and 200")
        if request.offset < 0:
            raise ValueError("Offset cannot be negative")

        return await self._repository.list_all(
            category=request.category,
            status=request.status,
            created_by_id=request.created_by_id,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit,
            offset=request.offset,
        )
