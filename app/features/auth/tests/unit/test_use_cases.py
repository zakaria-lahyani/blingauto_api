import pytest
from unittest.mock import AsyncMock

from app.features.auth.domain import User, UserRole, UserStatus, EmailVerificationToken, RefreshToken
from app.features.auth.use_cases import (
    RegisterUserUseCase,
    RegisterUserRequest,
    LoginUserUseCase,
    LoginUserRequest,
    RefreshTokenUseCase,
    RefreshTokenRequest,
    VerifyEmailUseCase,
    VerifyEmailRequest,
    GetUserUseCase,
    GetUserRequest,
)
from app.core.errors import ConflictError, AuthenticationError, NotFoundError, BusinessRuleViolationError


class TestRegisterUserUseCase:
    """Test RegisterUserUseCase business logic."""
    
    @pytest.mark.asyncio
    async def test_successful_registration(
        self,
        mock_user_repository,
        mock_email_verification_repository,
        mock_password_hasher,
        mock_email_service,
    ):
        """Test successful user registration."""
        # Setup mocks
        mock_user_repository.email_exists.return_value = False
        mock_user_repository.create.return_value = User.create(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            hashed_password="hashed_password",
        )
        mock_password_hasher.hash.return_value = "hashed_password"
        
        # Create use case
        use_case = RegisterUserUseCase(
            user_repository=mock_user_repository,
            token_repository=mock_email_verification_repository,
            password_hasher=mock_password_hasher,
            email_service=mock_email_service,
        )
        
        # Execute
        request = RegisterUserRequest(
            email="test@example.com",
            password="securepassword123",
            first_name="John",
            last_name="Doe",
            phone_number="+1234567890",
        )
        
        response = await use_case.execute(request)
        
        # Verify response
        assert response.email == "test@example.com"
        assert response.full_name == "John Doe"
        assert "verification" in response.message.lower()
        
        # Verify calls
        mock_user_repository.email_exists.assert_called_once_with("test@example.com")
        mock_password_hasher.hash.assert_called_once_with("securepassword123")
        mock_user_repository.create.assert_called_once()
        mock_email_verification_repository.create.assert_called_once()
        mock_email_service.send_verification_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_registration_with_existing_email(
        self,
        mock_user_repository,
        mock_email_verification_repository,
        mock_password_hasher,
        mock_email_service,
    ):
        """Test registration fails with existing email."""
        # Setup mocks
        mock_user_repository.email_exists.return_value = True
        
        # Create use case
        use_case = RegisterUserUseCase(
            user_repository=mock_user_repository,
            token_repository=mock_email_verification_repository,
            password_hasher=mock_password_hasher,
            email_service=mock_email_service,
        )
        
        # Execute and expect failure
        request = RegisterUserRequest(
            email="existing@example.com",
            password="securepassword123",
            first_name="John",
            last_name="Doe",
        )
        
        with pytest.raises(ConflictError) as exc_info:
            await use_case.execute(request)
        
        assert "already registered" in str(exc_info.value).lower()
        mock_user_repository.email_exists.assert_called_once()
        mock_user_repository.create.assert_not_called()


class TestLoginUserUseCase:
    """Test LoginUserUseCase business logic."""
    
    @pytest.mark.asyncio
    async def test_successful_login(
        self,
        sample_user,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_password_hasher,
        mock_token_service,
        mock_cache_service,
    ):
        """Test successful user login."""
        # Setup user as verified and active
        sample_user.verify_email()
        
        # Setup mocks
        mock_user_repository.get_by_email.return_value = sample_user
        mock_password_hasher.verify.return_value = True
        mock_token_service.create_access_token.return_value = "access_token"
        
        # Create use case
        use_case = LoginUserUseCase(
            user_repository=mock_user_repository,
            refresh_token_repository=mock_refresh_token_repository,
            password_hasher=mock_password_hasher,
            token_service=mock_token_service,
            cache_service=mock_cache_service,
        )
        
        # Execute
        request = LoginUserRequest(
            email="test@example.com",
            password="correct_password",
        )
        
        response = await use_case.execute(request)
        
        # Verify response
        assert response.access_token == "access_token"
        assert response.user_id == sample_user.id
        assert response.email == sample_user.email
        assert response.role == sample_user.role.value
        
        # Verify calls
        mock_user_repository.get_by_email.assert_called_once_with("test@example.com")
        mock_password_hasher.verify.assert_called_once()
        mock_user_repository.update.assert_called_once()
        mock_refresh_token_repository.create.assert_called_once()
        mock_cache_service.set_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_with_invalid_email(
        self,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_password_hasher,
        mock_token_service,
        mock_cache_service,
    ):
        """Test login fails with invalid email."""
        # Setup mocks
        mock_user_repository.get_by_email.return_value = None
        
        # Create use case
        use_case = LoginUserUseCase(
            user_repository=mock_user_repository,
            refresh_token_repository=mock_refresh_token_repository,
            password_hasher=mock_password_hasher,
            token_service=mock_token_service,
            cache_service=mock_cache_service,
        )
        
        # Execute and expect failure
        request = LoginUserRequest(
            email="invalid@example.com",
            password="password",
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            await use_case.execute(request)
        
        assert "invalid email or password" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_login_with_invalid_password(
        self,
        sample_user,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_password_hasher,
        mock_token_service,
        mock_cache_service,
    ):
        """Test login fails with invalid password."""
        # Setup mocks
        mock_user_repository.get_by_email.return_value = sample_user
        mock_password_hasher.verify.return_value = False
        
        # Create use case
        use_case = LoginUserUseCase(
            user_repository=mock_user_repository,
            refresh_token_repository=mock_refresh_token_repository,
            password_hasher=mock_password_hasher,
            token_service=mock_token_service,
            cache_service=mock_cache_service,
        )
        
        # Execute and expect failure
        request = LoginUserRequest(
            email="test@example.com",
            password="wrong_password",
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            await use_case.execute(request)
        
        assert "invalid email or password" in str(exc_info.value).lower()
        
        # Verify failed attempt was recorded
        mock_user_repository.update.assert_called_once()
        assert sample_user.failed_login_attempts == 1
    
    @pytest.mark.asyncio
    async def test_login_with_unverified_email(
        self,
        sample_user,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_password_hasher,
        mock_token_service,
        mock_cache_service,
    ):
        """Test login fails with unverified email."""
        # User is not verified (default state)
        
        # Setup mocks
        mock_user_repository.get_by_email.return_value = sample_user
        mock_password_hasher.verify.return_value = True
        
        # Create use case
        use_case = LoginUserUseCase(
            user_repository=mock_user_repository,
            refresh_token_repository=mock_refresh_token_repository,
            password_hasher=mock_password_hasher,
            token_service=mock_token_service,
            cache_service=mock_cache_service,
        )
        
        # Execute and expect failure
        request = LoginUserRequest(
            email="test@example.com",
            password="correct_password",
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            await use_case.execute(request)
        
        assert "verification" in str(exc_info.value).lower()


class TestRefreshTokenUseCase:
    """Test RefreshTokenUseCase business logic."""
    
    @pytest.mark.asyncio
    async def test_successful_token_refresh(
        self,
        sample_user,
        refresh_token,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_token_service,
    ):
        """Test successful token refresh."""
        # Setup user as active
        sample_user.verify_email()
        
        # Setup mocks
        mock_refresh_token_repository.get_by_token.return_value = refresh_token
        mock_user_repository.get_by_id.return_value = sample_user
        mock_token_service.create_access_token.return_value = "new_access_token"
        
        # Create use case
        use_case = RefreshTokenUseCase(
            user_repository=mock_user_repository,
            refresh_token_repository=mock_refresh_token_repository,
            token_service=mock_token_service,
        )
        
        # Execute
        request = RefreshTokenRequest(refresh_token="valid_refresh_token")
        response = await use_case.execute(request)
        
        # Verify response
        assert response.access_token == "new_access_token"
        assert response.refresh_token != "valid_refresh_token"  # Should be rotated
        
        # Verify calls
        mock_refresh_token_repository.get_by_token.assert_called_once()
        mock_user_repository.get_by_id.assert_called_once()
        mock_token_service.create_access_token.assert_called_once()
        mock_refresh_token_repository.revoke.assert_called_once()
        mock_refresh_token_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(
        self,
        mock_user_repository,
        mock_refresh_token_repository,
        mock_token_service,
    ):
        """Test refresh fails with invalid token."""
        # Setup mocks
        mock_refresh_token_repository.get_by_token.return_value = None
        
        # Create use case
        use_case = RefreshTokenUseCase(
            user_repository=mock_user_repository,
            refresh_token_repository=mock_refresh_token_repository,
            token_service=mock_token_service,
        )
        
        # Execute and expect failure
        request = RefreshTokenRequest(refresh_token="invalid_token")
        
        with pytest.raises(AuthenticationError) as exc_info:
            await use_case.execute(request)
        
        assert "invalid refresh token" in str(exc_info.value).lower()


class TestVerifyEmailUseCase:
    """Test VerifyEmailUseCase business logic."""
    
    @pytest.mark.asyncio
    async def test_successful_email_verification(
        self,
        sample_user,
        email_verification_token,
        mock_user_repository,
        mock_email_verification_repository,
        mock_email_service,
    ):
        """Test successful email verification."""
        # Setup mocks
        mock_email_verification_repository.get_by_token.return_value = email_verification_token
        mock_user_repository.get_by_id.return_value = sample_user
        
        # Create use case
        use_case = VerifyEmailUseCase(
            user_repository=mock_user_repository,
            token_repository=mock_email_verification_repository,
            email_service=mock_email_service,
        )
        
        # Execute
        request = VerifyEmailRequest(token="valid_verification_token")
        response = await use_case.execute(request)
        
        # Verify response
        assert response.user_id == sample_user.id
        assert response.email == sample_user.email
        assert "verified successfully" in response.message.lower()
        
        # Verify user was verified
        assert sample_user.email_verified
        assert sample_user.status == UserStatus.ACTIVE
        
        # Verify calls
        mock_email_verification_repository.get_by_token.assert_called_once()
        mock_user_repository.get_by_id.assert_called_once()
        mock_user_repository.update.assert_called_once()
        mock_email_verification_repository.mark_as_used.assert_called_once()
        mock_email_service.send_welcome_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verification_with_invalid_token(
        self,
        mock_user_repository,
        mock_email_verification_repository,
        mock_email_service,
    ):
        """Test verification fails with invalid token."""
        # Setup mocks
        mock_email_verification_repository.get_by_token.return_value = None
        
        # Create use case
        use_case = VerifyEmailUseCase(
            user_repository=mock_user_repository,
            token_repository=mock_email_verification_repository,
            email_service=mock_email_service,
        )
        
        # Execute and expect failure
        request = VerifyEmailRequest(token="invalid_token")
        
        with pytest.raises(NotFoundError) as exc_info:
            await use_case.execute(request)
        
        assert "verification token" in str(exc_info.value).lower()


class TestGetUserUseCase:
    """Test GetUserUseCase business logic."""
    
    @pytest.mark.asyncio
    async def test_get_user_from_cache(
        self,
        sample_user,
        mock_user_repository,
        mock_cache_service,
    ):
        """Test getting user from cache."""
        # Setup mocks - cache hit
        cached_data = {
            "id": sample_user.id,
            "email": sample_user.email,
            "first_name": sample_user.first_name,
            "last_name": sample_user.last_name,
            "full_name": sample_user.full_name,
            "role": sample_user.role.value,
            "status": sample_user.status.value,
            "phone_number": sample_user.phone_number,
            "email_verified": sample_user.email_verified,
            "created_at": sample_user.created_at.isoformat(),
            "last_login_at": None,
        }
        mock_cache_service.get_user.return_value = cached_data
        
        # Create use case
        use_case = GetUserUseCase(
            user_repository=mock_user_repository,
            cache_service=mock_cache_service,
        )
        
        # Execute
        request = GetUserRequest(user_id=sample_user.id)
        response = await use_case.execute(request)
        
        # Verify response
        assert response.id == sample_user.id
        assert response.email == sample_user.email
        
        # Verify cache was checked, but repository was not called
        mock_cache_service.get_user.assert_called_once_with(sample_user.id)
        mock_user_repository.get_by_id.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_user_from_repository(
        self,
        sample_user,
        mock_user_repository,
        mock_cache_service,
    ):
        """Test getting user from repository when not in cache."""
        # Setup mocks - cache miss
        mock_cache_service.get_user.return_value = None
        mock_user_repository.get_by_id.return_value = sample_user
        
        # Create use case
        use_case = GetUserUseCase(
            user_repository=mock_user_repository,
            cache_service=mock_cache_service,
        )
        
        # Execute
        request = GetUserRequest(user_id=sample_user.id)
        response = await use_case.execute(request)
        
        # Verify response
        assert response.id == sample_user.id
        assert response.email == sample_user.email
        
        # Verify both cache and repository were called
        mock_cache_service.get_user.assert_called_once_with(sample_user.id)
        mock_user_repository.get_by_id.assert_called_once_with(sample_user.id)
        mock_cache_service.set_user.assert_called_once()  # Cache the result
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_user(
        self,
        mock_user_repository,
        mock_cache_service,
    ):
        """Test getting non-existent user."""
        # Setup mocks
        mock_cache_service.get_user.return_value = None
        mock_user_repository.get_by_id.return_value = None
        
        # Create use case
        use_case = GetUserUseCase(
            user_repository=mock_user_repository,
            cache_service=mock_cache_service,
        )
        
        # Execute and expect failure
        request = GetUserRequest(user_id="nonexistent_id")
        
        with pytest.raises(NotFoundError) as exc_info:
            await use_case.execute(request)
        
        assert "user" in str(exc_info.value).lower()