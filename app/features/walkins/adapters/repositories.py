"""Walk-in repository implementation."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
import json

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.walkins.domain.entities import (
    WalkInService,
    WalkInServiceItem,
)
from app.features.walkins.domain.enums import (
    WalkInStatus,
    PaymentStatus,
    PaymentMethod,
    VehicleSize,
)
from app.features.walkins.ports.repositories import IWalkInRepository
from app.features.walkins.adapters.models import (
    WalkInServiceModel,
    WalkInServiceItemModel,
)


class WalkInRepository(IWalkInRepository):
    """Walk-in repository implementation using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self._session = session

    async def create(self, walkin: WalkInService) -> WalkInService:
        """Create walk-in service."""
        model = self._to_model(walkin)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def update(self, walkin: WalkInService) -> WalkInService:
        """Update walk-in service."""
        # Get existing model
        stmt = (
            select(WalkInServiceModel)
            .where(WalkInServiceModel.id == walkin.id)
            .options(selectinload(WalkInServiceModel.service_items))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise LookupError(f"Walk-in service {walkin.id} not found")

        # Update fields
        model.vehicle_make = walkin.vehicle_make
        model.vehicle_model = walkin.vehicle_model
        model.vehicle_color = walkin.vehicle_color
        model.vehicle_size = walkin.vehicle_size.value
        model.license_plate = walkin.license_plate
        model.customer_name = walkin.customer_name
        model.customer_phone = walkin.customer_phone
        model.status = walkin.status.value
        model.payment_status = walkin.payment_status.value
        model.total_amount = walkin.total_amount
        model.discount_amount = walkin.discount_amount
        model.discount_reason = walkin.discount_reason
        model.final_amount = walkin.final_amount
        model.paid_amount = walkin.paid_amount
        model.completed_at = walkin.completed_at
        model.cancelled_at = walkin.cancelled_at
        model.completed_by_id = walkin.completed_by_id
        model.cancelled_by_id = walkin.cancelled_by_id
        model.notes = walkin.notes
        model.cancellation_reason = walkin.cancellation_reason
        model.payment_details = (
            json.loads(walkin.payment_details) if walkin.payment_details else None
        )
        model.updated_at = datetime.utcnow()

        # Update service items - delete and recreate
        for item in model.service_items:
            await self._session.delete(item)

        for service in walkin.services:
            item_model = WalkInServiceItemModel(
                id=service.id,
                walkin_id=walkin.id,
                service_id=service.service_id,
                service_name=service.service_name,
                price=service.price,
                product_costs=service.product_costs,
                quantity=service.quantity,
                notes=service.notes,
            )
            self._session.add(item_model)

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, walkin_id: str) -> Optional[WalkInService]:
        """Get walk-in by ID."""
        stmt = (
            select(WalkInServiceModel)
            .where(WalkInServiceModel.id == walkin_id)
            .where(WalkInServiceModel.deleted_at.is_(None))
            .options(selectinload(WalkInServiceModel.service_items))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_service_number(
        self, service_number: str
    ) -> Optional[WalkInService]:
        """Get walk-in by service number."""
        stmt = (
            select(WalkInServiceModel)
            .where(WalkInServiceModel.service_number == service_number)
            .where(WalkInServiceModel.deleted_at.is_(None))
            .options(selectinload(WalkInServiceModel.service_items))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_date(self, service_date: date) -> List[WalkInService]:
        """List walk-ins by date."""
        start_datetime = datetime.combine(service_date, datetime.min.time())
        end_datetime = datetime.combine(service_date, datetime.max.time())

        stmt = (
            select(WalkInServiceModel)
            .where(
                and_(
                    WalkInServiceModel.started_at >= start_datetime,
                    WalkInServiceModel.started_at <= end_datetime,
                    WalkInServiceModel.deleted_at.is_(None),
                )
            )
            .options(selectinload(WalkInServiceModel.service_items))
            .order_by(WalkInServiceModel.started_at.desc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def list_with_filters(
        self,
        status: Optional[WalkInStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        created_by_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[WalkInService]:
        """List walk-ins with filters."""
        conditions = [WalkInServiceModel.deleted_at.is_(None)]

        if status:
            conditions.append(WalkInServiceModel.status == status.value)

        if payment_status:
            conditions.append(WalkInServiceModel.payment_status == payment_status.value)

        if created_by_id:
            conditions.append(WalkInServiceModel.created_by_id == created_by_id)

        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            conditions.append(WalkInServiceModel.started_at >= start_datetime)

        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            conditions.append(WalkInServiceModel.started_at <= end_datetime)

        stmt = (
            select(WalkInServiceModel)
            .where(and_(*conditions))
            .options(selectinload(WalkInServiceModel.service_items))
            .order_by(WalkInServiceModel.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def get_next_service_number(self, date_prefix: str) -> str:
        """
        Generate next service number for the day.
        Format: WI-20251002-001, WI-20251002-002, etc.
        """
        pattern = f"WI-{date_prefix}-%"

        stmt = select(func.count()).where(
            WalkInServiceModel.service_number.like(pattern)
        )
        result = await self._session.execute(stmt)
        count = result.scalar() or 0

        return f"WI-{date_prefix}-{count + 1:03d}"

    async def delete(self, walkin_id: str) -> None:
        """Soft delete walk-in (mark as deleted)."""
        stmt = select(WalkInServiceModel).where(WalkInServiceModel.id == walkin_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.deleted_at = datetime.utcnow()
            await self._session.flush()

    def _to_domain(self, model: WalkInServiceModel) -> WalkInService:
        """Convert model to domain entity."""
        service_items = [
            WalkInServiceItem(
                id=item.id,
                service_id=item.service_id,
                service_name=item.service_name,
                price=item.price,
                product_costs=item.product_costs,
                quantity=item.quantity,
                notes=item.notes,
            )
            for item in model.service_items
        ]

        return WalkInService(
            id=model.id,
            service_number=model.service_number,
            vehicle_make=model.vehicle_make,
            vehicle_model=model.vehicle_model,
            vehicle_color=model.vehicle_color,
            vehicle_size=VehicleSize(model.vehicle_size),
            license_plate=model.license_plate,
            customer_name=model.customer_name,
            customer_phone=model.customer_phone,
            status=WalkInStatus(model.status),
            payment_status=PaymentStatus(model.payment_status),
            services=service_items,
            total_amount=model.total_amount,
            discount_amount=model.discount_amount,
            discount_reason=model.discount_reason,
            final_amount=model.final_amount,
            paid_amount=model.paid_amount,
            started_at=model.started_at,
            completed_at=model.completed_at,
            cancelled_at=model.cancelled_at,
            created_by_id=model.created_by_id,
            completed_by_id=model.completed_by_id,
            cancelled_by_id=model.cancelled_by_id,
            notes=model.notes,
            cancellation_reason=model.cancellation_reason,
            payment_details=json.dumps(model.payment_details)
            if model.payment_details
            else None,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, walkin: WalkInService) -> WalkInServiceModel:
        """Convert domain entity to model."""
        model = WalkInServiceModel(
            id=walkin.id,
            service_number=walkin.service_number,
            vehicle_make=walkin.vehicle_make,
            vehicle_model=walkin.vehicle_model,
            vehicle_color=walkin.vehicle_color,
            vehicle_size=walkin.vehicle_size.value,
            license_plate=walkin.license_plate,
            customer_name=walkin.customer_name,
            customer_phone=walkin.customer_phone,
            status=walkin.status.value,
            payment_status=walkin.payment_status.value,
            total_amount=walkin.total_amount,
            discount_amount=walkin.discount_amount,
            discount_reason=walkin.discount_reason,
            final_amount=walkin.final_amount,
            paid_amount=walkin.paid_amount,
            started_at=walkin.started_at,
            completed_at=walkin.completed_at,
            cancelled_at=walkin.cancelled_at,
            created_by_id=walkin.created_by_id,
            completed_by_id=walkin.completed_by_id,
            cancelled_by_id=walkin.cancelled_by_id,
            notes=walkin.notes,
            cancellation_reason=walkin.cancellation_reason,
            payment_details=json.loads(walkin.payment_details)
            if walkin.payment_details
            else None,
            created_at=walkin.created_at if walkin.created_at else datetime.utcnow(),
            updated_at=walkin.updated_at if walkin.updated_at else datetime.utcnow(),
        )

        # Add service items
        model.service_items = [
            WalkInServiceItemModel(
                id=item.id,
                walkin_id=walkin.id,
                service_id=item.service_id,
                service_name=item.service_name,
                price=item.price,
                product_costs=item.product_costs,
                quantity=item.quantity,
                notes=item.notes,
            )
            for item in walkin.services
        ]

        return model
