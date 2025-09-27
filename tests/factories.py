"""
Test factories for generating realistic test data
"""
import factory
from faker import Faker
from typing import Dict, Any
import time
import uuid

fake = Faker()


class UserDataFactory(factory.Factory):
    """Factory for generating user registration data"""
    
    class Meta:
        model = dict
    
    email = factory.LazyFunction(lambda: f"test{int(time.time())}{uuid.uuid4().hex[:8]}@{fake.domain_name()}")
    password = factory.LazyFunction(lambda: fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True))
    first_name = factory.LazyFunction(lambda: fake.first_name())
    last_name = factory.LazyFunction(lambda: fake.last_name())


class AdminUserDataFactory(UserDataFactory):
    """Factory for admin user data"""
    email = factory.LazyFunction(lambda: f"admin{int(time.time())}{uuid.uuid4().hex[:8]}@{fake.domain_name()}")
    first_name = "Admin"
    last_name = "User"


class ManagerUserDataFactory(UserDataFactory):
    """Factory for manager user data"""
    email = factory.LazyFunction(lambda: f"manager{int(time.time())}{uuid.uuid4().hex[:8]}@{fake.domain_name()}")
    first_name = "Manager"
    last_name = "User"


class WasherUserDataFactory(UserDataFactory):
    """Factory for washer user data"""
    email = factory.LazyFunction(lambda: f"washer{int(time.time())}{uuid.uuid4().hex[:8]}@{fake.domain_name()}")
    first_name = "Washer"
    last_name = "User"


class WeakPasswordUserDataFactory(UserDataFactory):
    """Factory for user with weak password"""
    password = "123"


class InvalidEmailUserDataFactory(UserDataFactory):
    """Factory for user with invalid email"""
    email = "not-an-email"


class LongFieldUserDataFactory(UserDataFactory):
    """Factory for user with overly long fields"""
    first_name = factory.LazyFunction(lambda: "x" * 1000)
    last_name = factory.LazyFunction(lambda: "y" * 1000)


class SpecialCharacterUserDataFactory(UserDataFactory):
    """Factory for user with special characters"""
    first_name = "José-François"
    last_name = "müller@öäü"


class SQLInjectionUserDataFactory(UserDataFactory):
    """Factory for testing SQL injection attempts"""
    first_name = "'; DROP TABLE users; --"
    last_name = "' OR '1'='1"
    email = factory.LazyFunction(lambda: f"test{int(time.time())}@example.com")


class XSSUserDataFactory(UserDataFactory):
    """Factory for testing XSS attempts"""
    first_name = "<script>alert('xss')</script>"
    last_name = "javascript:alert('xss')"
    email = factory.LazyFunction(lambda: f"test{int(time.time())}@example.com")


def create_user_data(**kwargs) -> Dict[str, Any]:
    """Helper to create user data with overrides"""
    return UserDataFactory(**kwargs)


def create_admin_data(**kwargs) -> Dict[str, Any]:
    """Helper to create admin user data"""
    return AdminUserDataFactory(**kwargs)


def create_test_credentials(email: str, password: str) -> Dict[str, str]:
    """Helper to create login credentials"""
    return {
        "email": email,
        "password": password
    }


def create_malicious_payloads():
    """Generate various malicious payloads for security testing"""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "admin'/*",
            "' OR '1'='1",
            "'; DELETE FROM users; --"
        ],
        "xss": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ],
        "large_payloads": [
            "x" * 10000,
            "y" * 100000,
            {"large_field": "z" * 50000}
        ]
    }