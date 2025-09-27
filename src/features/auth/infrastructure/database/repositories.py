"""
Auth repository implementations
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.shared.database import get_db_session
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole
from src.features.auth.infrastructure.database.models import AuthUserModel


class AuthUserRepository:
    """Repository for auth users"""
    
    def __init__(self):
        pass
    
    async def create(self, user: AuthUser) -> AuthUser:
        """Create new user"""
        async with get_db_session() as session:
            model = AuthUserModel.from_entity(user)
            session.add(model)
            await session.flush()
            await session.refresh(model)
            return model.to_entity()
    
    async def get_by_id(self, user_id: UUID) -> Optional[AuthUser]:
        """Get user by ID"""
        async with get_db_session() as session:
            stmt = select(AuthUserModel).where(AuthUserModel.id == user_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return model.to_entity() if model else None
    
    async def get_by_email(self, email: str) -> Optional[AuthUser]:
        """Get user by email"""
        async with get_db_session() as session:
            stmt = select(AuthUserModel).where(AuthUserModel.email == email)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return model.to_entity() if model else None
    
    async def update(self, user: AuthUser) -> AuthUser:
        """Update user"""
        async with get_db_session() as session:
            stmt = select(AuthUserModel).where(AuthUserModel.id == user.id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                raise ValueError(f"User not found: {user.id}")
            
            model.update_from_entity(user)
            await session.flush()
            await session.refresh(model)
            return model.to_entity()
    
    async def delete(self, user_id: UUID) -> bool:
        """Delete user"""
        async with get_db_session() as session:
            stmt = select(AuthUserModel).where(AuthUserModel.id == user_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return False
            
            await session.delete(model)
            return True
    
    async def list_by_role(self, role: AuthRole, limit: int = 100, offset: int = 0) -> List[AuthUser]:
        """List users by role"""
        async with get_db_session() as session:
            stmt = (
                select(AuthUserModel)
                .where(AuthUserModel.role == role.value)
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [model.to_entity() for model in models]
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[AuthUser]:
        """List all users"""
        async with get_db_session() as session:
            stmt = select(AuthUserModel).limit(limit).offset(offset)
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [model.to_entity() for model in models]
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email"""
        user = await self.get_by_email(email)
        return user is not None
    
    async def count_by_role(self, role: AuthRole) -> int:
        """Count users by role"""
        async with get_db_session() as session:
            stmt = select(AuthUserModel).where(AuthUserModel.role == role.value)
            result = await session.execute(stmt)
            return len(result.scalars().all())
    
    async def get_by_verification_token(self, token: str) -> Optional[AuthUser]:
        """Get user by email verification token"""
        async with get_db_session() as session:
            stmt = select(AuthUserModel).where(
                AuthUserModel.email_verification_token == token
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return model.to_entity() if model else None
    
    async def get_by_reset_token(self, token: str) -> Optional[AuthUser]:
        """Get user by password reset token"""
        async with get_db_session() as session:
            stmt = select(AuthUserModel).where(
                AuthUserModel.password_reset_token == token
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return model.to_entity() if model else None