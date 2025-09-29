"""
Auth database models
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from typing import Optional

from src.shared.database import Base
from src.shared.utils.timestamp import db_utc_timestamp
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole


class AuthUserModel(Base):
    """Auth user database model"""
    
    __tablename__ = "auth_users"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    role = Column(String(20), nullable=False, default=AuthRole.CLIENT.value)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Email verification
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime(timezone=True))
    email_verification_token = Column(String(255))
    email_verification_expires = Column(DateTime(timezone=True))
    
    # Password reset
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime(timezone=True))
    password_reset_requested_at = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))
    
    # Account lockout
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    lockout_count = Column(Integer, default=0)
    last_failed_login = Column(DateTime(timezone=True))
    
    # Session management
    last_login = Column(DateTime(timezone=True))
    refresh_tokens = Column(JSON, default=list)
    
    # Timestamps - using standardized UTC timestamps
    created_at = Column(DateTime(timezone=True), server_default=db_utc_timestamp(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=db_utc_timestamp(), onupdate=db_utc_timestamp(), nullable=False)
    
    # Relationships - Temporarily disabled until VehicleModel and BookingModel are properly configured
    # TODO: Re-enable once vehicle and booking models are available and properly imported
    # vehicles = relationship(
    #     "VehicleModel", 
    #     back_populates="user", 
    #     cascade="all, delete-orphan",
    #     lazy="select"
    # )
    # 
    # bookings = relationship(
    #     "BookingModel", 
    #     back_populates="customer",
    #     cascade="all, delete-orphan",
    #     lazy="select"
    # )
    
    def to_entity(self) -> AuthUser:
        """Convert model to domain entity"""
        return AuthUser(
            id=self.id,
            email=self.email,
            password_hash=self.password_hash,
            first_name=self.first_name,
            last_name=self.last_name,
            phone=self.phone,
            role=AuthRole(self.role),
            is_active=self.is_active,
            email_verified=self.email_verified,
            email_verified_at=self.email_verified_at,
            email_verification_token=self.email_verification_token,
            email_verification_expires=self.email_verification_expires,
            password_reset_token=self.password_reset_token,
            password_reset_expires=self.password_reset_expires,
            password_reset_requested_at=self.password_reset_requested_at,
            password_changed_at=self.password_changed_at,
            failed_login_attempts=self.failed_login_attempts or 0,
            locked_until=self.locked_until,
            lockout_count=self.lockout_count or 0,
            last_failed_login=self.last_failed_login,
            last_login=self.last_login,
            refresh_tokens=self.refresh_tokens or [],
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    @classmethod
    def from_entity(cls, entity: AuthUser) -> "AuthUserModel":
        """Create model from domain entity"""
        return cls(
            id=entity.id,
            email=entity.email,
            password_hash=entity.password_hash,
            first_name=entity.first_name,
            last_name=entity.last_name,
            phone=entity.phone,
            role=entity.role.value,
            is_active=entity.is_active,
            email_verified=entity.email_verified,
            email_verified_at=entity.email_verified_at,
            email_verification_token=entity.email_verification_token,
            email_verification_expires=entity.email_verification_expires,
            password_reset_token=entity.password_reset_token,
            password_reset_expires=entity.password_reset_expires,
            password_reset_requested_at=entity.password_reset_requested_at,
            password_changed_at=entity.password_changed_at,
            failed_login_attempts=entity.failed_login_attempts,
            locked_until=entity.locked_until,
            lockout_count=entity.lockout_count,
            last_failed_login=entity.last_failed_login,
            last_login=entity.last_login,
            refresh_tokens=entity.refresh_tokens,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    def update_from_entity(self, entity: AuthUser) -> None:
        """Update model from entity"""
        self.email = entity.email
        self.password_hash = entity.password_hash
        self.first_name = entity.first_name
        self.last_name = entity.last_name
        self.phone = entity.phone
        self.role = entity.role.value
        self.is_active = entity.is_active
        self.email_verified = entity.email_verified
        self.email_verified_at = entity.email_verified_at
        self.email_verification_token = entity.email_verification_token
        self.email_verification_expires = entity.email_verification_expires
        self.password_reset_token = entity.password_reset_token
        self.password_reset_expires = entity.password_reset_expires
        self.password_reset_requested_at = entity.password_reset_requested_at
        self.password_changed_at = entity.password_changed_at
        self.failed_login_attempts = entity.failed_login_attempts
        self.locked_until = entity.locked_until
        self.lockout_count = entity.lockout_count
        self.last_failed_login = entity.last_failed_login
        self.last_login = entity.last_login
        self.refresh_tokens = entity.refresh_tokens
        self.updated_at = entity.updated_at