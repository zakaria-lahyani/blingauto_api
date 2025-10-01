"""Update staff member use case."""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from app.core.errors import NotFoundError, ValidationError
from app.features.staff.domain import (
    StaffMember,
    EmploymentType,
    StaffStatus,
    ServiceType,
    StaffManagementPolicy,
)
from app.features.staff.ports import IStaffRepository


@dataclass
class UpdateStaffRequest:
    """Request to update staff member."""

    staff_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    employment_type: Optional[EmploymentType] = None
    status: Optional[StaffStatus] = None
    hourly_rate: Optional[Decimal] = None
    assigned_bay_id: Optional[str] = None
    assigned_team_id: Optional[str] = None
    skills: Optional[List[ServiceType]] = None


class UpdateStaffUseCase:
    """
    Update staff member information.

    Business Rules:
    - Cannot update employee code or hire date
    - Hourly rate must be within acceptable range
    - Status transitions must follow business rules
    """

    def __init__(self, staff_repository: IStaffRepository):
        self._staff_repository = staff_repository

    async def execute(self, request: UpdateStaffRequest) -> StaffMember:
        """
        Execute the update staff use case.

        Args:
            request: Update staff request

        Returns:
            StaffMember: Updated staff member

        Raises:
            NotFoundError: If staff member not found
            ValidationError: If validation fails
        """
        # Get existing staff member
        staff = await self._staff_repository.get_by_id(request.staff_id)
        if not staff:
            raise NotFoundError(f"Staff member not found: {request.staff_id}")

        # Update fields if provided
        if request.first_name is not None:
            if not request.first_name.strip():
                raise ValidationError("First name cannot be empty")
            staff.first_name = request.first_name

        if request.last_name is not None:
            if not request.last_name.strip():
                raise ValidationError("Last name cannot be empty")
            staff.last_name = request.last_name

        if request.phone is not None:
            if not request.phone.strip():
                raise ValidationError("Phone cannot be empty")
            staff.phone = request.phone

        if request.email is not None:
            if not request.email.strip():
                raise ValidationError("Email cannot be empty")
            staff.email = request.email

        if request.employment_type is not None:
            staff.employment_type = request.employment_type

        if request.status is not None:
            # Validate status transition
            self._validate_status_transition(staff, request.status)
            staff.status = request.status

        if request.hourly_rate is not None:
            StaffManagementPolicy.validate_hourly_rate(request.hourly_rate)
            staff.hourly_rate = request.hourly_rate

        if request.assigned_bay_id is not None:
            staff.assigned_bay_id = request.assigned_bay_id

        if request.assigned_team_id is not None:
            staff.assigned_team_id = request.assigned_team_id

        if request.skills is not None:
            staff.skills = request.skills

        # Persist changes
        updated_staff = await self._staff_repository.update(staff)

        return updated_staff

    def _validate_status_transition(
        self, staff: StaffMember, new_status: StaffStatus
    ) -> None:
        """Validate status transition is allowed."""
        if new_status == staff.status:
            return  # No change

        if new_status == StaffStatus.TERMINATED:
            if not StaffManagementPolicy.can_terminate(staff):
                raise ValidationError(
                    f"Cannot terminate staff with status: {staff.status}"
                )

        if new_status == StaffStatus.SUSPENDED:
            if not StaffManagementPolicy.can_suspend(staff):
                raise ValidationError(f"Cannot suspend staff with status: {staff.status}")

        if new_status == StaffStatus.ACTIVE:
            if staff.status == StaffStatus.TERMINATED:
                raise ValidationError("Cannot reactivate terminated staff")
