"""Analytics API dependencies - Dependency injection setup with data providers."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db

# Analytics repositories and data providers
from app.features.analytics.adapters.repositories import (
    RevenueAnalyticsRepository,
    StaffAnalyticsRepository,
    CustomerAnalyticsRepository,
    FinancialAnalyticsRepository,
    ServiceAnalyticsRepository,
    DashboardRepository,
)
from app.features.analytics.adapters.data_adapters import (
    BookingDataAdapter,
    WalkInDataAdapter,
    StaffDataAdapter,
    ExpenseDataAdapter,
    ServiceDataAdapter,
)
from app.features.analytics.use_cases.get_revenue_metrics import (
    GetRevenueMetricsUseCase,
)
from app.features.analytics.use_cases.get_daily_revenue import GetDailyRevenueUseCase
from app.features.analytics.use_cases.get_staff_performance import (
    GetStaffPerformanceUseCase,
)
from app.features.analytics.use_cases.get_staff_leaderboard import (
    GetStaffLeaderboardUseCase,
)
from app.features.analytics.use_cases.get_customer_metrics import (
    GetCustomerMetricsUseCase,
)
from app.features.analytics.use_cases.get_customer_behavior import (
    GetCustomerBehaviorUseCase,
)
from app.features.analytics.use_cases.get_financial_kpis import (
    GetFinancialKPIsUseCase,
)
from app.features.analytics.use_cases.get_service_popularity import (
    GetServicePopularityUseCase,
)
from app.features.analytics.use_cases.get_dashboard_summary import (
    GetDashboardSummaryUseCase,
)

# Other features' dependencies for public use cases
from app.features.bookings.api.dependencies import get_booking_repository
from app.features.bookings.ports.repositories import IBookingRepository
from app.features.walkins.api.dependencies import get_walkin_repository
from app.features.walkins.ports.repositories import IWalkInRepository
from app.features.staff.api.dependencies import (
    get_staff_repository,
    get_attendance_repository,
)
from app.features.staff.ports.repositories import (
    IStaffRepository,
    IAttendanceRepository,
)
from app.features.expenses.api.dependencies import (
    get_expense_repository,
    get_budget_repository,
)
from app.features.expenses.ports.repositories import (
    IExpenseRepository,
    IBudgetRepository,
)
from app.features.services.api.dependencies import get_service_repository
from app.features.services.ports.repositories import IServiceRepository

# Import public use cases from other features
from app.features.bookings.use_cases.get_revenue_data import GetRevenueDataUseCase
from app.features.bookings.use_cases.get_customer_stats import (
    GetCustomerStatsUseCase,
    GetTopCustomersUseCase,
)
from app.features.bookings.use_cases.get_service_stats import GetServiceStatsUseCase
from app.features.walkins.use_cases.get_revenue_data import (
    GetWalkInRevenueDataUseCase,
)
from app.features.staff.use_cases.get_staff_data_for_analytics import (
    GetStaffWorkDataUseCase,
    GetAttendanceDataUseCase,
    GetActiveStaffIdsUseCase,
)
from app.features.expenses.use_cases.get_expense_data_for_analytics import (
    GetExpenseDataUseCase,
    GetBudgetDataUseCase,
)
from app.features.services.use_cases.get_service_name import GetServiceNameUseCase


# ============================================================================
# Data Provider Factories - Analytics owns these adapters
# ============================================================================


def get_booking_data_provider(
    booking_repo: Annotated[IBookingRepository, Depends(get_booking_repository)]
) -> BookingDataAdapter:
    """Get booking data provider (analytics owns this adapter)."""
    # Create public use cases from bookings feature
    revenue_use_case = GetRevenueDataUseCase(booking_repo)
    customer_stats_use_case = GetCustomerStatsUseCase(booking_repo)
    top_customers_use_case = GetTopCustomersUseCase(booking_repo)
    service_stats_use_case = GetServiceStatsUseCase(booking_repo)

    # Return analytics-owned adapter
    return BookingDataAdapter(
        revenue_use_case,
        customer_stats_use_case,
        top_customers_use_case,
        service_stats_use_case,
    )


def get_walkin_data_provider(
    walkin_repo: Annotated[IWalkInRepository, Depends(get_walkin_repository)]
) -> WalkInDataAdapter:
    """Get walk-in data provider (analytics owns this adapter)."""
    revenue_use_case = GetWalkInRevenueDataUseCase(walkin_repo)
    return WalkInDataAdapter(revenue_use_case)


def get_staff_data_provider(
    staff_repo: Annotated[IStaffRepository, Depends(get_staff_repository)],
    attendance_repo: Annotated[
        IAttendanceRepository, Depends(get_attendance_repository)
    ],
) -> StaffDataAdapter:
    """Get staff data provider (analytics owns this adapter)."""
    work_data_use_case = GetStaffWorkDataUseCase(staff_repo, attendance_repo)
    attendance_use_case = GetAttendanceDataUseCase(attendance_repo)
    active_staff_use_case = GetActiveStaffIdsUseCase(staff_repo)

    return StaffDataAdapter(
        work_data_use_case, attendance_use_case, active_staff_use_case
    )


def get_expense_data_provider(
    expense_repo: Annotated[IExpenseRepository, Depends(get_expense_repository)],
    budget_repo: Annotated[IBudgetRepository, Depends(get_budget_repository)],
) -> ExpenseDataAdapter:
    """Get expense data provider (analytics owns this adapter)."""
    expense_use_case = GetExpenseDataUseCase(expense_repo)
    budget_use_case = GetBudgetDataUseCase(budget_repo)

    return ExpenseDataAdapter(expense_use_case, budget_use_case)


def get_service_data_provider(
    service_repo: Annotated[IServiceRepository, Depends(get_service_repository)]
) -> ServiceDataAdapter:
    """Get service data provider (analytics owns this adapter)."""
    service_name_use_case = GetServiceNameUseCase(service_repo)
    return ServiceDataAdapter(service_name_use_case)


# ============================================================================
# Analytics Repository Factories - Use data providers instead of session
# ============================================================================


def get_revenue_analytics_repository(
    booking_provider: Annotated[BookingDataAdapter, Depends(get_booking_data_provider)],
    walkin_provider: Annotated[WalkInDataAdapter, Depends(get_walkin_data_provider)],
) -> RevenueAnalyticsRepository:
    """Get revenue analytics repository instance."""
    return RevenueAnalyticsRepository(booking_provider, walkin_provider)


def get_staff_analytics_repository(
    staff_provider: Annotated[StaffDataAdapter, Depends(get_staff_data_provider)]
) -> StaffAnalyticsRepository:
    """Get staff analytics repository instance."""
    return StaffAnalyticsRepository(staff_provider)


def get_customer_analytics_repository(
    booking_provider: Annotated[BookingDataAdapter, Depends(get_booking_data_provider)]
) -> CustomerAnalyticsRepository:
    """Get customer analytics repository instance."""
    return CustomerAnalyticsRepository(booking_provider)


def get_financial_analytics_repository(
    booking_provider: Annotated[BookingDataAdapter, Depends(get_booking_data_provider)],
    walkin_provider: Annotated[WalkInDataAdapter, Depends(get_walkin_data_provider)],
    expense_provider: Annotated[ExpenseDataAdapter, Depends(get_expense_data_provider)],
) -> FinancialAnalyticsRepository:
    """Get financial analytics repository instance."""
    return FinancialAnalyticsRepository(
        booking_provider, walkin_provider, expense_provider
    )


def get_service_analytics_repository(
    booking_provider: Annotated[BookingDataAdapter, Depends(get_booking_data_provider)],
    service_provider: Annotated[ServiceDataAdapter, Depends(get_service_data_provider)],
) -> ServiceAnalyticsRepository:
    """Get service analytics repository instance."""
    return ServiceAnalyticsRepository(booking_provider, service_provider)


def get_dashboard_repository(
    revenue_repo: Annotated[
        RevenueAnalyticsRepository, Depends(get_revenue_analytics_repository)
    ],
    financial_repo: Annotated[
        FinancialAnalyticsRepository, Depends(get_financial_analytics_repository)
    ],
    customer_repo: Annotated[
        CustomerAnalyticsRepository, Depends(get_customer_analytics_repository)
    ],
    service_repo: Annotated[
        ServiceAnalyticsRepository, Depends(get_service_analytics_repository)
    ],
) -> DashboardRepository:
    """Get dashboard repository instance."""
    return DashboardRepository(
        revenue_repo, financial_repo, customer_repo, service_repo
    )


# ============================================================================
# Use Case Factories - Revenue
# ============================================================================


def get_revenue_metrics_use_case(
    repository: Annotated[
        RevenueAnalyticsRepository, Depends(get_revenue_analytics_repository)
    ]
) -> GetRevenueMetricsUseCase:
    """Get revenue metrics use case instance."""
    return GetRevenueMetricsUseCase(repository)


def get_daily_revenue_use_case(
    repository: Annotated[
        RevenueAnalyticsRepository, Depends(get_revenue_analytics_repository)
    ]
) -> GetDailyRevenueUseCase:
    """Get daily revenue use case instance."""
    return GetDailyRevenueUseCase(repository)


# ============================================================================
# Use Case Factories - Staff
# ============================================================================


def get_staff_performance_use_case(
    repository: Annotated[
        StaffAnalyticsRepository, Depends(get_staff_analytics_repository)
    ]
) -> GetStaffPerformanceUseCase:
    """Get staff performance use case instance."""
    return GetStaffPerformanceUseCase(repository)


def get_staff_leaderboard_use_case(
    repository: Annotated[
        StaffAnalyticsRepository, Depends(get_staff_analytics_repository)
    ]
) -> GetStaffLeaderboardUseCase:
    """Get staff leaderboard use case instance."""
    return GetStaffLeaderboardUseCase(repository)


# ============================================================================
# Use Case Factories - Customer
# ============================================================================


def get_customer_metrics_use_case(
    repository: Annotated[
        CustomerAnalyticsRepository, Depends(get_customer_analytics_repository)
    ]
) -> GetCustomerMetricsUseCase:
    """Get customer metrics use case instance."""
    return GetCustomerMetricsUseCase(repository)


def get_customer_behavior_use_case(
    repository: Annotated[
        CustomerAnalyticsRepository, Depends(get_customer_analytics_repository)
    ]
) -> GetCustomerBehaviorUseCase:
    """Get customer behavior use case instance."""
    return GetCustomerBehaviorUseCase(repository)


# ============================================================================
# Use Case Factories - Financial
# ============================================================================


def get_financial_kpis_use_case(
    repository: Annotated[
        FinancialAnalyticsRepository, Depends(get_financial_analytics_repository)
    ]
) -> GetFinancialKPIsUseCase:
    """Get financial KPIs use case instance."""
    return GetFinancialKPIsUseCase(repository)


# ============================================================================
# Use Case Factories - Service
# ============================================================================


def get_service_popularity_use_case(
    repository: Annotated[
        ServiceAnalyticsRepository, Depends(get_service_analytics_repository)
    ]
) -> GetServicePopularityUseCase:
    """Get service popularity use case instance."""
    return GetServicePopularityUseCase(repository)


# ============================================================================
# Use Case Factories - Dashboard
# ============================================================================


def get_dashboard_summary_use_case(
    repository: Annotated[DashboardRepository, Depends(get_dashboard_repository)]
) -> GetDashboardSummaryUseCase:
    """Get dashboard summary use case instance."""
    return GetDashboardSummaryUseCase(repository)
