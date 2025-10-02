"""Shared authentication contracts and utilities."""

from .contracts import AuthenticatedUser, AuthenticationPort
from .dependencies import (
    get_current_user,
    get_current_user_id,
    require_role,
    require_any_role,
    require_admin,
    require_manager,
    require_washer,
    require_client,
    require_staff,
    CurrentUser,
    AdminUser,
    ManagerUser,
    WasherUser,
    ClientUser,
    StaffUser,
    register_auth_adapter,
)

__all__ = [
    # Contracts
    "AuthenticatedUser",
    "AuthenticationPort",
    # Dependencies
    "get_current_user",
    "get_current_user_id",
    "require_role",
    "require_any_role",
    "require_admin",
    "require_manager",
    "require_washer",
    "require_client",
    "require_staff",
    # Type annotations
    "CurrentUser",
    "AdminUser",
    "ManagerUser",
    "WasherUser",
    "ClientUser",
    "StaffUser",
    # Setup
    "register_auth_adapter",
]