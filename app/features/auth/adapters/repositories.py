from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func

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

# Note: SQLAlchemy relationship resolution is handled at the application level
# by importing all models during app startup in main.py


class UserRepository(IUserRepository):
    """Async SQLAlchemy implementation of user repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, model: UserModel) -> User:
        """Convert database model to domain entity."""
        # Check if the model has the correct field names
        password_hash = getattr(model, 'password_hash', None) or getattr(model, 'hashed_password', None)
        is_active = getattr(model, 'is_active', None)
        is_email_verified = getattr(model, 'is_email_verified', None) or getattr(model, 'email_verified', None)

        # Convert is_active boolean to UserStatus enum
        if is_active is not None:
            status = UserStatus.ACTIVE if is_active else UserStatus.INACTIVE
        else:
            # Fallback to status field if it exists
            status_value = getattr(model, 'status', 'active')
            status = UserStatus(status_value)

        return User(
            id=model.id,
            email=model.email,
            first_name=model.first_name,
            last_name=model.last_name,
            hashed_password=password_hash,
            role=UserRole(model.role),
            status=status,
            phone_number=getattr(model, 'phone_number', None),
            email_verified=is_email_verified if is_email_verified is not None else False,
            email_verified_at=getattr(model, 'email_verified_at', None),
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login_at=getattr(model, 'last_login_at', None),
            failed_login_attempts=getattr(model, 'failed_login_attempts', 0),
            locked_until=getattr(model, 'locked_until', None),
            password_changed_at=getattr(model, 'password_changed_at', None)
        )

    def _to_model(self, user: User) -> UserModel:
        """Convert domain entity to database model."""
        return UserModel(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            password_hash=user.hashed_password,
            role=user.role.value,
            is_active=(user.status == UserStatus.ACTIVE),
            phone_number=user.phone_number,
            is_email_verified=user.email_verified,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
            failed_login_attempts=user.failed_login_attempts,
            locked_until=user.locked_until,
            password_changed_at=user.password_changed_at
        )

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(UserModel).where(UserModel.email == email.lower())
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def create(self, user: User) -> User:
        """Create a new user."""
        model = self._to_model(user)
        self.session.add(model)
        await self.session.flush()
        # Refresh to load any database-generated values and prevent lazy loading issues
        await self.session.refresh(model)
        return self._to_domain(model)

    async def update(self, user: User) -> User:
        """Update an existing user."""
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"User {user.id} not found")

        # Update fields
        model.email = user.email
        model.first_name = user.first_name
        model.last_name = user.last_name
        model.password_hash = user.hashed_password
        model.role = user.role.value
        model.is_active = (user.status == UserStatus.ACTIVE)
        model.phone_number = user.phone_number
        model.is_email_verified = user.email_verified
        model.email_verified_at = user.email_verified_at
        model.updated_at = user.updated_at
        model.last_login_at = user.last_login_at
        model.failed_login_attempts = user.failed_login_attempts
        model.locked_until = user.locked_until
        model.password_changed_at = user.password_changed_at

        await self.session.flush()
        # Refresh to load any database-generated values and prevent lazy loading issues
        await self.session.refresh(model)
        return self._to_domain(model)

    async def delete(self, user_id: str) -> bool:
        """Delete a user."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self.session.delete(model)
        return True

    async def list(
        self,
        offset: int = 0,
        limit: int = 20,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[User]:
        """List users with optional filters."""
        stmt = select(UserModel)

        if role:
            stmt = stmt.where(UserModel.role == role)
        if status:
            # Convert status to is_active boolean
            is_active = (status == 'active')
            stmt = stmt.where(UserModel.is_active == is_active)

        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def count(
        self,
        role: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count users with optional filters."""
        stmt = select(func.count()).select_from(UserModel)

        if role:
            stmt = stmt.where(UserModel.role == role)
        if status:
            is_active = (status == 'active')
            stmt = stmt.where(UserModel.is_active == is_active)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        stmt = select(func.count()).select_from(UserModel).where(
            UserModel.email == email.lower()
        )
        result = await self.session.execute(stmt)
        count = result.scalar_one()
        return count > 0


class PasswordResetTokenRepository(IPasswordResetTokenRepository):
    """Async SQLAlchemy implementation of password reset token repository."""

    def __init__(self, session: AsyncSession):
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
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def get_by_token(self, token: str) -> Optional[PasswordResetToken]:
        """Get password reset token by token string."""
        stmt = select(PasswordResetTokenModel).where(
            PasswordResetTokenModel.token == token
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def mark_as_used(self, token: str) -> bool:
        """Mark token as used."""
        stmt = select(PasswordResetTokenModel).where(
            PasswordResetTokenModel.token == token
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        model.used = True
        await self.session.flush()
        await self.session.refresh(model)
        return True

    async def delete_expired(self) -> int:
        """Delete expired tokens."""
        from datetime import datetime

        # Count first
        count_stmt = select(func.count()).select_from(PasswordResetTokenModel).where(
            PasswordResetTokenModel.expires_at < datetime.utcnow()
        )
        result = await self.session.execute(count_stmt)
        count = result.scalar_one()

        # Then delete
        delete_stmt = delete(PasswordResetTokenModel).where(
            PasswordResetTokenModel.expires_at < datetime.utcnow()
        )
        await self.session.execute(delete_stmt)

        return count


class EmailVerificationTokenRepository(IEmailVerificationTokenRepository):
    """Async SQLAlchemy implementation of email verification token repository."""

    def __init__(self, session: AsyncSession):
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
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def get_by_token(self, token: str) -> Optional[EmailVerificationToken]:
        """Get email verification token by token string."""
        stmt = select(EmailVerificationTokenModel).where(
            EmailVerificationTokenModel.token == token
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def mark_as_used(self, token: str) -> bool:
        """Mark token as used."""
        stmt = select(EmailVerificationTokenModel).where(
            EmailVerificationTokenModel.token == token
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        model.used = True
        await self.session.flush()
        await self.session.refresh(model)
        return True

    async def delete_expired(self) -> int:
        """Delete expired tokens."""
        from datetime import datetime

        # Count first
        count_stmt = select(func.count()).select_from(EmailVerificationTokenModel).where(
            EmailVerificationTokenModel.expires_at < datetime.utcnow()
        )
        result = await self.session.execute(count_stmt)
        count = result.scalar_one()

        # Then delete
        delete_stmt = delete(EmailVerificationTokenModel).where(
            EmailVerificationTokenModel.expires_at < datetime.utcnow()
        )
        await self.session.execute(delete_stmt)

        return count


class RefreshTokenRepository(IRefreshTokenRepository):
    """Async SQLAlchemy implementation of refresh token repository."""

    def __init__(self, session: AsyncSession):
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
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def get_by_token(self, token: str) -> Optional[RefreshToken]:
        """Get refresh token by token string."""
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.token == token)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def revoke(self, token: str) -> bool:
        """Revoke a refresh token."""
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.token == token)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        model.revoked = True
        await self.session.flush()
        await self.session.refresh(model)
        return True

    async def revoke_all_for_user(self, user_id: str) -> int:
        """Revoke all refresh tokens for a user."""
        # Count first
        count_stmt = select(func.count()).select_from(RefreshTokenModel).where(
            RefreshTokenModel.user_id == user_id,
            RefreshTokenModel.revoked == False
        )
        result = await self.session.execute(count_stmt)
        count = result.scalar_one()

        # Then update
        update_stmt = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id, RefreshTokenModel.revoked == False)
            .values(revoked=True)
        )
        await self.session.execute(update_stmt)

        return count

    async def delete_expired(self) -> int:
        """Delete expired tokens."""
        from datetime import datetime

        # Count first
        count_stmt = select(func.count()).select_from(RefreshTokenModel).where(
            RefreshTokenModel.expires_at < datetime.utcnow()
        )
        result = await self.session.execute(count_stmt)
        count = result.scalar_one()

        # Then delete
        delete_stmt = delete(RefreshTokenModel).where(
            RefreshTokenModel.expires_at < datetime.utcnow()
        )
        await self.session.execute(delete_stmt)

        return count
