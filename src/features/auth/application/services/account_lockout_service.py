"""
Account lockout service for brute force protection
"""
from datetime import datetime, timedelta
import logging

from src.features.auth.config import AuthConfig, AuthFeature
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.events import UserAccountLocked
from src.features.auth.infrastructure.database.repositories import AuthUserRepository
from src.shared.events import get_event_bus

logger = logging.getLogger(__name__)


class AccountLockoutService:
    """Protect against brute force attacks with progressive lockout"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self._user_repo = AuthUserRepository()
        self._event_bus = get_event_bus()
    
    async def record_failed_attempt(self, user: AuthUser) -> int:
        """Record failed login attempt and return remaining attempts"""
        if not self.config.is_feature_enabled(AuthFeature.ACCOUNT_LOCKOUT):
            return self.config.max_login_attempts
        
        try:
            # Check if currently locked out
            if user.is_locked:
                logger.warning(f"Login attempt on locked account: {user.email}")
                return 0
            
            # Increment failed attempts
            user.record_failed_login()
            
            # Check if should lock out
            if user.failed_login_attempts >= self.config.max_login_attempts:
                await self._lock_account(user)
                remaining = 0
            else:
                remaining = self.config.max_login_attempts - user.failed_login_attempts
            
            await self._user_repo.update(user)
            
            logger.info(f"Failed login attempt {user.failed_login_attempts} for {user.email}")
            return remaining
            
        except Exception as e:
            logger.error(f"Failed to record login attempt: {e}")
            return 0
    
    async def record_successful_login(self, user: AuthUser):
        """Reset failed attempts after successful login"""
        if not self.config.is_feature_enabled(AuthFeature.ACCOUNT_LOCKOUT):
            return
        
        try:
            if user.failed_login_attempts > 0:
                logger.info(f"Resetting {user.failed_login_attempts} failed attempts for {user.email}")
            
            user.unlock_account()
            user.record_successful_login()
            await self._user_repo.update(user)
            
        except Exception as e:
            logger.error(f"Failed to record successful login: {e}")
    
    async def unlock_account(self, user: AuthUser) -> bool:
        """Manually unlock account (admin action)"""
        try:
            user.unlock_account()
            await self._user_repo.update(user)
            
            logger.info(f"Account manually unlocked: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unlock account: {e}")
            return False
    
    async def _lock_account(self, user: AuthUser):
        """Lock account with progressive lockout duration"""
        # Calculate lockout duration using progressive backoff
        lockout_minutes = min(
            self.config.initial_lockout_minutes * (self.config.lockout_multiplier ** user.lockout_count),
            self.config.max_lockout_minutes
        )
        
        locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
        user.lock_account(locked_until)
        
        # Publish event
        await self._event_bus.publish(UserAccountLocked(
            user_id=user.id,
            email=user.email,
            locked_until=locked_until,
            attempt_count=user.failed_login_attempts,
            lockout_count=user.lockout_count
        ))
        
        logger.warning(
            f"Account locked for {lockout_minutes} minutes: {user.email} "
            f"(lockout #{user.lockout_count})"
        )
    
    async def get_lockout_info(self, user: AuthUser) -> dict:
        """Get detailed lockout information"""
        return {
            "is_locked": user.is_locked,
            "failed_attempts": user.failed_login_attempts,
            "max_attempts": self.config.max_login_attempts,
            "locked_until": user.locked_until.isoformat() if user.locked_until else None,
            "lockout_count": user.lockout_count,
            "last_failed_login": user.last_failed_login.isoformat() if user.last_failed_login else None,
            "last_successful_login": user.last_login.isoformat() if user.last_login else None
        }