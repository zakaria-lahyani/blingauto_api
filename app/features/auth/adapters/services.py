from typing import Optional, Dict, Any
import logging

from app.features.auth.ports import (
    IPasswordHasher,
    ITokenService,
    IEmailService,
    ICacheService,
)
from app.core.security import password_hasher, jwt_handler
from app.core.cache import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class PasswordHasherAdapter(IPasswordHasher):
    """Adapter for password hashing service."""
    
    def hash(self, password: str) -> str:
        """Hash a password."""
        return password_hasher.hash(password)
    
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return password_hasher.verify(plain_password, hashed_password)


class TokenServiceAdapter(ITokenService):
    """Adapter for JWT token service."""
    
    def create_access_token(self, user_id: str, role: str) -> str:
        """Create an access token."""
        return jwt_handler.create_access_token(user_id, role)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a refresh token."""
        return jwt_handler.create_refresh_token(user_id)
    
    def validate_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate an access token."""
        return jwt_handler.validate_access_token(token)
    
    def validate_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a refresh token."""
        return jwt_handler.validate_refresh_token(token)


class EmailServiceAdapter(IEmailService):
    """Adapter for email service using SMTP."""

    def __init__(self):
        """Initialize email service with SMTP configuration."""
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.smtp_from_email = settings.smtp_from_email
        self.smtp_from_name = settings.smtp_from_name
        self.frontend_url = settings.frontend_url
        self.use_tls = settings.smtp_use_tls

    async def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Send email using SMTP."""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.smtp_from_name} <{self.smtp_from_email}>"
            msg['To'] = to_email

            # Add both text and HTML parts
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_verification_email(self, email: str, token: str) -> bool:
        """Send email verification."""
        verification_url = f"{self.frontend_url}/verify-email?token={token}"

        subject = "Verify Your Email - BlingAuto Car Wash"

        html_body = f"""
        <html>
        <body>
            <h2>Welcome to BlingAuto Car Wash!</h2>
            <p>Thank you for registering. Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_url}">Verify Email</a></p>
            <p>Or copy and paste this link in your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account, please ignore this email.</p>
            <br>
            <p>Best regards,<br>BlingAuto Team</p>
        </body>
        </html>
        """

        text_body = f"""
        Welcome to BlingAuto Car Wash!

        Thank you for registering. Please verify your email address by visiting:
        {verification_url}

        This link will expire in 24 hours.

        If you didn't create an account, please ignore this email.

        Best regards,
        BlingAuto Team
        """

        return await self._send_email(email, subject, html_body, text_body)

    async def send_password_reset_email(self, email: str, token: str) -> bool:
        """Send password reset email."""
        reset_url = f"{self.frontend_url}/reset-password?token={token}"

        subject = "Password Reset Request - BlingAuto Car Wash"

        html_body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You requested to reset your password. Click the link below to set a new password:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>Or copy and paste this link in your browser:</p>
            <p>{reset_url}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, please ignore this email and your password will remain unchanged.</p>
            <br>
            <p>Best regards,<br>BlingAuto Team</p>
        </body>
        </html>
        """

        text_body = f"""
        Password Reset Request

        You requested to reset your password. Visit this link to set a new password:
        {reset_url}

        This link will expire in 1 hour.

        If you didn't request this, please ignore this email and your password will remain unchanged.

        Best regards,
        BlingAuto Team
        """

        return await self._send_email(email, subject, html_body, text_body)

    async def send_welcome_email(self, email: str, first_name: str) -> bool:
        """Send welcome email."""
        subject = "Welcome to BlingAuto Car Wash!"

        html_body = f"""
        <html>
        <body>
            <h2>Welcome to BlingAuto, {first_name}!</h2>
            <p>Your account has been successfully verified.</p>
            <p>You can now book car wash services and enjoy our premium services.</p>
            <p><a href="{self.frontend_url}/login">Login to Your Account</a></p>
            <br>
            <p>Best regards,<br>BlingAuto Team</p>
        </body>
        </html>
        """

        text_body = f"""
        Welcome to BlingAuto, {first_name}!

        Your account has been successfully verified.

        You can now book car wash services and enjoy our premium services.

        Visit {self.frontend_url}/login to login to your account.

        Best regards,
        BlingAuto Team
        """

        return await self._send_email(email, subject, html_body, text_body)

    async def send_account_locked_email(self, email: str, locked_until: str) -> bool:
        """Send account locked notification."""
        subject = "Account Locked - BlingAuto Car Wash"

        html_body = f"""
        <html>
        <body>
            <h2>Account Security Alert</h2>
            <p>Your account has been temporarily locked due to multiple failed login attempts.</p>
            <p>Your account will be automatically unlocked at: <strong>{locked_until}</strong></p>
            <p>If you believe this was not you, please contact our support team immediately.</p>
            <br>
            <p>Best regards,<br>BlingAuto Team</p>
        </body>
        </html>
        """

        text_body = f"""
        Account Security Alert

        Your account has been temporarily locked due to multiple failed login attempts.

        Your account will be automatically unlocked at: {locked_until}

        If you believe this was not you, please contact our support team immediately.

        Best regards,
        BlingAuto Team
        """

        return await self._send_email(email, subject, html_body, text_body)


class CacheServiceAdapter(ICacheService):
    """Adapter for cache service using Redis."""

    def __init__(self):
        """Initialize cache service with Redis client."""
        self.redis = redis_client

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user data."""
        try:
            import json
            data = self.redis.get(f"user:{user_id}")
            if data:
                return json.loads(data) if isinstance(data, (str, bytes)) else data
            return None
        except Exception as e:
            logger.error(f"Failed to get user from cache: {str(e)}")
            return None

    async def set_user(self, user_id: str, user_data: Dict[str, Any], ttl: int = 300) -> bool:
        """Cache user data."""
        try:
            import json
            return self.redis.setex(
                f"user:{user_id}",
                ttl,
                json.dumps(user_data)
            )
        except Exception as e:
            logger.error(f"Failed to set user in cache: {str(e)}")
            return False

    async def delete_user(self, user_id: str) -> bool:
        """Delete cached user data."""
        try:
            return self.redis.delete(f"user:{user_id}") > 0
        except Exception as e:
            logger.error(f"Failed to delete user from cache: {str(e)}")
            return False

    def invalidate_user_cache(self, user_id: str) -> bool:
        """Invalidate all cache entries for a user."""
        try:
            # Delete user cache
            self.redis.delete(f"user:{user_id}")
            # Delete all user sessions using pattern matching
            pattern = f"session:{user_id}:*"
            for key in self.redis.scan_iter(match=pattern):
                self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate user cache: {str(e)}")
            return False

    def invalidate_user_sessions(self, user_id: str) -> bool:
        """Invalidate all active sessions for a user."""
        try:
            pattern = f"session:{user_id}:*"
            count = 0
            for key in self.redis.scan_iter(match=pattern):
                self.redis.delete(key)
                count += 1
            logger.info(f"Invalidated {count} sessions for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate user sessions: {str(e)}")
            return False

    def blacklist_token(self, token: str, ttl: int = 3600) -> bool:
        """Blacklist a token until its expiry."""
        try:
            # Store token in blacklist with TTL matching token expiry
            return self.redis.setex(f"blacklist:token:{token}", ttl, "1")
        except Exception as e:
            logger.error(f"Failed to blacklist token: {str(e)}")
            return False

    def is_token_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted."""
        try:
            return self.redis.exists(f"blacklist:token:{token}") > 0
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {str(e)}")
            return False

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached session data."""
        try:
            import json
            data = self.redis.get(f"session:{session_id}")
            if data:
                return json.loads(data) if isinstance(data, (str, bytes)) else data
            return None
        except Exception as e:
            logger.error(f"Failed to get session from cache: {str(e)}")
            return None

    async def set_session(self, session_id: str, session_data: Dict[str, Any], ttl: int = 900) -> bool:
        """Cache session data."""
        try:
            import json
            return self.redis.setex(
                f"session:{session_id}",
                ttl,
                json.dumps(session_data)
            )
        except Exception as e:
            logger.error(f"Failed to set session in cache: {str(e)}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        """Delete cached session data."""
        try:
            return self.redis.delete(f"session:{session_id}") > 0
        except Exception as e:
            logger.error(f"Failed to delete session from cache: {str(e)}")
            return False