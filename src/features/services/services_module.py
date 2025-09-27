"""
Services Module
Provides services and categories management functionality
"""
import logging
from sqlalchemy.orm import Session

from src.features.services.infrastructure.database.repositories import ServiceCategoryRepository, ServiceRepository
from src.features.services.application.services import CategoryService, ServiceService

logger = logging.getLogger(__name__)


class ServicesModule:
    """Services module for dependency injection"""
    
    def __init__(self):
        self._category_repository = None
        self._service_repository = None
        self._category_service = None
        self._service_service = None
        self._initialized = False
    
    def get_category_repository(self, db: Session) -> ServiceCategoryRepository:
        """Get category repository instance"""
        return ServiceCategoryRepository(db)
    
    def get_service_repository(self, db: Session) -> ServiceRepository:
        """Get service repository instance"""
        return ServiceRepository(db)
    
    def get_category_service(self, db: Session) -> CategoryService:
        """Get category service instance"""
        category_repository = self.get_category_repository(db)
        return CategoryService(category_repository)
    
    def get_service_service(self, db: Session) -> ServiceService:
        """Get service service instance"""
        service_repository = self.get_service_repository(db)
        category_repository = self.get_category_repository(db)
        return ServiceService(service_repository, category_repository)
    
    async def initialize(self):
        """Initialize the services module"""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing services module...")
            
            # Setup database tables
            await self._setup_database()
            
            self._initialized = True
            logger.info("Services module initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize services module: {e}")
            raise
    
    async def _setup_database(self):
        """Setup services database tables - now handled centrally"""
        # Database table creation is now handled centrally in shared.database
        # This method is kept for backward compatibility and future services-specific setup
        logger.info("Services database setup completed")


# Module instance
services_module = ServicesModule()