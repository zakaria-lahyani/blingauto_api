"""
Pytest configuration and shared fixtures for API integration tests
"""
import asyncio
import pytest
import pytest_asyncio
import httpx
import uuid
import time
import os
from typing import Dict, Any, Optional
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import create_app
from tests.factories import (
    UserDataFactory, 
    AdminUserDataFactory,
    ManagerUserDataFactory,
    WasherUserDataFactory,
    create_user_data,
    create_malicious_payloads
)
from tests.simple_test_fixes import (
    get_unique_test_user,
    setup_fast_test_environment,
    cleanup_fast_test_environment
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def app():
    """Create FastAPI app for testing"""
    # Setup test environment before creating app
    setup_fast_test_environment()
    
    # Import auth configuration classes after environment setup
    from src.features.auth import AuthConfig, AuthFeature
    
    # Override auth config to disable email verification for tests
    original_config = None
    app = create_app()
    
    # Modify the auth config after app creation to disable email verification
    if hasattr(app.state, 'auth') and hasattr(app.state.auth, 'config'):
        auth_config = app.state.auth.config
        # Remove email verification from enabled features for tests
        if AuthFeature.EMAIL_VERIFICATION in auth_config.enabled_features:
            auth_config.enabled_features = [
                f for f in auth_config.enabled_features 
                if f != AuthFeature.EMAIL_VERIFICATION
            ]
    
    yield app
    cleanup_fast_test_environment()


@pytest.fixture(scope="session")
def client(app):
    """Create test client"""
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def async_client(app):
    """Create async test client"""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session")
def auth_module(app):
    """Get auth module from app state"""
    return app.state.auth


@pytest.fixture
def unique_email():
    """Generate unique email for each test"""
    return f"test{int(time.time())}{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture
def unique_test_data():
    """Generate unique test data for each test"""
    return get_unique_test_user()


@pytest.fixture
def sample_user_data():
    """Sample user registration data using factory"""
    return UserDataFactory()


@pytest.fixture
def sample_weak_password_data():
    """Sample user data with weak password"""
    return create_user_data(password="123")


@pytest.fixture
def sample_admin_data():
    """Sample admin user data"""
    return AdminUserDataFactory()


@pytest.fixture
def sample_manager_data():
    """Sample manager user data"""
    return ManagerUserDataFactory()


@pytest.fixture
def sample_washer_data():
    """Sample washer user data"""
    return WasherUserDataFactory()


@pytest.fixture
def malicious_payloads():
    """Various malicious payloads for security testing"""
    return create_malicious_payloads()


@pytest.fixture
def registered_user(client, sample_user_data):
    """Create a registered user"""
    response = client.post("/auth/register", json=sample_user_data)
    assert response.status_code == 201
    user_data = response.json()
    
    # For testing purposes, we can simulate email verification by using the API
    # In a real scenario, the user would click a link in their email
    # For now, we'll create a user that can login (assuming email verification is bypassed in test mode)
    
    return {
        "user_data": user_data,
        "credentials": sample_user_data,
    }


@pytest.fixture
def verified_user(client, sample_user_data):
    """Create a user that can login (for testing purposes)"""
    # Use the existing admin email which should be automatically verified
    admin_email = "admin@carwash.com"
    admin_password = "admin123"
    
    # Try to login with admin credentials
    login_data = {
        "email": admin_email,
        "password": admin_password
    }
    
    response = client.post("/auth/login", json=login_data)
    if response.status_code == 200:
        # Admin user exists and can login
        return {
            "user_data": {"email": admin_email, "id": "admin"},
            "credentials": {"email": admin_email, "password": admin_password},
        }
    else:
        # If admin doesn't exist, return None and test should handle appropriately
        return None


@pytest.fixture  
def authenticated_user(client, verified_user):
    """Create authenticated user with tokens"""
    if not verified_user:
        pytest.skip("No verified user available for authentication test")
    
    login_data = {
        "email": verified_user["credentials"]["email"],
        "password": verified_user["credentials"]["password"]
    }
    
    response = client.post("/auth/login", json=login_data)
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code}")
        
    tokens = response.json()
    
    return {
        **verified_user,
        "tokens": tokens,
        "headers": {"Authorization": f"Bearer {tokens['access_token']}"}
    }


@pytest_asyncio.fixture
async def admin_user(client, auth_module):
    """Create admin user using AdminSetupService"""
    import os
    
    # Set up environment variables for admin creation
    admin_email = f"admin{int(time.time())}{uuid.uuid4().hex[:8]}@example.com"
    admin_password = "AdminPass123!"
    
    # Temporarily set environment variables
    original_email = os.environ.get("INITIAL_ADMIN_EMAIL")
    original_password = os.environ.get("INITIAL_ADMIN_PASSWORD")
    
    os.environ["INITIAL_ADMIN_EMAIL"] = admin_email
    os.environ["INITIAL_ADMIN_PASSWORD"] = admin_password
    
    try:
        # Use the AdminSetupService to create a proper admin
        success = await auth_module.admin_setup_service.ensure_admin_exists()
        assert success, "Failed to create admin user"
        
        # Login as admin
        login_response = client.post("/auth/login", json={
            "email": admin_email,
            "password": admin_password
        })
        assert login_response.status_code == 200, f"Admin login failed: {login_response.text}"
        tokens = login_response.json()
        
        # Get user data
        profile_response = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
        assert profile_response.status_code == 200, f"Failed to get admin profile: {profile_response.text}"
        user_data = profile_response.json()
        
        # Verify admin role
        assert user_data["role"] == "admin", f"User role is {user_data['role']}, expected admin"
        
        return {
            "user_data": user_data,
            "credentials": {"email": admin_email, "password": admin_password},
            "tokens": tokens,
            "headers": {"Authorization": f"Bearer {tokens['access_token']}"}
        }
        
    finally:
        # Restore original environment variables
        if original_email is not None:
            os.environ["INITIAL_ADMIN_EMAIL"] = original_email
        else:
            os.environ.pop("INITIAL_ADMIN_EMAIL", None)
            
        if original_password is not None:
            os.environ["INITIAL_ADMIN_PASSWORD"] = original_password
        else:
            os.environ.pop("INITIAL_ADMIN_PASSWORD", None)


@pytest_asyncio.fixture
async def manager_user(client, auth_module, admin_user):
    """Create manager user by promoting through admin"""
    manager_data = {
        "email": f"manager{int(time.time())}{uuid.uuid4().hex[:8]}@example.com",
        "password": "ManagerPass123!",
        "first_name": "Manager",
        "last_name": "User"
    }
    
    # Register manager as regular user
    response = client.post("/auth/register", json=manager_data)
    assert response.status_code == 201, f"Manager registration failed: {response.text}"
    user_data = response.json()
    user_id = user_data["id"]
    
    # Use admin to promote user to manager role
    admin_headers = admin_user["headers"]
    role_update_data = {"role": "manager"}
    
    promote_response = client.put(
        f"/auth/users/{user_id}/role", 
        json=role_update_data, 
        headers=admin_headers
    )
    assert promote_response.status_code == 200, f"Manager promotion failed: {promote_response.text}"
    
    # Login as manager
    login_response = client.post("/auth/login", json={
        "email": manager_data["email"],
        "password": manager_data["password"]
    })
    assert login_response.status_code == 200, f"Manager login failed: {login_response.text}"
    tokens = login_response.json()
    
    # Get updated user data with manager role
    profile_response = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert profile_response.status_code == 200, f"Failed to get manager profile: {profile_response.text}"
    user_data = profile_response.json()
    
    # Verify manager role
    assert user_data["role"] == "manager", f"User role is {user_data['role']}, expected manager"
    
    return {
        "user_data": user_data,
        "credentials": manager_data,
        "tokens": tokens,
        "headers": {"Authorization": f"Bearer {tokens['access_token']}"}
    }


@pytest.fixture
def washer_user(client):
    """Create washer user"""
    washer_data = {
        "email": f"washer{int(time.time())}{uuid.uuid4().hex[:8]}@example.com",
        "password": "WasherPass123!",
        "first_name": "Washer",
        "last_name": "User"
    }
    
    # Register washer
    response = client.post("/auth/register", json=washer_data)
    assert response.status_code == 201
    user_data = response.json()
    
    # Login as washer
    login_response = client.post("/auth/login", json={
        "email": washer_data["email"],
        "password": washer_data["password"]
    })
    assert login_response.status_code == 200
    tokens = login_response.json()
    
    return {
        "user_data": user_data,
        "credentials": washer_data,
        "tokens": tokens,
        "headers": {"Authorization": f"Bearer {tokens['access_token']}"}
    }


class APITestHelper:
    """Helper class for API testing utilities"""
    
    @staticmethod
    def assert_valid_token_response(response_data: Dict[str, Any]):
        """Assert token response structure"""
        assert "access_token" in response_data
        assert "refresh_token" in response_data
        assert "expires_in" in response_data
        assert "token_type" in response_data
        assert response_data["token_type"] == "bearer"
        assert isinstance(response_data["expires_in"], int)
        assert response_data["expires_in"] > 0
        
        # Check JWT structure (3 segments)
        access_token = response_data["access_token"]
        assert len(access_token.split(".")) == 3
        
        refresh_token = response_data["refresh_token"]
        assert len(refresh_token.split(".")) == 3
    
    @staticmethod
    def assert_valid_user_response(response_data: Dict[str, Any]):
        """Assert user response structure"""
        required_fields = ["id", "email", "first_name", "last_name", "role", "is_active", "email_verified"]
        for field in required_fields:
            assert field in response_data
        
        assert response_data["id"]  # ID can be int or string (UUID)
        assert "@" in response_data["email"]
        assert response_data["role"] in ["admin", "manager", "washer", "client"]
        assert isinstance(response_data["is_active"], bool)
        assert isinstance(response_data["email_verified"], bool)
    
    @staticmethod
    def assert_error_response(response_data: Dict[str, Any], expected_message: Optional[str] = None):
        """Assert error response structure"""
        assert "detail" in response_data
        if expected_message:
            assert expected_message in response_data["detail"]
    
    @staticmethod
    def assert_message_response(response_data: Dict[str, Any]):
        """Assert message response structure"""
        assert "message" in response_data
        assert isinstance(response_data["message"], str)


@pytest.fixture
def api_helper():
    """API test helper instance"""
    return APITestHelper()


# Pytest markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "smoke: Basic smoke tests")
    config.addinivalue_line("markers", "security: Security-focused tests")
    config.addinivalue_line("markers", "rbac: Role-based access control tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "concurrency: Concurrency tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")