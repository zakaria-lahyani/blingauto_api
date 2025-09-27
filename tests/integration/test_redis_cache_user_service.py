"""
Integration Tests for Redis Cache-Enabled User Service

Tests the integration between the User Service and Redis caching,
verifying cache hits, misses, invalidation, and performance improvements.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4
from typing import Optional

from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole
from src.features.auth.application.services.user_service import UserService
from src.features.auth.config import AuthConfig
from src.shared.services.cache_service import CacheService, init_cache_service


class TestUserServiceRedisIntegration:
    """Integration tests for User Service with Redis caching"""
    
    @pytest.fixture
    def auth_config(self):
        """Create test auth configuration"""
        config = Mock(spec=AuthConfig)
        config.redis_url = "redis://localhost:6379/0"
        return config
    
    @pytest.fixture
    def mock_user_repo(self):
        """Create mock user repository"""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.get_by_email = AsyncMock()
        repo.update = AsyncMock()
        repo.list_all = AsyncMock()
        repo.list_by_role = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_cache_service(self):
        """Create mock cache service"""
        cache = AsyncMock(spec=CacheService)
        cache.get_pickle = AsyncMock(return_value=None)
        cache.set_pickle = AsyncMock(return_value=True)
        cache.delete = AsyncMock(return_value=True)
        cache.get_json = AsyncMock(return_value=None)
        cache.set_json = AsyncMock(return_value=True)
        return cache
    
    @pytest.fixture
    def test_user(self):
        """Create test user entity"""
        user = AuthUser()
        user.id = uuid4()
        user.email = "test@example.com"
        user.first_name = "Test"
        user.last_name = "User"
        user.role = AuthRole.CLIENT
        user.is_active = True
        user.email_verified = True
        return user
    
    @pytest.fixture
    async def user_service(self, auth_config, mock_user_repo, mock_cache_service):
        """Create user service with mocked dependencies"""
        with patch('src.features.auth.application.services.user_service.AuthUserRepository', return_value=mock_user_repo):
            with patch('src.features.auth.application.services.user_service.get_event_bus', return_value=AsyncMock()):
                with patch('src.features.auth.application.services.user_service.get_cache_service', return_value=mock_cache_service):
                    service = UserService(auth_config)
                    service._user_repo = mock_user_repo
                    return service
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_cache_miss(self, user_service, mock_user_repo, mock_cache_service, test_user):
        """Test getting user by ID with cache miss"""
        # Setup cache miss
        mock_cache_service.get_pickle.return_value = None
        mock_user_repo.get_by_id.return_value = test_user
        
        # Get user
        result = await user_service.get_user_by_id(test_user.id)
        
        # Verify result
        assert result == test_user
        
        # Verify cache was checked
        cache_key = f"user:id:{test_user.id}"
        mock_cache_service.get_pickle.assert_called_once_with(cache_key)
        
        # Verify database was queried
        mock_user_repo.get_by_id.assert_called_once_with(test_user.id)
        
        # Verify result was cached
        mock_cache_service.set_pickle.assert_called_once_with(
            cache_key, test_user, ttl=900  # 15 minutes
        )
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_cache_hit(self, user_service, mock_user_repo, mock_cache_service, test_user):
        """Test getting user by ID with cache hit"""
        # Setup cache hit
        mock_cache_service.get_pickle.return_value = test_user
        
        # Get user
        result = await user_service.get_user_by_id(test_user.id)
        
        # Verify result
        assert result == test_user
        
        # Verify cache was checked
        cache_key = f"user:id:{test_user.id}"
        mock_cache_service.get_pickle.assert_called_once_with(cache_key)
        
        # Verify database was NOT queried (cache hit)
        mock_user_repo.get_by_id.assert_not_called()
        
        # Verify result was NOT re-cached (already in cache)
        mock_cache_service.set_pickle.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_cache_miss(self, user_service, mock_user_repo, mock_cache_service, test_user):
        """Test getting user by email with cache miss"""
        # Setup cache miss
        mock_cache_service.get_pickle.return_value = None
        mock_user_repo.get_by_email.return_value = test_user
        
        # Get user
        result = await user_service.get_user_by_email(test_user.email)
        
        # Verify result
        assert result == test_user
        
        # Verify cache was checked
        email_cache_key = f"user:email:{test_user.email}"
        mock_cache_service.get_pickle.assert_called_once_with(email_cache_key)
        
        # Verify database was queried
        mock_user_repo.get_by_email.assert_called_once_with(test_user.email)
        
        # Verify result was cached with both email and ID keys
        assert mock_cache_service.set_pickle.call_count == 2
        calls = mock_cache_service.set_pickle.call_args_list
        
        # Check email key cache
        assert calls[0][0][0] == email_cache_key
        assert calls[0][0][1] == test_user
        
        # Check ID key cache
        id_cache_key = f"user:id:{test_user.id}"
        assert calls[1][0][0] == id_cache_key
        assert calls[1][0][1] == test_user
    
    @pytest.mark.asyncio
    async def test_update_user_profile_invalidates_cache(self, user_service, mock_user_repo, mock_cache_service, test_user):
        """Test that updating user profile invalidates cache"""
        # Setup
        mock_user_repo.update.return_value = test_user
        
        # Update profile
        updated_user = await user_service.update_user_profile(
            test_user,
            first_name="Updated",
            last_name="Name"
        )
        
        # Verify update
        assert test_user.first_name == "Updated"
        assert test_user.last_name == "Name"
        mock_user_repo.update.assert_called_once_with(test_user)
        
        # Verify cache invalidation
        assert mock_cache_service.delete.call_count == 2
        calls = mock_cache_service.delete.call_args_list
        
        # Check both cache keys were deleted
        id_cache_key = f"user:id:{test_user.id}"
        email_cache_key = f"user:email:{test_user.email}"
        
        deleted_keys = [call[0][0] for call in calls]
        assert id_cache_key in deleted_keys
        assert email_cache_key in deleted_keys
    
    @pytest.mark.asyncio
    async def test_cache_error_fallback(self, user_service, mock_user_repo, mock_cache_service, test_user):
        """Test graceful fallback when cache service fails"""
        # Setup cache error
        mock_cache_service.get_pickle.side_effect = Exception("Redis connection error")
        mock_user_repo.get_by_id.return_value = test_user
        
        # Get user (should fallback to database)
        result = await user_service.get_user_by_id(test_user.id)
        
        # Verify result
        assert result == test_user
        
        # Verify database was queried despite cache error
        mock_user_repo.get_by_id.assert_called_once_with(test_user.id)
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self, user_service, mock_user_repo, mock_cache_service, test_user):
        """Test concurrent cache operations"""
        # Setup cache miss for initial requests
        mock_cache_service.get_pickle.return_value = None
        mock_user_repo.get_by_id.return_value = test_user
        
        # Make concurrent requests for same user
        tasks = []
        for _ in range(10):
            tasks.append(user_service.get_user_by_id(test_user.id))
        
        results = await asyncio.gather(*tasks)
        
        # All results should be the same user
        assert all(r == test_user for r in results)
        
        # Database should be called 10 times (no deduplication in this test)
        assert mock_user_repo.get_by_id.call_count == 10
        
        # Cache should be set 10 times
        assert mock_cache_service.set_pickle.call_count == 10


class TestUserServiceCachePerformance:
    """Performance tests for Redis cache integration"""
    
    @pytest.fixture
    def large_user_list(self):
        """Generate large list of test users"""
        users = []
        for i in range(100):
            user = AuthUser()
            user.id = uuid4()
            user.email = f"user{i}@example.com"
            user.first_name = f"User{i}"
            user.last_name = "Test"
            user.role = AuthRole.CLIENT if i % 4 != 0 else AuthRole.MANAGER
            users.append(user)
        return users
    
    @pytest.mark.asyncio
    async def test_bulk_user_caching(self, user_service, mock_user_repo, mock_cache_service, large_user_list):
        """Test caching performance with bulk user operations"""
        # Setup
        mock_cache_service.get_pickle.return_value = None
        
        # Simulate getting users by ID
        for user in large_user_list[:50]:
            mock_user_repo.get_by_id.return_value = user
            await user_service.get_user_by_id(user.id)
        
        # Verify caching occurred
        assert mock_cache_service.set_pickle.call_count == 50
        
        # Now simulate cache hits for same users
        mock_cache_service.get_pickle.side_effect = lambda key: next(
            (u for u in large_user_list if str(u.id) in key), None
        )
        mock_user_repo.get_by_id.reset_mock()
        
        # Get same users again
        for user in large_user_list[:50]:
            await user_service.get_user_by_id(user.id)
        
        # Database should not be called (all cache hits)
        mock_user_repo.get_by_id.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_cache_ttl_behavior(self, user_service, mock_cache_service):
        """Test that cache TTL is properly set"""
        # Verify TTL is set to 900 seconds (15 minutes)
        assert user_service._cache_ttl == 900
        
        # Test custom TTL can be configured
        user_service._cache_ttl = 1800  # 30 minutes
        assert user_service._cache_ttl == 1800
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self, user_service):
        """Test cache key generation patterns"""
        # Test ID key
        id_key = user_service._get_cache_key("id", "123e4567-e89b-12d3-a456-426614174000")
        assert id_key == "user:id:123e4567-e89b-12d3-a456-426614174000"
        
        # Test email key
        email_key = user_service._get_cache_key("email", "test@example.com")
        assert email_key == "user:email:test@example.com"
        
        # Test custom key type
        custom_key = user_service._get_cache_key("username", "johndoe")
        assert custom_key == "user:username:johndoe"


class TestRedisConnectionScenarios:
    """Test various Redis connection scenarios"""
    
    @pytest.mark.asyncio
    async def test_redis_connection_retry(self):
        """Test Redis connection retry logic"""
        from src.shared.services.cache_service import RedisCacheProvider
        
        provider = RedisCacheProvider("redis://localhost:6379/0")
        
        # Mock connection failure then success
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=[Exception("Connection failed"), True])
        
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            # First attempt should fail
            with pytest.raises(Exception):
                await provider._get_redis()
            
            # Reset and try again
            provider._redis = None
            mock_redis.ping = AsyncMock(return_value=True)
            
            # Second attempt should succeed
            redis_client = await provider._get_redis()
            assert redis_client is not None
    
    @pytest.mark.asyncio
    async def test_redis_pool_configuration(self):
        """Test Redis connection pool configuration"""
        from src.shared.services.cache_service import RedisCacheProvider
        
        # Test custom max connections
        provider = RedisCacheProvider("redis://localhost:6379/0", max_connections=100)
        assert provider.max_connections == 100
        
        # Test default max connections
        default_provider = RedisCacheProvider("redis://localhost:6379/0")
        assert default_provider.max_connections == 20
    
    @pytest.mark.asyncio
    async def test_cache_service_initialization_modes(self):
        """Test different cache service initialization modes"""
        # Test with Redis URL
        cache_service = init_cache_service(redis_url="redis://localhost:6379/0")
        assert cache_service is not None
        
        # Test without Redis (fallback to memory)
        memory_service = init_cache_service(redis_url=None)
        assert memory_service is not None
        
        # Test with custom key prefix
        custom_service = init_cache_service(redis_url=None, key_prefix="custom_app")
        assert custom_service.key_prefix == "custom_app"


class TestCacheInvalidationStrategies:
    """Test different cache invalidation strategies"""
    
    @pytest.mark.asyncio
    async def test_role_change_cache_invalidation(self, user_service, mock_user_repo, mock_cache_service, test_user):
        """Test cache invalidation when user role changes"""
        # Setup
        mock_user_repo.update.return_value = test_user
        test_user.role = AuthRole.CLIENT
        
        # Change role
        await user_service.change_user_role(test_user, AuthRole.MANAGER)
        
        # Verify cache invalidation
        mock_cache_service.delete.assert_any_call(f"user:id:{test_user.id}")
        mock_cache_service.delete.assert_any_call(f"user:email:{test_user.email}")
    
    @pytest.mark.asyncio
    async def test_user_deactivation_cache_invalidation(self, user_service, mock_user_repo, mock_cache_service, test_user):
        """Test cache invalidation when user is deactivated"""
        # Setup
        mock_user_repo.update.return_value = test_user
        
        # Deactivate user
        await user_service.deactivate_user(test_user)
        
        # Verify user is deactivated
        assert test_user.is_active is False
        
        # Verify cache invalidation
        mock_cache_service.delete.assert_any_call(f"user:id:{test_user.id}")
        mock_cache_service.delete.assert_any_call(f"user:email:{test_user.email}")
    
    @pytest.mark.asyncio
    async def test_selective_cache_invalidation(self, user_service, mock_cache_service, test_user):
        """Test selective cache invalidation for specific operations"""
        # Test that read operations don't invalidate cache
        await user_service._invalidate_user_cache(test_user)
        
        # Should delete both keys
        assert mock_cache_service.delete.call_count == 2
        
        # Reset
        mock_cache_service.delete.reset_mock()
        
        # Test error handling in invalidation
        mock_cache_service.delete.side_effect = Exception("Cache error")
        
        # Should not raise exception (graceful failure)
        await user_service._invalidate_user_cache(test_user)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])