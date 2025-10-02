"""Get daily walk-in report use case."""

from datetime import date, datetime, timezone
from decimal import Decimal

from app.features.walkins.domain.entities import DailyWalkInReport
from app.features.walkins.domain.enums import WalkInStatus
from app.features.walkins.ports.repositories import IWalkInRepository


class GetDailyReportUseCase:
    """Use case for getting daily walk-in report with statistics."""

    def __init__(self, repository: IWalkInRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, report_date: date) -> DailyWalkInReport:
        """
        Get daily walk-in report with statistics.

        Args:
            report_date: Date for the report

        Returns:
            Daily walk-in report with statistics

        Raises:
            ValueError: If date is in the future
        """
        # Validate date
        if report_date > datetime.now(timezone.utc).date():
            raise ValueError("Cannot generate report for future dates")

        # Get all walk-ins for the date
        walkins = await self._repository.list_by_date(report_date)

        # Calculate statistics
        total_services = len(walkins)
        completed_services = len(
            [w for w in walkins if w.status == WalkInStatus.COMPLETED]
        )
        cancelled_services = len(
            [w for w in walkins if w.status == WalkInStatus.CANCELLED]
        )
        in_progress_services = len(
            [w for w in walkins if w.status == WalkInStatus.IN_PROGRESS]
        )

        total_revenue = sum(
            (w.final_amount for w in walkins if w.status == WalkInStatus.COMPLETED),
            start=Decimal("0"),
        )

        total_costs = sum(
            (
                sum((item.product_costs for item in w.services), start=Decimal("0"))
                for w in walkins
                if w.status == WalkInStatus.COMPLETED
            ),
            start=Decimal("0"),
        )

        total_profit = total_revenue - total_costs

        total_discounts = sum(
            (w.discount_amount for w in walkins if w.status == WalkInStatus.COMPLETED),
            start=Decimal("0"),
        )

        # Calculate average service time for completed services
        completed = [w for w in walkins if w.status == WalkInStatus.COMPLETED]
        if completed:
            total_minutes = sum(
                (
                    (w.completed_at - w.started_at).total_seconds() / 60
                    for w in completed
                    if w.completed_at
                ),
                start=0.0,
            )
            avg_service_time_minutes = int(total_minutes / len(completed))
        else:
            avg_service_time_minutes = 0

        # Create report
        report = DailyWalkInReport(
            report_date=report_date,
            total_services=total_services,
            completed_services=completed_services,
            cancelled_services=cancelled_services,
            in_progress_services=in_progress_services,
            total_revenue=total_revenue,
            total_costs=total_costs,
            total_profit=total_profit,
            total_discounts=total_discounts,
            avg_service_time_minutes=avg_service_time_minutes,
        )

        return report
