from dataclasses import dataclass
from typing import Optional, List

from app.features.auth.domain import User, UserRole, UserStatus, RoleTransitionPolicy
from app.features.auth.ports import IUserRepository, ICacheService
from app.core.errors import NotFoundError, BusinessRuleViolationError


@dataclass
class GetUserRequest:
    """Request to get user by ID."""
    user_id: str


@dataclass
class ListUsersRequest:
    """Request to list users."""
    offset: int = 0
    limit: int = 20
    role: Optional[str] = None
    status: Optional[str] = None


@dataclass
class UpdateUserRoleRequest:
    """Request to update user role."""
    user_id: str
    new_role: UserRole
    initiator_role: str


@dataclass
class UserResponse:
    """User response data."""
    id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    role: str
    status: str
    phone_number: Optional[str]
    email_verified: bool
    created_at: str
    last_login_at: Optional[str]


@dataclass
class UserListResponse:
    """Response for user list."""
    users: List[UserResponse]
    total: int
    offset: int
    limit: int


class GetUserUseCase:
    """Use case for getting a user by ID."""
    
    def __init__(self, user_repository: IUserRepository, cache_service: ICacheService):
        self.user_repository = user_repository
        self.cache_service = cache_service
    
    async def execute(self, request: GetUserRequest) -> UserResponse:
        """Get user by ID with caching."""
        
        # Try cache first
        cached_user = await self.cache_service.get_user(request.user_id)
        if cached_user:
            return UserResponse(**cached_user)
        
        # Get from repository
        user = await self.user_repository.get_by_id(request.user_id)
        if not user:
            raise NotFoundError("User", request.user_id)
        
        response = UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            phone_number=user.phone_number,
            email_verified=user.email_verified,
            created_at=user.created_at.isoformat(),
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        )
        
        # Cache for future requests
        await self.cache_service.set_user(
            user_id=user.id,
            user_data=response.__dict__,
            ttl=300,
        )
        
        return response


class ListUsersUseCase:
    """Use case for listing users."""
    
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
    
    async def execute(self, request: ListUsersRequest) -> UserListResponse:
        """List users with pagination and filters."""
        
        # Get users and total count
        users = await self.user_repository.list(
            offset=request.offset,
            limit=request.limit,
            role=request.role,
            status=request.status,
        )
        
        total = await self.user_repository.count(
            role=request.role,
            status=request.status,
        )
        
        # Convert to response format
        user_responses = [
            UserResponse(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                full_name=user.full_name,
                role=user.role.value,
                status=user.status.value,
                phone_number=user.phone_number,
                email_verified=user.email_verified,
                created_at=user.created_at.isoformat(),
                last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
            )
            for user in users
        ]
        
        return UserListResponse(
            users=user_responses,
            total=total,
            offset=request.offset,
            limit=request.limit,
        )


class UpdateUserRoleUseCase:
    """Use case for updating user role."""
    
    def __init__(self, user_repository: IUserRepository, cache_service: ICacheService):
        self.user_repository = user_repository
        self.cache_service = cache_service
    
    async def execute(self, request: UpdateUserRoleRequest) -> UserResponse:
        """
        Update user role.
        
        Business rules:
        - RG-AUTH-009: Role transition validation
        """
        
        # Get user
        user = await self.user_repository.get_by_id(request.user_id)
        if not user:
            raise NotFoundError("User", request.user_id)
        
        # Validate role transition
        RoleTransitionPolicy.validate_transition(
            current_role=user.role.value,
            new_role=request.new_role.value,
            initiator_role=request.initiator_role,
        )
        
        # Update role
        user.role = request.new_role
        user.updated_at = user.updated_at
        
        # Save changes
        updated_user = await self.user_repository.update(user)
        
        # Invalidate cache
        await self.cache_service.delete_user(user.id)
        
        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            full_name=updated_user.full_name,
            role=updated_user.role.value,
            status=updated_user.status.value,
            phone_number=updated_user.phone_number,
            email_verified=updated_user.email_verified,
            created_at=updated_user.created_at.isoformat(),
            last_login_at=updated_user.last_login_at.isoformat() if updated_user.last_login_at else None,
        )