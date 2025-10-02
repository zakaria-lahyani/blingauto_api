from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base, TimestampMixin


class UserModel(Base, TimestampMixin):
    """User database model."""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="client", index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    phone_number = Column(String(20), nullable=True)
    is_email_verified = Column(Boolean, nullable=False, default=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships - using lazy='noload' to prevent automatic loading in async context
    # These relationships can be accessed using explicit queries when needed
    vehicles = relationship("Vehicle", back_populates="customer", cascade="all, delete-orphan", lazy='noload')
    bookings = relationship("Booking", back_populates="customer", lazy='noload')
    password_reset_tokens = relationship("PasswordResetTokenModel", cascade="all, delete-orphan", lazy='noload')
    email_verification_tokens = relationship("EmailVerificationTokenModel", cascade="all, delete-orphan", lazy='noload')
    refresh_tokens = relationship("RefreshTokenModel", cascade="all, delete-orphan", lazy='noload')

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class PasswordResetTokenModel(Base):
    """Password reset token database model."""
    
    __tablename__ = "password_reset_tokens"
    
    token = Column(String(255), primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    
    def __repr__(self):
        return f"<PasswordResetToken(token={self.token}, user_id={self.user_id})>"


class EmailVerificationTokenModel(Base):
    """Email verification token database model."""
    
    __tablename__ = "email_verification_tokens"
    
    token = Column(String(255), primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    
    def __repr__(self):
        return f"<EmailVerificationToken(token={self.token}, user_id={self.user_id})>"


class RefreshTokenModel(Base):
    """Refresh token database model."""
    
    __tablename__ = "refresh_tokens"
    
    token = Column(String(255), primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    
    def __repr__(self):
        return f"<RefreshToken(token={self.token}, user_id={self.user_id})>"