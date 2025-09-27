"""
Core authentication service
"""
from typing import Optional, Tuple
from datetime import datetime
import logging

from src.features.auth.config import AuthConfig, AuthFeature
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole
from src.features.auth.domain.events import UserRegistered, UserLoggedIn
from src.features.auth.infrastructure.database.repositories import AuthUserRepository
from src.features.auth.infrastructure.security import hash_password, JWTHandler
from src.shared.events import get_event_bus

logger = logging.getLogger(__name__)


class AuthService:
    """Core authentication service"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self._user_repo = AuthUserRepository()
        self._jwt_handler = JWTHandler(config)
        self._event_bus = get_event_bus()
    
    async def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        role: AuthRole = AuthRole.CLIENT
    ) -> AuthUser:
        """Register new user"""
        
        # Check if user already exists
        existing_user = await self._user_repo.get_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Create user entity
        user = AuthUser(
            email=email.lower().strip(),
            password_hash=hash_password(password),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            phone=phone,
            role=role,
            email_verified=not self.config.is_feature_enabled(AuthFeature.EMAIL_VERIFICATION)
        )
        
        # Save user
        created_user = await self._user_repo.create(user)
        
        # Publish event
        await self._event_bus.publish(UserRegistered(
            user_id=created_user.id,
            email=created_user.email,
            first_name=created_user.first_name,
            last_name=created_user.last_name,
            role=created_user.role.value,
            requires_verification=self.config.is_feature_enabled(AuthFeature.EMAIL_VERIFICATION)
        ))
        
        logger.info(f"User registered: {created_user.email}")
        return created_user
    
    async def authenticate_user(self, email: str, password: str) -> Tuple[AuthUser, str, str]:
        """Authenticate user and return tokens"""
        
        # Get user
        user = await self._user_repo.get_by_email(email.lower().strip())
        if not user:
            raise ValueError("Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            raise ValueError("Account is disabled")
        
        # Check account lockout
        if self.config.is_feature_enabled(AuthFeature.ACCOUNT_LOCKOUT) and user.is_locked:
            raise ValueError(f"Account is locked until {user.locked_until}")
        
        # Verify password
        if not user.verify_password(password):
            # Handle failed login if lockout is enabled
            if self.config.is_feature_enabled(AuthFeature.ACCOUNT_LOCKOUT):
                from .account_lockout_service import AccountLockoutService
                lockout_service = AccountLockoutService(self.config)
                await lockout_service.record_failed_attempt(user)
            
            raise ValueError("Invalid credentials")
        
        # Check email verification
        if self.config.is_feature_enabled(AuthFeature.EMAIL_VERIFICATION) and not user.email_verified:
            raise ValueError("Email verification required")
        
        # Record successful login
        user.record_successful_login()
        await self._user_repo.update(user)
        
        # Generate tokens
        access_token = self._jwt_handler.create_access_token(
            user_id=str(user.id),
            email=user.email,
            role=user.role.value
        )
        
        refresh_token = self._jwt_handler.create_refresh_token(user_id=str(user.id))
        
        # Handle token rotation if enabled
        if self.config.is_feature_enabled(AuthFeature.TOKEN_ROTATION):
            from .token_rotation_service import TokenRotationService
            rotation_service = TokenRotationService(self.config)
            await rotation_service.store_refresh_token(user, refresh_token)
        
        # Publish event
        await self._event_bus.publish(UserLoggedIn(
            user_id=user.id,
            email=user.email,
            login_time=datetime.utcnow()
        ))
        
        logger.info(f"User authenticated: {user.email}")
        return user, access_token, refresh_token
    
    async def get_user_from_token(self, token: str) -> Optional[AuthUser]:
        """Get user from access token"""
        payload = self._jwt_handler.verify_token(token)
        if not payload:
            return None
        
        if payload.get("type") != "access":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        try:
            from uuid import UUID
            user = await self._user_repo.get_by_id(UUID(user_id))
            
            # Check if user is still active
            if user and not user.is_active:
                return None
            
            return user
        except (ValueError, TypeError):
            return None
    
    async def refresh_tokens(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Refresh access and refresh tokens"""
        if not self.config.is_feature_enabled(AuthFeature.TOKEN_ROTATION):
            # Simple refresh without rotation
            payload = self._jwt_handler.verify_token(refresh_token)
            if not payload or payload.get("type") != "refresh":
                return None
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            try:
                from uuid import UUID
                user = await self._user_repo.get_by_id(UUID(user_id))
                if not user or not user.is_active:
                    return None
                
                # Generate new tokens
                new_access_token = self._jwt_handler.create_access_token(
                    user_id=str(user.id),
                    email=user.email,
                    role=user.role.value
                )
                
                return new_access_token, refresh_token
            except (ValueError, TypeError):
                return None
        else:
            # Use token rotation service
            from .token_rotation_service import TokenRotationService
            rotation_service = TokenRotationService(self.config)
            return await rotation_service.rotate_refresh_token(refresh_token)
    
    async def logout_user(self, user: AuthUser, refresh_token: str = None):
        """Logout user"""
        if refresh_token and self.config.is_feature_enabled(AuthFeature.TOKEN_ROTATION):
            from .token_rotation_service import TokenRotationService
            rotation_service = TokenRotationService(self.config)
            await rotation_service.revoke_refresh_token(user, refresh_token)
        
        logger.info(f"User logged out: {user.email}")
    
    async def logout_all_devices(self, user: AuthUser):
        """Logout user from all devices"""
        if self.config.is_feature_enabled(AuthFeature.TOKEN_ROTATION):
            user.clear_all_refresh_tokens()
            await self._user_repo.update(user)
        
        logger.info(f"User logged out from all devices: {user.email}")