"""
Unit tests for AuthService
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from src.features.auth.application.services.auth_service import AuthService
from src.features.auth.config import AuthConfig
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole
from src.features.auth.infrastructure.security import hash_password


@pytest.fixture
def auth_service(auth_config):
    """Auth service instance for testing"""
    return AuthService(auth_config)


@pytest.fixture
def mock_user_repo():
    """Mock user repository"""
    return AsyncMock()


@pytest.fixture
def mock_jwt_handler():
    """Mock JWT handler"""
    return MagicMock()


@pytest.fixture
def mock_event_bus():
    """Mock event bus"""
    return AsyncMock()


@pytest.fixture
def test_user():
    """Test user entity"""
    return AuthUser(
        id=uuid4(),
        email="test@example.com",
        hashed_password=hash_password("TestPassword123!"),
        first_name="Test",
        last_name="User",
        role=AuthRole.CLIENT,
        email_verified=True,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


class TestAuthService:
    """Test cases for AuthService"""
    
    @pytest.mark.asyncio
    async def test_register_user_success(
        self,
        auth_service,
        mock_user_repo,
        mock_event_bus
    ):
        """Test successful user registration"""
        # Arrange
        email = "newuser@example.com"
        password = "NewPassword123!"
        first_name = "New"
        last_name = "User"
        
        expected_user = AuthUser(
            id=uuid4(),
            email=email,
            hashed_password=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role=AuthRole.CLIENT,
            email_verified=False,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_user_repo.get_user_by_email.return_value = None  # User doesn't exist
        mock_user_repo.create_user.return_value = expected_user
        
        with patch.object(auth_service, 'user_repository', mock_user_repo), \
             patch('src.shared.events.get_event_bus', return_value=mock_event_bus):
            
            # Act
            result = await auth_service.register_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Assert
            assert result.email == email
            assert result.first_name == first_name
            assert result.last_name == last_name
            assert result.role == AuthRole.CLIENT
            assert not result.email_verified
            
            mock_user_repo.get_user_by_email.assert_called_once_with(email)
            mock_user_repo.create_user.assert_called_once()
            mock_event_bus.publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_user_already_exists(
        self,
        auth_service,
        mock_user_repo,
        test_user
    ):
        """Test registration with existing email"""
        # Arrange
        mock_user_repo.get_user_by_email.return_value = test_user
        
        with patch.object(auth_service, 'user_repository', mock_user_repo):
            
            # Act & Assert
            with pytest.raises(ValueError, match="User with email .* already exists"):
                await auth_service.register_user(
                    email=test_user.email,
                    password="password",
                    first_name="Test",
                    last_name="User"
                )
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(
        self,
        auth_service,
        mock_user_repo,
        mock_jwt_handler,
        test_user
    ):
        """Test successful user authentication"""
        # Arrange
        password = "TestPassword123!"
        access_token = "access_token_123"
        refresh_token = "refresh_token_123"
        
        mock_user_repo.get_user_by_email.return_value = test_user
        mock_jwt_handler.create_access_token.return_value = access_token
        mock_jwt_handler.create_refresh_token.return_value = refresh_token
        
        with patch.object(auth_service, 'user_repository', mock_user_repo), \
             patch.object(auth_service, 'jwt_handler', mock_jwt_handler), \
             patch('src.features.auth.infrastructure.security.verify_password', return_value=True):
            
            # Act
            result = await auth_service.authenticate_user(test_user.email, password)
            
            # Assert
            assert result["access_token"] == access_token
            assert result["refresh_token"] == refresh_token
            assert result["token_type"] == "bearer"
            assert result["user"]["email"] == test_user.email
            
            mock_user_repo.get_user_by_email.assert_called_once_with(test_user.email)
            mock_jwt_handler.create_access_token.assert_called_once()
            mock_jwt_handler.create_refresh_token.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(
        self,
        auth_service,
        mock_user_repo,
        test_user
    ):
        """Test authentication with invalid credentials"""
        # Arrange
        password = "WrongPassword123!"
        
        mock_user_repo.get_user_by_email.return_value = test_user
        
        with patch.object(auth_service, 'user_repository', mock_user_repo), \
             patch('src.features.auth.infrastructure.security.verify_password', return_value=False):
            
            # Act & Assert
            with pytest.raises(ValueError, match="Invalid credentials"):
                await auth_service.authenticate_user(test_user.email, password)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(
        self,
        auth_service,
        mock_user_repo
    ):
        """Test authentication with non-existent user"""
        # Arrange
        email = "nonexistent@example.com"
        password = "password"
        
        mock_user_repo.get_user_by_email.return_value = None
        
        with patch.object(auth_service, 'user_repository', mock_user_repo):
            
            # Act & Assert
            with pytest.raises(ValueError, match="Invalid credentials"):
                await auth_service.authenticate_user(email, password)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(
        self,
        auth_service,
        mock_user_repo,
        test_user
    ):
        """Test authentication with inactive user"""
        # Arrange
        password = "TestPassword123!"
        test_user.is_active = False
        
        mock_user_repo.get_user_by_email.return_value = test_user
        
        with patch.object(auth_service, 'user_repository', mock_user_repo), \
             patch('src.features.auth.infrastructure.security.verify_password', return_value=True):
            
            # Act & Assert
            with pytest.raises(ValueError, match="Account is inactive"):
                await auth_service.authenticate_user(test_user.email, password)
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_success(
        self,
        auth_service,
        mock_user_repo,
        mock_jwt_handler,
        test_user
    ):
        """Test successful token refresh"""
        # Arrange
        refresh_token = "refresh_token_123"
        new_access_token = "new_access_token_123"
        new_refresh_token = "new_refresh_token_123"
        
        token_payload = {
            "sub": str(test_user.id),
            "type": "refresh",
            "family_id": "family_123"
        }
        
        mock_jwt_handler.verify_token.return_value = token_payload
        mock_jwt_handler.create_access_token.return_value = new_access_token
        mock_jwt_handler.create_refresh_token.return_value = new_refresh_token
        mock_user_repo.get_user_by_id.return_value = test_user
        
        with patch.object(auth_service, 'user_repository', mock_user_repo), \
             patch.object(auth_service, 'jwt_handler', mock_jwt_handler):
            
            # Act
            result = await auth_service.refresh_access_token(refresh_token)
            
            # Assert
            assert result["access_token"] == new_access_token
            assert result["refresh_token"] == new_refresh_token
            assert result["token_type"] == "bearer"
            
            mock_jwt_handler.verify_token.assert_called_once_with(refresh_token)
            mock_user_repo.get_user_by_id.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid_token(
        self,
        auth_service,
        mock_jwt_handler
    ):
        """Test token refresh with invalid token"""
        # Arrange
        refresh_token = "invalid_token"
        
        mock_jwt_handler.verify_token.return_value = None
        
        with patch.object(auth_service, 'jwt_handler', mock_jwt_handler):
            
            # Act & Assert
            with pytest.raises(ValueError, match="Invalid refresh token"):
                await auth_service.refresh_access_token(refresh_token)
    
    @pytest.mark.asyncio
    async def test_refresh_access_token_wrong_type(
        self,
        auth_service,
        mock_jwt_handler
    ):
        """Test token refresh with access token instead of refresh token"""
        # Arrange
        access_token = "access_token_123"
        
        token_payload = {
            "sub": str(uuid4()),
            "type": "access",  # Wrong type
            "family_id": "family_123"
        }
        
        mock_jwt_handler.verify_token.return_value = token_payload
        
        with patch.object(auth_service, 'jwt_handler', mock_jwt_handler):
            
            # Act & Assert
            with pytest.raises(ValueError, match="Invalid refresh token"):
                await auth_service.refresh_access_token(access_token)
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self,
        auth_service,
        mock_user_repo,
        mock_jwt_handler,
        test_user
    ):
        """Test successful current user retrieval"""
        # Arrange
        access_token = "access_token_123"
        
        token_payload = {
            "sub": str(test_user.id),
            "type": "access",
            "email": test_user.email,
            "role": test_user.role.value
        }
        
        mock_jwt_handler.verify_token.return_value = token_payload
        mock_user_repo.get_user_by_id.return_value = test_user
        
        with patch.object(auth_service, 'user_repository', mock_user_repo), \
             patch.object(auth_service, 'jwt_handler', mock_jwt_handler):
            
            # Act
            result = await auth_service.get_current_user(access_token)
            
            # Assert
            assert result.id == test_user.id
            assert result.email == test_user.email
            
            mock_jwt_handler.verify_token.assert_called_once_with(access_token)
            mock_user_repo.get_user_by_id.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(
        self,
        auth_service,
        mock_jwt_handler
    ):
        """Test current user retrieval with invalid token"""
        # Arrange
        access_token = "invalid_token"
        
        mock_jwt_handler.verify_token.return_value = None
        
        with patch.object(auth_service, 'jwt_handler', mock_jwt_handler):
            
            # Act & Assert
            with pytest.raises(ValueError, match="Invalid access token"):
                await auth_service.get_current_user(access_token)
    
    @pytest.mark.asyncio
    async def test_logout_user_success(
        self,
        auth_service,
        mock_user_repo,
        test_user
    ):
        """Test successful user logout"""
        # Arrange
        user_id = test_user.id
        
        mock_user_repo.invalidate_user_tokens.return_value = True
        
        with patch.object(auth_service, 'user_repository', mock_user_repo):
            
            # Act
            result = await auth_service.logout_user(user_id)
            
            # Assert
            assert result is True
            mock_user_repo.invalidate_user_tokens.assert_called_once_with(user_id)