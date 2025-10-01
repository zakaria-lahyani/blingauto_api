"""Services API dependencies."""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

from app.shared.auth import CurrentUser
from app.core.db import get_db
from app.features.services.adapters import (
    SqlCategoryRepository,
    SqlServiceRepository,
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


def get_current_user():
    """Get current authenticated user."""
    return CurrentUser


def get_category_repository(db: Session = Depends(get_db)) -> SqlCategoryRepository:
    """Get category repository."""
    return SqlCategoryRepository(db)


def get_service_repository(db: Session = Depends(get_db)) -> SqlServiceRepository:
    """Get service repository."""
    return SqlServiceRepository(db)


def get_cache_service() -> RedisCacheService:
    """Get cache service."""
    return RedisCacheService()


def get_event_service() -> EventBusService:
    """Get event service."""
    return EventBusService()


def get_notification_service() -> EmailNotificationService:
    """Get notification service."""
    return EmailNotificationService()


def get_audit_service() -> AuditService:
    """Get audit service."""
    return AuditService()


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
    cache_service: Annotated[RedisCacheService, Depends(get_cache_service)],
    event_service: Annotated[EventBusService, Depends(get_event_service)],
    notification_service: Annotated[EmailNotificationService, Depends(get_notification_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> UpdateServicePriceUseCase:
    """Get update service price use case."""
    # Note: BookingRepository not available in this context, using None for now
    return UpdateServicePriceUseCase(
        service_repository=service_repo,
        booking_repository=None,  # TODO: Add booking repository dependency
        cache_service=cache_service,
        event_service=event_service,
        notification_service=notification_service,
        audit_service=audit_service,
    )


def get_set_service_popular_use_case(
    service_repo: Annotated[SqlServiceRepository, Depends(get_service_repository)],
    category_repo: Annotated[SqlCategoryRepository, Depends(get_category_repository)],
    cache_service: Annotated[RedisCacheService, Depends(get_cache_service)],
    event_service: Annotated[EventBusService, Depends(get_event_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> SetServicePopularUseCase:
    """Get set service popular use case."""
    return SetServicePopularUseCase(
        service_repository=service_repo,
        category_repository=category_repo,
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