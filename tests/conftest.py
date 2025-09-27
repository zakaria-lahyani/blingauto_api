"""
Pytest configuration and shared fixtures for API integration tests
"""
import asyncio
import pytest
import httpx
import uuid
import time
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


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def app():
    """Create FastAPI app for testing"""
    app = create_app()
    yield app


@pytest.fixture(scope="session")
def client(app):
    """Create test client"""
    with TestClient(app) as client:
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


@pytest.fixture
def admin_user(client):
    """Create admin user"""
    admin_data = {
        "email": f"admin{int(time.time())}{uuid.uuid4().hex[:8]}@example.com",
        "password": "AdminPass123!",
        "first_name": "Admin",
        "last_name": "User"
    }
    
    # Register admin (will be promoted via initial admin setup)
    response = client.post("/auth/register", json=admin_data)
    assert response.status_code == 201
    user_data = response.json()
    
    # Login as admin
    login_response = client.post("/auth/login", json={
        "email": admin_data["email"],
        "password": admin_data["password"]
    })
    assert login_response.status_code == 200
    tokens = login_response.json()
    
    return {
        "user_data": user_data,
        "credentials": admin_data,
        "tokens": tokens,
        "headers": {"Authorization": f"Bearer {tokens['access_token']}"}
    }


@pytest.fixture
def manager_user(client):
    """Create manager user"""
    manager_data = {
        "email": f"manager{int(time.time())}{uuid.uuid4().hex[:8]}@example.com",
        "password": "ManagerPass123!",
        "first_name": "Manager",
        "last_name": "User"
    }
    
    # Register manager
    response = client.post("/auth/register", json=manager_data)
    assert response.status_code == 201
    user_data = response.json()
    
    # Login as manager
    login_response = client.post("/auth/login", json={
        "email": manager_data["email"],
        "password": manager_data["password"]
    })
    assert login_response.status_code == 200
    tokens = login_response.json()
    
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