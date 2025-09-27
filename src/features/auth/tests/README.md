# Auth Feature Tests

This directory contains comprehensive tests for the authentication feature module.

## Test Structure

```
auth/tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── README.md               # This file
├── fixtures/               # Test fixtures and utilities
│   ├── __init__.py
│   └── auth_fixtures.py    # Auth-specific test fixtures
├── unit/                   # Unit tests for individual components
│   ├── __init__.py
│   ├── test_auth_service.py      # AuthService unit tests
│   ├── test_jwt_handler.py       # JWTHandler unit tests
│   └── test_user_service.py      # UserService unit tests
└── integration/            # Integration tests for API endpoints
    ├── __init__.py
    ├── test_auth_api.py           # Core auth API endpoints
    ├── test_role_based_access.py  # RBAC functionality
    └── test_security_flows.py     # Security and edge cases
```

## Test Categories

### Unit Tests (`unit/`)
Test individual components in isolation:
- **AuthService**: Registration, login, token management
- **JWTHandler**: Token creation, verification, expiry
- **UserService**: User management operations
- **Password handling**: Hashing, verification
- **Domain entities**: User entities and enums

### Integration Tests (`integration/`)
Test complete workflows and API endpoints:
- **Auth API**: Registration, login, logout, token refresh
- **Role-Based Access**: Permissions for different user roles
- **Security Flows**: JWT security, session management, attack protection

## Running Tests

### Run All Auth Tests
```bash
# From project root
pytest src/features/auth/tests/

# With coverage
pytest src/features/auth/tests/ --cov=src.features.auth
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest src/features/auth/tests/unit/

# Integration tests only
pytest src/features/auth/tests/integration/

# Specific test file
pytest src/features/auth/tests/unit/test_auth_service.py

# Specific test method
pytest src/features/auth/tests/unit/test_auth_service.py::TestAuthService::test_register_user_success
```

### Run with Different Options
```bash
# Verbose output
pytest src/features/auth/tests/ -v

# Stop on first failure
pytest src/features/auth/tests/ -x

# Run only failed tests from last run
pytest src/features/auth/tests/ --lf

# Parallel execution (requires pytest-xdist)
pytest src/features/auth/tests/ -n auto
```

## Test Configuration

### Database
Tests use an in-memory SQLite database by default, configured in `conftest.py`:
- Fresh database for each test session
- Automatic table creation
- No cleanup needed (in-memory)

### Authentication
Test fixtures provide authenticated clients:
- `authenticated_client`: Regular user with CLIENT role
- `admin_client`: Admin user with ADMIN role
- `manager_client`: Manager user (create as needed)

### Environment
Tests run with:
- Rate limiting disabled
- Security logging disabled
- Debug mode enabled
- Test-specific JWT secret

## Test Data

### Fixtures
- `user_data`: Valid user registration data
- `admin_data`: Admin user data
- `test_user`: Created user entity
- `auth_config`: Test auth configuration

### Helpers
- `AuthTestHelpers`: Utility methods for creating test payloads
- `create_test_user()`: Helper to create users with specific roles

## Coverage Goals

Aim for high test coverage across:

### Unit Tests
- ✅ Service layer logic
- ✅ JWT token handling
- ✅ Password security
- ✅ Domain entity validation
- ✅ Error handling

### Integration Tests
- ✅ API endpoint responses
- ✅ Authentication flows
- ✅ Authorization (RBAC)
- ✅ Security protections
- ✅ Edge cases and error scenarios

### Security Testing
- ✅ JWT manipulation protection
- ✅ SQL injection prevention
- ✅ Password security requirements
- ✅ Account lockout mechanisms
- ✅ Session management
- ✅ Data exposure prevention

## Writing New Tests

### Unit Test Example
```python
@pytest.mark.asyncio
async def test_new_service_method(self, auth_service, mock_user_repo):
    # Arrange
    mock_user_repo.some_method.return_value = expected_result
    
    with patch.object(auth_service, 'user_repository', mock_user_repo):
        # Act
        result = await auth_service.new_method(test_data)
        
        # Assert
        assert result == expected_result
        mock_user_repo.some_method.assert_called_once_with(test_data)
```

### Integration Test Example
```python
@pytest.mark.asyncio
async def test_new_endpoint(self, authenticated_client):
    # Arrange
    client, tokens = authenticated_client
    test_payload = {"key": "value"}
    
    # Act
    response = await client.post("/auth/new-endpoint", json=test_payload)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "expected_value"
```

## Test Dependencies

The following packages are required for testing:
- `pytest`: Test framework
- `pytest-asyncio`: Async test support
- `pytest-mock`: Mocking utilities
- `httpx`: HTTP client for API testing
- `faker`: Test data generation
- `factory-boy`: Test object factories

## Continuous Integration

These tests are designed to run in CI/CD pipelines:
- No external dependencies (uses in-memory DB)
- Deterministic test data
- Proper cleanup and isolation
- Fast execution times

## Troubleshooting

### Common Issues

**Import Errors**
- Ensure `src/` is in Python path
- Check for circular imports
- Verify absolute import paths

**Database Errors**
- Check that `aiosqlite` is installed
- Verify async session handling
- Ensure proper test isolation

**Authentication Errors**
- Check JWT secret consistency
- Verify token format and expiry
- Ensure proper header format: `Bearer <token>`

**Async Errors**
- Use `@pytest.mark.asyncio` for async tests
- Ensure proper `await` usage
- Check event loop configuration

### Debug Mode
Run tests with debug output:
```bash
pytest src/features/auth/tests/ -v --tb=long --log-cli-level=DEBUG
```