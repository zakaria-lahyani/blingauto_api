"""Analytics repository interfaces."""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from app.features.analytics.domain.entities import (
    RevenueMetrics,
    DailyRevenue,
    StaffPerformanceMetrics,
    StaffLeaderboard,
    CustomerMetrics,
    CustomerBehavior,
    FinancialKPIs,
    BudgetPerformance,
    ServicePopularity,
    PeakHoursAnalysis,
    DashboardSummary,
)


class IRevenueAnalyticsRepository(ABC):
    """Interface for revenue analytics repository."""

    @abstractmethod
    async def get_revenue_metrics(
        self, start_date: date, end_date: date
    ) -> RevenueMetrics:
        """Get revenue metrics for a period."""
        pass

    @abstractmethod
    async def get_daily_revenue(
        self, start_date: date, end_date: date
    ) -> List[DailyRevenue]:
        """Get daily revenue breakdown."""
        pass

    @abstractmethod
    async def get_revenue_growth_rate(
        self, start_date: date, end_date: date
    ) -> Optional[float]:
        """Calculate revenue growth rate compared to previous period."""
        pass


class IStaffAnalyticsRepository(ABC):
    """Interface for staff analytics repository."""

    @abstractmethod
    async def get_staff_performance(
        self, staff_id: str, start_date: date, end_date: date
    ) -> StaffPerformanceMetrics:
        """Get performance metrics for a staff member."""
        pass

    @abstractmethod
    async def get_all_staff_performance(
        self, start_date: date, end_date: date
    ) -> List[StaffPerformanceMetrics]:
        """Get performance metrics for all staff."""
        pass

    @abstractmethod
    async def get_staff_leaderboard(
        self, start_date: date, end_date: date, limit: int = 10
    ) -> StaffLeaderboard:
        """Get top performing staff members."""
        pass


class ICustomerAnalyticsRepository(ABC):
    """Interface for customer analytics repository."""

    @abstractmethod
    async def get_customer_metrics(
        self, start_date: date, end_date: date
    ) -> CustomerMetrics:
        """Get customer metrics for a period."""
        pass

    @abstractmethod
    async def get_customer_behavior(
        self, customer_id: str
    ) -> Optional[CustomerBehavior]:
        """Get behavior analysis for a customer."""
        pass

    @abstractmethod
    async def get_top_customers(
        self, start_date: date, end_date: date, limit: int = 10
    ) -> List[CustomerBehavior]:
        """Get top customers by spending."""
        pass


class IFinancialAnalyticsRepository(ABC):
    """Interface for financial analytics repository."""

    @abstractmethod
    async def get_financial_kpis(
        self, start_date: date, end_date: date
    ) -> FinancialKPIs:
        """Get financial KPIs for a period."""
        pass

    @abstractmethod
    async def get_budget_performance(
        self, start_date: date, end_date: date
    ) -> BudgetPerformance:
        """Get budget vs actual performance."""
        pass


class IServiceAnalyticsRepository(ABC):
    """Interface for service analytics repository."""

    @abstractmethod
    async def get_service_popularity(
        self, start_date: date, end_date: date
    ) -> List[ServicePopularity]:
        """Get service popularity metrics."""
        pass

    @abstractmethod
    async def get_peak_hours_analysis(
        self, start_date: date, end_date: date
    ) -> PeakHoursAnalysis:
        """Get peak hours and booking patterns."""
        pass


class IDashboardRepository(ABC):
    """Interface for dashboard repository."""

    @abstractmethod
    async def get_dashboard_summary(
        self, start_date: date, end_date: date
    ) -> DashboardSummary:
        """Get comprehensive dashboard summary."""
        pass
