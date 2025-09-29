"""
Auth API router
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List, Optional
from uuid import UUID
import logging

from src.features.auth.presentation.api.schemas import (
    UserRegister, UserLogin, TokenResponse, RefreshTokenRequest,
    EmailVerificationRequest, EmailVerificationConfirm,
    ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest,
    UserResponse, UserUpdateProfile, UserRoleUpdate, UserListResponse,
    MessageResponse, AccountLockoutInfo, AuthFeatureStatus
)
from src.features.auth.presentation.api.dependencies import (
    get_current_user, get_current_active_user, require_admin, 
    require_manager_or_admin, get_optional_user
)
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole
from src.features.auth.config import AuthFeature
from src.shared.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    BusinessLogicError,
    InternalServerError,
    ErrorMessages,
    ErrorDetail
)

logger = logging.getLogger(__name__)


def create_auth_router(auth_module) -> APIRouter:
    """Create auth router with all endpoints"""
    
    router = APIRouter(prefix="/auth", tags=["Authentication"])
    
    # Dependencies
    current_user = get_current_active_user(auth_module)
    admin_required = require_admin(auth_module)
    manager_or_admin = require_manager_or_admin(auth_module)
    optional_user = get_optional_user(auth_module)
    
    @router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
    async def register(data: UserRegister, request: Request):
        """Register new user with enhanced error handling"""
        try:
            user = await auth_module.auth_service.register_user(
                email=data.email,
                password=data.password,
                first_name=data.first_name,
                last_name=data.last_name,
                phone=data.phone
            )
            
            # Send verification email if enabled
            if auth_module.config.is_feature_enabled(AuthFeature.EMAIL_VERIFICATION):
                try:
                    await auth_module.email_verification_service.send_verification_email(user)
                except Exception as email_error:
                    logger.warning(f"Failed to send verification email for user {user.id}: {email_error}")
                    # Continue with registration even if email fails
            
            logger.info(f"User registered successfully: {user.id}")
            return UserResponse.from_entity(user)
            
        except ValueError as e:
            # Handle validation errors
            error_message = str(e)
            logger.warning(f"Registration validation failed: {error_message}")
            
            # Check for specific business logic errors
            if error_message == "EMAIL_ALREADY_EXISTS":
                raise BusinessLogicError(
                    "A user with this email address already exists",
                    error_code="EMAIL_ALREADY_EXISTS",
                    details=[ErrorDetail(field="email", message="This email is already registered", code="EMAIL_ALREADY_EXISTS")]
                )
            elif error_message == "PHONE_ALREADY_EXISTS":
                raise BusinessLogicError(
                    "A user with this phone number already exists",
                    error_code="PHONE_ALREADY_EXISTS",
                    details=[ErrorDetail(field="phone", message="This phone number is already registered", code="PHONE_ALREADY_EXISTS")]
                )
            elif error_message == "USER_ALREADY_EXISTS":
                raise BusinessLogicError(
                    "A user with this information already exists. Please use different email or phone number.",
                    error_code="USER_ALREADY_EXISTS",
                    details=[ErrorDetail(message="User with this information already exists", code="USER_ALREADY_EXISTS")]
                )
            elif "password" in error_message.lower():
                raise ValidationError(
                    ErrorMessages.VALIDATION_PASSWORD_WEAK,
                    [ErrorDetail(field="password", message=error_message)]
                )
            else:
                raise ValidationError(error_message)
                
        except Exception as e:
            # Handle database constraint violations and other errors
            error_str = str(e).lower()
            
            # Check for database constraint violations that might have slipped through
            if "unique constraint" in error_str or "duplicate" in error_str or "already exists" in error_str:
                if "email" in error_str:
                    raise BusinessLogicError(
                        "A user with this email address already exists",
                        error_code="EMAIL_ALREADY_EXISTS",
                        details=[ErrorDetail(field="email", message="This email is already registered", code="EMAIL_ALREADY_EXISTS")]
                    )
                elif "phone" in error_str:
                    raise BusinessLogicError(
                        "A user with this phone number already exists",
                        error_code="PHONE_ALREADY_EXISTS",
                        details=[ErrorDetail(field="phone", message="This phone number is already registered", code="PHONE_ALREADY_EXISTS")]
                    )
                else:
                    raise BusinessLogicError(
                        "A user with this information already exists. Please use different email or phone number.",
                        error_code="USER_ALREADY_EXISTS",
                        details=[ErrorDetail(message="User with this information already exists", code="USER_ALREADY_EXISTS")]
                    )
            
            # Log unexpected errors with full traceback
            import traceback
            logger.error(f"Registration failed with unexpected error: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise InternalServerError(f"Failed to create user account: {str(e)}")
    
    @router.post("/login", response_model=TokenResponse)
    async def login(data: UserLogin, request: Request):
        """Login user with enhanced error handling"""
        try:
            user, access_token, refresh_token = await auth_module.auth_service.authenticate_user(
                email=data.email,
                password=data.password
            )
            
            logger.info(f"User {user.id} logged in successfully from {request.client.host if request.client else 'unknown'}")
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=auth_module.config.access_token_expire_minutes * 60
            )
            
        except ValueError as e:
            # Handle authentication failures
            error_message = str(e).lower()
            logger.warning(f"Login failed for email {data.email}: {e}")
            
            if "email verification required" in error_message:
                raise BusinessLogicError(
                    "Email verification required. Please check your email and verify your account before logging in.",
                    error_code="EMAIL_VERIFICATION_REQUIRED",
                    details=[ErrorDetail(field="email", message="Please verify your email address to log in", code="EMAIL_VERIFICATION_REQUIRED")]
                )
            elif "password" in error_message:
                from src.shared.exceptions import AuthenticationError
                raise AuthenticationError("Invalid email or password")
            elif "not found" in error_message or "invalid" in error_message:
                from src.shared.exceptions import AuthenticationError
                raise AuthenticationError("Invalid email or password")
            elif "inactive" in error_message or "disabled" in error_message:
                raise BusinessLogicError(ErrorMessages.BUSINESS_INACTIVE_USER)
            else:
                from src.shared.exceptions import AuthenticationError
                raise AuthenticationError("Authentication failed")
                
        except Exception as e:
            logger.error(f"Login failed with unexpected error: {e}")
            raise InternalServerError("Login service temporarily unavailable")
    
    @router.post("/refresh", response_model=TokenResponse)
    async def refresh_token(data: RefreshTokenRequest):
        """Refresh access token"""
        try:
            result = await auth_module.auth_service.refresh_tokens(data.refresh_token)
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token"
                )
            
            new_access_token, new_refresh_token = result
            
            return TokenResponse(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_in=auth_module.config.access_token_expire_minutes * 60
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token refresh failed")
    
    @router.post("/logout", response_model=MessageResponse)
    async def logout(
        data: RefreshTokenRequest,
        current_user: AuthUser = Depends(current_user)
    ):
        """Logout user"""
        try:
            await auth_module.auth_service.logout_user(current_user, data.refresh_token)
            return MessageResponse(message="Logged out successfully")
            
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed")
    
    @router.post("/logout-all", response_model=MessageResponse)
    async def logout_all_devices(current_user: AuthUser = Depends(current_user)):
        """Logout from all devices"""
        try:
            await auth_module.auth_service.logout_all_devices(current_user)
            return MessageResponse(message="Logged out from all devices")
            
        except Exception as e:
            logger.error(f"Logout all failed: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed")
    
    @router.post("/verify-email/request", response_model=MessageResponse)
    async def request_email_verification(data: EmailVerificationRequest):
        """Request email verification"""
        if not auth_module.config.is_feature_enabled(AuthFeature.EMAIL_VERIFICATION):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature not enabled")
        
        try:
            success = await auth_module.email_verification_service.resend_verification_email(data.email)
            return MessageResponse(message="If this email exists, verification email was sent")
            
        except Exception as e:
            logger.error(f"Email verification request failed: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send verification email")
    
    @router.get("/verify-email/confirm")
    async def verify_email_with_link(token: str):
        """Verify email with token from email link (GET request)"""
        if not auth_module.config.is_feature_enabled(AuthFeature.EMAIL_VERIFICATION):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature not enabled")
        
        try:
            user = await auth_module.email_verification_service.verify_email_with_token(token)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired verification token"
                )
            
            return {
                "success": True,
                "message": "Email verified successfully",
                "user_id": str(user.id),
                "email": user.email,
                "verified_at": user.email_verified_at.isoformat() if user.email_verified_at else None
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Email verification failed: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Email verification failed")

    @router.post("/verify-email/confirm", response_model=MessageResponse)
    async def confirm_email_verification(data: EmailVerificationConfirm):
        """Confirm email verification (POST with JSON - for API clients)"""
        if not auth_module.config.is_feature_enabled(AuthFeature.EMAIL_VERIFICATION):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature not enabled")
        
        try:
            user = await auth_module.email_verification_service.verify_email_with_token(data.token)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired verification token"
                )
            
            return MessageResponse(message="Email verified successfully")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Email verification failed: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Email verification failed")
    
    @router.post("/forgot-password", response_model=MessageResponse)
    async def forgot_password(data: ForgotPasswordRequest):
        """Request password reset"""
        if not auth_module.config.is_feature_enabled(AuthFeature.PASSWORD_RESET):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature not enabled")
        
        try:
            success = await auth_module.password_reset_service.request_password_reset(data.email)
            return MessageResponse(message="If this email exists, password reset instructions were sent")
            
        except Exception as e:
            logger.error(f"Password reset request failed: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Password reset request failed")
    
    @router.post("/reset-password", response_model=MessageResponse)
    async def reset_password(data: ResetPasswordRequest):
        """Reset password with token"""
        if not auth_module.config.is_feature_enabled(AuthFeature.PASSWORD_RESET):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature not enabled")
        
        try:
            user = await auth_module.password_reset_service.reset_password_with_token(
                data.token, data.new_password
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired reset token"
                )
            
            return MessageResponse(message="Password reset successful")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password reset failed: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Password reset failed")
    
    @router.post("/change-password", response_model=MessageResponse)
    async def change_password(
        data: ChangePasswordRequest,
        current_user: AuthUser = Depends(current_user)
    ):
        """Change password"""
        try:
            success = await auth_module.password_reset_service.change_password(
                current_user, data.current_password, data.new_password
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            return MessageResponse(message="Password changed successfully")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password change failed: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Password change failed")
    
    @router.get("/me", response_model=UserResponse)
    async def get_current_user_profile(current_user: AuthUser = Depends(current_user)):
        """Get current user profile"""
        return UserResponse.from_entity(current_user)
    
    @router.put("/me", response_model=UserResponse)
    async def update_current_user_profile(
        data: UserUpdateProfile,
        current_user: AuthUser = Depends(current_user)
    ):
        """Update current user profile"""
        try:
            updated_user = await auth_module.user_service.update_user_profile(
                current_user,
                first_name=data.first_name,
                last_name=data.last_name,
                phone=data.phone
            )
            
            return UserResponse.from_entity(updated_user)
            
        except Exception as e:
            logger.error(f"Profile update failed: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Profile update failed")
    
    @router.get("/users", response_model=UserListResponse)
    async def list_users(
        limit: int = 100,
        offset: int = 0,
        role: Optional[AuthRole] = None,
        admin_user: AuthUser = Depends(manager_or_admin)
    ):
        """List users (Manager/Admin only)"""
        try:
            if role:
                users = await auth_module.user_service.list_users_by_role(role, limit=limit, offset=offset)
            else:
                users = await auth_module.user_service.list_users(limit=limit, offset=offset)
            
            user_responses = [UserResponse.from_entity(user) for user in users]
            
            return UserListResponse(
                users=user_responses,
                total=len(user_responses),
                limit=limit,
                offset=offset
            )
            
        except Exception as e:
            logger.error(f"List users failed: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list users")
    
    @router.get("/users/{user_id}", response_model=UserResponse)
    async def get_user(
        user_id: UUID,
        admin_user: AuthUser = Depends(manager_or_admin)
    ):
        """Get user by ID (Manager/Admin only)"""
        try:
            user = await auth_module.user_service.get_user_by_id(user_id)
            
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            
            # Check if current user can manage this user
            if not auth_module.user_service.can_manage_user(admin_user, user):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access this user")
            
            return UserResponse.from_entity(user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get user failed: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user")
    
    @router.put("/users/{user_id}/role", response_model=UserResponse)
    async def change_user_role(
        user_id: UUID,
        data: UserRoleUpdate,
        admin_user: AuthUser = Depends(manager_or_admin)
    ):
        """Change user role (Manager/Admin only)"""
        try:
            user = await auth_module.user_service.get_user_by_id(user_id)
            
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            
            # Check permissions
            if not auth_module.user_service.can_manage_user(admin_user, user):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot manage this user")
            
            if not auth_module.user_service.can_assign_role(admin_user, data.role):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Cannot assign {data.role.value} role")
            
            updated_user = await auth_module.user_service.change_user_role(
                user, data.role, changed_by=admin_user.id
            )
            
            return UserResponse.from_entity(updated_user)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Role change failed: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Role change failed")
    
    @router.delete("/users/{user_id}", response_model=MessageResponse)
    async def delete_user(
        user_id: UUID,
        admin_user: AuthUser = Depends(admin_required)
    ):
        """Delete user (Admin only)"""
        try:
            success = await auth_module.user_service.delete_user(user_id)
            
            if not success:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            
            return MessageResponse(message="User deleted successfully")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Delete user failed: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete user")
    
    @router.get("/features", response_model=AuthFeatureStatus)
    async def get_auth_features():
        """Get auth feature status"""
        return AuthFeatureStatus(**auth_module.get_feature_status())
    
    @router.get("/verification-status/{email}")
    async def get_verification_status(email: str):
        """Get email verification status for a user"""
        from src.features.auth.infrastructure.database.repositories import AuthUserRepository
        from src.shared.simple_database import get_db_session
        
        async with get_db_session() as session:
            user_repo = AuthUserRepository(session)
            user = await user_repo.get_by_email(email.lower().strip())
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            return {
                "email": user.email,
                "email_verified": user.email_verified,
                "email_verified_at": user.email_verified_at.isoformat() if user.email_verified_at else None,
                "has_verification_token": bool(user.email_verification_token),
                "token_expires": user.email_verification_expires.isoformat() if user.email_verification_expires else None
            }

    return router