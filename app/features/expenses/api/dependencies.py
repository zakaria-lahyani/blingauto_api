"""Expense API dependencies - Dependency injection setup."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_session
from app.features.expenses.adapters.repositories import (
    ExpenseRepository,
    BudgetRepository,
)
from app.features.expenses.use_cases.create_expense import CreateExpenseUseCase
from app.features.expenses.use_cases.update_expense import UpdateExpenseUseCase
from app.features.expenses.use_cases.get_expense import GetExpenseUseCase
from app.features.expenses.use_cases.list_expenses import ListExpensesUseCase
from app.features.expenses.use_cases.approve_expense import ApproveExpenseUseCase
from app.features.expenses.use_cases.reject_expense import RejectExpenseUseCase
from app.features.expenses.use_cases.mark_expense_as_paid import MarkExpenseAsPaidUseCase
from app.features.expenses.use_cases.cancel_expense import CancelExpenseUseCase
from app.features.expenses.use_cases.create_budget import CreateBudgetUseCase
from app.features.expenses.use_cases.update_budget import UpdateBudgetUseCase
from app.features.expenses.use_cases.get_budget import GetBudgetUseCase
from app.features.expenses.use_cases.list_budgets import ListBudgetsUseCase
from app.features.expenses.use_cases.delete_budget import DeleteBudgetUseCase
from app.features.expenses.use_cases.get_monthly_summary import GetMonthlySummaryUseCase


# ============================================================================
# Repository Factories
# ============================================================================

def get_expense_repository(
    session: Annotated[AsyncSession, Depends(get_session)]
) -> ExpenseRepository:
    """Get expense repository instance."""
    return ExpenseRepository(session)


def get_budget_repository(
    session: Annotated[AsyncSession, Depends(get_session)]
) -> BudgetRepository:
    """Get budget repository instance."""
    return BudgetRepository(session)


# ============================================================================
# Expense Use Case Factories
# ============================================================================

def get_create_expense_use_case(
    expense_repo: Annotated[ExpenseRepository, Depends(get_expense_repository)]
) -> CreateExpenseUseCase:
    """Get create expense use case instance."""
    return CreateExpenseUseCase(expense_repo)


def get_update_expense_use_case(
    expense_repo: Annotated[ExpenseRepository, Depends(get_expense_repository)]
) -> UpdateExpenseUseCase:
    """Get update expense use case instance."""
    return UpdateExpenseUseCase(expense_repo)


def get_get_expense_use_case(
    expense_repo: Annotated[ExpenseRepository, Depends(get_expense_repository)]
) -> GetExpenseUseCase:
    """Get expense by ID use case instance."""
    return GetExpenseUseCase(expense_repo)


def get_list_expenses_use_case(
    expense_repo: Annotated[ExpenseRepository, Depends(get_expense_repository)]
) -> ListExpensesUseCase:
    """Get list expenses use case instance."""
    return ListExpensesUseCase(expense_repo)


def get_approve_expense_use_case(
    expense_repo: Annotated[ExpenseRepository, Depends(get_expense_repository)],
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)]
) -> ApproveExpenseUseCase:
    """Get approve expense use case instance."""
    return ApproveExpenseUseCase(expense_repo, budget_repo)


def get_reject_expense_use_case(
    expense_repo: Annotated[ExpenseRepository, Depends(get_expense_repository)]
) -> RejectExpenseUseCase:
    """Get reject expense use case instance."""
    return RejectExpenseUseCase(expense_repo)


def get_mark_expense_as_paid_use_case(
    expense_repo: Annotated[ExpenseRepository, Depends(get_expense_repository)]
) -> MarkExpenseAsPaidUseCase:
    """Get mark expense as paid use case instance."""
    return MarkExpenseAsPaidUseCase(expense_repo)


def get_cancel_expense_use_case(
    expense_repo: Annotated[ExpenseRepository, Depends(get_expense_repository)],
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)]
) -> CancelExpenseUseCase:
    """Get cancel expense use case instance."""
    return CancelExpenseUseCase(expense_repo, budget_repo)


# ============================================================================
# Budget Use Case Factories
# ============================================================================

def get_create_budget_use_case(
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)]
) -> CreateBudgetUseCase:
    """Get create budget use case instance."""
    return CreateBudgetUseCase(budget_repo)


def get_update_budget_use_case(
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)]
) -> UpdateBudgetUseCase:
    """Get update budget use case instance."""
    return UpdateBudgetUseCase(budget_repo)


def get_get_budget_use_case(
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)]
) -> GetBudgetUseCase:
    """Get budget by ID use case instance."""
    return GetBudgetUseCase(budget_repo)


def get_list_budgets_use_case(
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)]
) -> ListBudgetsUseCase:
    """Get list budgets use case instance."""
    return ListBudgetsUseCase(budget_repo)


def get_delete_budget_use_case(
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)]
) -> DeleteBudgetUseCase:
    """Get delete budget use case instance."""
    return DeleteBudgetUseCase(budget_repo)


# ============================================================================
# Report Use Case Factories
# ============================================================================

def get_monthly_summary_use_case(
    expense_repo: Annotated[ExpenseRepository, Depends(get_expense_repository)]
) -> GetMonthlySummaryUseCase:
    """Get monthly summary use case instance."""
    return GetMonthlySummaryUseCase(expense_repo)
