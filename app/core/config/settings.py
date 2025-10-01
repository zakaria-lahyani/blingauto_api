from typing import Optional, Literal, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, BeforeValidator
from typing_extensions import Annotated


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from .env
        env_parse_enums=True,  # Parse enums from env vars
    )

    # Environment
    environment: Literal["development", "staging", "production"] = Field(
        default="development", alias="ENVIRONMENT"
    )

    # Application
    app_name: str = Field(default="BlingAuto API", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    workers: int = Field(default=1, alias="WORKERS")

    # Database
    database_url: str = Field(
        default="sqlite:///./carwash.db", alias="DATABASE_URL"
    )
    database_pool_size: int = Field(default=5, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, alias="DATABASE_POOL_TIMEOUT")
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")

    # Redis
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    redis_max_connections: int = Field(default=10, alias="REDIS_MAX_CONNECTIONS")
    redis_ttl: int = Field(default=300, alias="REDIS_TTL")

    # Security
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        alias="SECRET_KEY",
    )
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(
        default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS"
    )
    password_reset_token_expire_hours: int = Field(
        default=1, alias="PASSWORD_RESET_TOKEN_EXPIRE_HOURS"
    )
    email_verification_token_expire_hours: int = Field(
        default=24, alias="EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS"
    )

    # Email
    smtp_host: Optional[str] = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(
        default="noreply@blingauto.com", alias="SMTP_FROM_EMAIL"
    )
    smtp_from_name: str = Field(default="BlingAuto", alias="SMTP_FROM_NAME")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    frontend_url: str = Field(
        default="http://localhost:3000", alias="FRONTEND_URL"
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_requests_per_minute: int = Field(
        default=60, alias="RATE_LIMIT_REQUESTS_PER_MINUTE"
    )
    rate_limit_requests_per_hour: int = Field(
        default=1000, alias="RATE_LIMIT_REQUESTS_PER_HOUR"
    )

    # CORS - for lists in env vars, use JSON format: ["item1","item2"]
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        alias="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(
        default=True, alias="CORS_ALLOW_CREDENTIALS"
    )
    cors_allow_methods: list[str] = Field(
        default_factory=lambda: ["*"],
        alias="CORS_ALLOW_METHODS"
    )
    cors_allow_headers: list[str] = Field(
        default_factory=lambda: ["*"],
        alias="CORS_ALLOW_HEADERS"
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        alias="LOG_FORMAT",
    )

    # Business Rules
    max_services_per_booking: int = Field(
        default=10, alias="MAX_SERVICES_PER_BOOKING"
    )
    min_booking_duration_minutes: int = Field(
        default=30, alias="MIN_BOOKING_DURATION_MINUTES"
    )
    max_booking_duration_minutes: int = Field(
        default=240, alias="MAX_BOOKING_DURATION_MINUTES"
    )
    max_booking_advance_days: int = Field(
        default=90, alias="MAX_BOOKING_ADVANCE_DAYS"
    )
    min_booking_advance_hours: int = Field(
        default=2, alias="MIN_BOOKING_ADVANCE_HOURS"
    )
    booking_slot_duration_minutes: int = Field(
        default=30, alias="BOOKING_SLOT_DURATION_MINUTES"
    )
    booking_buffer_minutes: int = Field(
        default=15, alias="BOOKING_BUFFER_MINUTES"
    )

    # Account Security
    max_login_attempts: int = Field(default=5, alias="MAX_LOGIN_ATTEMPTS")
    lockout_duration_minutes: int = Field(
        default=30, alias="LOCKOUT_DURATION_MINUTES"
    )
    password_min_length: int = Field(default=8, alias="PASSWORD_MIN_LENGTH")
    password_max_length: int = Field(default=128, alias="PASSWORD_MAX_LENGTH")

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


settings = Settings()