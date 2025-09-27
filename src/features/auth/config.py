"""
Authentication Module Configuration
"""
import asyncio
import logging
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class AuthFeature(str, Enum):
    """Available auth features"""
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_LOCKOUT = "account_lockout"
    TOKEN_ROTATION = "token_rotation"
    RATE_LIMITING = "rate_limiting"
    ADMIN_SETUP = "admin_setup"


class AuthConfig(BaseSettings):
    """Authentication module configuration with secure secrets management"""
    
    # Core settings
    enabled_features: List[AuthFeature] = Field(
        default=[
            AuthFeature.EMAIL_VERIFICATION,
            AuthFeature.PASSWORD_RESET,
            AuthFeature.ACCOUNT_LOCKOUT,
            AuthFeature.TOKEN_ROTATION,
            AuthFeature.RATE_LIMITING,
            AuthFeature.ADMIN_SETUP
        ]
    )
    
    # JWT settings (will be loaded from secrets)
    jwt_secret_key: Optional[str] = Field(default=None, description="Secret key for JWT tokens")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=7)
    
    # Database settings
    database_url: Optional[str] = Field(default=None)
    table_prefix: str = Field(default="auth_")
    
    # Redis settings
    redis_url: Optional[str] = Field(default=None, description="Redis URL for caching and rate limiting")
    
    # Email verification
    email_verification_expire_hours: int = Field(default=24)
    email_verification_rate_limit_minutes: int = Field(default=5)
    
    # Password reset
    password_reset_expire_hours: int = Field(default=2)
    password_reset_rate_limit_hours: int = Field(default=1)
    
    # Account lockout
    max_login_attempts: int = Field(default=5)
    initial_lockout_minutes: int = Field(default=5)
    max_lockout_minutes: int = Field(default=60)
    lockout_multiplier: int = Field(default=2)
    
    # Rate limiting
    enable_rate_limiting: bool = Field(default=True)
    
    # Role-based rate limits (requests per minute)
    admin_rate_limit: int = Field(default=200)
    manager_rate_limit: int = Field(default=100)
    washer_rate_limit: int = Field(default=60)
    client_rate_limit: int = Field(default=30)
    
    # Security logging
    enable_security_logging: bool = Field(default=True)
    log_failed_attempts: bool = Field(default=True)
    log_successful_auth: bool = Field(default=True)
    
    # Email provider settings
    email_provider: str = Field(default="mock", description="Email provider type: smtp, mock")
    smtp_host: Optional[str] = Field(default=None, description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    from_email: str = Field(default="noreply@carwash.com", description="From email address")
    support_email: str = Field(default="support@carwash.com", description="Support email address")
    app_name: str = Field(default="Car Wash Service", description="Application name for emails")
    app_url: str = Field(default="https://carwash.com", description="Application URL for links")
    
    # Admin setup (will be loaded from secrets)
    initial_admin_email: Optional[str] = Field(default=None)
    initial_admin_password: Optional[str] = Field(default=None)
    initial_admin_first_name: str = Field(default="System")
    initial_admin_last_name: str = Field(default="Administrator")
    clear_admin_env_vars: bool = Field(default=True)
    disable_admin_setup: bool = Field(default=False)
    
    # Secrets management
    use_secrets_manager: bool = Field(default=False, description="Use AWS Secrets Manager for secrets")
    aws_secrets_name: Optional[str] = Field(default=None, description="AWS Secrets Manager secret name")
    aws_region: str = Field(default="us-east-1", description="AWS region")
    
    # Internal flag to track if secrets are loaded
    _secrets_loaded: bool = False
    
    class Config:
        env_prefix = "AUTH_"
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    @validator('jwt_secret_key')
    def validate_jwt_secret(cls, v):
        """Validate JWT secret key strength"""
        if v and len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
        
        # Check for weak default values
        weak_secrets = [
            "your-super-secret-jwt-key-change-this-in-production",
            "secret",
            "password", 
            "123456",
            "change-me"
        ]
        
        if v and v.lower() in [s.lower() for s in weak_secrets]:
            raise ValueError("JWT secret key appears to be a default/weak value. Please use a strong, unique secret.")
        
        return v
    
    @validator('email_provider')
    def validate_email_provider(cls, v, values):
        """Warn if using mock email provider in production"""
        environment = values.get('environment', 'development')
        if v == "mock" and environment == "production":
            logger.warning("Using mock email provider in production environment")
        return v
    
    async def load_secrets(self) -> None:
        """Load secrets from configured provider"""
        if self._secrets_loaded:
            return
        
        try:
            from src.shared.services.secrets_manager import get_secrets_manager
            
            secrets_manager = get_secrets_manager()
            secrets = await secrets_manager.get_secrets(self.aws_secrets_name or "default")
            
            if secrets:
                # Update configuration with secrets
                self._update_from_secrets(secrets)
                logger.info("Successfully loaded secrets from secrets manager")
            else:
                logger.warning("No secrets loaded from secrets manager")
            
            self._secrets_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")
            # Don't raise - allow fallback to environment variables
            self._secrets_loaded = True
    
    def _update_from_secrets(self, secrets: Dict[str, Any]) -> None:
        """Update configuration with loaded secrets"""
        secret_mappings = {
            'jwt_secret_key': 'jwt_secret_key',
            'database_url': 'database_url',
            'redis_url': 'redis_url',
            'smtp_password': 'smtp_password',
            'initial_admin_password': 'initial_admin_password',
            'initial_admin_email': 'initial_admin_email'
        }
        
        for config_key, secret_key in secret_mappings.items():
            if secret_key in secrets and secrets[secret_key]:
                setattr(self, config_key, secrets[secret_key])
                logger.debug(f"Updated {config_key} from secrets")
    
    def validate_required_secrets(self) -> None:
        """Validate that all required secrets are present"""
        if not self.jwt_secret_key:
            raise ValueError("JWT secret key is required but not configured")
        
        # Validate JWT secret strength
        if len(self.jwt_secret_key) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
    
    def is_feature_enabled(self, feature: AuthFeature) -> bool:
        """Check if a feature is enabled"""
        return feature in self.enabled_features
    
    def get_table_name(self, base_name: str) -> str:
        """Get prefixed table name"""
        return f"{self.table_prefix}{base_name}"
    
    def get_role_rate_limit(self, role: str) -> int:
        """Get rate limit for a specific role"""
        role_limits = {
            "admin": self.admin_rate_limit,
            "manager": self.manager_rate_limit, 
            "washer": self.washer_rate_limit,
            "client": self.client_rate_limit
        }
        return role_limits.get(role.lower(), self.client_rate_limit)
    
    def is_production_ready(self) -> tuple[bool, List[str]]:
        """Check if configuration is production ready"""
        issues = []
        
        # Check secrets
        if not self.jwt_secret_key:
            issues.append("JWT secret key not configured")
        elif len(self.jwt_secret_key) < 32:
            issues.append("JWT secret key too short (minimum 32 characters)")
        
        # Check database
        if not self.database_url:
            issues.append("Database URL not configured")
        
        # Check Redis for production
        if not self.redis_url and self.enable_rate_limiting:
            issues.append("Redis URL not configured but rate limiting is enabled")
        
        # Check email configuration
        if self.email_provider == "mock":
            issues.append("Using mock email provider (not suitable for production)")
        elif self.email_provider == "smtp" and not self.smtp_password:
            issues.append("SMTP email provider configured but no password provided")
        
        return len(issues) == 0, issues