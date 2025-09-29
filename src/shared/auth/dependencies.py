
"""
Shared authentication dependencies for all API routes
"""
import logging
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole
from src.shared.exceptions import (
    AuthenticationError, 
    AuthorizationError, 
    SessionError,
    ErrorMessages
)

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)

# Global auth module placeholder - will be injected by the application
_auth_module = None


def set_auth_module(auth_module):
    """Set the global auth module instance"""
    global _auth_module
    _auth_module = auth_module


def get_auth_module():
    """Get the global auth module instance"""
    if _auth_module is None:
        logger.error("Authentication module not configured")
        raise AuthenticationError(ErrorMessages.AUTH_REQUIRED)
    return _auth_module


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    request: Request = None
) -> AuthUser:
    """Get current user from token with enhanced session validation"""
    
    if not credentials or not credentials.credentials:
        logger.warning(f"Authentication required for {request.url.path if request else 'unknown path'}")
        raise AuthenticationError(ErrorMessages.AUTH_REQUIRED)
    
    try:
        auth_module = get_auth_module()
        
        # Validate token and get user
        user = await auth_module.auth_service.get_user_from_token(credentials.credentials)
        
        if not user:
            logger.warning(f"Invalid token provided for {request.url.path if request else 'unknown path'}")
            raise SessionError(ErrorMessages.AUTH_INVALID_CREDENTIALS)
        
        # Additional session validation
        if hasattr(auth_module.auth_service, 'validate_session'):
            is_valid = await auth_module.auth_service.validate_session(user.id, credentials.credentials)
            if not is_valid:
                logger.warning(f"Invalid session for user {user.id}")
                raise SessionError(ErrorMessages.SESSION_EXPIRED)
        
        # Log successful authentication for security monitoring
        logger.info(f"User {user.id} authenticated successfully for {request.url.path if request else 'unknown path'}")
        
        return user
        
    except (AuthenticationError, SessionError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error during authentication: {str(e)}")
        raise SessionError(ErrorMessages.SESSION_INVALID)


async def get_current_active_user(
    current_user: AuthUser = Depends(get_current_user)
) -> AuthUser:
    """Get current active user with enhanced validation"""
    
    if not current_user.is_active:
        logger.warning(f"Inactive user {current_user.id} attempted access")
        raise AuthorizationError(ErrorMessages.BUSINESS_INACTIVE_USER)
    
    return current_user


def require_role(required_role: AuthRole):
    """Create dependency that requires specific role"""
    
    async def _check_role(
        current_user: AuthUser = Depends(get_current_active_user)
    ) -> AuthUser:
        """Check if user has required role"""
        
        if current_user.role != required_role:
            logger.warning(f"User {current_user.id} with role {current_user.role.value} attempted to access {required_role.value} endpoint")
            raise AuthorizationError(
                f"Operation requires {required_role.value} role",
                required_role=required_role.value
            )
        
        return current_user
    
    return _check_role


async def require_admin(
    current_user: AuthUser = Depends(get_current_active_user)
) -> AuthUser:
    """Require admin role"""
    if current_user.role != AuthRole.ADMIN:
        logger.warning(f"User {current_user.id} with role {current_user.role.value} attempted admin access")
        raise AuthorizationError(ErrorMessages.AUTHZ_ADMIN_REQUIRED, required_role="admin")
    
    return current_user


async def require_manager_or_admin(
    current_user: AuthUser = Depends(get_current_active_user)
) -> AuthUser:
    """Require manager or admin role"""
    
    if current_user.role not in [AuthRole.ADMIN, AuthRole.MANAGER]:
        logger.warning(f"User {current_user.id} with role {current_user.role.value} attempted manager/admin access")
        raise AuthorizationError(ErrorMessages.AUTHZ_MANAGER_REQUIRED, required_role="manager or admin")
    
    return current_user


async def require_staff(
    current_user: AuthUser = Depends(get_current_active_user)
) -> AuthUser:
    """Require staff (manager, admin, or staff) role"""
    
    if current_user.role not in [AuthRole.ADMIN, AuthRole.MANAGER, AuthRole.STAFF]:
        logger.warning(f"User {current_user.id} with role {current_user.role.value} attempted staff access")
        raise AuthorizationError(ErrorMessages.AUTHZ_STAFF_REQUIRED, required_role="staff")
    
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthUser]:
    """Get current user if authenticated, None otherwise"""
    
    if not credentials:
        return None
    
    try:
        auth_module = get_auth_module()
        user = await auth_module.auth_service.get_user_from_token(credentials.credentials)
        return user if user and user.is_active else None
    except Exception:
        return None


async def require_owner_or_staff(resource_owner_id: str):
    """Create dependency that requires user to be owner of resource or staff"""
    
    async def _check_owner_or_staff(
        current_user: AuthUser = Depends(get_current_active_user)
    ) -> AuthUser:
        """Check if user owns resource or is staff"""
        
        # Staff can access any resource
        if current_user.role in [AuthRole.ADMIN, AuthRole.MANAGER, AuthRole.STAFF]:
            return current_user
        
        # Regular users can only access their own resources
        if str(current_user.id) != str(resource_owner_id):
            logger.warning(f"User {current_user.id} attempted to access resource owned by {resource_owner_id}")
            raise AuthorizationError(ErrorMessages.AUTHZ_OWNER_REQUIRED)
        
        return current_user
    
    return _check_owner_or_staff