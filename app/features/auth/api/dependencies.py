"""FastAPI dependencies for auth feature - NO BUSINESS LOGIC."""

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.shared.auth import AuthenticatedUser
from app.core.db import get_db
from ..adapters.http_auth import HttpAuthenticationAdapter
from ..domain import UserRole
from ..use_cases.check_authorization import Permission

security = HTTPBearer()


# This is NOT a dependency - it's a factory function
# Dependencies should use get_auth_adapter_dep instead
def create_auth_adapter(db) -> HttpAuthenticationAdapter:
    """Create authentication adapter with dependencies."""
    from ..use_cases.authenticate_user import AuthenticateUserUseCase
    from ..use_cases.check_authorization import CheckRoleUseCase, CheckPermissionUseCase, CheckStaffUseCase
    from ..adapters.repositories import UserRepository
    from ..adapters.services import TokenServiceAdapter

    user_repo = UserRepository(db)
    token_service = TokenServiceAdapter()

    authenticate_use_case = AuthenticateUserUseCase(user_repo, token_service)
    check_role_use_case = CheckRoleUseCase()
    check_permission_use_case = CheckPermissionUseCase()
    check_staff_use_case = CheckStaffUseCase()

    return HttpAuthenticationAdapter(
        authenticate_use_case,
        check_role_use_case,
        check_permission_use_case,
        check_staff_use_case,
    )


# Proper async dependency
async def get_auth_adapter_dep(db = Depends(get_db)) -> HttpAuthenticationAdapter:
    """Get configured authentication adapter - proper async dependency."""
    return create_auth_adapter(db)


# Keep old name for backward compatibility
get_auth_adapter = get_auth_adapter_dep


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_adapter: HttpAuthenticationAdapter = Depends(get_auth_adapter)
) -> AuthenticatedUser:
    """Get current authenticated user - delegates to use case."""
    return await auth_adapter.authenticate_from_credentials(credentials)


def require_role(required_role: UserRole):
    """Dependency factory to require specific user role."""
    async def role_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
        auth_adapter: HttpAuthenticationAdapter = Depends(get_auth_adapter)
    ):
        return await auth_adapter.require_role(current_user, required_role)
    return role_checker


def require_permission(permission: Permission):
    """Dependency factory to require specific permission."""
    async def permission_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
        auth_adapter: HttpAuthenticationAdapter = Depends(get_auth_adapter)
    ):
        return await auth_adapter.require_permission(current_user, permission)
    return permission_checker


def require_admin():
    """Dependency to require admin role."""
    return require_role(UserRole.ADMIN)


def require_staff():
    """Dependency to require staff role."""
    async def staff_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
        auth_adapter: HttpAuthenticationAdapter = Depends(get_auth_adapter)
    ):
        return await auth_adapter.require_staff(current_user)
    return staff_checker


# Commonly used dependencies
CurrentUser = Depends(get_current_user)
AdminUser = Depends(require_admin())
StaffUser = Depends(require_staff())