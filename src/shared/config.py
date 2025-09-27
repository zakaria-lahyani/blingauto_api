"""
Global Application Configuration

Manages configuration settings that affect the entire application,
including middleware, CORS, security, and infrastructure settings.
"""
import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class SecurityConfig(BaseSettings):
    """Security-related configuration"""
    
    # HSTS (HTTP Strict Transport Security)
    enable_hsts: bool = Field(default=True, description="Enable HSTS headers")
    hsts_max_age: int = Field(default=31536000, description="HSTS max age in seconds")
    hsts_include_subdomains: bool = Field(default=True, description="Include subdomains in HSTS")
    
    # Content Security Policy
    enable_csp: bool = Field(default=True, description="Enable Content Security Policy")
    csp_policy: str = Field(
        default="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
        description="CSP policy string"
    )
    
    # Other security headers
    enable_x_frame_options: bool = Field(default=True)
    enable_x_content_type_options: bool = Field(default=True)
    enable_x_xss_protection: bool = Field(default=True)
    
    class Config:
        env_prefix = "SECURITY_"
        extra = "ignore"


class CORSConfig(BaseSettings):
    """CORS configuration"""
    
    # Origins
    allow_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )
    allow_all_origins: bool = Field(default=False, description="Allow all origins (dev only)")
    
    # Methods and headers
    allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        description="Allowed HTTP methods"
    )
    allow_headers: List[str] = Field(
        default=["*"],
        description="Allowed headers"
    )
    allow_credentials: bool = Field(default=True, description="Allow credentials")
    
    # Response headers to expose
    expose_headers: List[str] = Field(
        default=["X-Total-Count", "X-Page-Count", "X-Process-Time"],
        description="Headers to expose to browser"
    )
    
    class Config:
        env_prefix = "CORS_"
        extra = "ignore"


class LoggingConfig(BaseSettings):
    """Logging configuration"""
    
    # Request logging
    enable_request_logging: bool = Field(default=True, description="Enable request logging")
    log_request_body: bool = Field(default=False, description="Log request body (sensitive)")
    log_response_body: bool = Field(default=False, description="Log response body (sensitive)")
    
    # Performance logging
    log_slow_requests: bool = Field(default=True, description="Log slow requests")
    slow_request_threshold: float = Field(default=1.0, description="Slow request threshold in seconds")
    
    # Log level
    log_level: str = Field(default="INFO", description="Log level")
    
    class Config:
        env_prefix = "LOGGING_"
        extra = "ignore"


class CompressionConfig(BaseSettings):
    """Response compression configuration"""
    
    enable_gzip: bool = Field(default=True, description="Enable GZIP compression")
    gzip_minimum_size: int = Field(default=1000, description="Minimum size for compression")
    
    class Config:
        env_prefix = "COMPRESSION_"
        extra = "ignore"


class GlobalConfig(BaseSettings):
    """Global application configuration"""
    
    # Environment
    environment: str = Field(default="development", description="Application environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Host validation
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1", "0.0.0.0"],
        description="Allowed hosts"
    )
    
    # Sub-configurations
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    cors: CORSConfig = Field(default_factory=CORSConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    compression: CompressionConfig = Field(default_factory=CompressionConfig)
    
    class Config:
        env_prefix = "GLOBAL_"
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() == "development"
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins based on environment"""
        if self.cors.allow_all_origins and self.is_development:
            return ["*"]
        return self.cors.allow_origins