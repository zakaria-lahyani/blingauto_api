from typing import Annotated
from fastapi import Depends

from app.core.db import UnitOfWork, get_unit_of_work
# TODO: Fix service imports - using stubs for now
def get_email_service():
    """Stub for email service."""
    class StubEmailService:
        def send_email(self, *args, **kwargs):
            pass
    return StubEmailService()

def get_cache_service():
    """Stub for cache service.""" 
    class StubCacheService:
        def get(self, *args, **kwargs):
            return None
        def set(self, *args, **kwargs):
            pass
    return StubCacheService()

def get_event_service():
    """Stub for event service."""
    class StubEventService:
        def publish(self, *args, **kwargs):
            pass
    return StubEventService()

def get_lock_service():
    """Stub for lock service."""
    class StubLockService:
        def acquire_lock(self, *args, **kwargs):
            return True
        def release_lock(self, *args, **kwargs):
            pass
    return StubLockService()
from app.features.bookings.adapters import (
    SqlBookingRepository,
    SqlServiceRepository,
    SqlVehicleRepository,
    SqlCustomerRepository,
    EmailNotificationService,
    StripePaymentService,
    RedisCacheService,
    EventBusService,
    RedisLockService,
)
from app.features.bookings.adapters.capacity_service import WashBayCapacityService
from app.features.bookings.use_cases import (
    CreateBookingUseCase,
    CancelBookingUseCase,
    GetBookingUseCase,
    ListBookingsUseCase,
    UpdateBookingUseCase,
    ConfirmBookingUseCase,
    StartBookingUseCase,
    CompleteBookingUseCase,
    RescheduleBookingUseCase,
    AddServiceToBookingUseCase,
    RemoveServiceFromBookingUseCase,
    MarkNoShowUseCase,
    RateBookingUseCase,
)


def get_booking_repository(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)]
) -> SqlBookingRepository:
    """Get booking repository."""
    return SqlBookingRepository(uow.session)


def get_service_repository(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)]
) -> SqlServiceRepository:
    """Get service repository."""
    return SqlServiceRepository(uow.session)


def get_vehicle_repository(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)]
) -> SqlVehicleRepository:
    """Get vehicle repository."""
    return SqlVehicleRepository(uow.session)


def get_customer_repository(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)]
) -> SqlCustomerRepository:
    """Get customer repository."""
    return SqlCustomerRepository(uow.session)


def get_notification_service(
    email_service=Depends(get_email_service)
) -> EmailNotificationService:
    """Get notification service."""
    return EmailNotificationService(email_service)


def get_payment_service() -> StripePaymentService:
    """Get payment service."""
    # Would inject Stripe client
    return StripePaymentService(None)


def get_booking_cache_service(
    cache_service=Depends(get_cache_service)
) -> RedisCacheService:
    """Get cache service for bookings."""
    return RedisCacheService(cache_service)


def get_booking_event_service(
    event_service=Depends(get_event_service)
) -> EventBusService:
    """Get event service for bookings."""
    return EventBusService(event_service)


def get_booking_lock_service(
    lock_service=Depends(get_lock_service)
) -> RedisLockService:
    """Get lock service for bookings."""
    return RedisLockService(lock_service)


def get_capacity_service(
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)]
) -> WashBayCapacityService:
    """Get wash bay capacity service."""
    return WashBayCapacityService(uow.session)


def get_create_booking_use_case(
    booking_repo: Annotated[SqlBookingRepository, Depends(get_booking_repository)],
    service_repo: Annotated[SqlServiceRepository, Depends(get_service_repository)],
    vehicle_repo: Annotated[SqlVehicleRepository, Depends(get_vehicle_repository)],
    customer_repo: Annotated[SqlCustomerRepository, Depends(get_customer_repository)],
    notification_service: Annotated[EmailNotificationService, Depends(get_notification_service)],
    event_service: Annotated[EventBusService, Depends(get_booking_event_service)],
    lock_service: Annotated[RedisLockService, Depends(get_booking_lock_service)],
    capacity_service: Annotated[WashBayCapacityService, Depends(get_capacity_service)],
) -> CreateBookingUseCase:
    """Get create booking use case."""
    # Create validators
    from app.features.bookings.adapters.external_services import (
        ExternalServiceValidator,
        ExternalVehicleValidator,
    )
    service_validator = ExternalServiceValidator(service_repo, customer_repo)
    vehicle_validator = ExternalVehicleValidator(vehicle_repo)

    return CreateBookingUseCase(
        booking_repository=booking_repo,
        notification_service=notification_service,
        event_service=event_service,
        lock_service=lock_service,
        service_validator=service_validator,
        vehicle_validator=vehicle_validator,
        capacity_service=capacity_service,
    )


def get_cancel_booking_use_case(
    booking_repo: Annotated[SqlBookingRepository, Depends(get_booking_repository)],
    customer_repo: Annotated[SqlCustomerRepository, Depends(get_customer_repository)],
    notification_service: Annotated[EmailNotificationService, Depends(get_notification_service)],
    payment_service: Annotated[StripePaymentService, Depends(get_payment_service)],
    event_service: Annotated[EventBusService, Depends(get_booking_event_service)],
    cache_service: Annotated[RedisCacheService, Depends(get_booking_cache_service)],
) -> CancelBookingUseCase:
    """Get cancel booking use case."""
    return CancelBookingUseCase(
        booking_repository=booking_repo,
        customer_repository=customer_repo,
        notification_service=notification_service,
        payment_service=payment_service,
        event_service=event_service,
        cache_service=cache_service,
    )


def get_get_booking_use_case(
    booking_repo: Annotated[SqlBookingRepository, Depends(get_booking_repository)],
    service_repo: Annotated[SqlServiceRepository, Depends(get_service_repository)],
    vehicle_repo: Annotated[SqlVehicleRepository, Depends(get_vehicle_repository)],
    customer_repo: Annotated[SqlCustomerRepository, Depends(get_customer_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_booking_cache_service)],
) -> GetBookingUseCase:
    """Get get booking use case."""
    return GetBookingUseCase(
        booking_repository=booking_repo,
        service_repository=service_repo,
        vehicle_repository=vehicle_repo,
        customer_repository=customer_repo,
        cache_service=cache_service,
    )


def get_list_bookings_use_case(
    booking_repo: Annotated[SqlBookingRepository, Depends(get_booking_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_booking_cache_service)],
) -> ListBookingsUseCase:
    """Get list bookings use case."""
    return ListBookingsUseCase(
        booking_repository=booking_repo,
        cache_service=cache_service,
    )


def get_update_booking_use_case(
    booking_repo: Annotated[SqlBookingRepository, Depends(get_booking_repository)],
    service_repo: Annotated[SqlServiceRepository, Depends(get_service_repository)],
    vehicle_repo: Annotated[SqlVehicleRepository, Depends(get_vehicle_repository)],
    customer_repo: Annotated[SqlCustomerRepository, Depends(get_customer_repository)],
    notification_service: Annotated[EmailNotificationService, Depends(get_notification_service)],
    event_service: Annotated[EventBusService, Depends(get_booking_event_service)],
    cache_service: Annotated[RedisCacheService, Depends(get_booking_cache_service)],
    lock_service: Annotated[RedisLockService, Depends(get_booking_lock_service)],
) -> UpdateBookingUseCase:
    """Get update booking use case."""
    return UpdateBookingUseCase(
        booking_repository=booking_repo,
        service_repository=service_repo,
        vehicle_repository=vehicle_repo,
        customer_repository=customer_repo,
        notification_service=notification_service,
        event_service=event_service,
        cache_service=cache_service,
        lock_service=lock_service,
    )


# ============================================================================
# NEW USE CASES - State Transition & Service Management
# ============================================================================

def get_confirm_booking_use_case(
    booking_repo: Annotated[SqlBookingRepository, Depends(get_booking_repository)],
    notification_service: Annotated[EmailNotificationService, Depends(get_notification_service)],
    event_service: Annotated[EventBusService, Depends(get_booking_event_service)],
    cache_service: Annotated[RedisCacheService, Depends(get_booking_cache_service)],
) -> ConfirmBookingUseCase:
    """Get confirm booking use case."""
    return ConfirmBookingUseCase(
        booking_repository=booking_repo,
        notification_service=notification_service,
        event_service=event_service,
        cache_service=cache_service,
    )


def get_start_booking_use_case(
    booking_repo: Annotated[SqlBookingRepository, Depends(get_booking_repository)],
    notification_service: Annotated[EmailNotificationService, Depends(get_notification_service)],
    event_service: Annotated[EventBusService, Depends(get_booking_event_service)],
    cache_service: Annotated[RedisCacheService, Depends(get_booking_cache_service)],
) -> StartBookingUseCase:
    """Get start booking use case."""
    return StartBookingUseCase(
        booking_repository=booking_repo,
        notification_service=notification_service,
        event_service=event_service,
        cache_service=cache_service,
    )


def get_complete_booking_use_case(
    booking_repo: Annotated[SqlBookingRepository, Depends(get_booking_repository)],
    notification_service: Annotated[EmailNotificationService, Depends(get_notification_service)],
    event_service: Annotated[EventBusService, Depends(get_booking_event_service)],
    cache_service: Annotated[RedisCacheService, Depends(get_booking_cache_service)],
) -> CompleteBookingUseCase:
    """Get complete booking use case."""
    return CompleteBookingUseCase(
        booking_repository=booking_repo,
        notification_service=notification_service,
        event_service=event_service,
        cache_service=cache_service,
    )


def get_reschedule_booking_use_case(
    booking_repo: Annotated[SqlBookingRepository, Depends(get_booking_repository)],
    notification_service: Annotated[EmailNotificationService, Depends(get_notification_service)],
    event_service: Annotated[EventBusService, Depends(get_booking_event_service)],
    cache_service: Annotated[RedisCacheService, Depends(get_booking_cache_service)],
    lock_service: Annotated[RedisLockService, Depends(get_booking_lock_service)],
) -> RescheduleBookingUseCase:
    """Get reschedule booking use case."""
    return RescheduleBookingUseCase(
        booking_repository=booking_repo,
        notification_service=notification_service,
        event_service=event_service,
        cache_service=cache_service,
        lock_service=lock_service,
    )


def get_add_service_to_booking_use_case(
    booking_repo: Annotated[SqlBookingRepository, Depends(get_booking_repository)],
    service_repo: Annotated[SqlServiceRepository, Depends(get_service_repository)],
    notification_service: Annotated[EmailNotificationService, Depends(get_notification_service)],
    event_service: Annotated[EventBusService, Depends(get_booking_event_service)],
    cache_service: Annotated[RedisCacheService, Depends(get_booking_cache_service)],
) -> AddServiceToBookingUseCase:
    """Get add service to booking use case."""
    # Create service validator adapter
    from app.features.bookings.adapters.external_services import ExternalServiceValidator
    service_validator = ExternalServiceValidator(service_repo)

    return AddServiceToBookingUseCase(
        booking_repository=booking_repo,
        notification_service=notification_service,
        event_service=event_service,
        cache_service=cache_service,
        service_validator=service_validator,
    )


def get_remove_service_from_booking_use_case(
    booking_repo: Annotated[SqlBookingRepository, Depends(get_booking_repository)],
    notification_service: Annotated[EmailNotificationService, Depends(get_notification_service)],
    event_service: Annotated[EventBusService, Depends(get_booking_event_service)],
    cache_service: Annotated[RedisCacheService, Depends(get_booking_cache_service)],
) -> RemoveServiceFromBookingUseCase:
    """Get remove service from booking use case."""
    return RemoveServiceFromBookingUseCase(
        booking_repository=booking_repo,
        notification_service=notification_service,
        event_service=event_service,
        cache_service=cache_service,
    )


def get_mark_no_show_use_case(
    booking_repo: Annotated[SqlBookingRepository, Depends(get_booking_repository)],
    notification_service: Annotated[EmailNotificationService, Depends(get_notification_service)],
    event_service: Annotated[EventBusService, Depends(get_booking_event_service)],
    cache_service: Annotated[RedisCacheService, Depends(get_booking_cache_service)],
    payment_service: Annotated[StripePaymentService, Depends(get_payment_service)],
) -> MarkNoShowUseCase:
    """Get mark no-show use case."""
    return MarkNoShowUseCase(
        booking_repository=booking_repo,
        notification_service=notification_service,
        event_service=event_service,
        cache_service=cache_service,
        payment_service=payment_service,
    )


def get_rate_booking_use_case(
    booking_repo: Annotated[SqlBookingRepository, Depends(get_booking_repository)],
    notification_service: Annotated[EmailNotificationService, Depends(get_notification_service)],
    event_service: Annotated[EventBusService, Depends(get_booking_event_service)],
    cache_service: Annotated[RedisCacheService, Depends(get_booking_cache_service)],
) -> RateBookingUseCase:
    """Get rate booking use case."""
    return RateBookingUseCase(
        booking_repository=booking_repo,
        notification_service=notification_service,
        event_service=event_service,
        cache_service=cache_service,
    )