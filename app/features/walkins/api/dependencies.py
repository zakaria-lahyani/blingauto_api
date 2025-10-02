"""Walk-in API dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.features.walkins.adapters.repositories import WalkInRepository
from app.features.walkins.use_cases.create_walkin import CreateWalkInUseCase
from app.features.walkins.use_cases.add_service import AddServiceUseCase
from app.features.walkins.use_cases.remove_service import RemoveServiceUseCase
from app.features.walkins.use_cases.apply_discount import ApplyDiscountUseCase
from app.features.walkins.use_cases.complete_walkin import CompleteWalkInUseCase
from app.features.walkins.use_cases.record_payment import RecordPaymentUseCase
from app.features.walkins.use_cases.cancel_walkin import CancelWalkInUseCase
from app.features.walkins.use_cases.get_walkin import GetWalkInUseCase
from app.features.walkins.use_cases.list_walkins import ListWalkInsUseCase
from app.features.walkins.use_cases.get_daily_report import GetDailyReportUseCase


# ============================================================================
# Repository Dependencies
# ============================================================================


def get_walkin_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> WalkInRepository:
    """Get walk-in repository."""
    return WalkInRepository(session)


# ============================================================================
# Use Case Dependencies
# ============================================================================


def get_create_walkin_use_case(
    repository: Annotated[WalkInRepository, Depends(get_walkin_repository)]
) -> CreateWalkInUseCase:
    """Get create walk-in use case."""
    return CreateWalkInUseCase(repository)


def get_add_service_use_case(
    repository: Annotated[WalkInRepository, Depends(get_walkin_repository)]
) -> AddServiceUseCase:
    """Get add service use case."""
    return AddServiceUseCase(repository)


def get_remove_service_use_case(
    repository: Annotated[WalkInRepository, Depends(get_walkin_repository)]
) -> RemoveServiceUseCase:
    """Get remove service use case."""
    return RemoveServiceUseCase(repository)


def get_apply_discount_use_case(
    repository: Annotated[WalkInRepository, Depends(get_walkin_repository)]
) -> ApplyDiscountUseCase:
    """Get apply discount use case."""
    return ApplyDiscountUseCase(repository)


def get_complete_walkin_use_case(
    repository: Annotated[WalkInRepository, Depends(get_walkin_repository)]
) -> CompleteWalkInUseCase:
    """Get complete walk-in use case."""
    return CompleteWalkInUseCase(repository)


def get_record_payment_use_case(
    repository: Annotated[WalkInRepository, Depends(get_walkin_repository)]
) -> RecordPaymentUseCase:
    """Get record payment use case."""
    return RecordPaymentUseCase(repository)


def get_cancel_walkin_use_case(
    repository: Annotated[WalkInRepository, Depends(get_walkin_repository)]
) -> CancelWalkInUseCase:
    """Get cancel walk-in use case."""
    return CancelWalkInUseCase(repository)


def get_get_walkin_use_case(
    repository: Annotated[WalkInRepository, Depends(get_walkin_repository)]
) -> GetWalkInUseCase:
    """Get get walk-in use case."""
    return GetWalkInUseCase(repository)


def get_list_walkins_use_case(
    repository: Annotated[WalkInRepository, Depends(get_walkin_repository)]
) -> ListWalkInsUseCase:
    """Get list walk-ins use case."""
    return ListWalkInsUseCase(repository)


def get_daily_report_use_case(
    repository: Annotated[WalkInRepository, Depends(get_walkin_repository)]
) -> GetDailyReportUseCase:
    """Get daily report use case."""
    return GetDailyReportUseCase(repository)
