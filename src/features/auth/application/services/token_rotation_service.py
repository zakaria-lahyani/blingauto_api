"""
JWT refresh token rotation service
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import hashlib
import logging

from src.features.auth.config import AuthConfig, AuthFeature
from src.features.auth.domain.entities import AuthUser
from src.features.auth.infrastructure.database.repositories import AuthUserRepository
from src.features.auth.infrastructure.security import JWTHandler

logger = logging.getLogger(__name__)


class TokenRotationService:
    """Secure JWT token management with refresh token rotation"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self._user_repo = AuthUserRepository()
        self._jwt_handler = JWTHandler(config)
        self.max_tokens_per_user = 5  # Allow multiple devices
    
    async def store_refresh_token(self, user: AuthUser, refresh_token: str):
        """Store refresh token metadata in user"""
        if not self.config.is_feature_enabled(AuthFeature.TOKEN_ROTATION):
            return
        
        try:
            # Extract family ID from token
            payload = self._jwt_handler.decode_token(refresh_token)
            if not payload:
                return
            
            family_id = payload.get("family_id")
            expires_at = datetime.fromtimestamp(payload.get("exp", 0))
            
            # Hash token for storage
            token_hash = self._hash_token(refresh_token)
            
            # Clean up expired tokens
            self._cleanup_expired_tokens(user)
            
            # Check token limit per user
            if len(user.refresh_tokens) >= self.max_tokens_per_user:
                # Remove oldest token (handle both datetime and ISO string formats)
                def get_created_at(token):
                    created_at = token.get('created_at', datetime.min.isoformat())
                    if isinstance(created_at, str):
                        try:
                            return datetime.fromisoformat(created_at)
                        except:
                            return datetime.min
                    return created_at if isinstance(created_at, datetime) else datetime.min
                
                user.refresh_tokens.sort(key=get_created_at)
                user.refresh_tokens.pop(0)
            
            # Store new token metadata (convert datetime to ISO string for JSON serialization)
            token_info = {
                'token_hash': token_hash,
                'family_id': family_id,
                'expires_at': expires_at.isoformat(),
                'created_at': datetime.utcnow().isoformat(),
                'last_used': datetime.utcnow().isoformat()
            }
            
            user.add_refresh_token(token_info)
            await self._user_repo.update(user)
            
        except Exception as e:
            logger.error(f"Failed to store refresh token: {e}")
    
    async def rotate_refresh_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Rotate refresh token - invalidate old, issue new pair"""
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
            
            # Get user
            from uuid import UUID
            user = await self._user_repo.get_by_id(UUID(user_id))
            if not user or not user.is_active:
                logger.warning(f"Refresh token for inactive user: {user_id}")
                return None
            
            # Check if token exists and is valid
            token_hash = self._hash_token(refresh_token)
            if not self._validate_refresh_token(user, token_hash, family_id):
                # Potential token reuse attack - invalidate all tokens in family
                await self._invalidate_token_family(user, family_id)
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
            
            # Store new refresh token
            await self.store_refresh_token(user, new_refresh_token)
            
            logger.info(f"Rotated refresh token for user: {user.email}")
            return new_access_token, new_refresh_token
            
        except Exception as e:
            logger.error(f"Failed to rotate refresh token: {e}")
            return None
    
    async def revoke_refresh_token(self, user: AuthUser, refresh_token: str) -> bool:
        """Revoke a specific refresh token"""
        if not self.config.is_feature_enabled(AuthFeature.TOKEN_ROTATION):
            return True
        
        try:
            token_hash = self._hash_token(refresh_token)
            self._remove_refresh_token(user, token_hash)
            await self._user_repo.update(user)
            
            logger.info(f"Revoked refresh token for user: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke refresh token: {e}")
            return False
    
    async def revoke_all_user_tokens(self, user: AuthUser) -> bool:
        """Revoke all refresh tokens for a user (logout from all devices)"""
        try:
            user.clear_all_refresh_tokens()
            await self._user_repo.update(user)
            
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
    
    async def _invalidate_token_family(self, user: AuthUser, family_id: str):
        """Invalidate all tokens in a family (potential security breach)"""
        user.refresh_tokens = [
            token for token in user.refresh_tokens
            if token.get('family_id') != family_id
        ]
        await self._user_repo.update(user)
        
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
    
    @staticmethod
    def _hash_token(token: str) -> str:
        """Create secure hash of token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()