"""
User management service with distributed caching
"""
from typing import List, Optional
from uuid import UUID
import logging

from src.features.auth.config import AuthConfig
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole
from src.features.auth.domain.events import UserRoleChanged
from src.features.auth.infrastructure.database.repositories import AuthUserRepository
from src.shared.events import get_event_bus
from src.shared.services.cache_service import get_cache_service

logger = logging.getLogger(__name__)


class UserService:
    """User management service with distributed caching"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self._user_repo = AuthUserRepository()
        self._event_bus = get_event_bus()
        self._cache_ttl = 900  # 15 minutes cache TTL
    
    def _get_cache_key(self, key_type: str, identifier: str) -> str:
        """Generate cache key for user data"""
        return f"user:{key_type}:{identifier}"
    
    async def _invalidate_user_cache(self, user: AuthUser) -> None:
        """Invalidate all cache entries for a user"""
        try:
            cache = get_cache_service()
            
            # Delete cache entries for both ID and email
            await cache.delete(self._get_cache_key("id", str(user.id)))
            await cache.delete(self._get_cache_key("email", user.email))
            
        except Exception as e:
            logger.warning(f"Failed to invalidate user cache: {e}")
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[AuthUser]:
        """Get user by ID with caching"""
        cache_key = self._get_cache_key("id", str(user_id))
        
        try:
            cache = get_cache_service()
            
            # Try cache first
            cached_user = await cache.get_pickle(cache_key)
            if cached_user:
                return cached_user
            
            # Cache miss - get from database
            user = await self._user_repo.get_by_id(user_id)
            if user:
                # Cache for future requests
                await cache.set_pickle(cache_key, user, ttl=self._cache_ttl)
            
            return user
            
        except Exception as e:
            logger.warning(f"Cache error in get_user_by_id: {e}")
            # Fallback to database only
            return await self._user_repo.get_by_id(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[AuthUser]:
        """Get user by email with caching"""
        email = email.lower().strip()
        cache_key = self._get_cache_key("email", email)
        
        try:
            cache = get_cache_service()
            
            # Try cache first
            cached_user = await cache.get_pickle(cache_key)
            if cached_user:
                return cached_user
            
            # Cache miss - get from database
            user = await self._user_repo.get_by_email(email)
            if user:
                # Cache for future requests with both email and ID keys
                await cache.set_pickle(cache_key, user, ttl=self._cache_ttl)
                await cache.set_pickle(self._get_cache_key("id", str(user.id)), user, ttl=self._cache_ttl)
            
            return user
            
        except Exception as e:
            logger.warning(f"Cache error in get_user_by_email: {e}")
            # Fallback to database only
            return await self._user_repo.get_by_email(email)
    
    async def list_users(self, limit: int = 100, offset: int = 0) -> List[AuthUser]:
        """List all users"""
        return await self._user_repo.list_all(limit=limit, offset=offset)
    
    async def list_users_by_role(self, role: AuthRole, limit: int = 100, offset: int = 0) -> List[AuthUser]:
        """List users by role"""
        return await self._user_repo.list_by_role(role, limit=limit, offset=offset)
    
    async def update_user_profile(
        self, 
        user: AuthUser, 
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None
    ) -> AuthUser:
        """Update user profile and invalidate cache"""
        try:
            if first_name is not None:
                user.first_name = first_name.strip()
            if last_name is not None:
                user.last_name = last_name.strip()
            if phone is not None:
                user.phone = phone.strip() if phone else None
            
            user.update_timestamp()
            updated_user = await self._user_repo.update(user)
            
            # Invalidate cache
            await self._invalidate_user_cache(user)
            
            logger.info(f"Updated profile for user: {user.email}")
            return updated_user
            
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            raise
    
    async def change_user_role(
        self, 
        user: AuthUser, 
        new_role: AuthRole, 
        changed_by: Optional[UUID] = None
    ) -> AuthUser:
        """Change user role"""
        try:
            old_role = user.role
            
            if old_role == new_role:
                return user  # No change needed
            
            user.change_role(new_role)
            updated_user = await self._user_repo.update(user)
            
            # Publish event
            await self._event_bus.publish(UserRoleChanged(
                user_id=user.id,
                email=user.email,
                old_role=old_role.value,
                new_role=new_role.value,
                changed_by=changed_by
            ))
            
            logger.info(f"Changed role for {user.email}: {old_role.value} -> {new_role.value}")
            return updated_user
            
        except Exception as e:
            logger.error(f"Failed to change user role: {e}")
            raise
    
    async def activate_user(self, user: AuthUser) -> AuthUser:
        """Activate user account"""
        try:
            user.is_active = True
            user.update_timestamp()
            updated_user = await self._user_repo.update(user)
            
            logger.info(f"Activated user: {user.email}")
            return updated_user
            
        except Exception as e:
            logger.error(f"Failed to activate user: {e}")
            raise
    
    async def deactivate_user(self, user: AuthUser) -> AuthUser:
        """Deactivate user account"""
        try:
            user.is_active = False
            user.clear_all_refresh_tokens()  # Logout from all devices
            user.update_timestamp()
            updated_user = await self._user_repo.update(user)
            
            logger.info(f"Deactivated user: {user.email}")
            return updated_user
            
        except Exception as e:
            logger.error(f"Failed to deactivate user: {e}")
            raise
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user account"""
        try:
            user = await self._user_repo.get_by_id(user_id)
            if not user:
                return False
            
            success = await self._user_repo.delete(user_id)
            
            if success:
                logger.info(f"Deleted user: {user.email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            return False
    
    async def get_user_stats(self) -> dict:
        """Get user statistics"""
        try:
            stats = {}
            
            for role in AuthRole:
                count = await self._user_repo.count_by_role(role)
                stats[role.value] = count
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            return {}
    
    def can_manage_user(self, manager: AuthUser, target: AuthUser) -> bool:
        """Check if manager can manage target user"""
        # Admin can manage everyone
        if manager.role == AuthRole.ADMIN:
            return True
        
        # Manager can manage washers and clients, but not other managers or admins
        if manager.role == AuthRole.MANAGER:
            return target.role in [AuthRole.WASHER, AuthRole.CLIENT]
        
        # Others can only manage themselves
        return manager.id == target.id
    
    def can_assign_role(self, assigner: AuthUser, target_role: AuthRole) -> bool:
        """Check if user can assign a specific role"""
        # Admin can assign any role
        if assigner.role == AuthRole.ADMIN:
            return True
        
        # Manager can assign washer and client roles
        if assigner.role == AuthRole.MANAGER:
            return target_role in [AuthRole.WASHER, AuthRole.CLIENT]
        
        # Others cannot assign roles
        return False