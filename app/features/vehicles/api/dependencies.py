from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.shared.auth import CurrentUser
from app.core.db import AsyncSession, get_db
from app.core.dependencies import (
    get_cache_service,
    get_event_service,
    get_email_service,
    get_audit_service,
    get_current_user,
)
from app.features.vehicles.adapters import (
    SqlVehicleRepository,
    SqlCustomerRepository,
    SqlBookingRepository,
    RedisCacheService,
    EventBusService,
    EmailNotificationService,
    VehicleDataService,
    AuditService,
)
from app.features.vehicles.use_cases import (
    CreateVehicleUseCase,
    UpdateVehicleUseCase,
    DeleteVehicleUseCase,
    SetDefaultVehicleUseCase,
    ListVehiclesUseCase,
    GetVehicleUseCase,
)

security = HTTPBearer()


# get_current_user is imported from app.core.dependencies


def get_vehicle_repository(
    session: Annotated[AsyncSession, Depends(get_db)]
) -> SqlVehicleRepository:
    """Get vehicle repository."""
    return SqlVehicleRepository(session)


def get_customer_repository(
    session: Annotated[AsyncSession, Depends(get_db)]
) -> SqlCustomerRepository:
    """Get customer repository."""
    return SqlCustomerRepository(session)


def get_booking_repository(
    session: Annotated[AsyncSession, Depends(get_db)]
) -> SqlBookingRepository:
    """Get booking repository."""
    return SqlBookingRepository(session)


def get_vehicle_cache_service(
    cache_service=Depends(get_cache_service)
) -> RedisCacheService:
    """Get cache service for vehicles."""
    return RedisCacheService(cache_service)


def get_vehicle_event_service(
    event_service=Depends(get_event_service)
) -> EventBusService:
    """Get event service for vehicles."""
    return EventBusService(event_service)


def get_vehicle_notification_service(
    email_service=Depends(get_email_service)
) -> EmailNotificationService:
    """Get notification service for vehicles."""
    return EmailNotificationService(email_service)


def get_vehicle_data_service() -> VehicleDataService:
    """Get vehicle data service."""
    return VehicleDataService()


def get_vehicle_audit_service(
    audit_service=Depends(get_audit_service)
) -> AuditService:
    """Get audit service for vehicles."""
    return AuditService(audit_service)


def get_create_vehicle_use_case(
    vehicle_repo: Annotated[SqlVehicleRepository, Depends(get_vehicle_repository)],
    customer_repo: Annotated[SqlCustomerRepository, Depends(get_customer_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_vehicle_cache_service)],
    event_service: Annotated[EventBusService, Depends(get_vehicle_event_service)],
    notification_service: Annotated[EmailNotificationService, Depends(get_vehicle_notification_service)],
    audit_service: Annotated[AuditService, Depends(get_vehicle_audit_service)],
) -> CreateVehicleUseCase:
    """Get create vehicle use case."""
    return CreateVehicleUseCase(
        vehicle_repository=vehicle_repo,
        customer_repository=customer_repo,
        cache_service=cache_service,
        event_service=event_service,
        notification_service=notification_service,
        audit_service=audit_service,
    )


def get_update_vehicle_use_case(
    vehicle_repo: Annotated[SqlVehicleRepository, Depends(get_vehicle_repository)],
    customer_repo: Annotated[SqlCustomerRepository, Depends(get_customer_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_vehicle_cache_service)],
    event_service: Annotated[EventBusService, Depends(get_vehicle_event_service)],
    notification_service: Annotated[EmailNotificationService, Depends(get_vehicle_notification_service)],
    audit_service: Annotated[AuditService, Depends(get_vehicle_audit_service)],
) -> UpdateVehicleUseCase:
    """Get update vehicle use case."""
    return UpdateVehicleUseCase(
        vehicle_repository=vehicle_repo,
        customer_repository=customer_repo,
        cache_service=cache_service,
        event_service=event_service,
        notification_service=notification_service,
        audit_service=audit_service,
    )


def get_delete_vehicle_use_case(
    vehicle_repo: Annotated[SqlVehicleRepository, Depends(get_vehicle_repository)],
    booking_repo: Annotated[SqlBookingRepository, Depends(get_booking_repository)],
    customer_repo: Annotated[SqlCustomerRepository, Depends(get_customer_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_vehicle_cache_service)],
    event_service: Annotated[EventBusService, Depends(get_vehicle_event_service)],
    notification_service: Annotated[EmailNotificationService, Depends(get_vehicle_notification_service)],
    audit_service: Annotated[AuditService, Depends(get_vehicle_audit_service)],
) -> DeleteVehicleUseCase:
    """Get delete vehicle use case."""
    return DeleteVehicleUseCase(
        vehicle_repository=vehicle_repo,
        booking_repository=booking_repo,
        customer_repository=customer_repo,
        cache_service=cache_service,
        event_service=event_service,
        notification_service=notification_service,
        audit_service=audit_service,
    )


def get_set_default_vehicle_use_case(
    vehicle_repo: Annotated[SqlVehicleRepository, Depends(get_vehicle_repository)],
    customer_repo: Annotated[SqlCustomerRepository, Depends(get_customer_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_vehicle_cache_service)],
    event_service: Annotated[EventBusService, Depends(get_vehicle_event_service)],
    notification_service: Annotated[EmailNotificationService, Depends(get_vehicle_notification_service)],
    audit_service: Annotated[AuditService, Depends(get_vehicle_audit_service)],
) -> SetDefaultVehicleUseCase:
    """Get set default vehicle use case."""
    return SetDefaultVehicleUseCase(
        vehicle_repository=vehicle_repo,
        customer_repository=customer_repo,
        cache_service=cache_service,
        event_service=event_service,
        notification_service=notification_service,
        audit_service=audit_service,
    )


def get_list_vehicles_use_case(
    vehicle_repo: Annotated[SqlVehicleRepository, Depends(get_vehicle_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_vehicle_cache_service)],
) -> ListVehiclesUseCase:
    """Get list vehicles use case."""
    return ListVehiclesUseCase(
        vehicle_repository=vehicle_repo,
        cache_service=cache_service,
    )


def get_get_vehicle_use_case(
    vehicle_repo: Annotated[SqlVehicleRepository, Depends(get_vehicle_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_vehicle_cache_service)],
) -> GetVehicleUseCase:
    """Get get vehicle use case."""
    return GetVehicleUseCase(
        vehicle_repository=vehicle_repo,
        cache_service=cache_service,
    )