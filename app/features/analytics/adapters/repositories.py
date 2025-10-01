"""Analytics repository implementations using data providers (NO cross-feature imports)."""

from datetime import date, datetime, timedelta
from decimal import Decimal
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
from app.features.analytics.domain.enums import RevenueSource, CustomerSegment
from app.features.analytics.ports.repositories import (
    IRevenueAnalyticsRepository,
    IStaffAnalyticsRepository,
    ICustomerAnalyticsRepository,
    IFinancialAnalyticsRepository,
    IServiceAnalyticsRepository,
    IDashboardRepository,
)
from app.features.analytics.ports.data_providers import (
    IBookingDataProvider,
    IWalkInDataProvider,
    IStaffDataProvider,
    IExpenseDataProvider,
    IServiceDataProvider,
)


class RevenueAnalyticsRepository(IRevenueAnalyticsRepository):
    """Repository for revenue analytics using data providers."""

    def __init__(
        self,
        booking_provider: IBookingDataProvider,
        walkin_provider: IWalkInDataProvider,
    ):
        self._booking_provider = booking_provider
        self._walkin_provider = walkin_provider

    async def get_revenue_metrics(
        self, start_date: date, end_date: date
    ) -> RevenueMetrics:
        """Get revenue metrics by calling other features' use cases."""
        # Get booking revenue data
        booking_data = await self._booking_provider.get_revenue_data(
            start_date, end_date
        )
        bookings_revenue = sum(b.total_amount for b in booking_data)
        bookings_count = len(booking_data)

        # Get walk-in revenue data
        walkin_data = await self._walkin_provider.get_revenue_data(
            start_date, end_date
        )
        walkins_revenue = sum(w.final_amount for w in walkin_data)

        total_revenue = bookings_revenue + walkins_revenue
        total_bookings = bookings_count
        avg_transaction = (
            total_revenue / Decimal(str(total_bookings))
            if total_bookings > 0
            else Decimal("0")
        )

        revenue_by_source = {
            RevenueSource.BOOKINGS: bookings_revenue,
            RevenueSource.WALK_INS: walkins_revenue,
        }

        # Calculate growth rate
        growth_rate = await self.get_revenue_growth_rate(start_date, end_date)

        return RevenueMetrics(
            period_start=start_date,
            period_end=end_date,
            total_revenue=total_revenue,
            revenue_by_source=revenue_by_source,
            total_bookings=total_bookings,
            average_transaction_value=avg_transaction,
            growth_rate=growth_rate,
        )

    async def get_daily_revenue(
        self, start_date: date, end_date: date
    ) -> List[DailyRevenue]:
        """Get daily revenue breakdown."""
        # Get all data for period
        booking_data = await self._booking_provider.get_revenue_data(
            start_date, end_date
        )
        walkin_data = await self._walkin_provider.get_revenue_data(
            start_date, end_date
        )

        # Group by date
        daily_revenues = []
        current_date = start_date

        while current_date <= end_date:
            # Bookings for this day
            day_bookings = [b for b in booking_data if b.booking_date == current_date]
            bookings_revenue = sum(b.total_amount for b in day_bookings)
            bookings_count = len(day_bookings)

            # Walk-ins for this day
            day_walkins = [w for w in walkin_data if w.service_date == current_date]
            walkins_revenue = sum(w.final_amount for w in day_walkins)
            walkins_count = len(day_walkins)

            total_revenue = bookings_revenue + walkins_revenue
            total_count = bookings_count + walkins_count
            avg_value = (
                total_revenue / Decimal(str(total_count))
                if total_count > 0
                else Decimal("0")
            )

            daily_revenues.append(
                DailyRevenue(
                    date=current_date,
                    revenue=total_revenue,
                    bookings_count=bookings_count,
                    walkins_count=walkins_count,
                    average_value=avg_value,
                )
            )

            current_date += timedelta(days=1)

        return daily_revenues

    async def get_revenue_growth_rate(
        self, start_date: date, end_date: date
    ) -> Optional[Decimal]:
        """Calculate revenue growth rate compared to previous period."""
        period_length = (end_date - start_date).days + 1
        previous_start = start_date - timedelta(days=period_length)
        previous_end = start_date - timedelta(days=1)

        current_metrics = await self.get_revenue_metrics(start_date, end_date)
        current_revenue = current_metrics.total_revenue

        previous_metrics = await self.get_revenue_metrics(previous_start, previous_end)
        previous_revenue = previous_metrics.total_revenue

        if previous_revenue == Decimal("0"):
            return None

        growth_rate = (
            (current_revenue - previous_revenue) / previous_revenue
        ) * Decimal("100")
        return growth_rate


class StaffAnalyticsRepository(IStaffAnalyticsRepository):
    """Repository for staff analytics using data providers."""

    def __init__(self, staff_provider: IStaffDataProvider):
        self._staff_provider = staff_provider

    async def get_staff_performance(
        self, staff_id: str, start_date: date, end_date: date
    ) -> StaffPerformanceMetrics:
        """Get performance metrics for a staff member."""
        # Get work data via provider
        work_data = await self._staff_provider.get_staff_work_data(
            staff_id, start_date, end_date
        )

        # Get attendance data
        attendance_data = await self._staff_provider.get_attendance_data(
            staff_id, start_date, end_date
        )

        total_days = len(attendance_data)
        present_days = sum(1 for a in attendance_data if a.status == "present")
        total_hours = sum(a.hours_worked for a in attendance_data)

        attendance_rate = (
            (Decimal(str(present_days)) / Decimal(str(total_days))) * Decimal("100")
            if total_days > 0
            else Decimal("0")
        )

        productivity_score = (
            work_data.revenue_generated / total_hours
            if total_hours > Decimal("0")
            else Decimal("0")
        )

        return StaffPerformanceMetrics(
            staff_id=staff_id,
            staff_name=work_data.staff_name,
            period_start=start_date,
            period_end=end_date,
            total_services_completed=work_data.services_completed,
            total_revenue_generated=work_data.revenue_generated,
            average_service_rating=None,
            total_hours_worked=total_hours,
            attendance_rate=attendance_rate,
            productivity_score=productivity_score,
        )

    async def get_all_staff_performance(
        self, start_date: date, end_date: date
    ) -> List[StaffPerformanceMetrics]:
        """Get performance metrics for all active staff."""
        # Get all active staff IDs
        staff_ids = await self._staff_provider.get_all_active_staff_ids()

        performance_list = []
        for staff_id in staff_ids:
            try:
                performance = await self.get_staff_performance(
                    staff_id, start_date, end_date
                )
                performance_list.append(performance)
            except LookupError:
                # Skip if staff not found
                continue

        return performance_list

    async def get_staff_leaderboard(
        self, start_date: date, end_date: date, limit: int = 10
    ) -> StaffLeaderboard:
        """Get top performing staff members."""
        all_performance = await self.get_all_staff_performance(start_date, end_date)

        top_by_revenue = sorted(
            all_performance, key=lambda x: x.total_revenue_generated, reverse=True
        )[:limit]

        top_by_services = sorted(
            all_performance, key=lambda x: x.total_services_completed, reverse=True
        )[:limit]

        with_ratings = [p for p in all_performance if p.average_service_rating]
        top_by_rating = sorted(
            with_ratings,
            key=lambda x: x.average_service_rating or Decimal("0"),
            reverse=True,
        )[:limit]

        return StaffLeaderboard(
            period_start=start_date,
            period_end=end_date,
            top_by_revenue=top_by_revenue,
            top_by_services=top_by_services,
            top_by_rating=top_by_rating,
        )


class CustomerAnalyticsRepository(ICustomerAnalyticsRepository):
    """Repository for customer analytics using data providers."""

    def __init__(self, booking_provider: IBookingDataProvider):
        self._booking_provider = booking_provider

    async def get_customer_metrics(
        self, start_date: date, end_date: date
    ) -> CustomerMetrics:
        """Get customer metrics for a period."""
        # Get booking data
        booking_data = await self._booking_provider.get_revenue_data(
            start_date, end_date
        )

        # Get unique customers
        unique_customers = set(b.customer_id for b in booking_data)
        total_customers = len(unique_customers)

        # Simplified segmentation
        new_customers = 0
        returning_customers = total_customers - new_customers

        retention_rate = (
            (Decimal(str(returning_customers)) / Decimal(str(total_customers)))
            * Decimal("100")
            if total_customers > 0
            else Decimal("0")
        )

        avg_ltv = Decimal("0")

        customers_by_segment = {
            CustomerSegment.NEW: new_customers,
            CustomerSegment.RETURNING: returning_customers,
            CustomerSegment.VIP: 0,
            CustomerSegment.INACTIVE: 0,
        }

        return CustomerMetrics(
            period_start=start_date,
            period_end=end_date,
            total_customers=total_customers,
            new_customers=new_customers,
            returning_customers=returning_customers,
            customer_retention_rate=retention_rate,
            average_customer_lifetime_value=avg_ltv,
            customers_by_segment=customers_by_segment,
        )

    async def get_customer_behavior(
        self, customer_id: str
    ) -> Optional[CustomerBehavior]:
        """Get behavior analysis for a customer."""
        customer_data = await self._booking_provider.get_customer_booking_data(
            customer_id
        )

        if not customer_data:
            return None

        days_since_last = (date.today() - customer_data.last_booking_date).days

        return CustomerBehavior(
            customer_id=customer_id,
            total_bookings=customer_data.booking_count,
            total_spent=customer_data.total_spent,
            average_booking_value=(
                customer_data.total_spent / Decimal(str(customer_data.booking_count))
                if customer_data.booking_count > 0
                else Decimal("0")
            ),
            first_booking_date=customer_data.first_booking_date,
            last_booking_date=customer_data.last_booking_date,
            favorite_services=[],
            preferred_booking_time=None,
            days_since_last_booking=days_since_last,
        )

    async def get_top_customers(
        self, start_date: date, end_date: date, limit: int = 10
    ) -> List[CustomerBehavior]:
        """Get top customers by spending."""
        top_customers_data = await self._booking_provider.get_top_customers_data(
            start_date, end_date, limit
        )

        behaviors = []
        for customer_data in top_customers_data:
            days_since_last = (
                date.today() - customer_data.last_booking_date
            ).days

            behaviors.append(
                CustomerBehavior(
                    customer_id=customer_data.customer_id,
                    total_bookings=customer_data.booking_count,
                    total_spent=customer_data.total_spent,
                    average_booking_value=(
                        customer_data.total_spent
                        / Decimal(str(customer_data.booking_count))
                    ),
                    first_booking_date=customer_data.first_booking_date,
                    last_booking_date=customer_data.last_booking_date,
                    favorite_services=[],
                    preferred_booking_time=None,
                    days_since_last_booking=days_since_last,
                )
            )

        return behaviors


class FinancialAnalyticsRepository(IFinancialAnalyticsRepository):
    """Repository for financial analytics using data providers."""

    def __init__(
        self,
        booking_provider: IBookingDataProvider,
        walkin_provider: IWalkInDataProvider,
        expense_provider: IExpenseDataProvider,
    ):
        self._booking_provider = booking_provider
        self._walkin_provider = walkin_provider
        self._expense_provider = expense_provider

    async def get_financial_kpis(
        self, start_date: date, end_date: date
    ) -> FinancialKPIs:
        """Get financial KPIs by combining revenue and expense data."""
        # Get revenue data
        booking_data = await self._booking_provider.get_revenue_data(
            start_date, end_date
        )
        walkin_data = await self._walkin_provider.get_revenue_data(
            start_date, end_date
        )

        bookings_revenue = sum(b.total_amount for b in booking_data)
        walkins_revenue = sum(w.final_amount for w in walkin_data)
        total_revenue = bookings_revenue + walkins_revenue

        # Get expense data
        expense_data = await self._expense_provider.get_expense_data(
            start_date, end_date
        )
        total_expenses = sum(e.amount for e in expense_data)

        gross_profit = total_revenue
        net_profit = total_revenue - total_expenses
        profit_margin = (
            (net_profit / total_revenue) * Decimal("100")
            if total_revenue > Decimal("0")
            else Decimal("0")
        )

        booking_count = len(booking_data)
        revenue_per_booking = (
            total_revenue / Decimal(str(booking_count))
            if booking_count > 0
            else Decimal("0")
        )
        expenses_per_booking = (
            total_expenses / Decimal(str(booking_count))
            if booking_count > 0
            else Decimal("0")
        )

        return FinancialKPIs(
            period_start=start_date,
            period_end=end_date,
            total_revenue=total_revenue,
            total_expenses=total_expenses,
            gross_profit=gross_profit,
            net_profit=net_profit,
            profit_margin=profit_margin,
            operating_expenses=total_expenses,
            cost_of_goods_sold=Decimal("0"),
            revenue_per_booking=revenue_per_booking,
            expenses_per_booking=expenses_per_booking,
        )

    async def get_budget_performance(
        self, start_date: date, end_date: date
    ) -> BudgetPerformance:
        """Get budget vs actual performance."""
        budget_data = await self._expense_provider.get_budget_data(
            start_date, end_date
        )

        total_budgeted = sum(b.budgeted_amount for b in budget_data)
        total_spent = sum(b.spent_amount for b in budget_data)
        variance = total_budgeted - total_spent
        variance_percentage = (
            (variance / total_budgeted) * Decimal("100")
            if total_budgeted > Decimal("0")
            else Decimal("0")
        )

        return BudgetPerformance(
            period_start=start_date,
            period_end=end_date,
            total_budgeted=total_budgeted,
            total_spent=total_spent,
            variance=variance,
            variance_percentage=variance_percentage,
            categories_over_budget=[],
            categories_under_budget=[],
        )


class ServiceAnalyticsRepository(IServiceAnalyticsRepository):
    """Repository for service analytics using data providers."""

    def __init__(
        self,
        booking_provider: IBookingDataProvider,
        service_provider: IServiceDataProvider,
    ):
        self._booking_provider = booking_provider
        self._service_provider = service_provider

    async def get_service_popularity(
        self, start_date: date, end_date: date
    ) -> List[ServicePopularity]:
        """Get service popularity metrics."""
        service_booking_data = await self._booking_provider.get_service_booking_data(
            start_date, end_date
        )

        popularity_list = []
        for service_data in service_booking_data:
            # Get service name
            service_name = await self._service_provider.get_service_name(
                service_data.service_id
            )

            popularity_list.append(
                ServicePopularity(
                    service_id=service_data.service_id,
                    service_name=service_name or "Unknown",
                    total_bookings=service_data.booking_count,
                    total_revenue=service_data.total_revenue,
                    average_rating=None,
                    completion_rate=Decimal("100"),
                    cancellation_rate=Decimal("0"),
                )
            )

        return popularity_list

    async def get_peak_hours_analysis(
        self, start_date: date, end_date: date
    ) -> PeakHoursAnalysis:
        """Get peak hours and booking patterns."""
        return PeakHoursAnalysis(
            period_start=start_date,
            period_end=end_date,
            busiest_hours=[9, 10, 11, 14, 15, 16],
            busiest_days=["Saturday", "Sunday"],
            average_bookings_per_hour={},
            average_bookings_per_day={},
        )


class DashboardRepository(IDashboardRepository):
    """Repository for dashboard data."""

    def __init__(
        self,
        revenue_repo: RevenueAnalyticsRepository,
        financial_repo: FinancialAnalyticsRepository,
        customer_repo: CustomerAnalyticsRepository,
        service_repo: ServiceAnalyticsRepository,
    ):
        self._revenue_repo = revenue_repo
        self._financial_repo = financial_repo
        self._customer_repo = customer_repo
        self._service_repo = service_repo

    async def get_dashboard_summary(
        self, start_date: date, end_date: date
    ) -> DashboardSummary:
        """Get comprehensive dashboard summary."""
        revenue_metrics = await self._revenue_repo.get_revenue_metrics(
            start_date, end_date
        )
        financial_kpis = await self._financial_repo.get_financial_kpis(
            start_date, end_date
        )
        customer_metrics = await self._customer_repo.get_customer_metrics(
            start_date, end_date
        )
        top_services = await self._service_repo.get_service_popularity(
            start_date, end_date
        )

        return DashboardSummary(
            period_start=start_date,
            period_end=end_date,
            revenue_metrics=revenue_metrics,
            financial_kpis=financial_kpis,
            customer_metrics=customer_metrics,
            total_active_staff=0,
            total_completed_services=revenue_metrics.total_bookings,
            average_customer_satisfaction=None,
            top_performing_services=top_services[:5],
            generated_at=datetime.now(),
        )
