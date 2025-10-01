"""
Shared authentication dependencies for FastAPI.
These are the ONLY dependencies that should be imported across features for auth.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated, Callable

from .contracts import AuthenticatedUser

security = HTTPBearer()


# This will be injected by the composition root (interfaces layer)
_auth_adapter = None


def register_auth_adapter(adapter):
    """Register the authentication adapter (called from composition root)."""
    global _auth_adapter
    _auth_adapter = adapter


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> AuthenticatedUser:
    """
    Get current authenticated user from JWT token.
    This is the main dependency for authentication across features.
    """
    if _auth_adapter is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not properly configured"
        )

    try:
        user = await _auth_adapter.authenticate_from_credentials(credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        return user
    except HTTPException:
        # Re-raise HTTP exceptions from adapter
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


def require_role(role: str) -> Callable:
    """
    Dependency factory to require a specific role.
    Usage: dependencies=[Depends(require_role("admin"))]
    """
    async def role_checker(
        current_user: AuthenticatedUser = Depends(get_current_user)
    ) -> AuthenticatedUser:
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {role} role"
            )
        return current_user
    return role_checker


def require_any_role(*roles: str) -> Callable:
    """
    Dependency factory to require any of multiple roles.
    Usage: dependencies=[Depends(require_any_role("admin", "manager"))]
    """
    async def role_checker(
        current_user: AuthenticatedUser = Depends(get_current_user)
    ) -> AuthenticatedUser:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(roles)}"
            )
        return current_user
    return role_checker


# Common role dependencies
def require_admin() -> Callable:
    """Dependency to require admin role."""
    return require_role("admin")


def require_manager() -> Callable:
    """Dependency to require manager role."""
    return require_role("manager")


def require_washer() -> Callable:
    """Dependency to require washer role."""
    return require_role("washer")


def require_client() -> Callable:
    """Dependency to require client role."""
    return require_role("client")


def require_staff() -> Callable:
    """Dependency to require admin, manager, or washer role."""
    return require_any_role("admin", "manager", "washer")


# Type annotations for convenience
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
AdminUser = Annotated[AuthenticatedUser, Depends(require_admin())]
ManagerUser = Annotated[AuthenticatedUser, Depends(require_manager())]
WasherUser = Annotated[AuthenticatedUser, Depends(require_washer())]
ClientUser = Annotated[AuthenticatedUser, Depends(require_client())]
StaffUser = Annotated[AuthenticatedUser, Depends(require_staff())]
