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
    """Use case for checking if user has required role."""
    
    async def execute(self, request: CheckRoleRequest) -> bool:
        """Check if user has required role.
        
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
    """Use case for checking if user is staff (admin or washer)."""
    
    STAFF_ROLES = [UserRole.ADMIN, UserRole.WASHER]
    
    async def execute(self, user: User) -> bool:
        """Check if user is staff.
        
        Returns:
            True if user is staff
            
        Raises:
            InsufficientPermissionError: If user is not staff
        """
        if user.role not in self.STAFF_ROLES:
            raise InsufficientPermissionError(
                "Staff access required"
            )
        
        return True