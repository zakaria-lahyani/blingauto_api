"""Analytics API schemas - Request/Response DTOs."""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.features.analytics.domain.enums import RevenueSource, CustomerSegment


# ============================================================================
# Revenue Analytics Schemas
# ============================================================================

class DailyRevenueSchema(BaseModel):
    """Schema for daily revenue data."""

    date: date
    revenue: Decimal
    bookings_count: int
    walkins_count: int
    average_value: Decimal

    class Config:
        from_attributes = True


class RevenueMetricsSchema(BaseModel):
    """Schema for revenue metrics response."""

    period_start: date
    period_end: date
    total_revenue: Decimal
    revenue_by_source: Dict[str, Decimal]
    total_bookings: int
    average_transaction_value: Decimal
    growth_rate: Optional[Decimal]

    class Config:
        from_attributes = True


class DailyRevenueListSchema(BaseModel):
    """Schema for daily revenue list."""

    items: List[DailyRevenueSchema]
    total_days: int


# ============================================================================
# Staff Performance Schemas
# ============================================================================

class StaffPerformanceSchema(BaseModel):
    """Schema for staff performance metrics."""

    staff_id: str
    staff_name: str
    period_start: date
    period_end: date
    total_services_completed: int
    total_revenue_generated: Decimal
    average_service_rating: Optional[Decimal]
    total_hours_worked: Decimal
    attendance_rate: Decimal
    productivity_score: Decimal

    class Config:
        from_attributes = True


class StaffLeaderboardSchema(BaseModel):
    """Schema for staff leaderboard."""

    period_start: date
    period_end: date
    top_by_revenue: List[StaffPerformanceSchema]
    top_by_services: List[StaffPerformanceSchema]
    top_by_rating: List[StaffPerformanceSchema]

    class Config:
        from_attributes = True


# ============================================================================
# Customer Analytics Schemas
# ============================================================================

class CustomerMetricsSchema(BaseModel):
    """Schema for customer metrics."""

    period_start: date
    period_end: date
    total_customers: int
    new_customers: int
    returning_customers: int
    customer_retention_rate: Decimal
    average_customer_lifetime_value: Decimal
    customers_by_segment: Dict[str, int]

    class Config:
        from_attributes = True


class CustomerBehaviorSchema(BaseModel):
    """Schema for customer behavior analysis."""

    customer_id: str
    total_bookings: int
    total_spent: Decimal
    average_booking_value: Decimal
    first_booking_date: date
    last_booking_date: date
    favorite_services: List[str]
    preferred_booking_time: Optional[str]
    days_since_last_booking: int

    class Config:
        from_attributes = True


class TopCustomersListSchema(BaseModel):
    """Schema for top customers list."""

    items: List[CustomerBehaviorSchema]
    total: int


# ============================================================================
# Financial KPIs Schemas
# ============================================================================

class FinancialKPIsSchema(BaseModel):
    """Schema for financial KPIs."""

    period_start: date
    period_end: date
    total_revenue: Decimal
    total_expenses: Decimal
    gross_profit: Decimal
    net_profit: Decimal
    profit_margin: Decimal
    operating_expenses: Decimal
    cost_of_goods_sold: Decimal
    revenue_per_booking: Decimal
    expenses_per_booking: Decimal

    class Config:
        from_attributes = True


class BudgetPerformanceSchema(BaseModel):
    """Schema for budget performance."""

    period_start: date
    period_end: date
    total_budgeted: Decimal
    total_spent: Decimal
    variance: Decimal
    variance_percentage: Decimal
    categories_over_budget: List[str]
    categories_under_budget: List[str]

    class Config:
        from_attributes = True


# ============================================================================
# Service Analytics Schemas
# ============================================================================

class ServicePopularitySchema(BaseModel):
    """Schema for service popularity metrics."""

    service_id: str
    service_name: str
    total_bookings: int
    total_revenue: Decimal
    average_rating: Optional[Decimal]
    completion_rate: Decimal
    cancellation_rate: Decimal

    class Config:
        from_attributes = True


class ServicePopularityListSchema(BaseModel):
    """Schema for service popularity list."""

    items: List[ServicePopularitySchema]
    total: int


class PeakHoursAnalysisSchema(BaseModel):
    """Schema for peak hours analysis."""

    period_start: date
    period_end: date
    busiest_hours: List[int]
    busiest_days: List[str]
    average_bookings_per_hour: Dict[int, Decimal]
    average_bookings_per_day: Dict[str, Decimal]

    class Config:
        from_attributes = True


# ============================================================================
# Dashboard Summary Schema
# ============================================================================

class DashboardSummarySchema(BaseModel):
    """Schema for comprehensive dashboard summary."""

    period_start: date
    period_end: date
    revenue_metrics: RevenueMetricsSchema
    financial_kpis: FinancialKPIsSchema
    customer_metrics: CustomerMetricsSchema
    total_active_staff: int
    total_completed_services: int
    average_customer_satisfaction: Optional[Decimal]
    top_performing_services: List[ServicePopularitySchema]
    generated_at: datetime

    class Config:
        from_attributes = True
