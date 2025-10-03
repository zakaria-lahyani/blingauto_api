"""Services API dependencies."""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.auth import CurrentUser
from app.core.db import get_db
from app.features.services.adapters import (
    SqlCategoryRepository,
    SqlServiceRepository,
    SqlBookingRepository,
    RedisCacheService,
    EventBusService,
    EmailNotificationService,
    AuditService,
)
from app.features.services.use_cases import (
    CreateCategoryUseCase,
    CreateServiceUseCase,
    ListCategoriesUseCase,
    ListServicesUseCase,
    GetServiceUseCase,
    UpdateServicePriceUseCase,
    SetServicePopularUseCase,
    DeactivateServiceUseCase,
    GetPopularServicesUseCase,
    SearchServicesUseCase,
)


def get_category_repository(db: AsyncSession = Depends(get_db)) -> SqlCategoryRepository:
    """Get category repository."""
    return SqlCategoryRepository(db)


def get_service_repository(db: AsyncSession = Depends(get_db)) -> SqlServiceRepository:
    """Get service repository."""
    return SqlServiceRepository(db)


def get_booking_repository(db: AsyncSession = Depends(get_db)) -> SqlBookingRepository:
    """Get booking repository."""
    return SqlBookingRepository(db)


def get_cache_service() -> RedisCacheService:
    """Get cache service."""
    from app.core.cache import redis_client
    return RedisCacheService(redis_client)


def get_event_service() -> EventBusService:
    """Get event service."""
    # TODO: Implement proper event bus
    return EventBusService(event_bus=None)


def get_notification_service() -> EmailNotificationService:
    """Get notification service."""
    # TODO: Implement proper email service
    return EmailNotificationService(email_service=None)


def get_audit_service() -> AuditService:
    """Get audit service."""
    # TODO: Implement proper audit logger
    return AuditService(audit_logger=None)


def get_create_category_use_case(
    category_repo: Annotated[SqlCategoryRepository, Depends(get_category_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_cache_service)],
    event_service: Annotated[EventBusService, Depends(get_event_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> CreateCategoryUseCase:
    """Get create category use case."""
    return CreateCategoryUseCase(
        category_repository=category_repo,
        cache_service=cache_service,
        event_service=event_service,
        audit_service=audit_service,
    )


def get_create_service_use_case(
    service_repo: Annotated[SqlServiceRepository, Depends(get_service_repository)],
    category_repo: Annotated[SqlCategoryRepository, Depends(get_category_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_cache_service)],
    event_service: Annotated[EventBusService, Depends(get_event_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> CreateServiceUseCase:
    """Get create service use case."""
    return CreateServiceUseCase(
        service_repository=service_repo,
        category_repository=category_repo,
        cache_service=cache_service,
        event_service=event_service,
        audit_service=audit_service,
    )


def get_list_categories_use_case(
    category_repo: Annotated[SqlCategoryRepository, Depends(get_category_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_cache_service)],
) -> ListCategoriesUseCase:
    """Get list categories use case."""
    return ListCategoriesUseCase(
        category_repository=category_repo,
        cache_service=cache_service,
    )


def get_list_services_use_case(
    service_repo: Annotated[SqlServiceRepository, Depends(get_service_repository)],
    category_repo: Annotated[SqlCategoryRepository, Depends(get_category_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_cache_service)],
) -> ListServicesUseCase:
    """Get list services use case."""
    return ListServicesUseCase(
        service_repository=service_repo,
        category_repository=category_repo,
        cache_service=cache_service,
    )


def get_get_service_use_case(
    service_repo: Annotated[SqlServiceRepository, Depends(get_service_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_cache_service)],
) -> GetServiceUseCase:
    """Get get service use case."""
    return GetServiceUseCase(
        service_repository=service_repo,
        cache_service=cache_service,
    )


def get_update_service_price_use_case(
    service_repo: Annotated[SqlServiceRepository, Depends(get_service_repository)],
    booking_repo: Annotated[SqlBookingRepository, Depends(get_booking_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_cache_service)],
    event_service: Annotated[EventBusService, Depends(get_event_service)],
    notification_service: Annotated[EmailNotificationService, Depends(get_notification_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> UpdateServicePriceUseCase:
    """Get update service price use case."""
    return UpdateServicePriceUseCase(
        service_repository=service_repo,
        booking_repository=booking_repo,
        cache_service=cache_service,
        event_service=event_service,
        notification_service=notification_service,
        audit_service=audit_service,
    )


def get_set_service_popular_use_case(
    service_repo: Annotated[SqlServiceRepository, Depends(get_service_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_cache_service)],
    event_service: Annotated[EventBusService, Depends(get_event_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> SetServicePopularUseCase:
    """Get set service popular use case."""
    return SetServicePopularUseCase(
        service_repository=service_repo,
        cache_service=cache_service,
        event_service=event_service,
        audit_service=audit_service,
    )


def get_deactivate_service_use_case(
    service_repo: Annotated[SqlServiceRepository, Depends(get_service_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_cache_service)],
    event_service: Annotated[EventBusService, Depends(get_event_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> DeactivateServiceUseCase:
    """Get deactivate service use case."""
    return DeactivateServiceUseCase(
        service_repository=service_repo,
        cache_service=cache_service,
        event_service=event_service,
        audit_service=audit_service,
    )


def get_popular_services_use_case(
    service_repo: Annotated[SqlServiceRepository, Depends(get_service_repository)],
    category_repo: Annotated[SqlCategoryRepository, Depends(get_category_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_cache_service)],
) -> GetPopularServicesUseCase:
    """Get popular services use case."""
    return GetPopularServicesUseCase(
        service_repository=service_repo,
        category_repository=category_repo,
        cache_service=cache_service,
    )


def get_search_services_use_case(
    service_repo: Annotated[SqlServiceRepository, Depends(get_service_repository)],
    category_repo: Annotated[SqlCategoryRepository, Depends(get_category_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_cache_service)],
) -> SearchServicesUseCase:
    """Get search services use case."""
    return SearchServicesUseCase(
        service_repository=service_repo,
        category_repository=category_repo,
        cache_service=cache_service,
    )