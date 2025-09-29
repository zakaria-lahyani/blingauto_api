"""
Password reset service
"""
from datetime import datetime, timedelta
from typing import Optional
import logging

from src.features.auth.config import AuthConfig, AuthFeature
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.events import UserPasswordChanged
from src.features.auth.infrastructure.database.repositories import AuthUserRepository
from src.features.auth.infrastructure.security.token_generator import generate_reset_token, hash_token
from src.shared.events import get_event_bus
from src.shared.services.email_service import get_email_service

logger = logging.getLogger(__name__)


class PasswordResetService:
    """Handle password reset functionality"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self._event_bus = get_event_bus()
    
    async def request_password_reset(self, email: str) -> bool:
        """Request password reset for email"""
        if not self.config.is_feature_enabled(AuthFeature.PASSWORD_RESET):
            return False
        
        try:
            # Use database session
            from src.shared.simple_database import get_db_session
            async with get_db_session() as session:
                user_repo = AuthUserRepository(session)
                user = await user_repo.get_by_email(email.lower().strip())
            
            if not user:
                # Don't reveal if email exists
                logger.warning(f"Password reset requested for non-existent email: {email}")
                return True
            
            # Check rate limiting
            if not await self._check_rate_limit(user):
                logger.warning(f"Rate limit exceeded for password reset: {email}")
                return False
            
            # Generate reset token
            token = generate_reset_token()
            expires_at = datetime.utcnow() + timedelta(hours=self.config.password_reset_expire_hours)
            
            # Store hashed token in user
            token_hash = hash_token(token)
            user.set_password_reset_token(token_hash, expires_at)
            
            # Update user with token
            async with get_db_session() as session:
                user_repo = AuthUserRepository(session)
                await user_repo.update(user)
            
            # Send reset email
            await self._send_reset_email(user, token)
            
            logger.info(f"Password reset email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to request password reset: {e}")
            return False
    
    async def reset_password_with_token(self, token: str, new_password: str) -> Optional[AuthUser]:
        """Reset password using token"""
        if not self.config.is_feature_enabled(AuthFeature.PASSWORD_RESET):
            return None
        
        try:
            # Hash the provided token to match stored version
            token_hash = hash_token(token)
            
            # Find user with this token
            from src.shared.simple_database import get_db_session
            async with get_db_session() as session:
                user_repo = AuthUserRepository(session)
                user = await user_repo.get_by_reset_token(token_hash)
            
            if not user:
                logger.warning("Invalid password reset token attempted")
                return None
            
            # Check if token is expired
            if user.password_reset_expires and datetime.utcnow() > user.password_reset_expires:
                logger.warning(f"Expired password reset token for user: {user.email}")
                return None
            
            # Update password
            user.change_password(new_password)
            user.clear_password_reset_token()
            
            # Clear all refresh tokens for security
            user.clear_all_refresh_tokens()
            
            # Update user
            async with get_db_session() as session:
                user_repo = AuthUserRepository(session)
                updated_user = await user_repo.update(user)
            
            # Send confirmation email
            await self._send_password_changed_email(user)
            
            # Publish event
            await self._event_bus.publish(UserPasswordChanged(
                user_id=user.id,
                email=user.email,
                changed_at=datetime.utcnow(),
                via_reset=True
            ))
            
            logger.info(f"Password reset successful for user: {user.email}")
            return updated_user
            
        except Exception as e:
            logger.error(f"Password reset failed: {e}")
            return None
    
    async def change_password(self, user: AuthUser, current_password: str, new_password: str) -> bool:
        """Change password with current password verification"""
        try:
            # Verify current password
            if not user.verify_password(current_password):
                return False
            
            # Update password
            user.change_password(new_password)
            
            # Update user in database
            from src.shared.simple_database import get_db_session
            async with get_db_session() as session:
                user_repo = AuthUserRepository(session)
                await user_repo.update(user)
            
            # Send confirmation email
            await self._send_password_changed_email(user)
            
            # Publish event
            await self._event_bus.publish(UserPasswordChanged(
                user_id=user.id,
                email=user.email,
                changed_at=datetime.utcnow(),
                via_reset=False
            ))
            
            logger.info(f"Password changed for user: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Password change failed: {e}")
            return False
    
    async def _check_rate_limit(self, user: AuthUser) -> bool:
        """Check if user has exceeded password reset rate limit"""
        if not user.password_reset_requested_at:
            return True
        
        time_since_last = datetime.utcnow() - user.password_reset_requested_at
        min_interval = timedelta(hours=self.config.password_reset_rate_limit_hours)
        
        return time_since_last >= min_interval
    
    async def _send_reset_email(self, user: AuthUser, token: str):
        """Send password reset email using the email service"""
        try:
            # Build reset link
            base_url = self.config.app_url or "https://carwash.com"
            reset_link = f"{base_url}/reset-password?token={token}"
            
            # Get email service
            email_service = get_email_service()
            
            # Send password reset email using template
            success = await email_service.send_password_reset_email(
                to=user.email,
                first_name=user.first_name,
                reset_link=reset_link,
                expires_hours=self.config.password_reset_expire_hours
            )
            
            if success:
                logger.info(f"Password reset email sent successfully to {user.email}")
            else:
                logger.error(f"Failed to send password reset email to {user.email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending password reset email to {user.email}: {e}")
            return False
    
    async def _send_password_changed_email(self, user: AuthUser):
        """Send password changed confirmation email"""
        try:
            # Get email service
            email_service = get_email_service()
            
            # Create simple password change notification
            subject = "Password Changed - Car Wash Service"
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2>Password Changed Successfully</h2>
                <p>Hello {user.first_name},</p>
                <p>Your password has been successfully changed for your Car Wash Service account.</p>
                <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0;">
                    <strong>Security Notice:</strong> If you didn't make this change, please contact our support team immediately.
                </div>
                <p>Best regards,<br>Car Wash Service Team</p>
            </body>
            </html>
            """
            
            text_body = f"""
            Password Changed Successfully
            
            Hello {user.first_name},
            
            Your password has been successfully changed for your Car Wash Service account.
            
            Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
            
            Security Notice: If you didn't make this change, please contact our support team immediately.
            
            Best regards,
            Car Wash Service Team
            """
            
            # Send password change notification
            success = await email_service.send_email(
                to=user.email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
            if success:
                logger.info(f"Password change notification sent successfully to {user.email}")
            else:
                logger.error(f"Failed to send password change notification to {user.email}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending password change notification to {user.email}: {e}")
            return False