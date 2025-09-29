"""
Shared authentication module
"""
from .dependencies import (
    get_current_user,
    get_current_active_user,
    require_role,
    require_admin,
    require_manager_or_admin,
    require_staff,
    get_optional_user,
    require_owner_or_staff,
    set_auth_module,
    get_auth_module
)

__all__ = [
    "get_current_user",
    "get_current_active_user", 
    "require_role",
    "require_admin",
    "require_manager_or_admin",
    "require_staff",
    "get_optional_user",
    "require_owner_or_staff",
    "set_auth_module",
    "get_auth_module"
]