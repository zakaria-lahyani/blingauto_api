"""
Unit tests for UserService
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from uuid import uuid4

from src.features.auth.application.services.user_service import UserService
from src.features.auth.config import AuthConfig
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole


@pytest.fixture
def user_service(auth_config):
    """User service instance for testing"""
    return UserService(auth_config)


@pytest.fixture
def mock_user_repo():
    """Mock user repository"""
    return AsyncMock()


@pytest.fixture
def test_users():
    """Test user entities"""
    return [
        AuthUser(
            id=uuid4(),
            email="user1@example.com",
            hashed_password="hashed_password_1",
            first_name="User",
            last_name="One",
            role=AuthRole.CLIENT,
            email_verified=True,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        AuthUser(
            id=uuid4(),
            email="admin@example.com",
            hashed_password="hashed_password_2",
            first_name="Admin",
            last_name="User",
            role=AuthRole.ADMIN,
            email_verified=True,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        AuthUser(
            id=uuid4(),
            email="manager@example.com",
            hashed_password="hashed_password_3",
            first_name="Manager",
            last_name="User",
            role=AuthRole.MANAGER,
            email_verified=True,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]


class TestUserService:
    """Test cases for UserService"""
    
    @pytest.mark.asyncio
    async def test_get_all_users(self, user_service, mock_user_repo, test_users):
        """Test getting all users"""
        # Arrange
        mock_user_repo.get_all_users.return_value = test_users
        
        with patch.object(user_service, 'user_repository', mock_user_repo):
            
            # Act
            result = await user_service.get_all_users()
            
            # Assert
            assert len(result) == 3
            assert result[0].email == "user1@example.com"
            assert result[1].email == "admin@example.com"
            assert result[2].email == "manager@example.com"
            
            mock_user_repo.get_all_users.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_all_users_with_pagination(
        self, 
        user_service, 
        mock_user_repo, 
        test_users
    ):
        """Test getting all users with pagination"""
        # Arrange
        offset = 0
        limit = 2
        paginated_users = test_users[:2]
        
        mock_user_repo.get_all_users.return_value = paginated_users
        
        with patch.object(user_service, 'user_repository', mock_user_repo):
            
            # Act
            result = await user_service.get_all_users(offset=offset, limit=limit)
            
            # Assert
            assert len(result) == 2
            assert result[0].email == "user1@example.com"
            assert result[1].email == "admin@example.com"
            
            mock_user_repo.get_all_users.assert_called_once_with(offset=offset, limit=limit)
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_found(
        self, 
        user_service, 
        mock_user_repo, 
        test_users
    ):
        """Test getting user by ID when user exists"""
        # Arrange
        target_user = test_users[0]
        user_id = target_user.id
        
        mock_user_repo.get_user_by_id.return_value = target_user
        
        with patch.object(user_service, 'user_repository', mock_user_repo):
            
            # Act
            result = await user_service.get_user_by_id(user_id)
            
            # Assert
            assert result.id == user_id
            assert result.email == target_user.email
            
            mock_user_repo.get_user_by_id.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(
        self, 
        user_service, 
        mock_user_repo
    ):
        """Test getting user by ID when user doesn't exist"""
        # Arrange
        user_id = uuid4()
        mock_user_repo.get_user_by_id.return_value = None
        
        with patch.object(user_service, 'user_repository', mock_user_repo):
            
            # Act & Assert
            with pytest.raises(ValueError, match="User not found"):
                await user_service.get_user_by_id(user_id)
    
    @pytest.mark.asyncio
    async def test_update_user_profile_success(
        self, 
        user_service, 
        mock_user_repo, 
        test_users
    ):
        """Test successful user profile update"""
        # Arrange
        user = test_users[0]
        updated_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        
        updated_user = AuthUser(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            first_name=updated_data["first_name"],
            last_name=updated_data["last_name"],
            role=user.role,
            email_verified=user.email_verified,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=datetime.utcnow()
        )
        
        mock_user_repo.get_user_by_id.return_value = user
        mock_user_repo.update_user.return_value = updated_user
        
        with patch.object(user_service, 'user_repository', mock_user_repo):
            
            # Act
            result = await user_service.update_user_profile(user.id, updated_data)
            
            # Assert
            assert result.first_name == "Updated"
            assert result.last_name == "Name"
            assert result.email == user.email  # Should remain unchanged
            
            mock_user_repo.get_user_by_id.assert_called_once_with(user.id)
            mock_user_repo.update_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_profile_user_not_found(
        self, 
        user_service, 
        mock_user_repo
    ):
        """Test profile update when user doesn't exist"""
        # Arrange
        user_id = uuid4()
        updated_data = {"first_name": "Updated"}
        
        mock_user_repo.get_user_by_id.return_value = None
        
        with patch.object(user_service, 'user_repository', mock_user_repo):
            
            # Act & Assert
            with pytest.raises(ValueError, match="User not found"):
                await user_service.update_user_profile(user_id, updated_data)
    
    @pytest.mark.asyncio
    async def test_change_user_role_success(
        self, 
        user_service, 
        mock_user_repo, 
        test_users
    ):
        """Test successful user role change"""
        # Arrange
        user = test_users[0]  # CLIENT role
        new_role = AuthRole.MANAGER
        
        updated_user = AuthUser(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            first_name=user.first_name,
            last_name=user.last_name,
            role=new_role,
            email_verified=user.email_verified,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=datetime.utcnow()
        )
        
        mock_user_repo.get_user_by_id.return_value = user
        mock_user_repo.update_user.return_value = updated_user
        
        with patch.object(user_service, 'user_repository', mock_user_repo), \
             patch('src.shared.events.get_event_bus') as mock_event_bus:
            
            # Act
            result = await user_service.change_user_role(user.id, new_role)
            
            # Assert
            assert result.role == new_role
            
            mock_user_repo.get_user_by_id.assert_called_once_with(user.id)
            mock_user_repo.update_user.assert_called_once()
            mock_event_bus.return_value.publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_user_role_same_role(
        self, 
        user_service, 
        mock_user_repo, 
        test_users
    ):
        """Test role change to same role"""
        # Arrange
        user = test_users[0]  # CLIENT role
        same_role = AuthRole.CLIENT
        
        mock_user_repo.get_user_by_id.return_value = user
        
        with patch.object(user_service, 'user_repository', mock_user_repo):
            
            # Act & Assert
            with pytest.raises(ValueError, match="User already has this role"):
                await user_service.change_user_role(user.id, same_role)
    
    @pytest.mark.asyncio
    async def test_change_user_role_user_not_found(
        self, 
        user_service, 
        mock_user_repo
    ):
        """Test role change when user doesn't exist"""
        # Arrange
        user_id = uuid4()
        new_role = AuthRole.MANAGER
        
        mock_user_repo.get_user_by_id.return_value = None
        
        with patch.object(user_service, 'user_repository', mock_user_repo):
            
            # Act & Assert
            with pytest.raises(ValueError, match="User not found"):
                await user_service.change_user_role(user_id, new_role)
    
    @pytest.mark.asyncio
    async def test_deactivate_user_success(
        self, 
        user_service, 
        mock_user_repo, 
        test_users
    ):
        """Test successful user deactivation"""
        # Arrange
        user = test_users[0]
        
        deactivated_user = AuthUser(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            email_verified=user.email_verified,
            is_active=False,
            created_at=user.created_at,
            updated_at=datetime.utcnow()
        )
        
        mock_user_repo.get_user_by_id.return_value = user
        mock_user_repo.update_user.return_value = deactivated_user
        
        with patch.object(user_service, 'user_repository', mock_user_repo):
            
            # Act
            result = await user_service.deactivate_user(user.id)
            
            # Assert
            assert result.is_active is False
            
            mock_user_repo.get_user_by_id.assert_called_once_with(user.id)
            mock_user_repo.update_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deactivate_user_already_inactive(
        self, 
        user_service, 
        mock_user_repo, 
        test_users
    ):
        """Test deactivating already inactive user"""
        # Arrange
        user = test_users[0]
        user.is_active = False
        
        mock_user_repo.get_user_by_id.return_value = user
        
        with patch.object(user_service, 'user_repository', mock_user_repo):
            
            # Act & Assert
            with pytest.raises(ValueError, match="User is already inactive"):
                await user_service.deactivate_user(user.id)
    
    @pytest.mark.asyncio
    async def test_delete_user_success(
        self, 
        user_service, 
        mock_user_repo, 
        test_users
    ):
        """Test successful user deletion"""
        # Arrange
        user = test_users[0]
        
        mock_user_repo.get_user_by_id.return_value = user
        mock_user_repo.delete_user.return_value = True
        
        with patch.object(user_service, 'user_repository', mock_user_repo):
            
            # Act
            result = await user_service.delete_user(user.id)
            
            # Assert
            assert result is True
            
            mock_user_repo.get_user_by_id.assert_called_once_with(user.id)
            mock_user_repo.delete_user.assert_called_once_with(user.id)
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(
        self, 
        user_service, 
        mock_user_repo
    ):
        """Test deleting non-existent user"""
        # Arrange
        user_id = uuid4()
        
        mock_user_repo.get_user_by_id.return_value = None
        
        with patch.object(user_service, 'user_repository', mock_user_repo):
            
            # Act & Assert
            with pytest.raises(ValueError, match="User not found"):
                await user_service.delete_user(user_id)