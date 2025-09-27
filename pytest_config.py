"""
Test-specific configuration overrides
"""
import os

# Override environment variables for testing
os.environ["AUTH_EMAIL_VERIFICATION_REQUIRED"] = "false"
os.environ["AUTH_REQUIRE_EMAIL_VERIFICATION"] = "false"