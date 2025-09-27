"""
Unit tests for JWTHandler
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.features.auth.infrastructure.security.jwt_handler import JWTHandler
from src.features.auth.config import AuthConfig


@pytest.fixture
def jwt_config():
    """JWT configuration for testing"""
    return AuthConfig(
        jwt_secret_key="Dev_Test_Secret_K3y_F0r_JWT_T3st1ng_M1n1mum_Ent40py_V4l1d4t10n_P4ss_9$2z",
        jwt_algorithm="HS256",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7
    )


@pytest.fixture
def jwt_handler(jwt_config):
    """JWT handler instance for testing"""
    return JWTHandler(jwt_config)


class TestJWTHandler:
    """Test cases for JWTHandler"""
    
    def test_create_access_token(self, jwt_handler):
        """Test access token creation"""
        # Arrange
        user_id = str(uuid4())
        email = "test@example.com"
        role = "client"
        
        # Act
        token = jwt_handler.create_access_token(user_id, email, role)
        
        # Assert
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token content
        payload = jwt_handler.verify_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["email"] == email
        assert payload["role"] == role
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_access_token_custom_expiry(self, jwt_handler):
        """Test access token creation with custom expiry"""
        # Arrange
        user_id = str(uuid4())
        email = "test@example.com"
        role = "client"
        expires_minutes = 60
        
        # Act
        token = jwt_handler.create_access_token(
            user_id, email, role, expires_minutes
        )
        
        # Assert
        payload = jwt_handler.verify_token(token)
        assert payload is not None
        
        # Check expiry time (allow for small time differences)
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + timedelta(minutes=expires_minutes)
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 60  # Within 1 minute
    
    def test_create_refresh_token(self, jwt_handler):
        """Test refresh token creation"""
        # Arrange
        user_id = str(uuid4())
        
        # Act
        token = jwt_handler.create_refresh_token(user_id)
        
        # Assert
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token content
        payload = jwt_handler.verify_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "family_id" in payload
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_refresh_token_with_family_id(self, jwt_handler):
        """Test refresh token creation with specific family ID"""
        # Arrange
        user_id = str(uuid4())
        family_id = "custom_family_id"
        
        # Act
        token = jwt_handler.create_refresh_token(user_id, family_id)
        
        # Assert
        payload = jwt_handler.verify_token(token)
        assert payload is not None
        assert payload["family_id"] == family_id
    
    def test_create_refresh_token_custom_expiry(self, jwt_handler):
        """Test refresh token creation with custom expiry"""
        # Arrange
        user_id = str(uuid4())
        expires_days = 14
        
        # Act
        token = jwt_handler.create_refresh_token(
            user_id, expires_days=expires_days
        )
        
        # Assert
        payload = jwt_handler.verify_token(token)
        assert payload is not None
        
        # Check expiry time
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + timedelta(days=expires_days)
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 3600  # Within 1 hour
    
    def test_verify_token_valid(self, jwt_handler):
        """Test token verification with valid token"""
        # Arrange
        user_id = str(uuid4())
        email = "test@example.com"
        role = "client"
        token = jwt_handler.create_access_token(user_id, email, role)
        
        # Act
        payload = jwt_handler.verify_token(token)
        
        # Assert
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["email"] == email
        assert payload["role"] == role
    
    def test_verify_token_invalid(self, jwt_handler):
        """Test token verification with invalid token"""
        # Arrange
        invalid_token = "invalid.token.here"
        
        # Act
        payload = jwt_handler.verify_token(invalid_token)
        
        # Assert
        assert payload is None
    
    def test_verify_token_wrong_secret(self, jwt_config):
        """Test token verification with wrong secret"""
        # Arrange
        handler1 = JWTHandler(jwt_config)
        
        # Create token with one handler
        user_id = str(uuid4())
        token = handler1.create_access_token(user_id, "test@example.com", "client")
        
        # Try to verify with different secret
        jwt_config.jwt_secret_key = "different-secret-key"
        handler2 = JWTHandler(jwt_config)
        
        # Act
        payload = handler2.verify_token(token)
        
        # Assert
        assert payload is None
    
    def test_decode_token_without_verification(self, jwt_handler):
        """Test token decoding without verification"""
        # Arrange
        user_id = str(uuid4())
        email = "test@example.com"
        role = "client"
        token = jwt_handler.create_access_token(user_id, email, role)
        
        # Act
        payload = jwt_handler.decode_token(token)
        
        # Assert
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["email"] == email
        assert payload["role"] == role
    
    def test_decode_expired_token(self, jwt_handler):
        """Test decoding expired token"""
        # Arrange - create token that expires immediately
        user_id = str(uuid4())
        email = "test@example.com"
        role = "client"
        token = jwt_handler.create_access_token(user_id, email, role, expires_minutes=-1)
        
        # Act
        payload = jwt_handler.decode_token(token)
        
        # Assert - should still decode even if expired
        assert payload is not None
        assert payload["sub"] == user_id
    
    def test_is_token_expired_not_expired(self, jwt_handler):
        """Test token expiry check with valid token"""
        # Arrange
        user_id = str(uuid4())
        token = jwt_handler.create_access_token(user_id, "test@example.com", "client")
        
        # Act
        is_expired = jwt_handler.is_token_expired(token)
        
        # Assert
        assert is_expired is False
    
    def test_is_token_expired_expired(self, jwt_handler):
        """Test token expiry check with expired token"""
        # Arrange
        user_id = str(uuid4())
        token = jwt_handler.create_access_token(
            user_id, "test@example.com", "client", expires_minutes=-1
        )
        
        # Act
        is_expired = jwt_handler.is_token_expired(token)
        
        # Assert
        assert is_expired is True
    
    def test_is_token_expired_invalid_token(self, jwt_handler):
        """Test token expiry check with invalid token"""
        # Arrange
        invalid_token = "invalid.token.here"
        
        # Act
        is_expired = jwt_handler.is_token_expired(invalid_token)
        
        # Assert
        assert is_expired is True
    
    def test_get_token_user_id(self, jwt_handler):
        """Test extracting user ID from token"""
        # Arrange
        user_id = str(uuid4())
        token = jwt_handler.create_access_token(user_id, "test@example.com", "client")
        
        # Act
        extracted_user_id = jwt_handler.get_token_user_id(token)
        
        # Assert
        assert extracted_user_id == user_id
    
    def test_get_token_user_id_invalid_token(self, jwt_handler):
        """Test extracting user ID from invalid token"""
        # Arrange
        invalid_token = "invalid.token.here"
        
        # Act
        extracted_user_id = jwt_handler.get_token_user_id(invalid_token)
        
        # Assert
        assert extracted_user_id is None
    
    def test_token_algorithms_mismatch(self, jwt_config):
        """Test token verification with different algorithms"""
        # Arrange
        handler1 = JWTHandler(jwt_config)
        user_id = str(uuid4())
        token = handler1.create_access_token(user_id, "test@example.com", "client")
        
        # Change algorithm
        jwt_config.jwt_algorithm = "HS512"
        handler2 = JWTHandler(jwt_config)
        
        # Act
        payload = handler2.verify_token(token)
        
        # Assert
        assert payload is None