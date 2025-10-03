from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.db import get_db, UnitOfWork
from app.shared.auth import AuthenticatedUser
from app.features.auth.api.schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    VerifyEmailRequest,
    RequestPasswordResetRequest,
    ResetPasswordRequest,
    MessageResponse,
    UserResponse,
    UserListResponse,
    UpdateUserRoleRequest,
    ChangePasswordRequest,
    ChangePasswordResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
    LogoutResponse,
)
from app.features.auth.api.dependencies import CurrentUser, AdminUser, StaffUser, ManagerUser
from app.features.auth.domain import User, UserRole
from app.features.auth.use_cases import (
    RegisterUserUseCase,
    RegisterUserRequest,
    LoginUserUseCase,
    LoginUserRequest,
    RefreshTokenUseCase,
    RefreshTokenRequest as RefreshTokenUseCaseRequest,
    VerifyEmailUseCase,
    VerifyEmailRequest as VerifyEmailUseCaseRequest,
    RequestPasswordResetUseCase,
    RequestPasswordResetRequest as RequestPasswordResetUseCaseRequest,
    ResetPasswordUseCase,
    ResetPasswordRequest as ResetPasswordUseCaseRequest,
    GetUserUseCase,
    GetUserRequest,
    ListUsersUseCase,
    ListUsersRequest,
    UpdateUserRoleUseCase,
    UpdateUserRoleRequest as UpdateUserRoleUseCaseRequest,
)
from app.features.auth.use_cases.change_password import (
    ChangePasswordUseCase,
    ChangePasswordRequest as ChangePasswordUseCaseRequest,
)
from app.features.auth.use_cases.update_profile import (
    UpdateProfileUseCase,
    UpdateProfileRequest as UpdateProfileUseCaseRequest,
)
from app.features.auth.use_cases.logout import (
    LogoutUseCase,
    LogoutRequest as LogoutUseCaseRequest,
)
from app.features.auth.adapters import (
    UserRepository,
    PasswordResetTokenRepository,
    EmailVerificationTokenRepository,
    RefreshTokenRepository,
    PasswordHasherAdapter,
    TokenServiceAdapter,
    EmailServiceAdapter,
    CacheServiceAdapter,
)

router = APIRouter()


def get_use_case_dependencies(db: Session):
    """Factory to create use case dependencies."""
    user_repo = UserRepository(db)
    password_reset_repo = PasswordResetTokenRepository(db)
    email_verification_repo = EmailVerificationTokenRepository(db)
    refresh_token_repo = RefreshTokenRepository(db)
    password_hasher = PasswordHasherAdapter()
    token_service = TokenServiceAdapter()
    email_service = EmailServiceAdapter()
    cache_service = CacheServiceAdapter()
    
    return {
        "user_repo": user_repo,
        "password_reset_repo": password_reset_repo,
        "email_verification_repo": email_verification_repo,
        "refresh_token_repo": refresh_token_repo,
        "password_hasher": password_hasher,
        "token_service": token_service,
        "email_service": email_service,
        "cache_service": cache_service,
    }


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Creates a new user account with email verification required.
    The user will receive an email with a verification link.
    """
    async with UnitOfWork() as uow:
        deps = get_use_case_dependencies(uow.session)
        
        use_case = RegisterUserUseCase(
            user_repository=deps["user_repo"],
            token_repository=deps["email_verification_repo"],
            password_hasher=deps["password_hasher"],
            email_service=deps["email_service"],
        )
        
        use_case_request = RegisterUserRequest(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            phone_number=request.phone_number,
        )
        
        response = await use_case.execute(use_case_request)
        
        return RegisterResponse(
            user_id=response.user_id,
            email=response.email,
            full_name=response.full_name,
            message=response.message,
        )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return access and refresh tokens.

    Returns JWT access token for API authentication and refresh token
    for obtaining new access tokens.
    """
    async with UnitOfWork() as uow:
        deps = get_use_case_dependencies(uow.session)

        use_case = LoginUserUseCase(
            user_repository=deps["user_repo"],
            refresh_token_repository=deps["refresh_token_repo"],
            password_hasher=deps["password_hasher"],
            token_service=deps["token_service"],
            cache_service=deps["cache_service"],
        )

        use_case_request = LoginUserRequest(
            email=request.email,
            password=request.password,
        )

        response = await use_case.execute(use_case_request)

        from app.core.config.settings import settings
        from app.features.auth.api.schemas import UserInfo

        return LoginResponse(
            access_token=response.access_token,
            refresh_token=response.refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserInfo(
                user_id=response.user_id,
                email=response.email,
                full_name=response.full_name,
                role=response.role,
            ),
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token.
    
    Returns new access token and optionally rotates the refresh token.
    """
    async with UnitOfWork() as uow:
        deps = get_use_case_dependencies(uow.session)
        
        use_case = RefreshTokenUseCase(
            user_repository=deps["user_repo"],
            refresh_token_repository=deps["refresh_token_repo"],
            token_service=deps["token_service"],
        )
        
        use_case_request = RefreshTokenUseCaseRequest(
            refresh_token=request.refresh_token,
        )
        
        response = await use_case.execute(use_case_request)
        
        return RefreshTokenResponse(
            access_token=response.access_token,
            refresh_token=response.refresh_token,
        )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(request: VerifyEmailRequest, db: Session = Depends(get_db)):
    """
    Verify user email address using verification token.
    
    Activates the user account after successful email verification.
    """
    async with UnitOfWork() as uow:
        deps = get_use_case_dependencies(uow.session)
        
        use_case = VerifyEmailUseCase(
            user_repository=deps["user_repo"],
            token_repository=deps["email_verification_repo"],
            email_service=deps["email_service"],
        )
        
        use_case_request = VerifyEmailUseCaseRequest(token=request.token)
        response = await use_case.execute(use_case_request)
        
        return MessageResponse(message=response.message)


@router.post("/request-password-reset", response_model=MessageResponse)
@router.post("/forgot-password", response_model=MessageResponse)  # Alias for Postman compatibility
async def request_password_reset(
    request: RequestPasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset for user account.

    Sends password reset email if the email address exists.
    """
    async with UnitOfWork() as uow:
        deps = get_use_case_dependencies(uow.session)

        use_case = RequestPasswordResetUseCase(
            user_repository=deps["user_repo"],
            token_repository=deps["password_reset_repo"],
            email_service=deps["email_service"],
        )

        use_case_request = RequestPasswordResetUseCaseRequest(email=request.email)
        response = await use_case.execute(use_case_request)

        return MessageResponse(message=response.message)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password using reset token.
    
    Changes the user's password using a valid reset token.
    """
    async with UnitOfWork() as uow:
        deps = get_use_case_dependencies(uow.session)
        
        use_case = ResetPasswordUseCase(
            user_repository=deps["user_repo"],
            token_repository=deps["password_reset_repo"],
            password_hasher=deps["password_hasher"],
        )
        
        use_case_request = ResetPasswordUseCaseRequest(
            token=request.token,
            new_password=request.new_password,
        )
        
        response = await use_case.execute(use_case_request)
        
        return MessageResponse(message=response.message)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: AuthenticatedUser = CurrentUser):
    """
    Get current user profile information.

    Returns the authenticated user's profile data.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.full_name,
        role=current_user.role,  # Already a string, not an enum
        status=current_user.status,  # Already a string, not an enum
        phone_number=current_user.phone_number,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at.isoformat(),
        last_login_at=current_user.last_login_at.isoformat() if current_user.last_login_at else None,
    )


@router.get("/users", response_model=UserListResponse)
async def list_users(
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Limit for pagination"),
    role: Optional[str] = Query(None, description="Filter by role"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = ManagerUser,
    db: Session = Depends(get_db)
):
    """
    List all users with pagination and filters.

    Manager/Admin endpoint to list all users in the system.
    """
    deps = get_use_case_dependencies(db)
    
    use_case = ListUsersUseCase(user_repository=deps["user_repo"])
    
    use_case_request = ListUsersRequest(
        offset=offset,
        limit=limit,
        role=role,
        status=status,
    )
    
    response = await use_case.execute(use_case_request)

    return UserListResponse(
        users=[UserResponse(**user.__dict__) for user in response.users],
        total=response.total,
        offset=response.offset,
        limit=response.limit,
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = AdminUser,
    db: Session = Depends(get_db)
):
    """
    Get user by ID.
    
    Admin only endpoint to get any user's information.
    """
    deps = get_use_case_dependencies(db)
    
    use_case = GetUserUseCase(
        user_repository=deps["user_repo"],
        cache_service=deps["cache_service"],
    )
    
    use_case_request = GetUserRequest(user_id=user_id)
    response = await use_case.execute(use_case_request)
    
    return response


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: str,
    request: UpdateUserRoleRequest,
    current_user: User = AdminUser,
    db: Session = Depends(get_db)
):
    """
    Update user role.

    Admin only endpoint to change a user's role.
    """
    async with UnitOfWork() as uow:
        deps = get_use_case_dependencies(uow.session)

        use_case = UpdateUserRoleUseCase(
            user_repository=deps["user_repo"],
            cache_service=deps["cache_service"],
        )

        use_case_request = UpdateUserRoleUseCaseRequest(
            user_id=user_id,
            new_role=UserRole(request.role),
            initiator_role=current_user.role,
        )

        response = await use_case.execute(use_case_request)

        return response


@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Change current user's password.

    Requires current password for verification. All user sessions will be
    invalidated after password change for security.
    """
    async with UnitOfWork() as uow:
        deps = get_use_case_dependencies(uow.session)

        use_case = ChangePasswordUseCase(
            user_repository=deps["user_repo"],
            password_hasher=deps["password_hasher"],
            cache_service=deps["cache_service"],
        )

        use_case_request = ChangePasswordUseCaseRequest(
            user_id=current_user.id,
            current_password=request.current_password,
            new_password=request.new_password,
        )

        response = await use_case.execute(use_case_request)

        return ChangePasswordResponse(
            success=response.success,
            message=response.message,
        )


@router.put("/profile", response_model=UpdateProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information.

    Allows updating first name, last name, and phone number.
    Email cannot be changed through this endpoint.
    """
    async with UnitOfWork() as uow:
        deps = get_use_case_dependencies(uow.session)

        use_case = UpdateProfileUseCase(
            user_repository=deps["user_repo"],
            cache_service=deps["cache_service"],
        )

        use_case_request = UpdateProfileUseCaseRequest(
            user_id=current_user.id,
            first_name=request.first_name,
            last_name=request.last_name,
            phone_number=request.phone_number,
        )

        response = await use_case.execute(use_case_request)

        return UpdateProfileResponse(
            user_id=response.user_id,
            email=response.email,
            first_name=response.first_name,
            last_name=response.last_name,
            phone_number=response.phone_number,
            updated_at=response.updated_at,
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user: User = CurrentUser,
    db: Session = Depends(get_db)
):
    """
    Logout current user from all devices.

    Revokes all refresh tokens and invalidates all active sessions.
    The current access token will be blacklisted until its natural expiry.
    """
    from fastapi import Request
    from fastapi.security import HTTPBearer

    async with UnitOfWork() as uow:
        deps = get_use_case_dependencies(uow.session)

        # Extract token from Authorization header
        # In a real implementation, this should be passed from middleware
        token = ""  # Placeholder - will be extracted from request context

        use_case = LogoutUseCase(
            user_repository=deps["user_repo"],
            token_repository=deps["refresh_token_repo"],
            cache_service=deps["cache_service"],
        )

        use_case_request = LogoutUseCaseRequest(
            user_id=current_user.id,
            token=token,
        )

        response = await use_case.execute(use_case_request)

        return LogoutResponse(
            success=response.success,
            message=response.message,
        )