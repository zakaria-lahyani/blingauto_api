"""
JWT refresh token rotation service
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import hashlib
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.auth.config import AuthConfig, AuthFeature
from src.features.auth.domain.entities import AuthUser
from src.features.auth.infrastructure.database.repositories import AuthUserRepository
from src.features.auth.infrastructure.security import JWTHandler

logger = logging.getLogger(__name__)


class TokenRotationService:
    """Secure JWT token management with refresh token rotation
    
    Uses dependency injection for database sessions to avoid session conflicts.
    All methods that need database access require a session parameter.
    """
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self._jwt_handler = JWTHandler(config)
        self.max_tokens_per_user = 5  # Allow multiple devices
    
    async def store_refresh_token(
        self, 
        session: AsyncSession, 
        user: AuthUser, 
        refresh_token: str
    ) -> None:
        """Store refresh token metadata in user
        
        Args:
            session: Database session to use (injected from parent)
            user: User entity to update
            refresh_token: JWT refresh token to store metadata for
        """
        if not self.config.is_feature_enabled(AuthFeature.TOKEN_ROTATION):
            return
        
        try:
            # Extract family ID from token
            payload = self._jwt_handler.verify_token(refresh_token)
            if not payload:
                logger.warning("Failed to verify refresh token for storage")
                return
            
            family_id = payload.get("family_id")
            exp_timestamp = payload.get("exp", 0)
            if isinstance(exp_timestamp, (int, float)):
                expires_at = datetime.fromtimestamp(exp_timestamp)
            else:
                expires_at = datetime.utcnow() + timedelta(days=self.config.refresh_token_expire_days)
            
            # Hash token for storage
            token_hash = self._hash_token(refresh_token)
            
            # Clean up expired tokens first
            current_time = datetime.utcnow()
            user.refresh_tokens = [
                token for token in user.refresh_tokens
                if self._is_token_valid(token, current_time)
            ]
            
            # Check token limit per user
            if len(user.refresh_tokens) >= self.max_tokens_per_user:
                # Remove oldest token (simple FIFO)
                user.refresh_tokens.pop(0)
            
            # Store new token metadata
            token_info = {
                'token_hash': token_hash,
                'family_id': family_id,
                'expires_at': expires_at.isoformat(),
                'created_at': datetime.utcnow().isoformat(),
                'last_used': datetime.utcnow().isoformat()
            }
            
            # Add token directly to list (no encryption for simplicity)
            user.refresh_tokens.append(token_info)
            user.update_timestamp()
            
            # Update user using the provided session
            user_repo = AuthUserRepository(session)
            await user_repo.update(user)
            
            logger.debug(f"Stored refresh token for user {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to store refresh token: {e}")
            # Don't re-raise to avoid breaking authentication flow
    
    async def rotate_refresh_token(
        self, 
        session: AsyncSession, 
        refresh_token: str
    ) -> Optional[Tuple[str, str]]:
        """Rotate refresh token - invalidate old, issue new pair
        
        Args:
            session: Database session to use
            refresh_token: Current refresh token to rotate
            
        Returns:
            Tuple of (new_access_token, new_refresh_token) or None if rotation failed
        """
        if not self.config.is_feature_enabled(AuthFeature.TOKEN_ROTATION):
            return None
        
        try:
            # Verify refresh token
            payload = self._jwt_handler.verify_token(refresh_token)
            if not payload or payload.get("type") != "refresh":
                logger.warning("Invalid refresh token presented")
                return None
            
            user_id = payload.get("sub")
            family_id = payload.get("family_id")
            
            if not user_id or not family_id:
                logger.warning("Refresh token missing required claims")
                return None
            
            # Get user using provided session
            from uuid import UUID
            user_repo = AuthUserRepository(session)
            user = await user_repo.get_by_id(UUID(user_id))
            
            if not user or not user.is_active:
                logger.warning(f"Refresh token for inactive user: {user_id}")
                return None
            
            # Check if token exists and is valid
            token_hash = self._hash_token(refresh_token)
            if not self._validate_refresh_token(user, token_hash, family_id):
                # Potential token reuse attack - invalidate all tokens in family
                await self._invalidate_token_family(session, user, family_id)
                logger.warning(f"Possible token reuse attack for user: {user.email}")
                return None
            
            # Invalidate old token
            self._remove_refresh_token(user, token_hash)
            
            # Generate new token pair with same family ID
            new_access_token = self._jwt_handler.create_access_token(
                user_id=str(user.id),
                email=user.email,
                role=user.role.value
            )
            
            new_refresh_token = self._jwt_handler.create_refresh_token(
                user_id=str(user.id),
                family_id=family_id  # Keep same family ID
            )
            
            # Store new refresh token using same session
            await self.store_refresh_token(session, user, new_refresh_token)
            
            logger.info(f"Rotated refresh token for user: {user.email}")
            return new_access_token, new_refresh_token
            
        except Exception as e:
            logger.error(f"Failed to rotate refresh token: {e}")
            return None
    
    async def revoke_refresh_token(
        self, 
        session: AsyncSession, 
        user: AuthUser, 
        refresh_token: str
    ) -> bool:
        """Revoke a specific refresh token
        
        Args:
            session: Database session to use
            user: User entity to update
            refresh_token: Refresh token to revoke
            
        Returns:
            True if revocation succeeded, False otherwise
        """
        if not self.config.is_feature_enabled(AuthFeature.TOKEN_ROTATION):
            return True
        
        try:
            token_hash = self._hash_token(refresh_token)
            self._remove_refresh_token(user, token_hash)
            
            user_repo = AuthUserRepository(session)
            await user_repo.update(user)
            
            logger.info(f"Revoked refresh token for user: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke refresh token: {e}")
            return False
    
    async def revoke_all_user_tokens(
        self, 
        session: AsyncSession, 
        user: AuthUser
    ) -> bool:
        """Revoke all refresh tokens for a user (logout from all devices)
        
        Args:
            session: Database session to use
            user: User entity to update
            
        Returns:
            True if revocation succeeded, False otherwise
        """
        try:
            user.clear_all_refresh_tokens()
            
            user_repo = AuthUserRepository(session)
            await user_repo.update(user)
            
            logger.info(f"Revoked all refresh tokens for user: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke all tokens: {e}")
            return False
    
    def _validate_refresh_token(self, user: AuthUser, token_hash: str, family_id: str) -> bool:
        """Validate refresh token exists and hasn't been used"""
        for token_info in user.refresh_tokens:
            if (token_info.get('token_hash') == token_hash and 
                token_info.get('family_id') == family_id):
                
                # Check if token is not expired (handle both datetime and ISO string formats)
                expires_at = token_info.get('expires_at')
                if expires_at:
                    # Convert ISO string to datetime if needed
                    if isinstance(expires_at, str):
                        try:
                            expires_at = datetime.fromisoformat(expires_at)
                        except:
                            return False
                    
                    if isinstance(expires_at, datetime) and expires_at > datetime.utcnow():
                        # Update last used (store as ISO string)
                        token_info['last_used'] = datetime.utcnow().isoformat()
                        return True
        
        return False
    
    def _remove_refresh_token(self, user: AuthUser, token_hash: str):
        """Remove specific refresh token"""
        user.refresh_tokens = [
            token for token in user.refresh_tokens
            if token.get('token_hash') != token_hash
        ]
    
    async def _invalidate_token_family(
        self, 
        session: AsyncSession, 
        user: AuthUser, 
        family_id: str
    ) -> None:
        """Invalidate all tokens in a family (potential security breach)
        
        Args:
            session: Database session to use
            user: User entity to update
            family_id: Token family ID to invalidate
        """
        user.refresh_tokens = [
            token for token in user.refresh_tokens
            if token.get('family_id') != family_id
        ]
        
        user_repo = AuthUserRepository(session)
        await user_repo.update(user)
        
        logger.warning(f"Invalidated token family {family_id} for user: {user.email}")
    
    def _cleanup_expired_tokens(self, user: AuthUser):
        """Remove expired tokens from user"""
        now = datetime.utcnow()
        valid_tokens = []
        
        for token in user.refresh_tokens:
            expires_at = token.get('expires_at')
            if expires_at:
                # Convert ISO string to datetime if needed
                if isinstance(expires_at, str):
                    try:
                        expires_at = datetime.fromisoformat(expires_at)
                    except:
                        continue  # Skip invalid tokens
                
                if isinstance(expires_at, datetime) and expires_at > now:
                    valid_tokens.append(token)
            
        user.refresh_tokens = valid_tokens
    
    def _is_token_valid(self, token_info: dict, current_time: datetime) -> bool:
        """Check if a token is still valid (not expired)"""
        expires_at = token_info.get('expires_at')
        if not expires_at:
            return False
        
        if isinstance(expires_at, str):
            try:
                expires_at = datetime.fromisoformat(expires_at)
            except:
                return False
        
        return isinstance(expires_at, datetime) and expires_at > current_time
    
    @staticmethod
    def _hash_token(token: str) -> str:
        """Create secure hash of token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()