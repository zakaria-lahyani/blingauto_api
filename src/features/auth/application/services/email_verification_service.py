"""
Email verification service
"""
from datetime import datetime, timedelta
from typing import Optional
import logging

from src.features.auth.config import AuthConfig, AuthFeature
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.events import UserEmailVerified
from src.features.auth.infrastructure.database.repositories import AuthUserRepository
from src.features.auth.infrastructure.security.token_generator import generate_verification_token, hash_token
from src.shared.events import get_event_bus
from src.shared.services.email_service import get_email_service
from src.shared.simple_database import get_db_session

logger = logging.getLogger(__name__)


class EmailVerificationService:
    """Handle email verification"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self._event_bus = get_event_bus()
    
    async def send_verification_email(self, user: AuthUser) -> bool:
        """Send verification email to user"""
        if not self.config.is_feature_enabled(AuthFeature.EMAIL_VERIFICATION):
            return False
        
        try:
            # Check rate limiting
            if not await self._check_rate_limit(user):
                logger.warning(f"Rate limit exceeded for verification email: {user.email}")
                return False
            
            # Generate verification token
            token = generate_verification_token()
            expires_at = datetime.utcnow() + timedelta(hours=self.config.email_verification_expire_hours)
            
            # Store hashed token in user
            token_hash = hash_token(token)
            user.set_email_verification_token(token_hash, expires_at)
            
            async with get_db_session() as session:
                user_repo = AuthUserRepository(session)
                await user_repo.update(user)
            
            # Send email (this would integrate with email provider)
            await self._send_email(user, token)
            
            logger.info(f"Verification email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            return False
    
    async def verify_email_with_token(self, token: str) -> Optional[AuthUser]:
        """Verify email with token"""
        if not self.config.is_feature_enabled(AuthFeature.EMAIL_VERIFICATION):
            return None
        
        try:
            # Hash the provided token to match stored version
            token_hash = hash_token(token)
            
            async with get_db_session() as session:
                user_repo = AuthUserRepository(session)
                
                # Find user with this token
                user = await user_repo.get_by_verification_token(token_hash)
                
                if not user:
                    logger.warning("Invalid verification token attempted")
                    return None
                
                # Check if token is expired
                if user.email_verification_expires and datetime.utcnow() > user.email_verification_expires:
                    logger.warning(f"Expired verification token for user: {user.email}")
                    return None
                
                # Verify email
                user.verify_email()
                updated_user = await user_repo.update(user)
            
            # Send welcome email
            await self._send_welcome_email(user)
            
            # Publish event
            await self._event_bus.publish(UserEmailVerified(
                user_id=user.id,
                email=user.email,
                verified_at=datetime.utcnow()
            ))
            
            logger.info(f"Email verified for user: {user.email}")
            return updated_user
            
        except Exception as e:
            logger.error(f"Email verification failed: {e}")
            return None
    
    async def resend_verification_email(self, email: str) -> bool:
        """Resend verification email"""
        async with get_db_session() as session:
            user_repo = AuthUserRepository(session)
            user = await user_repo.get_by_email(email.lower().strip())
            
            if not user:
                logger.warning(f"Verification resend requested for non-existent email: {email}")
                return True  # Don't reveal if email exists
            
            if user.email_verified:
                logger.info(f"Verification resend requested for already verified email: {email}")
                return True  # Don't reveal verification status
            
            return await self.send_verification_email(user)
    
    async def _check_rate_limit(self, user: AuthUser) -> bool:
        """Check if user has exceeded verification email rate limit"""
        if not user.email_verification_expires:
            return True
        
        # Check if enough time has passed since last verification email
        time_since_last = datetime.utcnow() - (
            user.email_verification_expires - timedelta(hours=self.config.email_verification_expire_hours)
        )
        
        min_interval = timedelta(minutes=self.config.email_verification_rate_limit_minutes)
        return time_since_last >= min_interval
    
    async def _send_email(self, user: AuthUser, token: str):
        """Send verification email using the email service"""
        try:
            # Build verification link for API endpoint
            base_url = self.config.app_url or "http://localhost:8000"
            verification_link = f"{base_url}/auth/verify-email/confirm?token={token}"
            
            # Get email service
            email_service = get_email_service()
            
            # Send verification email using template
            success = await email_service.send_verification_email(
                to=user.email,
                first_name=user.first_name,
                verification_link=verification_link,
                expires_hours=self.config.email_verification_expire_hours
            )
            
            if success:
                logger.info(f"Verification email sent successfully to {user.email}")
            else:
                logger.error(f"Failed to send verification email to {user.email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending verification email to {user.email}: {e}")
            return False
    
    async def _send_welcome_email(self, user: AuthUser):
        """Send welcome email after successful verification"""
        try:
            # Get email service
            email_service = get_email_service()
            
            # Build login link
            base_url = self.config.app_url or "https://carwash.com"
            login_link = f"{base_url}/login"
            
            # Send welcome email using template
            success = await email_service.send_welcome_email(
                to=user.email,
                first_name=user.first_name,
                login_link=login_link
            )
            
            if success:
                logger.info(f"Welcome email sent successfully to {user.email}")
            else:
                logger.error(f"Failed to send welcome email to {user.email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending welcome email to {user.email}: {e}")
            return False