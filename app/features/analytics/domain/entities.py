"""Analytics domain entities - Value objects for reporting."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from app.features.analytics.domain.enums import (
    RevenueSource,
    CustomerSegment,
    TimeGranularity,
)


# ============================================================================
# Revenue Analytics
# ============================================================================

@dataclass
class RevenueMetrics:
    """Revenue metrics for a period."""

    period_start: date
    period_end: date
    total_revenue: Decimal
    revenue_by_source: dict[RevenueSource, Decimal]
    total_bookings: int
    average_transaction_value: Decimal
    growth_rate: Optional[Decimal] = None  # Compared to previous period

    def get_source_percentage(self, source: RevenueSource) -> Decimal:
        """Calculate percentage of revenue from a source."""
        if self.total_revenue == Decimal("0"):
            return Decimal("0")
        source_amount = self.revenue_by_source.get(source, Decimal("0"))
        return (source_amount / self.total_revenue) * Decimal("100")


@dataclass
class DailyRevenue:
    """Revenue breakdown by day."""

    date: date
    revenue: Decimal
    bookings_count: int
    walkins_count: int
    average_value: Decimal


# ============================================================================
# Staff Performance Analytics
# ============================================================================

@dataclass
class StaffPerformanceMetrics:
    """Staff performance metrics."""

    staff_id: str
    staff_name: str
    period_start: date
    period_end: date
    total_services_completed: int
    total_revenue_generated: Decimal
    average_service_rating: Optional[Decimal]
    total_hours_worked: Decimal
    attendance_rate: Decimal  # Percentage
    productivity_score: Decimal  # Revenue per hour

    def calculate_productivity(self) -> Decimal:
        """Calculate revenue per hour worked."""
        if self.total_hours_worked == Decimal("0"):
            return Decimal("0")
        return self.total_revenue_generated / self.total_hours_worked


@dataclass
class StaffLeaderboard:
    """Top performing staff members."""

    period_start: date
    period_end: date
    top_by_revenue: List["StaffPerformanceMetrics"]
    top_by_services: List["StaffPerformanceMetrics"]
    top_by_rating: List["StaffPerformanceMetrics"]


# ============================================================================
# Customer Analytics
# ============================================================================

@dataclass
class CustomerMetrics:
    """Customer analytics metrics."""

    period_start: date
    period_end: date
    total_customers: int
    new_customers: int
    returning_customers: int
    customer_retention_rate: Decimal  # Percentage
    average_customer_lifetime_value: Decimal
    customers_by_segment: dict[CustomerSegment, int]

    def get_segment_percentage(self, segment: CustomerSegment) -> Decimal:
        """Calculate percentage of customers in a segment."""
        if self.total_customers == 0:
            return Decimal("0")
        segment_count = self.customers_by_segment.get(segment, 0)
        return (Decimal(str(segment_count)) / Decimal(str(self.total_customers))) * Decimal("100")


@dataclass
class CustomerBehavior:
    """Customer behavior analysis."""

    customer_id: str
    total_bookings: int
    total_spent: Decimal
    average_booking_value: Decimal
    first_booking_date: date
    last_booking_date: date
    favorite_services: List[str]
    preferred_booking_time: Optional[str]  # e.g., "morning", "afternoon"
    days_since_last_booking: int


# ============================================================================
# Financial KPIs
# ============================================================================

@dataclass
class FinancialKPIs:
    """Key financial performance indicators."""

    period_start: date
    period_end: date
    total_revenue: Decimal
    total_expenses: Decimal
    gross_profit: Decimal
    net_profit: Decimal
    profit_margin: Decimal  # Percentage
    operating_expenses: Decimal
    cost_of_goods_sold: Decimal
    revenue_per_booking: Decimal
    expenses_per_booking: Decimal

    def calculate_profit_margin(self) -> Decimal:
        """Calculate profit margin percentage."""
        if self.total_revenue == Decimal("0"):
            return Decimal("0")
        return (self.net_profit / self.total_revenue) * Decimal("100")

    def calculate_roi(self) -> Decimal:
        """Calculate return on investment."""
        if self.total_expenses == Decimal("0"):
            return Decimal("0")
        return (self.net_profit / self.total_expenses) * Decimal("100")


@dataclass
class BudgetPerformance:
    """Budget vs actual performance."""

    period_start: date
    period_end: date
    total_budgeted: Decimal
    total_spent: Decimal
    variance: Decimal
    variance_percentage: Decimal
    categories_over_budget: List[str]
    categories_under_budget: List[str]


# ============================================================================
# Service Analytics
# ============================================================================

@dataclass
class ServicePopularity:
    """Service popularity metrics."""

    service_id: str
    service_name: str
    total_bookings: int
    total_revenue: Decimal
    average_rating: Optional[Decimal]
    completion_rate: Decimal  # Percentage
    cancellation_rate: Decimal  # Percentage


@dataclass
class PeakHoursAnalysis:
    """Peak hours and booking patterns."""

    period_start: date
    period_end: date
    busiest_hours: List[int]  # Hours of day (0-23)
    busiest_days: List[str]  # Day names
    average_bookings_per_hour: dict[int, Decimal]
    average_bookings_per_day: dict[str, Decimal]


# ============================================================================
# Dashboard Summary
# ============================================================================

@dataclass
class DashboardSummary:
    """Comprehensive dashboard summary."""

    period_start: date
    period_end: date
    revenue_metrics: RevenueMetrics
    financial_kpis: FinancialKPIs
    customer_metrics: CustomerMetrics
    total_active_staff: int
    total_completed_services: int
    average_customer_satisfaction: Optional[Decimal]
    top_performing_services: List[ServicePopularity]
    generated_at: datetime
