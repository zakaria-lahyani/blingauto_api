"""
Test-specific configuration overrides
"""
import os
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.features.auth.config import AuthConfig


class TestAuthConfig(AuthConfig):
    """Test-specific auth configuration with relaxed limits"""
    
    def __init__(self, **kwargs):
        # Set test-friendly defaults
        super().__init__(**kwargs)
        
        # Disable rate limiting for tests
        self.enable_rate_limiting = False
        
        # High rate limits if rate limiting is enabled  
        self.global_rate_limit = 10000
        self.admin_rate_limit = 10000
        self.manager_rate_limit = 10000
        self.washer_rate_limit = 10000
        self.client_rate_limit = 10000
        self.anonymous_rate_limit = 10000
        
        # High endpoint-specific limits
        self.login_rate_limit = 1000
        self.register_rate_limit = 1000
        self.password_reset_rate_limit = 1000
        self.email_verification_rate_limit = 1000
        
        # Disable security logging for faster tests
        self.enable_security_logging = False
        self.log_failed_attempts = False
        self.log_successful_auth = False
        
        # Shorter timeouts for faster tests
        self.access_token_expire_minutes = 5
        self.email_verification_expire_hours = 1
        self.password_reset_expire_hours = 1
        
        # Faster account lockout recovery
        self.initial_lockout_minutes = 1
        self.max_lockout_minutes = 5
        

def get_test_config():
    """Get test-specific configuration"""
    return TestAuthConfig()


def setup_test_environment_vars():
    """Setup environment variables for testing"""
    test_env_vars = {
        "AUTH_ENABLE_RATE_LIMITING": "false",
        "AUTH_ENABLE_SECURITY_LOGGING": "false", 
        "AUTH_LOG_FAILED_ATTEMPTS": "false",
        "AUTH_LOG_SUCCESSFUL_AUTH": "false",
        "AUTH_CLIENT_RATE_LIMIT": "10000",
        "AUTH_ADMIN_RATE_LIMIT": "10000",
        "AUTH_MANAGER_RATE_LIMIT": "10000", 
        "AUTH_WASHER_RATE_LIMIT": "10000",
        "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES": "5",
        "AUTH_INITIAL_LOCKOUT_MINUTES": "1",
        "AUTH_MAX_LOCKOUT_MINUTES": "5",
        "GLOBAL_DEBUG": "false",  # Reduce logging noise
        "LOGGING_LOG_LEVEL": "WARNING",  # Reduce logging
    }
    
    for key, value in test_env_vars.items():
        os.environ[key] = value


def cleanup_test_environment_vars():
    """Cleanup test environment variables"""
    test_env_vars = [
        "AUTH_ENABLE_RATE_LIMITING",
        "AUTH_ENABLE_SECURITY_LOGGING", 
        "AUTH_LOG_FAILED_ATTEMPTS",
        "AUTH_LOG_SUCCESSFUL_AUTH",
        "AUTH_CLIENT_RATE_LIMIT",
        "AUTH_ADMIN_RATE_LIMIT",
        "AUTH_MANAGER_RATE_LIMIT", 
        "AUTH_WASHER_RATE_LIMIT",
        "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES",
        "AUTH_INITIAL_LOCKOUT_MINUTES",
        "AUTH_MAX_LOCKOUT_MINUTES",
        "GLOBAL_DEBUG",
        "LOGGING_LOG_LEVEL",
    ]
    
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]