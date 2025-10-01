"""Expense domain enums."""

from enum import Enum


class ExpenseCategory(str, Enum):
    """Expense categories for business spending."""

    SUPPLIES = "SUPPLIES"  # Cleaning supplies, consumables
    UTILITIES = "UTILITIES"  # Water, electricity, gas
    MAINTENANCE = "MAINTENANCE"  # Equipment repairs, facility upkeep
    SALARIES = "SALARIES"  # Staff wages, benefits
    RENT = "RENT"  # Facility rent/lease
    EQUIPMENT = "EQUIPMENT"  # Equipment purchases
    MARKETING = "MARKETING"  # Advertising, promotions
    INSURANCE = "INSURANCE"  # Business insurance
    TAXES = "TAXES"  # Business taxes, fees
    FUEL = "FUEL"  # Vehicle fuel for mobile teams
    OTHER = "OTHER"  # Miscellaneous expenses


class ExpenseStatus(str, Enum):
    """Expense approval and payment status."""

    PENDING = "PENDING"  # Awaiting approval
    APPROVED = "APPROVED"  # Approved but not paid
    REJECTED = "REJECTED"  # Rejected by approver
    PAID = "PAID"  # Approved and paid
    CANCELLED = "CANCELLED"  # Cancelled before payment


class PaymentMethod(str, Enum):
    """Payment methods for expenses."""

    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    CHECK = "CHECK"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    MOBILE_MONEY = "MOBILE_MONEY"


class RecurrenceType(str, Enum):
    """Recurrence frequency for recurring expenses."""

    ONE_TIME = "ONE_TIME"  # Non-recurring
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"
