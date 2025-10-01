import os
import tempfile
from unittest.mock import patch

from app.core.config import Settings


def get_test_settings():
    """Get test settings without loading .env file."""
    with patch.dict(os.environ, {}, clear=True):
        # Set minimal required environment variables
        test_env = {
            "ENVIRONMENT": "testing",
            "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key-for-testing-only",
            "REDIS_URL": "",  # Disable Redis for tests
        }
        
        with patch.dict(os.environ, test_env):
            return Settings()


# Global test settings instance
test_settings = get_test_settings()