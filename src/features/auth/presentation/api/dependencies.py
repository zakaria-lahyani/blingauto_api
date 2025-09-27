"""
Auth API dependencies
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole

# Security scheme
security = HTTPBearer()


def get_current_user(auth_module):
    """Create dependency for getting current user"""
    
    async def _get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Optional[AuthUser]:
        """Get current user from token"""
        
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user = await auth_module.auth_service.get_user_from_token(credentials.credentials)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
    
    return _get_current_user


def get_current_active_user(auth_module):
    """Create dependency for getting current active user"""
    
    async def _get_current_active_user(
        current_user: AuthUser = Depends(get_current_user(auth_module))
    ) -> AuthUser:
        """Get current active user"""
        
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return current_user
    
    return _get_current_active_user


def require_role(required_role: AuthRole):
    """Create dependency that requires specific role"""
    
    def _require_role(auth_module):
        async def _check_role(
            current_user: AuthUser = Depends(get_current_active_user(auth_module))
        ) -> AuthUser:
            """Check if user has required role"""
            
            if current_user.role != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Operation requires {required_role.value} role"
                )
            
            return current_user
        
        return _check_role
    
    return _require_role


def require_admin(auth_module):
    """Require admin role"""
    return require_role(AuthRole.ADMIN)(auth_module)


def require_manager_or_admin(auth_module):
    """Create dependency that requires manager or admin role"""
    
    async def _require_manager_or_admin(
        current_user: AuthUser = Depends(get_current_active_user(auth_module))
    ) -> AuthUser:
        """Check if user is manager or admin"""
        
        if current_user.role not in [AuthRole.ADMIN, AuthRole.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation requires manager or admin role"
            )
        
        return current_user
    
    return _require_manager_or_admin


def get_optional_user(auth_module):
    """Create dependency for optional user (no error if not authenticated)"""
    
    async def _get_optional_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Optional[AuthUser]:
        """Get current user if authenticated, None otherwise"""
        
        if not credentials:
            return None
        
        try:
            user = await auth_module.auth_service.get_user_from_token(credentials.credentials)
            return user if user and user.is_active else None
        except Exception:
            return None
    
    return _get_optional_user