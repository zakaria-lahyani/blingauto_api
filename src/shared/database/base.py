"""
Database base classes and utilities
"""
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List
from uuid import UUID

class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


EntityType = TypeVar('EntityType')
ModelType = TypeVar('ModelType')


class BaseRepository(Generic[EntityType, ModelType], ABC):
    """Base repository interface"""
    
    def __init__(self, session: AsyncSession, model_class: type):
        self.session = session
        self.model_class = model_class
    
    @abstractmethod
    async def create(self, entity: EntityType) -> EntityType:
        """Create new entity"""
        pass
    
    @abstractmethod
    async def get(self, id: UUID) -> Optional[EntityType]:
        """Get entity by ID"""
        pass
    
    @abstractmethod
    async def update(self, entity: EntityType) -> EntityType:
        """Update entity"""
        pass
    
    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Delete entity"""
        pass
    
    @abstractmethod
    async def list(self, limit: int = 100, offset: int = 0) -> List[EntityType]:
        """List entities"""
        pass