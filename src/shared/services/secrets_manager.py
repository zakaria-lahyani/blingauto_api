"""
Secrets Management Service

Provides secure access to secrets from various providers:
- AWS Secrets Manager (production)
- Environment variables (development)
- Docker secrets (container deployments)
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from functools import lru_cache

logger = logging.getLogger(__name__)


class SecretsProvider(ABC):
    """Abstract base class for secrets providers"""
    
    @abstractmethod
    async def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Get secret by name"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available/configured"""
        pass


class EnvironmentSecretsProvider(SecretsProvider):
    """Environment variables secrets provider (development)"""
    
    def __init__(self):
        self.prefix = "SECRET_"
    
    async def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Get secrets from environment variables"""
        secrets = {}
        
        # Look for environment variables with SECRET_ prefix
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                secret_key = key[len(self.prefix):].lower()
                secrets[secret_key] = value
        
        # Also check direct environment variables
        direct_mappings = {
            "jwt_secret_key": "AUTH_JWT_SECRET_KEY",
            "database_url": "DATABASE_URL",
            "redis_url": "REDIS_URL",
            "smtp_password": "AUTH_SMTP_PASSWORD",
            "initial_admin_password": "AUTH_INITIAL_ADMIN_PASSWORD"
        }
        
        for secret_key, env_var in direct_mappings.items():
            if env_var in os.environ:
                secrets[secret_key] = os.environ[env_var]
        
        return secrets
    
    def is_available(self) -> bool:
        return True


class DockerSecretsProvider(SecretsProvider):
    """Docker secrets provider"""
    
    def __init__(self):
        self.secrets_path = "/run/secrets"
    
    async def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Get secrets from Docker secrets files"""
        secrets = {}
        
        if not os.path.exists(self.secrets_path):
            return secrets
        
        secret_files = {
            "jwt_secret_key": "jwt_secret",
            "database_url": "database_url", 
            "redis_url": "redis_url",
            "smtp_password": "smtp_password",
            "initial_admin_password": "admin_password"
        }
        
        for secret_key, filename in secret_files.items():
            file_path = os.path.join(self.secrets_path, filename)
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        secrets[secret_key] = f.read().strip()
            except Exception as e:
                logger.warning(f"Failed to read Docker secret {filename}: {e}")
        
        return secrets
    
    def is_available(self) -> bool:
        return os.path.exists(self.secrets_path)


class AWSSecretsProvider(SecretsProvider):
    """AWS Secrets Manager provider"""
    
    def __init__(self, region_name: str = "us-east-1"):
        self.region_name = region_name
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of boto3 client"""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client('secretsmanager', region_name=self.region_name)
            except ImportError:
                logger.error("boto3 not installed. Install with: pip install boto3")
                raise
            except Exception as e:
                logger.error(f"Failed to create AWS Secrets Manager client: {e}")
                raise
        return self._client
    
    @lru_cache(maxsize=10)
    async def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Get secret from AWS Secrets Manager with caching"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            secret_string = response.get('SecretString')
            
            if secret_string:
                return json.loads(secret_string)
            else:
                logger.error(f"Secret {secret_name} has no string value")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to retrieve AWS secret {secret_name}: {e}")
            return {}
    
    def is_available(self) -> bool:
        """Check if AWS credentials are configured"""
        try:
            import boto3
            # Try to create a client to check credentials
            boto3.client('secretsmanager', region_name=self.region_name)
            return True
        except ImportError:
            return False
        except Exception:
            return False


class SecretsManager:
    """
    Main secrets manager that tries providers in order of preference
    """
    
    def __init__(self, aws_region: str = "us-east-1"):
        self.providers = [
            AWSSecretsProvider(aws_region),
            DockerSecretsProvider(),
            EnvironmentSecretsProvider()
        ]
        self._secrets_cache: Dict[str, Dict[str, Any]] = {}
    
    async def get_secrets(self, secret_name: str = "default") -> Dict[str, Any]:
        """
        Get secrets from the first available provider
        """
        # Check cache first
        if secret_name in self._secrets_cache:
            return self._secrets_cache[secret_name]
        
        # Try providers in order
        for provider in self.providers:
            if provider.is_available():
                try:
                    secrets = await provider.get_secret(secret_name)
                    if secrets:
                        logger.info(f"Loaded secrets using {provider.__class__.__name__}")
                        
                        # Validate required secrets
                        self._validate_secrets(secrets)
                        
                        # Cache the secrets
                        self._secrets_cache[secret_name] = secrets
                        return secrets
                        
                except Exception as e:
                    logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
                    continue
        
        logger.error("No secrets provider was able to load secrets")
        return {}
    
    def _validate_secrets(self, secrets: Dict[str, Any]) -> None:
        """Validate that critical secrets are present and secure"""
        required_secrets = ["jwt_secret_key"]
        
        for secret_key in required_secrets:
            if secret_key not in secrets:
                raise ValueError(f"Required secret '{secret_key}' not found")
            
            secret_value = secrets[secret_key]
            
            # Validate JWT secret
            if secret_key == "jwt_secret_key":
                if not secret_value or len(secret_value) < 32:
                    raise ValueError("JWT secret key must be at least 32 characters long")
                
                # Check for common weak secrets
                weak_secrets = [
                    "your-super-secret-jwt-key-change-this-in-production",
                    "secret",
                    "password",
                    "123456",
                    "change-me"
                ]
                
                if secret_value.lower() in [s.lower() for s in weak_secrets]:
                    raise ValueError("JWT secret key appears to be a default/weak value")
    
    def clear_cache(self):
        """Clear secrets cache (useful for testing)"""
        self._secrets_cache.clear()


# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


def init_secrets_manager(aws_region: str = "us-east-1") -> SecretsManager:
    """Initialize global secrets manager"""
    global _secrets_manager
    _secrets_manager = SecretsManager(aws_region)
    return _secrets_manager


def get_secrets_manager() -> SecretsManager:
    """Get global secrets manager instance"""
    if _secrets_manager is None:
        raise RuntimeError("Secrets manager not initialized. Call init_secrets_manager() first.")
    return _secrets_manager


async def get_secrets(secret_name: str = "default") -> Dict[str, Any]:
    """Convenience function to get secrets"""
    manager = get_secrets_manager()
    return await manager.get_secrets(secret_name)