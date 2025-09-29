"""
Auth repository implementations
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.shared.database.base import BaseRepository
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole
from src.features.auth.infrastructure.database.models import AuthUserModel


class AuthUserRepository(BaseRepository[AuthUser, AuthUserModel]):
    """Repository for auth users"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, AuthUserModel)
    
    async def create(self, user: AuthUser) -> AuthUser:
        """Create new user"""
        model = AuthUserModel.from_entity(user)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()
    
    async def get(self, user_id: UUID) -> Optional[AuthUser]:
        """Get user by ID"""
        stmt = select(AuthUserModel).where(AuthUserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None
    
    async def get_by_id(self, user_id: UUID) -> Optional[AuthUser]:
        """Get user by ID - backwards compatibility"""
        return await self.get(user_id)
    
    async def get_by_email(self, email: str) -> Optional[AuthUser]:
        """Get user by email"""
        stmt = select(AuthUserModel).where(AuthUserModel.email == email)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None
    
    async def get_by_phone(self, phone: str) -> Optional[AuthUser]:
        """Get user by phone number"""
        stmt = select(AuthUserModel).where(AuthUserModel.phone == phone)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None
    
    async def update(self, user: AuthUser) -> AuthUser:
        """Update user"""
        stmt = select(AuthUserModel).where(AuthUserModel.id == user.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError(f"User not found: {user.id}")
        
        model.update_from_entity(user)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()
    
    async def delete(self, user_id: UUID) -> bool:
        """Delete user"""
        stmt = select(AuthUserModel).where(AuthUserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self.session.delete(model)
        return True
    
    async def list(self, limit: int = 100, offset: int = 0) -> List[AuthUser]:
        """List all users"""
        stmt = select(AuthUserModel).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [model.to_entity() for model in models]
    
    async def list_by_role(self, role: AuthRole, limit: int = 100, offset: int = 0) -> List[AuthUser]:
        """List users by role"""
        stmt = (
            select(AuthUserModel)
            .where(AuthUserModel.role == role.value)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [model.to_entity() for model in models]
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[AuthUser]:
        """List all users - backwards compatibility"""
        return await self.list(limit, offset)
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email"""
        user = await self.get_by_email(email)
        return user is not None
    
    async def count_by_role(self, role: AuthRole) -> int:
        """Count users by role"""
        stmt = select(AuthUserModel).where(AuthUserModel.role == role.value)
        result = await self.session.execute(stmt)
        return len(result.scalars().all())
    
    async def get_by_verification_token(self, token: str) -> Optional[AuthUser]:
        """Get user by email verification token"""
        stmt = select(AuthUserModel).where(
            AuthUserModel.email_verification_token == token
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None
    
    async def get_by_reset_token(self, token: str) -> Optional[AuthUser]:
        """Get user by password reset token"""
        stmt = select(AuthUserModel).where(
            AuthUserModel.password_reset_token == token
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None