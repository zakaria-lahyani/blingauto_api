"""Create staff member use case."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional
import uuid

from app.core.errors import ValidationError, BusinessRuleViolationError
from app.features.staff.domain import (
    StaffMember,
    EmploymentType,
    StaffStatus,
    ServiceType,
    StaffManagementPolicy,
)
from app.features.staff.ports import IStaffRepository


@dataclass
class CreateStaffRequest:
    """Request to create a staff member."""

    user_id: str
    first_name: str
    last_name: str
    phone: str
    email: str
    hire_date: date
    employment_type: EmploymentType
    hourly_rate: Decimal
    assigned_bay_id: Optional[str] = None
    assigned_team_id: Optional[str] = None
    skills: List[ServiceType] = None

    def __post_init__(self):
        if self.skills is None:
            self.skills = []


class CreateStaffUseCase:
    """
    Create a new staff member.

    Business Rules:
    - Employee code is auto-generated
    - Hourly rate must be within acceptable range
    - Hire date cannot be in the future
    - User ID must be unique (one staff profile per user)
    """

    def __init__(self, staff_repository: IStaffRepository):
        self._staff_repository = staff_repository

    async def execute(self, request: CreateStaffRequest) -> StaffMember:
        """
        Execute the create staff use case.

        Args:
            request: Create staff request

        Returns:
            StaffMember: Created staff member

        Raises:
            ValidationError: If validation fails
            BusinessRuleViolationError: If business rules are violated
        """
        # Validate input
        await self._validate_request(request)

        # Apply business rules
        StaffManagementPolicy.validate_hourly_rate(request.hourly_rate)
        StaffManagementPolicy.validate_hire_date(request.hire_date)

        # Check if user already has a staff profile
        existing_staff = await self._staff_repository.get_by_user_id(request.user_id)
        if existing_staff:
            raise BusinessRuleViolationError(
                "User already has a staff profile",
                details={"user_id": request.user_id, "staff_id": existing_staff.id},
            )

        # Generate employee code
        staff_count = await self._staff_repository.count()
        employee_code = StaffManagementPolicy.generate_employee_code(staff_count)

        # Ensure employee code is unique
        while await self._staff_repository.employee_code_exists(employee_code):
            staff_count += 1
            employee_code = StaffManagementPolicy.generate_employee_code(staff_count)

        # Create staff member entity
        staff = StaffMember(
            id=str(uuid.uuid4()),
            user_id=request.user_id,
            employee_code=employee_code,
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone,
            email=request.email,
            hire_date=request.hire_date,
            employment_type=request.employment_type,
            status=StaffStatus.ACTIVE,
            hourly_rate=request.hourly_rate,
            assigned_bay_id=request.assigned_bay_id,
            assigned_team_id=request.assigned_team_id,
            skills=request.skills or [],
        )

        # Persist to repository
        created_staff = await self._staff_repository.create(staff)

        return created_staff

    async def _validate_request(self, request: CreateStaffRequest) -> None:
        """Validate the request."""
        errors = []

        if not request.user_id or not request.user_id.strip():
            errors.append("User ID is required")

        if not request.first_name or not request.first_name.strip():
            errors.append("First name is required")

        if not request.last_name or not request.last_name.strip():
            errors.append("Last name is required")

        if not request.phone or not request.phone.strip():
            errors.append("Phone is required")

        if not request.email or not request.email.strip():
            errors.append("Email is required")

        if request.hourly_rate <= 0:
            errors.append("Hourly rate must be greater than 0")

        if errors:
            raise ValidationError("Invalid create staff request", details={"errors": errors})
