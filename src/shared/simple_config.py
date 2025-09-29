"""
Configuration simplifiée centralisée
"""
import os
from typing import Optional, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """Configuration principale de l'application"""
    
    # Base
    app_name: str = "Car Wash API"
    version: str = "3.1.0"
    environment: str = Field(default="development", env="GLOBAL_ENVIRONMENT")
    debug: bool = Field(default=False, env="GLOBAL_DEBUG")
    
    # Database
    database_url: str = Field(env="DATABASE_URL")
    
    # Auth
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="AUTH_JWT_SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="AUTH_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Cache/Redis
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # Email
    email_provider: str = Field(default="console", env="AUTH_EMAIL_PROVIDER")
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    
    # Features
    features_enabled: str = Field(default="auth,vehicles,services,bookings,scheduling", env="FEATURES_ENABLED")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables

    @property
    def enabled_features(self) -> list[str]:
        """Liste des features activées"""
        return [f.strip() for f in self.features_enabled.split(",")]
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Vérifie si une feature est activée"""
        return feature in self.enabled_features
    
    def get_feature_config(self, feature: str) -> Dict[str, Any]:
        """Configuration spécifique à une feature"""
        config = {}
        prefix = f"{feature.upper()}_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                config[config_key] = value
        
        return config


# Instance globale
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Récupère la configuration globale"""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def init_config(**kwargs) -> AppConfig:
    """Initialise la configuration avec des valeurs personnalisées"""
    global _config
    _config = AppConfig(**kwargs)
    return _config