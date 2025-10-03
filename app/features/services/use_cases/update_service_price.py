from dataclasses import dataclass
from decimal import Decimal
from typing import List

from app.core.errors import ValidationError, BusinessRuleViolationError, NotFoundError
from app.features.services.domain import ServiceManagementPolicy, ServiceStatus
from app.features.services.ports import (
    IServiceRepository,
    IBookingRepository,
    ICacheService,
    IEventService,
    INotificationService,
    IAuditService,
)


@dataclass
class UpdateServicePriceRequest:
    service_id: str
    new_price: Decimal
    updated_by: str
    notify_customers: bool = True


@dataclass
class UpdateServicePriceResponse:
    service_id: str
    old_price: Decimal
    new_price: Decimal
    price_change_percent: Decimal
    affected_future_bookings: int
    customers_notified: int
    price_display: str


class UpdateServicePriceUseCase:
    """Use case for updating service price."""
    
    def __init__(
        self,
        service_repository: IServiceRepository,
        booking_repository: IBookingRepository,
        cache_service: ICacheService,
        event_service: IEventService,
        notification_service: INotificationService,
        audit_service: IAuditService,
    ):
        self._service_repository = service_repository
        self._booking_repository = booking_repository
        self._cache_service = cache_service
        self._event_service = event_service
        self._notification_service = notification_service
        self._audit_service = audit_service
    
    async def execute(self, request: UpdateServicePriceRequest) -> UpdateServicePriceResponse:
        """Execute the update service price use case."""
        
        # Step 1: Get existing service
        service = await self._service_repository.get_by_id(request.service_id)
        if not service:
            raise NotFoundError(f"Service {request.service_id} not found")
        
        # Step 2: Validate service status
        if service.status == ServiceStatus.ARCHIVED:
            raise BusinessRuleViolationError("Cannot update price for archived service")
        
        # Step 3: Validate new price (RG-SVC-004)
        ServiceManagementPolicy.validate_pricing_rules(request.new_price)
        
        # Step 4: Calculate price change
        old_price = service.price
        price_change = request.new_price - old_price
        price_change_percent = (price_change / old_price * 100) if old_price > 0 else Decimal('0')

        # Step 5: Update service price (no restriction on price increase percentage)
        service.update_pricing(request.new_price)
        
        # Step 7: Save updated service
        updated_service = await self._service_repository.update(service)
        
        # Step 8: Clear cache
        await self._cache_service.delete_service(service.id)
        await self._cache_service.delete_category_services(service.category_id)
        
        # Step 9: Get affected future bookings count
        # This would query bookings with this service scheduled in the future
        affected_bookings_count = await self._booking_repository.count_bookings_for_service(
            service.id, start_date="future"
        )
        
        # Step 10: Publish price change event
        await self._event_service.publish_service_price_changed(
            updated_service, old_price, request.new_price
        )
        
        # Step 11: Notify affected customers if requested
        customers_notified = 0
        if request.notify_customers and affected_bookings_count > 0:
            # Get list of affected customers (simplified)
            affected_customers = []  # Would get from bookings
            
            await self._notification_service.notify_service_price_change(
                updated_service, old_price, request.new_price, affected_customers
            )
            customers_notified = len(affected_customers)
        
        # Step 12: Log audit event
        await self._audit_service.log_service_price_change(
            updated_service,
            request.updated_by,
            old_price,
            request.new_price,
            {
                "price_change": float(price_change),
                "price_change_percent": float(price_change_percent),
                "affected_bookings": affected_bookings_count,
                "customers_notified": customers_notified,
            }
        )
        
        # Step 13: Prepare response
        return UpdateServicePriceResponse(
            service_id=updated_service.id,
            old_price=old_price,
            new_price=updated_service.price,
            price_change_percent=price_change_percent,
            affected_future_bookings=affected_bookings_count,
            customers_notified=customers_notified,
            price_display=updated_service.price_display,
        )