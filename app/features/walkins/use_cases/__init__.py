"""Walk-in use cases - application logic."""

from .create_walkin import CreateWalkInUseCase, CreateWalkInRequest
from .add_service import AddServiceUseCase, AddServiceRequest
from .remove_service import RemoveServiceUseCase
from .apply_discount import ApplyDiscountUseCase, ApplyDiscountRequest
from .complete_walkin import CompleteWalkInUseCase
from .record_payment import RecordPaymentUseCase, RecordPaymentRequest
from .cancel_walkin import CancelWalkInUseCase
from .get_walkin import GetWalkInUseCase
from .list_walkins import ListWalkInsUseCase, ListWalkInsRequest
from .get_daily_report import GetDailyReportUseCase

__all__ = [
    "CreateWalkInUseCase",
    "CreateWalkInRequest",
    "AddServiceUseCase",
    "AddServiceRequest",
    "RemoveServiceUseCase",
    "ApplyDiscountUseCase",
    "ApplyDiscountRequest",
    "CompleteWalkInUseCase",
    "RecordPaymentUseCase",
    "RecordPaymentRequest",
    "CancelWalkInUseCase",
    "GetWalkInUseCase",
    "ListWalkInsUseCase",
    "ListWalkInsRequest",
    "GetDailyReportUseCase",
]
