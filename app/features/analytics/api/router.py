"""Analytics API router - REST endpoints for business intelligence."""

from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth.dependencies import require_any_role
from app.features.auth.domain.enums import UserRole
from app.features.analytics.api.dependencies import (
    get_revenue_metrics_use_case,
    get_daily_revenue_use_case,
    get_staff_performance_use_case,
    get_staff_leaderboard_use_case,
    get_customer_metrics_use_case,
    get_customer_behavior_use_case,
    get_financial_kpis_use_case,
    get_service_popularity_use_case,
    get_dashboard_summary_use_case,
)
from app.features.analytics.api.schemas import (
    RevenueMetricsSchema,
    DailyRevenueSchema,
    DailyRevenueListSchema,
    StaffPerformanceSchema,
    StaffLeaderboardSchema,
    CustomerMetricsSchema,
    CustomerBehaviorSchema,
    TopCustomersListSchema,
    FinancialKPIsSchema,
    ServicePopularitySchema,
    ServicePopularityListSchema,
    DashboardSummarySchema,
)
from app.features.analytics.use_cases.get_revenue_metrics import (
    GetRevenueMetricsRequest,
)
from app.features.analytics.use_cases.get_daily_revenue import GetDailyRevenueRequest
from app.features.analytics.use_cases.get_staff_performance import (
    GetStaffPerformanceRequest,
)
from app.features.analytics.use_cases.get_staff_leaderboard import (
    GetStaffLeaderboardRequest,
)
from app.features.analytics.use_cases.get_customer_metrics import (
    GetCustomerMetricsRequest,
)
from app.features.analytics.use_cases.get_customer_behavior import (
    GetCustomerBehaviorRequest,
)
from app.features.analytics.use_cases.get_financial_kpis import (
    GetFinancialKPIsRequest,
)
from app.features.analytics.use_cases.get_service_popularity import (
    GetServicePopularityRequest,
)
from app.features.analytics.use_cases.get_dashboard_summary import (
    GetDashboardSummaryRequest,
)


router = APIRouter()


# ============================================================================
# Revenue Analytics Endpoints
# ============================================================================


@router.get(
    "/analytics/revenue/metrics",
    response_model=RevenueMetricsSchema,
    dependencies=[
        Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))
    ],
)
async def get_revenue_metrics(
    start_date: date = Query(...),
    end_date: date = Query(...),
    use_case: Annotated[object, Depends(get_revenue_metrics_use_case)] = None,
) -> RevenueMetricsSchema:
    """Get revenue metrics for a period."""
    request = GetRevenueMetricsRequest(start_date=start_date, end_date=end_date)
    metrics = await use_case.execute(request)

    return RevenueMetricsSchema(
        period_start=metrics.period_start,
        period_end=metrics.period_end,
        total_revenue=metrics.total_revenue,
        revenue_by_source={k.value: v for k, v in metrics.revenue_by_source.items()},
        total_bookings=metrics.total_bookings,
        average_transaction_value=metrics.average_transaction_value,
        growth_rate=metrics.growth_rate,
    )


@router.get(
    "/analytics/revenue/daily",
    response_model=DailyRevenueListSchema,
    dependencies=[
        Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))
    ],
)
async def get_daily_revenue(
    start_date: date = Query(...),
    end_date: date = Query(...),
    use_case: Annotated[object, Depends(get_daily_revenue_use_case)] = None,
) -> DailyRevenueListSchema:
    """Get daily revenue breakdown."""
    request = GetDailyRevenueRequest(start_date=start_date, end_date=end_date)
    daily_revenues = await use_case.execute(request)

    items = [
        DailyRevenueSchema(
            date=dr.date,
            revenue=dr.revenue,
            bookings_count=dr.bookings_count,
            walkins_count=dr.walkins_count,
            average_value=dr.average_value,
        )
        for dr in daily_revenues
    ]

    return DailyRevenueListSchema(items=items, total_days=len(items))


# ============================================================================
# Staff Performance Endpoints
# ============================================================================


@router.get(
    "/analytics/staff/{staff_id}/performance",
    response_model=StaffPerformanceSchema,
    dependencies=[
        Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))
    ],
)
async def get_staff_performance(
    staff_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    use_case: Annotated[object, Depends(get_staff_performance_use_case)] = None,
) -> StaffPerformanceSchema:
    """Get performance metrics for a staff member."""
    request = GetStaffPerformanceRequest(
        staff_id=staff_id, start_date=start_date, end_date=end_date
    )

    try:
        performance = await use_case.execute(request)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return StaffPerformanceSchema(
        staff_id=performance.staff_id,
        staff_name=performance.staff_name,
        period_start=performance.period_start,
        period_end=performance.period_end,
        total_services_completed=performance.total_services_completed,
        total_revenue_generated=performance.total_revenue_generated,
        average_service_rating=performance.average_service_rating,
        total_hours_worked=performance.total_hours_worked,
        attendance_rate=performance.attendance_rate,
        productivity_score=performance.productivity_score,
    )


@router.get(
    "/analytics/staff/leaderboard",
    response_model=StaffLeaderboardSchema,
    dependencies=[
        Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))
    ],
)
async def get_staff_leaderboard(
    start_date: date = Query(...),
    end_date: date = Query(...),
    limit: int = Query(10, ge=1, le=50),
    use_case: Annotated[object, Depends(get_staff_leaderboard_use_case)] = None,
) -> StaffLeaderboardSchema:
    """Get top performing staff members."""
    request = GetStaffLeaderboardRequest(
        start_date=start_date, end_date=end_date, limit=limit
    )
    leaderboard = await use_case.execute(request)

    def to_schema(perf):
        return StaffPerformanceSchema(
            staff_id=perf.staff_id,
            staff_name=perf.staff_name,
            period_start=perf.period_start,
            period_end=perf.period_end,
            total_services_completed=perf.total_services_completed,
            total_revenue_generated=perf.total_revenue_generated,
            average_service_rating=perf.average_service_rating,
            total_hours_worked=perf.total_hours_worked,
            attendance_rate=perf.attendance_rate,
            productivity_score=perf.productivity_score,
        )

    return StaffLeaderboardSchema(
        period_start=leaderboard.period_start,
        period_end=leaderboard.period_end,
        top_by_revenue=[to_schema(p) for p in leaderboard.top_by_revenue],
        top_by_services=[to_schema(p) for p in leaderboard.top_by_services],
        top_by_rating=[to_schema(p) for p in leaderboard.top_by_rating],
    )


# ============================================================================
# Customer Analytics Endpoints
# ============================================================================


@router.get(
    "/analytics/customers/metrics",
    response_model=CustomerMetricsSchema,
    dependencies=[
        Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))
    ],
)
async def get_customer_metrics(
    start_date: date = Query(...),
    end_date: date = Query(...),
    use_case: Annotated[object, Depends(get_customer_metrics_use_case)] = None,
) -> CustomerMetricsSchema:
    """Get customer metrics for a period."""
    request = GetCustomerMetricsRequest(start_date=start_date, end_date=end_date)
    metrics = await use_case.execute(request)

    return CustomerMetricsSchema(
        period_start=metrics.period_start,
        period_end=metrics.period_end,
        total_customers=metrics.total_customers,
        new_customers=metrics.new_customers,
        returning_customers=metrics.returning_customers,
        customer_retention_rate=metrics.customer_retention_rate,
        average_customer_lifetime_value=metrics.average_customer_lifetime_value,
        customers_by_segment={
            k.value: v for k, v in metrics.customers_by_segment.items()
        },
    )


@router.get(
    "/analytics/customers/{customer_id}/behavior",
    response_model=CustomerBehaviorSchema,
    dependencies=[
        Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))
    ],
)
async def get_customer_behavior(
    customer_id: str,
    use_case: Annotated[object, Depends(get_customer_behavior_use_case)] = None,
) -> CustomerBehaviorSchema:
    """Get behavior analysis for a customer."""
    request = GetCustomerBehaviorRequest(customer_id=customer_id)
    behavior = await use_case.execute(request)

    if not behavior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No booking data found for customer {customer_id}",
        )

    return CustomerBehaviorSchema(
        customer_id=behavior.customer_id,
        total_bookings=behavior.total_bookings,
        total_spent=behavior.total_spent,
        average_booking_value=behavior.average_booking_value,
        first_booking_date=behavior.first_booking_date,
        last_booking_date=behavior.last_booking_date,
        favorite_services=behavior.favorite_services,
        preferred_booking_time=behavior.preferred_booking_time,
        days_since_last_booking=behavior.days_since_last_booking,
    )


# ============================================================================
# Financial Analytics Endpoints
# ============================================================================


@router.get(
    "/analytics/financial/kpis",
    response_model=FinancialKPIsSchema,
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value))],
)
async def get_financial_kpis(
    start_date: date = Query(...),
    end_date: date = Query(...),
    use_case: Annotated[object, Depends(get_financial_kpis_use_case)] = None,
) -> FinancialKPIsSchema:
    """Get financial KPIs for a period (Admin only)."""
    request = GetFinancialKPIsRequest(start_date=start_date, end_date=end_date)
    kpis = await use_case.execute(request)

    return FinancialKPIsSchema(
        period_start=kpis.period_start,
        period_end=kpis.period_end,
        total_revenue=kpis.total_revenue,
        total_expenses=kpis.total_expenses,
        gross_profit=kpis.gross_profit,
        net_profit=kpis.net_profit,
        profit_margin=kpis.profit_margin,
        operating_expenses=kpis.operating_expenses,
        cost_of_goods_sold=kpis.cost_of_goods_sold,
        revenue_per_booking=kpis.revenue_per_booking,
        expenses_per_booking=kpis.expenses_per_booking,
    )


# ============================================================================
# Service Analytics Endpoints
# ============================================================================


@router.get(
    "/analytics/services/popularity",
    response_model=ServicePopularityListSchema,
    dependencies=[
        Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))
    ],
)
async def get_service_popularity(
    start_date: date = Query(...),
    end_date: date = Query(...),
    use_case: Annotated[object, Depends(get_service_popularity_use_case)] = None,
) -> ServicePopularityListSchema:
    """Get service popularity metrics."""
    request = GetServicePopularityRequest(start_date=start_date, end_date=end_date)
    services = await use_case.execute(request)

    items = [
        ServicePopularitySchema(
            service_id=s.service_id,
            service_name=s.service_name,
            total_bookings=s.total_bookings,
            total_revenue=s.total_revenue,
            average_rating=s.average_rating,
            completion_rate=s.completion_rate,
            cancellation_rate=s.cancellation_rate,
        )
        for s in services
    ]

    return ServicePopularityListSchema(items=items, total=len(items))


# ============================================================================
# Dashboard Summary Endpoint
# ============================================================================


@router.get(
    "/analytics/dashboard",
    response_model=DashboardSummarySchema,
    dependencies=[
        Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))
    ],
)
async def get_dashboard_summary(
    start_date: date = Query(...),
    end_date: date = Query(...),
    use_case: Annotated[object, Depends(get_dashboard_summary_use_case)] = None,
) -> DashboardSummarySchema:
    """Get comprehensive dashboard summary."""
    request = GetDashboardSummaryRequest(start_date=start_date, end_date=end_date)
    summary = await use_case.execute(request)

    return DashboardSummarySchema(
        period_start=summary.period_start,
        period_end=summary.period_end,
        revenue_metrics=RevenueMetricsSchema(
            period_start=summary.revenue_metrics.period_start,
            period_end=summary.revenue_metrics.period_end,
            total_revenue=summary.revenue_metrics.total_revenue,
            revenue_by_source={
                k.value: v for k, v in summary.revenue_metrics.revenue_by_source.items()
            },
            total_bookings=summary.revenue_metrics.total_bookings,
            average_transaction_value=summary.revenue_metrics.average_transaction_value,
            growth_rate=summary.revenue_metrics.growth_rate,
        ),
        financial_kpis=FinancialKPIsSchema(
            period_start=summary.financial_kpis.period_start,
            period_end=summary.financial_kpis.period_end,
            total_revenue=summary.financial_kpis.total_revenue,
            total_expenses=summary.financial_kpis.total_expenses,
            gross_profit=summary.financial_kpis.gross_profit,
            net_profit=summary.financial_kpis.net_profit,
            profit_margin=summary.financial_kpis.profit_margin,
            operating_expenses=summary.financial_kpis.operating_expenses,
            cost_of_goods_sold=summary.financial_kpis.cost_of_goods_sold,
            revenue_per_booking=summary.financial_kpis.revenue_per_booking,
            expenses_per_booking=summary.financial_kpis.expenses_per_booking,
        ),
        customer_metrics=CustomerMetricsSchema(
            period_start=summary.customer_metrics.period_start,
            period_end=summary.customer_metrics.period_end,
            total_customers=summary.customer_metrics.total_customers,
            new_customers=summary.customer_metrics.new_customers,
            returning_customers=summary.customer_metrics.returning_customers,
            customer_retention_rate=summary.customer_metrics.customer_retention_rate,
            average_customer_lifetime_value=summary.customer_metrics.average_customer_lifetime_value,
            customers_by_segment={
                k.value: v
                for k, v in summary.customer_metrics.customers_by_segment.items()
            },
        ),
        total_active_staff=summary.total_active_staff,
        total_completed_services=summary.total_completed_services,
        average_customer_satisfaction=summary.average_customer_satisfaction,
        top_performing_services=[
            ServicePopularitySchema(
                service_id=s.service_id,
                service_name=s.service_name,
                total_bookings=s.total_bookings,
                total_revenue=s.total_revenue,
                average_rating=s.average_rating,
                completion_rate=s.completion_rate,
                cancellation_rate=s.cancellation_rate,
            )
            for s in summary.top_performing_services
        ],
        generated_at=summary.generated_at,
    )
