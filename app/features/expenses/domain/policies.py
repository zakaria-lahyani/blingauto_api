"""Expense domain policies - Business rules."""

from decimal import Decimal
from datetime import date


class ExpenseManagementPolicy:
    """Business rules for expense management."""

    # Expense number generation
    EXPENSE_NUMBER_PREFIX = "EXP"

    # Amount limits
    MIN_AMOUNT = Decimal("0.01")
    MAX_AMOUNT = Decimal("999999.99")

    # Approval requirements
    AUTO_APPROVE_THRESHOLD = Decimal("100.00")  # Auto-approve if <= $100
    MANAGER_APPROVAL_THRESHOLD = Decimal("1000.00")  # Manager can approve up to $1000
    # Above $1000 requires Admin approval

    @staticmethod
    def generate_expense_number(expense_date: date, daily_count: int) -> str:
        """
        Generate expense number.

        Format: EXP-20251002-001, EXP-20251002-002, etc.

        Args:
            expense_date: Date of expense
            daily_count: Count of expenses for that day

        Returns:
            Expense number
        """
        date_str = expense_date.strftime("%Y%m%d")
        return f"{ExpenseManagementPolicy.EXPENSE_NUMBER_PREFIX}-{date_str}-{daily_count + 1:03d}"

    @staticmethod
    def validate_amount(amount: Decimal) -> None:
        """
        Validate expense amount.

        Args:
            amount: Expense amount

        Raises:
            ValueError: If validation fails
        """
        if amount < ExpenseManagementPolicy.MIN_AMOUNT:
            raise ValueError(
                f"Expense amount must be >= {ExpenseManagementPolicy.MIN_AMOUNT}"
            )

        if amount > ExpenseManagementPolicy.MAX_AMOUNT:
            raise ValueError(
                f"Expense amount cannot exceed {ExpenseManagementPolicy.MAX_AMOUNT}"
            )

    @staticmethod
    def requires_approval(amount: Decimal) -> bool:
        """
        Check if expense requires manual approval.

        Args:
            amount: Expense amount

        Returns:
            True if manual approval required
        """
        return amount > ExpenseManagementPolicy.AUTO_APPROVE_THRESHOLD

    @staticmethod
    def requires_admin_approval(amount: Decimal) -> bool:
        """
        Check if expense requires admin approval.

        Args:
            amount: Expense amount

        Returns:
            True if admin approval required
        """
        return amount > ExpenseManagementPolicy.MANAGER_APPROVAL_THRESHOLD

    @staticmethod
    def validate_due_date(expense_date: date, due_date: date) -> None:
        """
        Validate due date is after expense date.

        Args:
            expense_date: Expense date
            due_date: Payment due date

        Raises:
            ValueError: If validation fails
        """
        if due_date < expense_date:
            raise ValueError("Due date cannot be before expense date")


class BudgetManagementPolicy:
    """Business rules for budget management."""

    # Budget limits
    MIN_BUDGET = Decimal("0.01")
    MAX_BUDGET = Decimal("9999999.99")

    # Alert thresholds
    DEFAULT_ALERT_THRESHOLD = Decimal("80.00")  # 80%
    MIN_ALERT_THRESHOLD = Decimal("50.00")  # 50%
    MAX_ALERT_THRESHOLD = Decimal("100.00")  # 100%

    @staticmethod
    def validate_budget_amount(amount: Decimal) -> None:
        """
        Validate budget amount.

        Args:
            amount: Budget amount

        Raises:
            ValueError: If validation fails
        """
        if amount < BudgetManagementPolicy.MIN_BUDGET:
            raise ValueError(
                f"Budget amount must be >= {BudgetManagementPolicy.MIN_BUDGET}"
            )

        if amount > BudgetManagementPolicy.MAX_BUDGET:
            raise ValueError(
                f"Budget amount cannot exceed {BudgetManagementPolicy.MAX_BUDGET}"
            )

    @staticmethod
    def validate_alert_threshold(threshold_percent: Decimal) -> None:
        """
        Validate alert threshold percentage.

        Args:
            threshold_percent: Alert threshold (0-100)

        Raises:
            ValueError: If validation fails
        """
        if threshold_percent < BudgetManagementPolicy.MIN_ALERT_THRESHOLD:
            raise ValueError(
                f"Alert threshold must be >= {BudgetManagementPolicy.MIN_ALERT_THRESHOLD}%"
            )

        if threshold_percent > BudgetManagementPolicy.MAX_ALERT_THRESHOLD:
            raise ValueError(
                f"Alert threshold cannot exceed {BudgetManagementPolicy.MAX_ALERT_THRESHOLD}%"
            )

    @staticmethod
    def calculate_recommended_budget(
        previous_month_spent: Decimal, growth_percent: Decimal = Decimal("10.00")
    ) -> Decimal:
        """
        Calculate recommended budget based on previous spending.

        Args:
            previous_month_spent: Amount spent in previous month
            growth_percent: Growth percentage (default 10%)

        Returns:
            Recommended budget amount
        """
        if previous_month_spent <= Decimal("0"):
            return Decimal("0")

        return previous_month_spent * (Decimal("1") + growth_percent / Decimal("100"))
