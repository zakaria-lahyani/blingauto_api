"""Authorization checking use cases."""

from typing import List
from dataclasses import dataclass
from enum import Enum

from ..domain import User, UserRole
from ..domain.exceptions import InsufficientPermissionError


class Permission(Enum):
    """Permission enumeration."""
    READ_USERS = "read_users"
    WRITE_USERS = "write_users"
    READ_BOOKINGS = "read_bookings"
    WRITE_BOOKINGS = "write_bookings"
    READ_SERVICES = "read_services"
    WRITE_SERVICES = "write_services"
    READ_VEHICLES = "read_vehicles"
    WRITE_VEHICLES = "write_vehicles"


@dataclass
class CheckRoleRequest:
    """Request to check if user has required role."""
    user: User
    required_role: UserRole


@dataclass
class CheckPermissionRequest:
    """Request to check if user has required permission."""
    user: User
    permission: Permission


class CheckRoleUseCase:
    """Use case for checking if user has required role with hierarchy support."""

    # Role hierarchy: admin > manager > washer > client
    ROLE_HIERARCHY = {
        UserRole.ADMIN: 4,
        UserRole.MANAGER: 3,
        UserRole.WASHER: 2,
        UserRole.CLIENT: 1,
    }

    def _has_role_or_higher(self, user_role: UserRole, required_role: UserRole) -> bool:
        """Check if user has required role or higher in hierarchy."""
        user_level = self.ROLE_HIERARCHY.get(user_role, 0)
        required_level = self.ROLE_HIERARCHY.get(required_role, 0)
        return user_level >= required_level

    async def execute(self, request: CheckRoleRequest) -> bool:
        """Check if user has required role (exact match only).

        Returns:
            True if user has required role

        Raises:
            InsufficientPermissionError: If user doesn't have required role
        """
        if request.user.role != request.required_role:
            raise InsufficientPermissionError(
                f"User role '{request.user.role.value}' does not match required role '{request.required_role.value}'"
            )

        return True


class CheckPermissionUseCase:
    """Use case for checking if user has required permission."""
    
    # Define role permissions (this is business logic in domain!)
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: [
            Permission.READ_USERS, Permission.WRITE_USERS,
            Permission.READ_BOOKINGS, Permission.WRITE_BOOKINGS,
            Permission.READ_SERVICES, Permission.WRITE_SERVICES,
            Permission.READ_VEHICLES, Permission.WRITE_VEHICLES,
        ],
        UserRole.WASHER: [
            Permission.READ_BOOKINGS, Permission.WRITE_BOOKINGS,
            Permission.READ_SERVICES, Permission.READ_VEHICLES,
        ],
        UserRole.CLIENT: [
            Permission.READ_SERVICES, Permission.READ_VEHICLES, Permission.WRITE_VEHICLES,
            Permission.READ_BOOKINGS, Permission.WRITE_BOOKINGS,
        ],
    }
    
    async def execute(self, request: CheckPermissionRequest) -> bool:
        """Check if user has required permission.
        
        Returns:
            True if user has permission
            
        Raises:
            InsufficientPermissionError: If user doesn't have permission
        """
        user_permissions = self.ROLE_PERMISSIONS.get(request.user.role, [])
        
        if request.permission not in user_permissions:
            raise InsufficientPermissionError(
                f"User role '{request.user.role.value}' does not have permission '{request.permission.value}'"
            )
        
        return True


class CheckStaffUseCase:
    """Use case for checking if user is staff (admin, manager, or washer)."""

    # Role hierarchy levels
    ROLE_HIERARCHY = {
        UserRole.ADMIN: 4,
        UserRole.MANAGER: 3,
        UserRole.WASHER: 2,
        UserRole.CLIENT: 1,
    }

    async def execute(self, user: User) -> bool:
        """Check if user is staff (washer or higher in hierarchy).

        Returns:
            True if user is staff

        Raises:
            InsufficientPermissionError: If user is not staff
        """
        # Staff = washer level or higher (washer, manager, admin)
        user_level = self.ROLE_HIERARCHY.get(user.role, 0)
        staff_level = self.ROLE_HIERARCHY.get(UserRole.WASHER, 2)

        if user_level < staff_level:
            raise InsufficientPermissionError(
                "Staff access required"
            )

        return True


class CheckManagerUseCase:
    """Use case for checking if user is manager or higher (admin, manager)."""

    # Role hierarchy levels
    ROLE_HIERARCHY = {
        UserRole.ADMIN: 4,
        UserRole.MANAGER: 3,
        UserRole.WASHER: 2,
        UserRole.CLIENT: 1,
    }

    async def execute(self, user: User) -> bool:
        """Check if user is manager or higher in hierarchy.

        Returns:
            True if user is manager or admin

        Raises:
            InsufficientPermissionError: If user is not manager or admin
        """
        # Manager level or higher (manager, admin)
        user_level = self.ROLE_HIERARCHY.get(user.role, 0)
        manager_level = self.ROLE_HIERARCHY.get(UserRole.MANAGER, 3)

        if user_level < manager_level:
            raise InsufficientPermissionError(
                "Manager access required"
            )

        return True


class CheckAdminUseCase:
    """Use case for checking if user is admin (admin-only operations)."""

    async def execute(self, user: User) -> bool:
        """Check if user is admin.

        Returns:
            True if user is admin

        Raises:
            InsufficientPermissionError: If user is not admin
        """
        if user.role != UserRole.ADMIN:
            raise InsufficientPermissionError(
                "Admin access required"
            )

        return True