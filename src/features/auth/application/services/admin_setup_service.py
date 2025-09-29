"""
Admin setup service for automatic admin user creation
"""
import os
from typing import Optional
import logging

from src.features.auth.config import AuthConfig, AuthFeature
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole
from src.features.auth.infrastructure.database.repositories import AuthUserRepository
from src.features.auth.infrastructure.security import hash_password
from src.shared.simple_database import get_db_session

logger = logging.getLogger(__name__)


class AdminSetupService:
    """Clean admin setup using environment variables"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
    
    async def ensure_admin_exists(self) -> bool:
        """Ensure admin user exists, create if needed"""
        if not self.config.is_feature_enabled(AuthFeature.ADMIN_SETUP):
            return True
        
        if self.config.disable_admin_setup:
            logger.info("Admin setup is disabled via configuration")
            return True
        
        try:
            # Check if any admin exists
            admin_exists = await self._admin_exists()
            if admin_exists:
                logger.info("Admin user already exists")
                return True
            
            # Try to create from environment
            admin_email = self.config.initial_admin_email or os.getenv("INITIAL_ADMIN_EMAIL")
            admin_password = self.config.initial_admin_password or os.getenv("INITIAL_ADMIN_PASSWORD")
            
            if not admin_email or not admin_password:
                logger.warning("No admin user exists and environment variables not set")
                logger.warning("Set INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_PASSWORD to create admin")
                return False
            
            # Create admin user
            admin_user = AuthUser(
                email=admin_email.lower().strip(),
                password_hash=hash_password(admin_password),
                first_name=self.config.initial_admin_first_name or os.getenv("INITIAL_ADMIN_FIRST_NAME", "System"),
                last_name=self.config.initial_admin_last_name or os.getenv("INITIAL_ADMIN_LAST_NAME", "Administrator"),
                phone=os.getenv("INITIAL_ADMIN_PHONE"),
                role=AuthRole.ADMIN,
                email_verified=True  # Admin doesn't need email verification
            )
            
            async with get_db_session() as session:
                user_repo = AuthUserRepository(session)
                created_user = await user_repo.create(admin_user)
            
            logger.info(f"✅ Admin user created: {admin_email}")
            logger.info(f"   User ID: {created_user.id}")
            
            # Clear environment variables for security if configured
            if self.config.clear_admin_env_vars:
                self._clear_env_vars()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create admin user: {e}")
            return False
    
    async def _admin_exists(self) -> bool:
        """Check if any admin user exists"""
        try:
            async with get_db_session() as session:
                user_repo = AuthUserRepository(session)
                admins = await user_repo.list_by_role(AuthRole.ADMIN, limit=1)
                return len(admins) > 0
        except Exception as e:
            logger.error(f"Failed to check admin existence: {e}")
            return False
    
    def _clear_env_vars(self):
        """Clear admin environment variables for security"""
        env_vars = [
            "INITIAL_ADMIN_EMAIL",
            "INITIAL_ADMIN_PASSWORD", 
            "INITIAL_ADMIN_FIRST_NAME",
            "INITIAL_ADMIN_LAST_NAME",
            "INITIAL_ADMIN_PHONE"
        ]
        
        cleared_count = 0
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]
                cleared_count += 1
        
        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} admin environment variables for security")
    
    def get_setup_instructions(self) -> str:
        """Get setup instructions for admin creation"""
        return """
Admin Setup Instructions:
========================

Set these environment variables to create the initial admin user:

Required:
  INITIAL_ADMIN_EMAIL=admin@yourcompany.com
  INITIAL_ADMIN_PASSWORD=your-secure-password

Optional:
  INITIAL_ADMIN_FIRST_NAME=Admin
  INITIAL_ADMIN_LAST_NAME=User
  INITIAL_ADMIN_PHONE=+1234567890

Security:
  AUTH_CLEAR_ADMIN_ENV_VARS=true  # Clear env vars after creation
  AUTH_DISABLE_ADMIN_SETUP=false  # Disable admin setup entirely

Example:
  export INITIAL_ADMIN_EMAIL="admin@carwash.com"
  export INITIAL_ADMIN_PASSWORD="$(openssl rand -base64 32)"
  python -m src.main

The admin user will be created automatically on application startup.
"""