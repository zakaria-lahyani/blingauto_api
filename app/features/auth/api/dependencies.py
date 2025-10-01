"""FastAPI dependencies for auth feature - NO BUSINESS LOGIC."""

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.shared.auth import AuthenticatedUser
from ..adapters.http_auth import HttpAuthenticationAdapter
from ..domain import UserRole
from ..use_cases.check_authorization import Permission

security = HTTPBearer()


# Dependency to get the auth adapter
async def get_auth_adapter() -> HttpAuthenticationAdapter:
    """Get configured authentication adapter."""
    # TODO: This should be properly injected via DI container
    # For now, create instances (this violates DI principles but is a start)
    from ..use_cases.authenticate_user import AuthenticateUserUseCase
    from ..use_cases.check_authorization import CheckRoleUseCase, CheckPermissionUseCase, CheckStaffUseCase
    from ..adapters.repositories import UserRepository
    from ..adapters.services import TokenService
    from app.core.db import get_db
    
    # This is a temporary implementation - should use proper DI
    db = next(get_db())
    user_repo = UserRepository(db)
    token_service = TokenService()
    
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