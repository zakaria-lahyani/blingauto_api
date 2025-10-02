"""Expense repository implementations."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.expenses.domain.entities import Expense, Budget, ExpenseSummary
from app.features.expenses.domain.enums import (
    ExpenseCategory,
    ExpenseStatus,
    PaymentMethod,
    RecurrenceType,
)
from app.features.expenses.ports.repositories import IExpenseRepository, IBudgetRepository
from app.features.expenses.adapters.models import ExpenseModel, BudgetModel


class ExpenseRepository(IExpenseRepository):
    """Expense repository implementation using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self._session = session

    async def create(self, expense: Expense) -> Expense:
        """Create new expense."""
        model = self._to_model(expense)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def update(self, expense: Expense) -> Expense:
        """Update existing expense."""
        stmt = select(ExpenseModel).where(ExpenseModel.id == expense.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise LookupError(f"Expense {expense.id} not found")

        # Update fields
        model.category = expense.category.value
        model.amount = expense.amount
        model.description = expense.description
        model.status = expense.status.value
        model.payment_method = expense.payment_method.value if expense.payment_method else None
        model.expense_date = expense.expense_date
        model.due_date = expense.due_date
        model.paid_date = expense.paid_date
        model.approved_by_id = expense.approved_by_id
        model.paid_by_id = expense.paid_by_id
        model.vendor_name = expense.vendor_name
        model.vendor_id = expense.vendor_id
        model.receipt_url = expense.receipt_url
        model.notes = expense.notes
        model.approval_notes = expense.approval_notes
        model.rejection_reason = expense.rejection_reason
        model.recurrence_type = expense.recurrence_type.value
        model.parent_expense_id = expense.parent_expense_id
        model.updated_at = datetime.now(timezone.utc)

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, expense_id: str) -> Optional[Expense]:
        """Get expense by ID."""
        stmt = (
            select(ExpenseModel)
            .where(ExpenseModel.id == expense_id)
            .where(ExpenseModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_expense_number(self, expense_number: str) -> Optional[Expense]:
        """Get expense by expense number."""
        stmt = (
            select(ExpenseModel)
            .where(ExpenseModel.expense_number == expense_number)
            .where(ExpenseModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

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
        conditions = [ExpenseModel.deleted_at.is_(None)]

        if category:
            conditions.append(ExpenseModel.category == category.value)
        if status:
            conditions.append(ExpenseModel.status == status.value)
        if created_by_id:
            conditions.append(ExpenseModel.created_by_id == created_by_id)
        if start_date:
            conditions.append(ExpenseModel.expense_date >= start_date)
        if end_date:
            conditions.append(ExpenseModel.expense_date <= end_date)

        stmt = (
            select(ExpenseModel)
            .where(and_(*conditions))
            .order_by(ExpenseModel.expense_date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def list_pending_approval(self, limit: int = 100) -> List[Expense]:
        """List expenses pending approval."""
        stmt = (
            select(ExpenseModel)
            .where(
                and_(
                    ExpenseModel.deleted_at.is_(None),
                    ExpenseModel.status == ExpenseStatus.PENDING.value,
                )
            )
            .order_by(ExpenseModel.expense_date)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def list_overdue(self) -> List[Expense]:
        """List overdue expenses."""
        today = datetime.now().date()
        stmt = (
            select(ExpenseModel)
            .where(
                and_(
                    ExpenseModel.deleted_at.is_(None),
                    ExpenseModel.status != ExpenseStatus.PAID.value,
                    ExpenseModel.due_date.is_not(None),
                    ExpenseModel.due_date < today,
                )
            )
            .order_by(ExpenseModel.due_date)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def get_daily_count(self, expense_date: date) -> int:
        """Get count of expenses for a specific date."""
        date_str = expense_date.strftime("%Y%m%d")
        pattern = f"EXP-{date_str}-%"

        stmt = select(func.count()).where(
            ExpenseModel.expense_number.like(pattern)
        )
        result = await self._session.execute(stmt)
        count = result.scalar() or 0
        return count

    async def get_monthly_summary(self, month: date) -> List[ExpenseSummary]:
        """Get monthly expense summary by category."""
        # Calculate month range
        start_date = month.replace(day=1)
        if month.month == 12:
            end_date = date(month.year + 1, 1, 1)
        else:
            end_date = date(month.year, month.month + 1, 1)

        # Query for each category
        stmt = select(
            ExpenseModel.category,
            func.count().label("total_expenses"),
            func.sum(ExpenseModel.amount).label("total_amount"),
            func.sum(
                func.case(
                    (ExpenseModel.status == ExpenseStatus.APPROVED.value, ExpenseModel.amount),
                    else_=0
                )
            ).label("approved_amount"),
            func.sum(
                func.case(
                    (ExpenseModel.status == ExpenseStatus.PENDING.value, ExpenseModel.amount),
                    else_=0
                )
            ).label("pending_amount"),
            func.sum(
                func.case(
                    (ExpenseModel.status == ExpenseStatus.PAID.value, ExpenseModel.amount),
                    else_=0
                )
            ).label("paid_amount"),
        ).where(
            and_(
                ExpenseModel.deleted_at.is_(None),
                ExpenseModel.expense_date >= start_date,
                ExpenseModel.expense_date < end_date,
            )
        ).group_by(ExpenseModel.category)

        result = await self._session.execute(stmt)
        rows = result.all()

        # Get budgets for the month
        budget_repo = BudgetRepository(self._session)
        budgets = await budget_repo.list_by_month(month)
        budget_map = {b.category: b for b in budgets}

        summaries = []
        for row in rows:
            category = ExpenseCategory(row.category)
            budget = budget_map.get(category)

            summaries.append(
                ExpenseSummary(
                    category=category,
                    month=month,
                    total_expenses=row.total_expenses or 0,
                    total_amount=row.total_amount or Decimal("0"),
                    approved_amount=row.approved_amount or Decimal("0"),
                    pending_amount=row.pending_amount or Decimal("0"),
                    paid_amount=row.paid_amount or Decimal("0"),
                    budgeted_amount=budget.budgeted_amount if budget else Decimal("0"),
                    over_budget=budget.is_over_budget() if budget else False,
                )
            )

        return summaries

    async def delete(self, expense_id: str) -> None:
        """Soft delete expense."""
        stmt = select(ExpenseModel).where(ExpenseModel.id == expense_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.deleted_at = datetime.now(timezone.utc)
            await self._session.flush()

    def _to_domain(self, model: ExpenseModel) -> Expense:
        """Convert model to domain entity."""
        return Expense(
            id=model.id,
            expense_number=model.expense_number,
            category=ExpenseCategory(model.category),
            amount=model.amount,
            description=model.description,
            status=ExpenseStatus(model.status),
            payment_method=PaymentMethod(model.payment_method) if model.payment_method else None,
            expense_date=model.expense_date,
            due_date=model.due_date,
            paid_date=model.paid_date,
            created_by_id=model.created_by_id,
            approved_by_id=model.approved_by_id,
            paid_by_id=model.paid_by_id,
            vendor_name=model.vendor_name,
            vendor_id=model.vendor_id,
            receipt_url=model.receipt_url,
            notes=model.notes,
            approval_notes=model.approval_notes,
            rejection_reason=model.rejection_reason,
            recurrence_type=RecurrenceType(model.recurrence_type),
            parent_expense_id=model.parent_expense_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, expense: Expense) -> ExpenseModel:
        """Convert domain entity to model."""
        return ExpenseModel(
            id=expense.id,
            expense_number=expense.expense_number,
            category=expense.category.value,
            amount=expense.amount,
            description=expense.description,
            status=expense.status.value,
            payment_method=expense.payment_method.value if expense.payment_method else None,
            expense_date=expense.expense_date,
            due_date=expense.due_date,
            paid_date=expense.paid_date,
            created_by_id=expense.created_by_id,
            approved_by_id=expense.approved_by_id,
            paid_by_id=expense.paid_by_id,
            vendor_name=expense.vendor_name,
            vendor_id=expense.vendor_id,
            receipt_url=expense.receipt_url,
            notes=expense.notes,
            approval_notes=expense.approval_notes,
            rejection_reason=expense.rejection_reason,
            recurrence_type=expense.recurrence_type.value,
            parent_expense_id=expense.parent_expense_id,
            created_at=expense.created_at,
            updated_at=expense.updated_at,
        )


class BudgetRepository(IBudgetRepository):
    """Budget repository implementation using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self._session = session

    async def create(self, budget: Budget) -> Budget:
        """Create budget."""
        model = self._to_model(budget)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def update(self, budget: Budget) -> Budget:
        """Update budget."""
        stmt = select(BudgetModel).where(BudgetModel.id == budget.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise LookupError(f"Budget {budget.id} not found")

        model.budgeted_amount = budget.budgeted_amount
        model.spent_amount = budget.spent_amount
        model.alert_threshold_percent = budget.alert_threshold_percent
        model.notes = budget.notes
        model.updated_at = datetime.now(timezone.utc)

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, budget_id: str) -> Optional[Budget]:
        """Get budget by ID."""
        stmt = select(BudgetModel).where(BudgetModel.id == budget_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_category_and_month(
        self, category: ExpenseCategory, month: date
    ) -> Optional[Budget]:
        """Get budget for specific category and month."""
        stmt = select(BudgetModel).where(
            and_(
                BudgetModel.category == category.value,
                BudgetModel.month == month,
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_month(self, month: date) -> List[Budget]:
        """List all budgets for a specific month."""
        stmt = (
            select(BudgetModel)
            .where(BudgetModel.month == month)
            .order_by(BudgetModel.category)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def list_over_budget(self, month: date) -> List[Budget]:
        """List budgets that are over budget for a month."""
        stmt = (
            select(BudgetModel)
            .where(
                and_(
                    BudgetModel.month == month,
                    BudgetModel.spent_amount > BudgetModel.budgeted_amount,
                )
            )
            .order_by(BudgetModel.category)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def delete(self, budget_id: str) -> None:
        """Delete budget."""
        stmt = select(BudgetModel).where(BudgetModel.id == budget_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            await self._session.delete(model)
            await self._session.flush()

    def _to_domain(self, model: BudgetModel) -> Budget:
        """Convert model to domain entity."""
        return Budget(
            id=model.id,
            category=ExpenseCategory(model.category),
            month=model.month,
            budgeted_amount=model.budgeted_amount,
            spent_amount=model.spent_amount,
            alert_threshold_percent=model.alert_threshold_percent,
            created_by_id=model.created_by_id,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, budget: Budget) -> BudgetModel:
        """Convert domain entity to model."""
        return BudgetModel(
            id=budget.id,
            category=budget.category.value,
            month=budget.month,
            budgeted_amount=budget.budgeted_amount,
            spent_amount=budget.spent_amount,
            alert_threshold_percent=budget.alert_threshold_percent,
            created_by_id=budget.created_by_id,
            notes=budget.notes,
            created_at=budget.created_at,
            updated_at=budget.updated_at,
        )
