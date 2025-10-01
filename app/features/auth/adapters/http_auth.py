"""HTTP authentication adapter - bridges FastAPI to auth use cases."""

from typing import Optional
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.shared.auth import AuthenticatedUser
from ..use_cases.authenticate_user import AuthenticateUserUseCase, AuthenticateUserRequest
from ..use_cases.check_authorization import (
    CheckRoleUseCase, CheckPermissionUseCase, CheckStaffUseCase,
    CheckRoleRequest, CheckPermissionRequest, Permission
)
from ..domain import UserRole
from ..domain.exceptions import (
    AuthenticationError, UserInactiveError, InsufficientPermissionError
)


class HttpAuthenticationAdapter:
    """Adapter that handles HTTP authentication using domain use cases."""
    
    def __init__(
        self,
        authenticate_user_use_case: AuthenticateUserUseCase,
        check_role_use_case: CheckRoleUseCase,
        check_permission_use_case: CheckPermissionUseCase,
        check_staff_use_case: CheckStaffUseCase,
    ):
        self._authenticate_user = authenticate_user_use_case
        self._check_role = check_role_use_case
        self._check_permission = check_permission_use_case
        self._check_staff = check_staff_use_case
    
    async def authenticate_from_credentials(
        self, 
        credentials: HTTPAuthorizationCredentials
    ) -> AuthenticatedUser:
        """Authenticate user from HTTP credentials.
        
        Raises:
            HTTPException: If authentication fails
        """
        try:
            request = AuthenticateUserRequest(token=credentials.credentials)
            user = await self._authenticate_user.execute(request)
            
            # Convert domain User to shared contract AuthenticatedUser
            return AuthenticatedUser(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                role=user.role.value,
                status=user.status.value,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            
        except (AuthenticationError, UserInactiveError) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def require_role(self, user: AuthenticatedUser, required_role: UserRole) -> AuthenticatedUser:
        """Require user to have specific role.
        
        Raises:
            HTTPException: If user doesn't have required role
        """
        try:
            # Convert back to domain User for use case
            domain_user = self._to_domain_user(user)
            request = CheckRoleRequest(user=domain_user, required_role=required_role)
            await self._check_role.execute(request)
            return user
            
        except InsufficientPermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
    
    async def require_permission(self, user: AuthenticatedUser, permission: Permission) -> AuthenticatedUser:
        """Require user to have specific permission.
        
        Raises:
            HTTPException: If user doesn't have permission
        """
        try:
            domain_user = self._to_domain_user(user)
            request = CheckPermissionRequest(user=domain_user, permission=permission)
            await self._check_permission.execute(request)
            return user
            
        except InsufficientPermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
    
    async def require_staff(self, user: AuthenticatedUser) -> AuthenticatedUser:
        """Require user to be staff.
        
        Raises:
            HTTPException: If user is not staff
        """
        try:
            domain_user = self._to_domain_user(user)
            await self._check_staff.execute(domain_user)
            return user
            
        except InsufficientPermissionError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
    
    def _to_domain_user(self, auth_user: AuthenticatedUser):
        """Convert AuthenticatedUser to domain User."""
        # Import here to avoid circular imports
        from ..domain import User, UserRole, UserStatus
        
        return User(
            id=auth_user.id,
            email=auth_user.email,
            first_name=auth_user.first_name,
            last_name=auth_user.last_name,
            role=UserRole(auth_user.role),
            status=UserStatus(auth_user.status),
            created_at=auth_user.created_at,
            updated_at=auth_user.updated_at,
            hashed_password="",  # Not needed for authorization
        )