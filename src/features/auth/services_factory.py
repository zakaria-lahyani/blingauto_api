"""
Auth Services Factory - Clean service creation with proper dependency management
"""
from typing import Optional
from .config import AuthConfig
from .application.services import (
    AuthService,
    UserService, 
    EmailVerificationService,
    PasswordResetService,
    AccountLockoutService,
    TokenRotationService,
    AdminSetupService
)


class AuthServicesFactory:
    """Factory for creating auth services with proper dependencies"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self._auth_service: Optional[AuthService] = None
        self._user_service: Optional[UserService] = None
        self._email_verification_service: Optional[EmailVerificationService] = None
        self._password_reset_service: Optional[PasswordResetService] = None
        self._account_lockout_service: Optional[AccountLockoutService] = None
        self._token_rotation_service: Optional[TokenRotationService] = None
        self._admin_setup_service: Optional[AdminSetupService] = None
    
    def get_auth_service(self) -> AuthService:
        """Get or create AuthService instance"""
        if self._auth_service is None:
            self._auth_service = AuthService(self.config)
        return self._auth_service
    
    def get_user_service(self) -> UserService:
        """Get or create UserService instance"""
        if self._user_service is None:
            self._user_service = UserService(self.config)
        return self._user_service
    
    def get_email_verification_service(self) -> EmailVerificationService:
        """Get or create EmailVerificationService instance"""
        if self._email_verification_service is None:
            self._email_verification_service = EmailVerificationService(self.config)
        return self._email_verification_service
    
    def get_password_reset_service(self) -> PasswordResetService:
        """Get or create PasswordResetService instance"""
        if self._password_reset_service is None:
            self._password_reset_service = PasswordResetService(self.config)
        return self._password_reset_service
    
    def get_account_lockout_service(self) -> AccountLockoutService:
        """Get or create AccountLockoutService instance"""
        if self._account_lockout_service is None:
            self._account_lockout_service = AccountLockoutService(self.config)
        return self._account_lockout_service
    
    def get_token_rotation_service(self) -> TokenRotationService:
        """Get or create TokenRotationService instance"""
        if self._token_rotation_service is None:
            self._token_rotation_service = TokenRotationService(self.config)
        return self._token_rotation_service
    
    def get_admin_setup_service(self) -> AdminSetupService:
        """Get or create AdminSetupService instance"""
        if self._admin_setup_service is None:
            self._admin_setup_service = AdminSetupService(self.config)
        return self._admin_setup_service
    
    def cleanup(self):
        """Clean up all service instances"""
        self._auth_service = None
        self._user_service = None
        self._email_verification_service = None
        self._password_reset_service = None
        self._account_lockout_service = None
        self._token_rotation_service = None
        self._admin_setup_service = None