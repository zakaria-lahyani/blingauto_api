from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.features.auth.ports import (
    User,
    UserRole,
    UserStatus,
    PasswordResetToken,
    EmailVerificationToken,
    RefreshToken,
    IUserRepository,
    IPasswordResetTokenRepository,
    IEmailVerificationTokenRepository,
    IRefreshTokenRepository,
)
from app.features.auth.adapters.models import (
    UserModel,
    PasswordResetTokenModel,
    EmailVerificationTokenModel,
    RefreshTokenModel,
)


class UserRepository(IUserRepository):
    """SQLAlchemy implementation of user repository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def _to_domain(self, model: UserModel) -> User:
        """Convert database model to domain entity."""
        return User(
            id=model.id,
            email=model.email,
            first_name=model.first_name,
            last_name=model.last_name,
            hashed_password=model.hashed_password,
            role=UserRole(model.role),
            status=UserStatus(model.status),
            phone_number=model.phone_number,
            email_verified=model.email_verified,
            email_verified_at=model.email_verified_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login_at=model.last_login_at,
            failed_login_attempts=model.failed_login_attempts,
            locked_until=model.locked_until,
            password_changed_at=model.password_changed_at,
        )
    
    def _to_model(self, user: User) -> UserModel:
        """Convert domain entity to database model."""
        return UserModel(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            hashed_password=user.hashed_password,
            role=user.role.value,
            status=user.status.value,
            phone_number=user.phone_number,
            email_verified=user.email_verified,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
            failed_login_attempts=user.failed_login_attempts,
            locked_until=user.locked_until,
            password_changed_at=user.password_changed_at,
        )
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_domain(model) if model else None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        model = (
            self.session.query(UserModel)
            .filter(UserModel.email == email.lower())
            .first()
        )
        return self._to_domain(model) if model else None
    
    async def create(self, user: User) -> User:
        """Create a new user."""
        model = self._to_model(user)
        self.session.add(model)
        self.session.flush()  # Get the ID
        return self._to_domain(model)
    
    async def update(self, user: User) -> User:
        """Update an existing user."""
        model = self.session.query(UserModel).filter(UserModel.id == user.id).first()
        if not model:
            raise ValueError(f"User {user.id} not found")
        
        # Update fields
        model.email = user.email
        model.first_name = user.first_name
        model.last_name = user.last_name
        model.hashed_password = user.hashed_password
        model.role = user.role.value
        model.status = user.status.value
        model.phone_number = user.phone_number
        model.email_verified = user.email_verified
        model.email_verified_at = user.email_verified_at
        model.updated_at = user.updated_at
        model.last_login_at = user.last_login_at
        model.failed_login_attempts = user.failed_login_attempts
        model.locked_until = user.locked_until
        model.password_changed_at = user.password_changed_at
        
        self.session.flush()
        return self._to_domain(model)
    
    async def delete(self, user_id: str) -> bool:
        """Delete a user."""
        model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        if not model:
            return False
        
        self.session.delete(model)
        return True
    
    async def list(
        self,
        offset: int = 0,
        limit: int = 20,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[User]:
        """List users with optional filters."""
        query = self.session.query(UserModel)
        
        if role:
            query = query.filter(UserModel.role == role)
        if status:
            query = query.filter(UserModel.status == status)
        
        models = query.offset(offset).limit(limit).all()
        return [self._to_domain(model) for model in models]
    
    async def count(
        self,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count users with optional filters."""
        query = self.session.query(UserModel)
        
        if role:
            query = query.filter(UserModel.role == role)
        if status:
            query = query.filter(UserModel.status == status)
        
        return query.count()
    
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        count = (
            self.session.query(UserModel)
            .filter(UserModel.email == email.lower())
            .count()
        )
        return count > 0


class PasswordResetTokenRepository(IPasswordResetTokenRepository):
    """SQLAlchemy implementation of password reset token repository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def _to_domain(self, model: PasswordResetTokenModel) -> PasswordResetToken:
        """Convert database model to domain entity."""
        return PasswordResetToken(
            token=model.token,
            user_id=model.user_id,
            created_at=model.created_at,
            expires_at=model.expires_at,
            used=model.used,
        )
    
    def _to_model(self, token: PasswordResetToken) -> PasswordResetTokenModel:
        """Convert domain entity to database model."""
        return PasswordResetTokenModel(
            token=token.token,
            user_id=token.user_id,
            created_at=token.created_at,
            expires_at=token.expires_at,
            used=token.used,
        )
    
    async def create(self, token: PasswordResetToken) -> PasswordResetToken:
        """Create a new password reset token."""
        model = self._to_model(token)
        self.session.add(model)
        self.session.flush()
        return self._to_domain(model)
    
    async def get_by_token(self, token: str) -> Optional[PasswordResetToken]:
        """Get password reset token by token string."""
        model = (
            self.session.query(PasswordResetTokenModel)
            .filter(PasswordResetTokenModel.token == token)
            .first()
        )
        return self._to_domain(model) if model else None
    
    async def mark_as_used(self, token: str) -> bool:
        """Mark token as used."""
        model = (
            self.session.query(PasswordResetTokenModel)
            .filter(PasswordResetTokenModel.token == token)
            .first()
        )
        if not model:
            return False
        
        model.used = True
        self.session.flush()
        return True
    
    async def delete_expired(self) -> int:
        """Delete expired tokens."""
        from datetime import datetime
        
        count = (
            self.session.query(PasswordResetTokenModel)
            .filter(PasswordResetTokenModel.expires_at < datetime.utcnow())
            .count()
        )
        
        self.session.query(PasswordResetTokenModel).filter(
            PasswordResetTokenModel.expires_at < datetime.utcnow()
        ).delete()
        
        return count


class EmailVerificationTokenRepository(IEmailVerificationTokenRepository):
    """SQLAlchemy implementation of email verification token repository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def _to_domain(self, model: EmailVerificationTokenModel) -> EmailVerificationToken:
        """Convert database model to domain entity."""
        return EmailVerificationToken(
            token=model.token,
            user_id=model.user_id,
            email=model.email,
            created_at=model.created_at,
            expires_at=model.expires_at,
            used=model.used,
        )
    
    def _to_model(self, token: EmailVerificationToken) -> EmailVerificationTokenModel:
        """Convert domain entity to database model."""
        return EmailVerificationTokenModel(
            token=token.token,
            user_id=token.user_id,
            email=token.email,
            created_at=token.created_at,
            expires_at=token.expires_at,
            used=token.used,
        )
    
    async def create(self, token: EmailVerificationToken) -> EmailVerificationToken:
        """Create a new email verification token."""
        model = self._to_model(token)
        self.session.add(model)
        self.session.flush()
        return self._to_domain(model)
    
    async def get_by_token(self, token: str) -> Optional[EmailVerificationToken]:
        """Get email verification token by token string."""
        model = (
            self.session.query(EmailVerificationTokenModel)
            .filter(EmailVerificationTokenModel.token == token)
            .first()
        )
        return self._to_domain(model) if model else None
    
    async def mark_as_used(self, token: str) -> bool:
        """Mark token as used."""
        model = (
            self.session.query(EmailVerificationTokenModel)
            .filter(EmailVerificationTokenModel.token == token)
            .first()
        )
        if not model:
            return False
        
        model.used = True
        self.session.flush()
        return True
    
    async def delete_expired(self) -> int:
        """Delete expired tokens."""
        from datetime import datetime
        
        count = (
            self.session.query(EmailVerificationTokenModel)
            .filter(EmailVerificationTokenModel.expires_at < datetime.utcnow())
            .count()
        )
        
        self.session.query(EmailVerificationTokenModel).filter(
            EmailVerificationTokenModel.expires_at < datetime.utcnow()
        ).delete()
        
        return count


class RefreshTokenRepository(IRefreshTokenRepository):
    """SQLAlchemy implementation of refresh token repository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def _to_domain(self, model: RefreshTokenModel) -> RefreshToken:
        """Convert database model to domain entity."""
        return RefreshToken(
            token=model.token,
            user_id=model.user_id,
            created_at=model.created_at,
            expires_at=model.expires_at,
            revoked=model.revoked,
        )
    
    def _to_model(self, token: RefreshToken) -> RefreshTokenModel:
        """Convert domain entity to database model."""
        return RefreshTokenModel(
            token=token.token,
            user_id=token.user_id,
            created_at=token.created_at,
            expires_at=token.expires_at,
            revoked=token.revoked,
        )
    
    async def create(self, token: RefreshToken) -> RefreshToken:
        """Create a new refresh token."""
        model = self._to_model(token)
        self.session.add(model)
        self.session.flush()
        return self._to_domain(model)
    
    async def get_by_token(self, token: str) -> Optional[RefreshToken]:
        """Get refresh token by token string."""
        model = (
            self.session.query(RefreshTokenModel)
            .filter(RefreshTokenModel.token == token)
            .first()
        )
        return self._to_domain(model) if model else None
    
    async def revoke(self, token: str) -> bool:
        """Revoke a refresh token."""
        model = (
            self.session.query(RefreshTokenModel)
            .filter(RefreshTokenModel.token == token)
            .first()
        )
        if not model:
            return False
        
        model.revoked = True
        self.session.flush()
        return True
    
    async def revoke_all_for_user(self, user_id: str) -> int:
        """Revoke all refresh tokens for a user."""
        count = (
            self.session.query(RefreshTokenModel)
            .filter(RefreshTokenModel.user_id == user_id)
            .filter(RefreshTokenModel.revoked == False)
            .count()
        )
        
        self.session.query(RefreshTokenModel).filter(
            RefreshTokenModel.user_id == user_id
        ).filter(RefreshTokenModel.revoked == False).update({"revoked": True})
        
        return count
    
    async def delete_expired(self) -> int:
        """Delete expired tokens."""
        from datetime import datetime
        
        count = (
            self.session.query(RefreshTokenModel)
            .filter(RefreshTokenModel.expires_at < datetime.utcnow())
            .count()
        )
        
        self.session.query(RefreshTokenModel).filter(
            RefreshTokenModel.expires_at < datetime.utcnow()
        ).delete()
        
        return count