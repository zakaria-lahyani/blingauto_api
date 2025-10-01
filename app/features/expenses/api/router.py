"""Expense API router - REST endpoints."""

from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth.dependencies import get_current_user_id, require_any_role
from app.features.auth.domain.enums import UserRole
from app.features.expenses.api.dependencies import (
    get_create_expense_use_case,
    get_update_expense_use_case,
    get_get_expense_use_case,
    get_list_expenses_use_case,
    get_approve_expense_use_case,
    get_reject_expense_use_case,
    get_mark_expense_as_paid_use_case,
    get_cancel_expense_use_case,
    get_create_budget_use_case,
    get_update_budget_use_case,
    get_get_budget_use_case,
    get_list_budgets_use_case,
    get_delete_budget_use_case,
    get_monthly_summary_use_case,
)
from app.features.expenses.api.schemas import (
    CreateExpenseSchema,
    UpdateExpenseSchema,
    ApproveExpenseSchema,
    RejectExpenseSchema,
    MarkExpenseAsPaidSchema,
    ExpenseSchema,
    ExpenseListSchema,
    CreateBudgetSchema,
    UpdateBudgetSchema,
    BudgetSchema,
    BudgetListSchema,
    MonthlySummarySchema,
    ExpenseSummarySchema,
)
from app.features.expenses.domain.enums import ExpenseCategory, ExpenseStatus
from app.features.expenses.use_cases.create_expense import CreateExpenseRequest
from app.features.expenses.use_cases.update_expense import UpdateExpenseRequest
from app.features.expenses.use_cases.get_expense import GetExpenseRequest
from app.features.expenses.use_cases.list_expenses import ListExpensesRequest
from app.features.expenses.use_cases.approve_expense import ApproveExpenseRequest
from app.features.expenses.use_cases.reject_expense import RejectExpenseRequest
from app.features.expenses.use_cases.mark_expense_as_paid import MarkExpenseAsPaidRequest
from app.features.expenses.use_cases.cancel_expense import CancelExpenseRequest
from app.features.expenses.use_cases.create_budget import CreateBudgetRequest
from app.features.expenses.use_cases.update_budget import UpdateBudgetRequest
from app.features.expenses.use_cases.get_budget import GetBudgetRequest
from app.features.expenses.use_cases.list_budgets import ListBudgetsRequest
from app.features.expenses.use_cases.delete_budget import DeleteBudgetRequest
from app.features.expenses.use_cases.get_monthly_summary import GetMonthlySummaryRequest


router = APIRouter()


# ============================================================================
# Expense Endpoints
# ============================================================================

@router.post(
    "/expenses",
    response_model=ExpenseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def create_expense(
    data: CreateExpenseSchema,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    use_case: Annotated[object, Depends(get_create_expense_use_case)],
) -> ExpenseSchema:
    """Create new expense."""
    request = CreateExpenseRequest(
        category=data.category,
        amount=data.amount,
        description=data.description,
        created_by_id=current_user_id,
        payment_method=data.payment_method,
        expense_date=data.expense_date,
        due_date=data.due_date,
        vendor_name=data.vendor_name,
        vendor_id=data.vendor_id,
        receipt_url=data.receipt_url,
        notes=data.notes,
        recurrence_type=data.recurrence_type,
        parent_expense_id=data.parent_expense_id,
    )

    expense = await use_case.execute(request)

    return ExpenseSchema(
        id=expense.id,
        expense_number=expense.expense_number,
        category=expense.category,
        amount=expense.amount,
        description=expense.description,
        status=expense.status,
        payment_method=expense.payment_method,
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
        recurrence_type=expense.recurrence_type,
        parent_expense_id=expense.parent_expense_id,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


@router.put(
    "/expenses/{expense_id}",
    response_model=ExpenseSchema,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def update_expense(
    expense_id: str,
    data: UpdateExpenseSchema,
    use_case: Annotated[object, Depends(get_update_expense_use_case)],
) -> ExpenseSchema:
    """Update expense details."""
    request = UpdateExpenseRequest(
        expense_id=expense_id,
        category=data.category,
        amount=data.amount,
        description=data.description,
        payment_method=data.payment_method,
        expense_date=data.expense_date,
        due_date=data.due_date,
        vendor_name=data.vendor_name,
        vendor_id=data.vendor_id,
        receipt_url=data.receipt_url,
        notes=data.notes,
    )

    try:
        expense = await use_case.execute(request)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return ExpenseSchema(
        id=expense.id,
        expense_number=expense.expense_number,
        category=expense.category,
        amount=expense.amount,
        description=expense.description,
        status=expense.status,
        payment_method=expense.payment_method,
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
        recurrence_type=expense.recurrence_type,
        parent_expense_id=expense.parent_expense_id,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


@router.get(
    "/expenses/{expense_id}",
    response_model=ExpenseSchema,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def get_expense(
    expense_id: str,
    use_case: Annotated[object, Depends(get_get_expense_use_case)],
) -> ExpenseSchema:
    """Get expense by ID."""
    request = GetExpenseRequest(expense_id=expense_id)
    expense = await use_case.execute(request)

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense {expense_id} not found",
        )

    return ExpenseSchema(
        id=expense.id,
        expense_number=expense.expense_number,
        category=expense.category,
        amount=expense.amount,
        description=expense.description,
        status=expense.status,
        payment_method=expense.payment_method,
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
        recurrence_type=expense.recurrence_type,
        parent_expense_id=expense.parent_expense_id,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


@router.get(
    "/expenses",
    response_model=ExpenseListSchema,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def list_expenses(
    category: Optional[ExpenseCategory] = Query(None),
    status: Optional[ExpenseStatus] = Query(None),
    created_by_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    use_case: Annotated[object, Depends(get_list_expenses_use_case)] = None,
) -> ExpenseListSchema:
    """List expenses with filters."""
    request = ListExpensesRequest(
        category=category,
        status=status,
        created_by_id=created_by_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    expenses = await use_case.execute(request)

    items = [
        ExpenseSchema(
            id=e.id,
            expense_number=e.expense_number,
            category=e.category,
            amount=e.amount,
            description=e.description,
            status=e.status,
            payment_method=e.payment_method,
            expense_date=e.expense_date,
            due_date=e.due_date,
            paid_date=e.paid_date,
            created_by_id=e.created_by_id,
            approved_by_id=e.approved_by_id,
            paid_by_id=e.paid_by_id,
            vendor_name=e.vendor_name,
            vendor_id=e.vendor_id,
            receipt_url=e.receipt_url,
            notes=e.notes,
            approval_notes=e.approval_notes,
            rejection_reason=e.rejection_reason,
            recurrence_type=e.recurrence_type,
            parent_expense_id=e.parent_expense_id,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )
        for e in expenses
    ]

    return ExpenseListSchema(items=items, total=len(items))


@router.post(
    "/expenses/{expense_id}/approve",
    response_model=ExpenseSchema,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def approve_expense(
    expense_id: str,
    data: ApproveExpenseSchema,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    use_case: Annotated[object, Depends(get_approve_expense_use_case)],
) -> ExpenseSchema:
    """Approve expense."""
    request = ApproveExpenseRequest(
        expense_id=expense_id,
        approved_by_id=current_user_id,
        approval_notes=data.approval_notes,
    )

    try:
        expense = await use_case.execute(request)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ExpenseSchema(
        id=expense.id,
        expense_number=expense.expense_number,
        category=expense.category,
        amount=expense.amount,
        description=expense.description,
        status=expense.status,
        payment_method=expense.payment_method,
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
        recurrence_type=expense.recurrence_type,
        parent_expense_id=expense.parent_expense_id,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


@router.post(
    "/expenses/{expense_id}/reject",
    response_model=ExpenseSchema,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def reject_expense(
    expense_id: str,
    data: RejectExpenseSchema,
    use_case: Annotated[object, Depends(get_reject_expense_use_case)],
) -> ExpenseSchema:
    """Reject expense."""
    request = RejectExpenseRequest(
        expense_id=expense_id,
        rejection_reason=data.rejection_reason,
    )

    try:
        expense = await use_case.execute(request)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ExpenseSchema(
        id=expense.id,
        expense_number=expense.expense_number,
        category=expense.category,
        amount=expense.amount,
        description=expense.description,
        status=expense.status,
        payment_method=expense.payment_method,
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
        recurrence_type=expense.recurrence_type,
        parent_expense_id=expense.parent_expense_id,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


@router.post(
    "/expenses/{expense_id}/mark-paid",
    response_model=ExpenseSchema,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def mark_expense_as_paid(
    expense_id: str,
    data: MarkExpenseAsPaidSchema,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    use_case: Annotated[object, Depends(get_mark_expense_as_paid_use_case)],
) -> ExpenseSchema:
    """Mark expense as paid."""
    request = MarkExpenseAsPaidRequest(
        expense_id=expense_id,
        paid_date=data.paid_date,
        payment_method=data.payment_method,
        paid_by_id=current_user_id,
        notes=data.notes,
    )

    try:
        expense = await use_case.execute(request)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ExpenseSchema(
        id=expense.id,
        expense_number=expense.expense_number,
        category=expense.category,
        amount=expense.amount,
        description=expense.description,
        status=expense.status,
        payment_method=expense.payment_method,
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
        recurrence_type=expense.recurrence_type,
        parent_expense_id=expense.parent_expense_id,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


@router.post(
    "/expenses/{expense_id}/cancel",
    response_model=ExpenseSchema,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def cancel_expense(
    expense_id: str,
    use_case: Annotated[object, Depends(get_cancel_expense_use_case)],
) -> ExpenseSchema:
    """Cancel expense."""
    request = CancelExpenseRequest(expense_id=expense_id)

    try:
        expense = await use_case.execute(request)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ExpenseSchema(
        id=expense.id,
        expense_number=expense.expense_number,
        category=expense.category,
        amount=expense.amount,
        description=expense.description,
        status=expense.status,
        payment_method=expense.payment_method,
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
        recurrence_type=expense.recurrence_type,
        parent_expense_id=expense.parent_expense_id,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


# ============================================================================
# Budget Endpoints
# ============================================================================

@router.post(
    "/budgets",
    response_model=BudgetSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def create_budget(
    data: CreateBudgetSchema,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    use_case: Annotated[object, Depends(get_create_budget_use_case)],
) -> BudgetSchema:
    """Create new budget."""
    request = CreateBudgetRequest(
        category=data.category,
        month=data.month,
        budgeted_amount=data.budgeted_amount,
        alert_threshold_percent=data.alert_threshold_percent,
        created_by_id=current_user_id,
        notes=data.notes,
    )

    try:
        budget = await use_case.execute(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return BudgetSchema(
        id=budget.id,
        category=budget.category,
        month=budget.month,
        budgeted_amount=budget.budgeted_amount,
        spent_amount=budget.spent_amount,
        remaining_amount=budget.get_remaining_amount(),
        utilization_percent=budget.get_utilization_percent(),
        is_over_budget=budget.is_over_budget(),
        alert_threshold_percent=budget.alert_threshold_percent,
        created_by_id=budget.created_by_id,
        notes=budget.notes,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
    )


@router.put(
    "/budgets/{budget_id}",
    response_model=BudgetSchema,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def update_budget(
    budget_id: str,
    data: UpdateBudgetSchema,
    use_case: Annotated[object, Depends(get_update_budget_use_case)],
) -> BudgetSchema:
    """Update budget."""
    request = UpdateBudgetRequest(
        budget_id=budget_id,
        budgeted_amount=data.budgeted_amount,
        alert_threshold_percent=data.alert_threshold_percent,
        notes=data.notes,
    )

    try:
        budget = await use_case.execute(request)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return BudgetSchema(
        id=budget.id,
        category=budget.category,
        month=budget.month,
        budgeted_amount=budget.budgeted_amount,
        spent_amount=budget.spent_amount,
        remaining_amount=budget.get_remaining_amount(),
        utilization_percent=budget.get_utilization_percent(),
        is_over_budget=budget.is_over_budget(),
        alert_threshold_percent=budget.alert_threshold_percent,
        created_by_id=budget.created_by_id,
        notes=budget.notes,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
    )


@router.get(
    "/budgets/{budget_id}",
    response_model=BudgetSchema,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def get_budget(
    budget_id: str,
    use_case: Annotated[object, Depends(get_get_budget_use_case)],
) -> BudgetSchema:
    """Get budget by ID."""
    request = GetBudgetRequest(budget_id=budget_id)
    budget = await use_case.execute(request)

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget {budget_id} not found",
        )

    return BudgetSchema(
        id=budget.id,
        category=budget.category,
        month=budget.month,
        budgeted_amount=budget.budgeted_amount,
        spent_amount=budget.spent_amount,
        remaining_amount=budget.get_remaining_amount(),
        utilization_percent=budget.get_utilization_percent(),
        is_over_budget=budget.is_over_budget(),
        alert_threshold_percent=budget.alert_threshold_percent,
        created_by_id=budget.created_by_id,
        notes=budget.notes,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
    )


@router.get(
    "/budgets",
    response_model=BudgetListSchema,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def list_budgets(
    category: Optional[ExpenseCategory] = Query(None),
    month: Optional[date] = Query(None),
    over_budget_only: bool = Query(False),
    use_case: Annotated[object, Depends(get_list_budgets_use_case)] = None,
) -> BudgetListSchema:
    """List budgets with filters."""
    request = ListBudgetsRequest(
        category=category,
        month=month,
        over_budget_only=over_budget_only,
    )

    budgets = await use_case.execute(request)

    items = [
        BudgetSchema(
            id=b.id,
            category=b.category,
            month=b.month,
            budgeted_amount=b.budgeted_amount,
            spent_amount=b.spent_amount,
            remaining_amount=b.get_remaining_amount(),
            utilization_percent=b.get_utilization_percent(),
            is_over_budget=b.is_over_budget(),
            alert_threshold_percent=b.alert_threshold_percent,
            created_by_id=b.created_by_id,
            notes=b.notes,
            created_at=b.created_at,
            updated_at=b.updated_at,
        )
        for b in budgets
    ]

    return BudgetListSchema(items=items, total=len(items))


@router.delete(
    "/budgets/{budget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value))],
)
async def delete_budget(
    budget_id: str,
    use_case: Annotated[object, Depends(get_delete_budget_use_case)],
) -> None:
    """Delete budget."""
    request = DeleteBudgetRequest(budget_id=budget_id)
    await use_case.execute(request)


# ============================================================================
# Report Endpoints
# ============================================================================

@router.get(
    "/reports/monthly-summary",
    response_model=MonthlySummarySchema,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def get_monthly_summary(
    month: date = Query(...),
    use_case: Annotated[object, Depends(get_monthly_summary_use_case)] = None,
) -> MonthlySummarySchema:
    """Get monthly expense summary."""
    # Ensure month is first day of month
    month = month.replace(day=1)

    request = GetMonthlySummaryRequest(month=month)
    summaries = await use_case.execute(request)

    summary_items = [
        ExpenseSummarySchema(
            category=s.category,
            month=s.month,
            total_expenses=s.total_expenses,
            total_amount=s.total_amount,
            approved_amount=s.approved_amount,
            pending_amount=s.pending_amount,
            paid_amount=s.paid_amount,
            budgeted_amount=s.budgeted_amount,
            over_budget=s.over_budget,
            utilization_percent=int((s.total_amount / s.budgeted_amount * 100) if s.budgeted_amount > 0 else 0),
        )
        for s in summaries
    ]

    # Calculate totals
    from decimal import Decimal
    total_expenses = sum(s.total_expenses for s in summaries)
    total_amount = sum(s.total_amount for s in summaries)
    total_approved = sum(s.approved_amount for s in summaries)
    total_pending = sum(s.pending_amount for s in summaries)
    total_paid = sum(s.paid_amount for s in summaries)
    total_budgeted = sum(s.budgeted_amount for s in summaries)

    return MonthlySummarySchema(
        month=month,
        summaries=summary_items,
        total_expenses=total_expenses,
        total_amount=total_amount,
        total_approved=total_approved,
        total_pending=total_pending,
        total_paid=total_paid,
        total_budgeted=total_budgeted,
    )
