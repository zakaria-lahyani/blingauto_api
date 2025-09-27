"""
Auth Module - Main interface for authentication feature
"""
import logging
from typing import Dict, Any

from src.features.auth.config import AuthConfig, AuthFeature
from src.features.auth.application.services import (
    AuthService, 
    UserService,
    EmailVerificationService,
    PasswordResetService,
    AccountLockoutService,
    TokenRotationService,
    AdminSetupService
)

logger = logging.getLogger(__name__)


class AuthModule:
    """Authentication Feature Module"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self._initialized = False
        
        # Services
        self._auth_service = None
        self._user_service = None
        self._email_verification_service = None
        self._password_reset_service = None
        self._account_lockout_service = None
        self._token_rotation_service = None
        self._admin_setup_service = None
    
    @property
    def auth_service(self) -> AuthService:
        if self._auth_service is None:
            self._auth_service = AuthService(self.config)
        return self._auth_service
    
    @property
    def user_service(self) -> UserService:
        if self._user_service is None:
            self._user_service = UserService(self.config)
        return self._user_service
    
    @property
    def email_verification_service(self) -> EmailVerificationService:
        if self._email_verification_service is None:
            self._email_verification_service = EmailVerificationService(self.config)
        return self._email_verification_service
    
    @property
    def password_reset_service(self) -> PasswordResetService:
        if self._password_reset_service is None:
            self._password_reset_service = PasswordResetService(self.config)
        return self._password_reset_service
    
    @property
    def account_lockout_service(self) -> AccountLockoutService:
        if self._account_lockout_service is None:
            self._account_lockout_service = AccountLockoutService(self.config)
        return self._account_lockout_service
    
    @property
    def token_rotation_service(self) -> TokenRotationService:
        if self._token_rotation_service is None:
            self._token_rotation_service = TokenRotationService(self.config)
        return self._token_rotation_service
    
    @property
    def admin_setup_service(self) -> AdminSetupService:
        if self._admin_setup_service is None:
            self._admin_setup_service = AdminSetupService(self.config)
        return self._admin_setup_service
    
    def setup(self, app, prefix: str = "/auth"):
        """Setup auth module with FastAPI app"""
        from .presentation.api.router import create_auth_router
        
        router = create_auth_router(self)
        
        # Note: Auth-specific middleware is applied as route dependencies
        # since FastAPI routers don't support middleware directly
        
        app.include_router(router, prefix=prefix, tags=["Authentication"])
        
        logger.info(f"Auth module setup complete with prefix: {prefix}")
        
        # Log middleware approach
        if self.config.enable_rate_limiting:
            logger.info("Auth rate limiting enabled via route dependencies")
        if self.config.enable_security_logging:
            logger.info("Auth security logging enabled via route dependencies")
    
    async def initialize(self):
        """Initialize auth module"""
        if self._initialized:
            return
        
        try:
            # Initialize database tables
            await self._setup_database()
            
            # Setup admin user if configured
            if self.config.is_feature_enabled(AuthFeature.ADMIN_SETUP):
                await self.admin_setup_service.ensure_admin_exists()
            
            self._initialized = True
            logger.info("Auth module initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize auth module: {e}")
            raise
    
    async def _setup_database(self):
        """Setup auth database tables"""
        from src.features.auth.infrastructure.database.models import AuthUserModel
        from src.shared.database import get_engine

        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(AuthUserModel.metadata.create_all)
        
        logger.info("Auth database tables created")
    
    def get_dependencies(self) -> Dict[str, Any]:
        """Get auth dependencies for other modules"""
        from .presentation.api.dependencies import (
            get_current_user, 
            get_current_active_user,
            require_admin,
            require_manager_or_admin,
            get_optional_user
        )
        
        return {
            "auth_service": self.auth_service,
            "user_service": self.user_service,
            "get_current_user": get_current_user(self),
            "get_current_active_user": get_current_active_user(self),
            "require_admin": require_admin(self),
            "require_manager_or_admin": require_manager_or_admin(self),
            "get_optional_user": get_optional_user(self)
        }
    
    @property
    def get_current_user(self):
        """Get current user dependency - for easy access"""
        from .presentation.api.dependencies import get_current_user
        return get_current_user(self)
    
    @property  
    def get_current_admin(self):
        """Get current admin user dependency - for easy access"""
        from .presentation.api.dependencies import require_admin
        return require_admin(self)
    
    @property
    def get_current_manager(self):
        """Get current manager+ user dependency - for easy access"""
        from .presentation.api.dependencies import require_manager_or_admin
        return require_manager_or_admin(self)
    
    def require_role(self, role):
        """Get role requirement dependency - for easy access"""
        from .presentation.api.dependencies import require_role
        return require_role(role)(self)
    
    async def shutdown(self):
        """Cleanup auth module resources"""
        logger.info("Auth module shutdown")
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    def get_feature_status(self) -> Dict[str, bool]:
        """Get status of auth features"""
        return {
            feature.value: self.config.is_feature_enabled(feature)
            for feature in AuthFeature
        }