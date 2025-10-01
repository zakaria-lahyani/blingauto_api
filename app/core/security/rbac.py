from typing import List, Optional, Set
from enum import Enum
from functools import wraps
from fastapi import HTTPException, status


class Role(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
    MANAGER = "manager"
    WASHER = "washer"
    CLIENT = "client"


class Permission(str, Enum):
    """System permissions."""
    # User management
    VIEW_ALL_USERS = "view_all_users"
    EDIT_ALL_USERS = "edit_all_users"
    DELETE_USERS = "delete_users"
    MANAGE_ROLES = "manage_roles"
    
    # Booking management
    VIEW_ALL_BOOKINGS = "view_all_bookings"
    EDIT_ALL_BOOKINGS = "edit_all_bookings"
    DELETE_BOOKINGS = "delete_bookings"
    ASSIGN_BOOKINGS = "assign_bookings"
    
    # Service management
    MANAGE_SERVICES = "manage_services"
    MANAGE_CATEGORIES = "manage_categories"
    MANAGE_PRICING = "manage_pricing"
    
    # Facility management
    MANAGE_FACILITIES = "manage_facilities"
    MANAGE_SCHEDULES = "manage_schedules"
    MANAGE_RESOURCES = "manage_resources"
    
    # Reports and analytics
    VIEW_REPORTS = "view_reports"
    EXPORT_DATA = "export_data"
    
    # Client permissions
    VIEW_OWN_PROFILE = "view_own_profile"
    EDIT_OWN_PROFILE = "edit_own_profile"
    VIEW_OWN_BOOKINGS = "view_own_bookings"
    CREATE_BOOKING = "create_booking"
    EDIT_OWN_BOOKING = "edit_own_booking"
    CANCEL_OWN_BOOKING = "cancel_own_booking"
    
    # Washer permissions
    VIEW_ASSIGNED_BOOKINGS = "view_assigned_bookings"
    UPDATE_BOOKING_STATUS = "update_booking_status"
    ADD_BOOKING_NOTES = "add_booking_notes"


class RBACService:
    """Role-Based Access Control service."""
    
    # Role hierarchy and permissions mapping
    ROLE_PERMISSIONS = {
        Role.ADMIN: {
            # Admin has all permissions
            Permission.VIEW_ALL_USERS,
            Permission.EDIT_ALL_USERS,
            Permission.DELETE_USERS,
            Permission.MANAGE_ROLES,
            Permission.VIEW_ALL_BOOKINGS,
            Permission.EDIT_ALL_BOOKINGS,
            Permission.DELETE_BOOKINGS,
            Permission.ASSIGN_BOOKINGS,
            Permission.MANAGE_SERVICES,
            Permission.MANAGE_CATEGORIES,
            Permission.MANAGE_PRICING,
            Permission.MANAGE_FACILITIES,
            Permission.MANAGE_SCHEDULES,
            Permission.MANAGE_RESOURCES,
            Permission.VIEW_REPORTS,
            Permission.EXPORT_DATA,
            Permission.VIEW_OWN_PROFILE,
            Permission.EDIT_OWN_PROFILE,
            Permission.VIEW_OWN_BOOKINGS,
            Permission.CREATE_BOOKING,
            Permission.EDIT_OWN_BOOKING,
            Permission.CANCEL_OWN_BOOKING,
        },
        Role.MANAGER: {
            # Manager permissions
            Permission.VIEW_ALL_USERS,
            Permission.VIEW_ALL_BOOKINGS,
            Permission.EDIT_ALL_BOOKINGS,
            Permission.ASSIGN_BOOKINGS,
            Permission.MANAGE_SERVICES,
            Permission.MANAGE_CATEGORIES,
            Permission.MANAGE_PRICING,
            Permission.MANAGE_SCHEDULES,
            Permission.MANAGE_RESOURCES,
            Permission.VIEW_REPORTS,
            Permission.EXPORT_DATA,
            Permission.VIEW_OWN_PROFILE,
            Permission.EDIT_OWN_PROFILE,
            Permission.VIEW_OWN_BOOKINGS,
            Permission.CREATE_BOOKING,
            Permission.EDIT_OWN_BOOKING,
            Permission.CANCEL_OWN_BOOKING,
        },
        Role.WASHER: {
            # Washer permissions
            Permission.VIEW_ASSIGNED_BOOKINGS,
            Permission.UPDATE_BOOKING_STATUS,
            Permission.ADD_BOOKING_NOTES,
            Permission.VIEW_OWN_PROFILE,
            Permission.EDIT_OWN_PROFILE,
        },
        Role.CLIENT: {
            # Client permissions
            Permission.VIEW_OWN_PROFILE,
            Permission.EDIT_OWN_PROFILE,
            Permission.VIEW_OWN_BOOKINGS,
            Permission.CREATE_BOOKING,
            Permission.EDIT_OWN_BOOKING,
            Permission.CANCEL_OWN_BOOKING,
        },
    }
    
    @classmethod
    def get_role_permissions(cls, role: Role) -> Set[Permission]:
        """Get all permissions for a role."""
        return cls.ROLE_PERMISSIONS.get(role, set())
    
    @classmethod
    def has_permission(cls, role: Role, permission: Permission) -> bool:
        """Check if a role has a specific permission."""
        permissions = cls.get_role_permissions(role)
        return permission in permissions
    
    @classmethod
    def check_permissions(
        cls,
        role: Role,
        required_permissions: List[Permission],
        require_all: bool = True,
    ) -> bool:
        """
        Check if a role has required permissions.
        
        Args:
            role: User's role
            required_permissions: List of required permissions
            require_all: If True, all permissions are required. If False, any permission is sufficient.
        """
        user_permissions = cls.get_role_permissions(role)
        
        if require_all:
            return all(perm in user_permissions for perm in required_permissions)
        else:
            return any(perm in user_permissions for perm in required_permissions)
    
    @classmethod
    def is_admin(cls, role: Role) -> bool:
        """Check if role is admin."""
        return role == Role.ADMIN
    
    @classmethod
    def is_manager_or_above(cls, role: Role) -> bool:
        """Check if role is manager or admin."""
        return role in [Role.ADMIN, Role.MANAGER]
    
    @classmethod
    def is_staff(cls, role: Role) -> bool:
        """Check if role is staff (not client)."""
        return role != Role.CLIENT


def require_permissions(
    permissions: List[Permission],
    require_all: bool = True,
):
    """
    Decorator to check permissions on endpoints.
    
    Args:
        permissions: List of required permissions
        require_all: If True, all permissions are required. If False, any permission is sufficient.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs (injected by dependency)
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                )
            
            # Check permissions
            if not RBACService.check_permissions(
                current_user.role,
                permissions,
                require_all,
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


rbac_service = RBACService()