"""Analytics data provider interfaces - For accessing data from other features."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional


# ============================================================================
# Data Transfer Objects (DTOs) - Analytics owns these
# ============================================================================

@dataclass
class BookingRevenueDTO:
    """DTO for booking revenue data."""

    booking_id: str
    booking_date: date
    total_amount: Decimal
    status: str
    customer_id: str
    service_id: str


@dataclass
class WalkInRevenueDTO:
    """DTO for walk-in revenue data."""

    walkin_id: str
    service_date: date
    final_amount: Decimal
    status: str


@dataclass
class StaffWorkDataDTO:
    """DTO for staff work data."""

    staff_id: str
    staff_name: str
    date: date
    hours_worked: Decimal
    services_completed: int
    revenue_generated: Decimal
    status: str


@dataclass
class AttendanceDataDTO:
    """DTO for attendance data."""

    staff_id: str
    date: date
    status: str
    hours_worked: Decimal


@dataclass
class ExpenseDataDTO:
    """DTO for expense data."""

    expense_id: str
    category: str
    amount: Decimal
    status: str
    expense_date: date


@dataclass
class BudgetDataDTO:
    """DTO for budget data."""

    category: str
    month: date
    budgeted_amount: Decimal
    spent_amount: Decimal


@dataclass
class ServiceBookingDataDTO:
    """DTO for service booking statistics."""

    service_id: str
    service_name: str
    booking_count: int
    total_revenue: Decimal
    status: str


@dataclass
class CustomerBookingDataDTO:
    """DTO for customer booking data."""

    customer_id: str
    booking_count: int
    total_spent: Decimal
    first_booking_date: date
    last_booking_date: date


# ============================================================================
# Data Provider Interfaces - Analytics owns these ports
# ============================================================================


class IBookingDataProvider(ABC):
    """Interface for accessing booking data from bookings feature."""

    @abstractmethod
    async def get_revenue_data(
        self, start_date: date, end_date: date
    ) -> List[BookingRevenueDTO]:
        """Get booking revenue data for a period."""
        pass

    @abstractmethod
    async def get_customer_booking_data(
        self, customer_id: str
    ) -> Optional[CustomerBookingDataDTO]:
        """Get booking statistics for a customer."""
        pass

    @abstractmethod
    async def get_top_customers_data(
        self, start_date: date, end_date: date, limit: int
    ) -> List[CustomerBookingDataDTO]:
        """Get top customers by spending."""
        pass

    @abstractmethod
    async def get_service_booking_data(
        self, start_date: date, end_date: date
    ) -> List[ServiceBookingDataDTO]:
        """Get booking statistics by service."""
        pass


class IWalkInDataProvider(ABC):
    """Interface for accessing walk-in data from walkins feature."""

    @abstractmethod
    async def get_revenue_data(
        self, start_date: date, end_date: date
    ) -> List[WalkInRevenueDTO]:
        """Get walk-in revenue data for a period."""
        pass


class IStaffDataProvider(ABC):
    """Interface for accessing staff data from staff feature."""

    @abstractmethod
    async def get_staff_work_data(
        self, staff_id: str, start_date: date, end_date: date
    ) -> StaffWorkDataDTO:
        """Get work data for a staff member."""
        pass

    @abstractmethod
    async def get_all_active_staff_ids(self) -> List[str]:
        """Get IDs of all active staff members."""
        pass

    @abstractmethod
    async def get_attendance_data(
        self, staff_id: str, start_date: date, end_date: date
    ) -> List[AttendanceDataDTO]:
        """Get attendance records for a staff member."""
        pass


class IExpenseDataProvider(ABC):
    """Interface for accessing expense data from expenses feature."""

    @abstractmethod
    async def get_expense_data(
        self, start_date: date, end_date: date
    ) -> List[ExpenseDataDTO]:
        """Get expense data for a period."""
        pass

    @abstractmethod
    async def get_budget_data(
        self, start_date: date, end_date: date
    ) -> List[BudgetDataDTO]:
        """Get budget data for a period."""
        pass


class IServiceDataProvider(ABC):
    """Interface for accessing service data from services feature."""

    @abstractmethod
    async def get_service_name(self, service_id: str) -> Optional[str]:
        """Get service name by ID."""
        pass
