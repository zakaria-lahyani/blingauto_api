"""
Simple fixes for test issues without complex database isolation
"""
import uuid
import time
import os


def get_unique_test_user():
    """Generate unique test user data to avoid email conflicts"""
    timestamp = int(time.time() * 1000)  # Millisecond precision
    unique_id = uuid.uuid4().hex[:6]  # Shorter for names
    
    # Generate name with only letters (no numbers to pass validation)
    import random
    import string
    name_suffix = ''.join(random.choices(string.ascii_lowercase, k=4))
    
    return {
        "email": f"test_{timestamp}_{unique_id}@carwash-test.com",
        "password": "TestPassword123!",
        "first_name": f"Test{name_suffix}",
        "last_name": f"User{name_suffix}"
    }


def setup_fast_test_environment():
    """Setup environment for fast, non-conflicting tests"""
    # Disable features that cause test slowdowns
    os.environ["AUTH_ENABLE_RATE_LIMITING"] = "false"
    os.environ["AUTH_ENABLE_SECURITY_LOGGING"] = "false"
    os.environ["AUTH_ENABLE_EMAIL_VERIFICATION"] = "false"  # Disable email verification for tests
    os.environ["GLOBAL_DEBUG"] = "false"
    os.environ["LOGGING_LOG_LEVEL"] = "ERROR"  # Reduce log noise
    
    # Set high rate limits if rate limiting gets enabled
    os.environ["AUTH_CLIENT_RATE_LIMIT"] = "10000"
    os.environ["AUTH_ADMIN_RATE_LIMIT"] = "10000"
    os.environ["AUTH_MANAGER_RATE_LIMIT"] = "10000"
    os.environ["AUTH_WASHER_RATE_LIMIT"] = "10000"
    os.environ["AUTH_LOGIN_RATE_LIMIT"] = "1000"
    os.environ["AUTH_REGISTER_RATE_LIMIT"] = "1000"
    
    # Shorter lockout times for faster test recovery
    os.environ["AUTH_INITIAL_LOCKOUT_MINUTES"] = "0"  # No lockout for tests
    os.environ["AUTH_MAX_LOGIN_ATTEMPTS"] = "1000"  # High threshold


def cleanup_fast_test_environment():
    """Cleanup test environment variables"""
    test_vars = [
        "AUTH_ENABLE_RATE_LIMITING",
        "AUTH_ENABLE_SECURITY_LOGGING",
        "AUTH_ENABLE_EMAIL_VERIFICATION",
        "GLOBAL_DEBUG",
        "LOGGING_LOG_LEVEL",
        "AUTH_CLIENT_RATE_LIMIT",
        "AUTH_ADMIN_RATE_LIMIT",
        "AUTH_MANAGER_RATE_LIMIT",
        "AUTH_WASHER_RATE_LIMIT",
        "AUTH_LOGIN_RATE_LIMIT",
        "AUTH_REGISTER_RATE_LIMIT",
        "AUTH_INITIAL_LOCKOUT_MINUTES",
        "AUTH_MAX_LOGIN_ATTEMPTS"
    ]
    
    for var in test_vars:
        if var in os.environ:
            del os.environ[var]