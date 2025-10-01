"""Analytics data adapters - Local adapters that call other features' public use cases."""

from datetime import date
from typing import List, Optional

from app.features.analytics.ports.data_providers import (
    IBookingDataProvider,
    IWalkInDataProvider,
    IStaffDataProvider,
    IExpenseDataProvider,
    IServiceDataProvider,
    BookingRevenueDTO,
    WalkInRevenueDTO,
    StaffWorkDataDTO,
    AttendanceDataDTO,
    ExpenseDataDTO,
    BudgetDataDTO,
    ServiceBookingDataDTO,
    CustomerBookingDataDTO,
)

# Import public use cases from other features
from app.features.bookings.use_cases.get_revenue_data import (
    GetRevenueDataUseCase as GetBookingRevenueUseCase,
    GetRevenueDataRequest as GetBookingRevenueRequest,
)
from app.features.bookings.use_cases.get_customer_stats import (
    GetCustomerStatsUseCase,
    GetCustomerStatsRequest,
    GetTopCustomersUseCase,
    GetTopCustomersRequest,
)
from app.features.bookings.use_cases.get_service_stats import (
    GetServiceStatsUseCase,
    GetServiceStatsRequest,
)
from app.features.walkins.use_cases.get_revenue_data import (
    GetWalkInRevenueDataUseCase,
    GetWalkInRevenueDataRequest,
)
from app.features.staff.use_cases.get_staff_data_for_analytics import (
    GetStaffWorkDataUseCase,
    GetStaffWorkDataRequest,
    GetAttendanceDataUseCase,
    GetAttendanceDataRequest,
    GetActiveStaffIdsUseCase,
)
from app.features.expenses.use_cases.get_expense_data_for_analytics import (
    GetExpenseDataUseCase,
    GetExpenseDataRequest,
    GetBudgetDataUseCase,
    GetBudgetDataRequest,
)
from app.features.services.use_cases.get_service_name import (
    GetServiceNameUseCase,
    GetServiceNameRequest,
)


# ============================================================================
# Booking Data Adapter - Analytics owns this
# ============================================================================


class BookingDataAdapter(IBookingDataProvider):
    """Adapter that calls bookings feature's public use cases."""

    def __init__(
        self,
        revenue_use_case: GetBookingRevenueUseCase,
        customer_stats_use_case: GetCustomerStatsUseCase,
        top_customers_use_case: GetTopCustomersUseCase,
        service_stats_use_case: GetServiceStatsUseCase,
    ):
        self._revenue_use_case = revenue_use_case
        self._customer_stats_use_case = customer_stats_use_case
        self._top_customers_use_case = top_customers_use_case
        self._service_stats_use_case = service_stats_use_case

    async def get_revenue_data(
        self, start_date: date, end_date: date
    ) -> List[BookingRevenueDTO]:
        """Get booking revenue data via bookings feature's use case."""
        request = GetBookingRevenueRequest(
            start_date=start_date, end_date=end_date
        )
        booking_data = await self._revenue_use_case.execute(request)

        # Convert to Analytics DTOs
        return [
            BookingRevenueDTO(
                booking_id=b.booking_id,
                booking_date=b.booking_date,
                total_amount=b.total_amount,
                status=b.status,
                customer_id=b.customer_id,
                service_id=b.service_id,
            )
            for b in booking_data
        ]

    async def get_customer_booking_data(
        self, customer_id: str
    ) -> Optional[CustomerBookingDataDTO]:
        """Get customer booking stats via bookings feature's use case."""
        request = GetCustomerStatsRequest(customer_id=customer_id)
        stats = await self._customer_stats_use_case.execute(request)

        if not stats:
            return None

        return CustomerBookingDataDTO(
            customer_id=stats.customer_id,
            booking_count=stats.booking_count,
            total_spent=stats.total_spent,
            first_booking_date=stats.first_booking_date,
            last_booking_date=stats.last_booking_date,
        )

    async def get_top_customers_data(
        self, start_date: date, end_date: date, limit: int
    ) -> List[CustomerBookingDataDTO]:
        """Get top customers via bookings feature's use case."""
        request = GetTopCustomersRequest(
            start_date=start_date, end_date=end_date, limit=limit
        )
        stats_list = await self._top_customers_use_case.execute(request)

        return [
            CustomerBookingDataDTO(
                customer_id=s.customer_id,
                booking_count=s.booking_count,
                total_spent=s.total_spent,
                first_booking_date=s.first_booking_date,
                last_booking_date=s.last_booking_date,
            )
            for s in stats_list
        ]

    async def get_service_booking_data(
        self, start_date: date, end_date: date
    ) -> List[ServiceBookingDataDTO]:
        """Get service booking stats via bookings feature's use case."""
        request = GetServiceStatsRequest(start_date=start_date, end_date=end_date)
        stats_list = await self._service_stats_use_case.execute(request)

        return [
            ServiceBookingDataDTO(
                service_id=s.service_id,
                service_name=s.service_name,
                booking_count=s.booking_count,
                total_revenue=s.total_revenue,
                status=s.status,
            )
            for s in stats_list
        ]


# ============================================================================
# Walk-in Data Adapter - Analytics owns this
# ============================================================================


class WalkInDataAdapter(IWalkInDataProvider):
    """Adapter that calls walkins feature's public use case."""

    def __init__(self, revenue_use_case: GetWalkInRevenueDataUseCase):
        self._revenue_use_case = revenue_use_case

    async def get_revenue_data(
        self, start_date: date, end_date: date
    ) -> List[WalkInRevenueDTO]:
        """Get walk-in revenue data via walkins feature's use case."""
        request = GetWalkInRevenueDataRequest(
            start_date=start_date, end_date=end_date
        )
        walkin_data = await self._revenue_use_case.execute(request)

        return [
            WalkInRevenueDTO(
                walkin_id=w.walkin_id,
                service_date=w.service_date,
                final_amount=w.final_amount,
                status=w.status,
            )
            for w in walkin_data
        ]


# ============================================================================
# Staff Data Adapter - Analytics owns this
# ============================================================================


class StaffDataAdapter(IStaffDataProvider):
    """Adapter that calls staff feature's public use cases."""

    def __init__(
        self,
        work_data_use_case: GetStaffWorkDataUseCase,
        attendance_use_case: GetAttendanceDataUseCase,
        active_staff_use_case: GetActiveStaffIdsUseCase,
    ):
        self._work_data_use_case = work_data_use_case
        self._attendance_use_case = attendance_use_case
        self._active_staff_use_case = active_staff_use_case

    async def get_staff_work_data(
        self, staff_id: str, start_date: date, end_date: date
    ) -> StaffWorkDataDTO:
        """Get staff work data via staff feature's use case."""
        request = GetStaffWorkDataRequest(
            staff_id=staff_id, start_date=start_date, end_date=end_date
        )
        work_data = await self._work_data_use_case.execute(request)

        return StaffWorkDataDTO(
            staff_id=work_data.staff_id,
            staff_name=work_data.staff_name,
            date=work_data.date,
            hours_worked=work_data.hours_worked,
            services_completed=work_data.services_completed,
            revenue_generated=work_data.revenue_generated,
            status=work_data.status,
        )

    async def get_all_active_staff_ids(self) -> List[str]:
        """Get active staff IDs via staff feature's use case."""
        return await self._active_staff_use_case.execute()

    async def get_attendance_data(
        self, staff_id: str, start_date: date, end_date: date
    ) -> List[AttendanceDataDTO]:
        """Get attendance data via staff feature's use case."""
        request = GetAttendanceDataRequest(
            staff_id=staff_id, start_date=start_date, end_date=end_date
        )
        attendance_list = await self._attendance_use_case.execute(request)

        return [
            AttendanceDataDTO(
                staff_id=a.staff_id,
                date=a.date,
                status=a.status,
                hours_worked=a.hours_worked,
            )
            for a in attendance_list
        ]


# ============================================================================
# Expense Data Adapter - Analytics owns this
# ============================================================================


class ExpenseDataAdapter(IExpenseDataProvider):
    """Adapter that calls expenses feature's public use cases."""

    def __init__(
        self,
        expense_use_case: GetExpenseDataUseCase,
        budget_use_case: GetBudgetDataUseCase,
    ):
        self._expense_use_case = expense_use_case
        self._budget_use_case = budget_use_case

    async def get_expense_data(
        self, start_date: date, end_date: date
    ) -> List[ExpenseDataDTO]:
        """Get expense data via expenses feature's use case."""
        request = GetExpenseDataRequest(start_date=start_date, end_date=end_date)
        expense_data = await self._expense_use_case.execute(request)

        return [
            ExpenseDataDTO(
                expense_id=e.expense_id,
                category=e.category,
                amount=e.amount,
                status=e.status,
                expense_date=e.expense_date,
            )
            for e in expense_data
        ]

    async def get_budget_data(
        self, start_date: date, end_date: date
    ) -> List[BudgetDataDTO]:
        """Get budget data via expenses feature's use case."""
        request = GetBudgetDataRequest(start_date=start_date, end_date=end_date)
        budget_data = await self._budget_use_case.execute(request)

        return [
            BudgetDataDTO(
                category=b.category,
                month=b.month,
                budgeted_amount=b.budgeted_amount,
                spent_amount=b.spent_amount,
            )
            for b in budget_data
        ]


# ============================================================================
# Service Data Adapter - Analytics owns this
# ============================================================================


class ServiceDataAdapter(IServiceDataProvider):
    """Adapter that calls services feature's public use case."""

    def __init__(self, service_name_use_case: GetServiceNameUseCase):
        self._service_name_use_case = service_name_use_case

    async def get_service_name(self, service_id: str) -> Optional[str]:
        """Get service name via services feature's use case."""
        request = GetServiceNameRequest(service_id=service_id)
        return await self._service_name_use_case.execute(request)
