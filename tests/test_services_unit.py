"""
Unit tests for services domain entities and business logic
"""
import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import datetime

from src.features.services.domain.entities import ServiceCategory, Service
from src.features.services.domain.enums import CategoryStatus, ServiceStatus


class TestServiceCategory:
    """Unit tests for ServiceCategory domain entity"""
    
    def test_create_category_valid(self):
        """Test creating a valid service category"""
        category = ServiceCategory(
            id=uuid4(),
            name="Basic Wash",
            description="Basic car washing services"
        )
        
        assert category.name == "Basic Wash"
        assert category.description == "Basic car washing services"
        assert category.status == CategoryStatus.ACTIVE
        assert isinstance(category.created_at, datetime)
        assert isinstance(category.updated_at, datetime)
    
    def test_create_category_minimal(self):
        """Test creating a category with minimal required fields"""
        category = ServiceCategory(
            id=uuid4(),
            name="Premium Wash"
        )
        
        assert category.name == "Premium Wash"
        assert category.description is None
        assert category.status == CategoryStatus.ACTIVE
    
    def test_create_category_empty_name_raises_error(self):
        """Test that empty name raises ValueError"""
        with pytest.raises(ValueError, match="Category name cannot be empty"):
            ServiceCategory(
                id=uuid4(),
                name=""
            )
    
    def test_create_category_whitespace_name_raises_error(self):
        """Test that whitespace-only name raises ValueError"""
        with pytest.raises(ValueError, match="Category name cannot be empty"):
            ServiceCategory(
                id=uuid4(),
                name="   "
            )
    
    def test_create_category_long_name_raises_error(self):
        """Test that overly long name raises ValueError"""
        long_name = "a" * 101  # Exceeds 100 character limit
        with pytest.raises(ValueError, match="Category name cannot exceed 100 characters"):
            ServiceCategory(
                id=uuid4(),
                name=long_name
            )
    
    def test_activate_category(self):
        """Test activating a deactivated category"""
        category = ServiceCategory(
            id=uuid4(),
            name="Test Category",
            status=CategoryStatus.INACTIVE
        )
        
        category.activate()
        assert category.status == CategoryStatus.ACTIVE
    
    def test_deactivate_category(self):
        """Test deactivating an active category"""
        category = ServiceCategory(
            id=uuid4(),
            name="Test Category"
        )
        
        category.deactivate()
        assert category.status == CategoryStatus.INACTIVE
    
    def test_is_active(self):
        """Test is_active property"""
        category = ServiceCategory(
            id=uuid4(),
            name="Test Category"
        )
        
        assert category.is_active is True
        
        category.deactivate()
        assert category.is_active is False
    
    def test_update_details(self):
        """Test updating category details"""
        category = ServiceCategory(
            id=uuid4(),
            name="Old Name",
            description="Old description"
        )
        
        old_updated_at = category.updated_at
        
        # Sleep a bit to ensure timestamp difference
        import time
        time.sleep(0.001)
        
        category.update_details(
            name="New Name",
            description="New description"
        )
        
        assert category.name == "New Name"
        assert category.description == "New description"
        assert category.updated_at > old_updated_at


class TestService:
    """Unit tests for Service domain entity"""
    
    def test_create_service_valid(self):
        """Test creating a valid service"""
        category_id = uuid4()
        service = Service(
            id=uuid4(),
            name="Basic Wash",
            price=Decimal("25.99"),
            duration=30,
            category_id=category_id,
            description="Basic exterior wash",
            point_description=["Soap wash", "Rinse", "Dry"]
        )
        
        assert service.name == "Basic Wash"
        assert service.price == Decimal("25.99")
        assert service.duration == 30
        assert service.category_id == category_id
        assert service.description == "Basic exterior wash"
        assert service.point_description == ["Soap wash", "Rinse", "Dry"]
        assert service.status == ServiceStatus.ACTIVE
        assert service.popular is False
        assert isinstance(service.created_at, datetime)
        assert isinstance(service.updated_at, datetime)
    
    def test_create_service_minimal(self):
        """Test creating service with minimal required fields"""
        category_id = uuid4()
        service = Service(
            id=uuid4(),
            name="Quick Wash",
            price=Decimal("15.00"),
            duration=15,
            category_id=category_id
        )
        
        assert service.name == "Quick Wash"
        assert service.price == Decimal("15.00")
        assert service.duration == 15
        assert service.category_id == category_id
        assert service.description is None
        assert service.point_description == []
    
    def test_create_service_empty_name_raises_error(self):
        """Test that empty name raises ValueError"""
        with pytest.raises(ValueError, match="Service name cannot be empty"):
            Service(
                id=uuid4(),
                name="",
                price=Decimal("25.99"),
                duration=30,
                category_id=uuid4()
            )
    
    def test_create_service_negative_price_raises_error(self):
        """Test that negative price raises ValueError"""
        with pytest.raises(ValueError, match="Service price must be positive"):
            Service(
                id=uuid4(),
                name="Test Service",
                price=Decimal("-10.00"),
                duration=30,
                category_id=uuid4()
            )
    
    def test_create_service_zero_price_raises_error(self):
        """Test that zero price raises ValueError"""
        with pytest.raises(ValueError, match="Service price must be positive"):
            Service(
                id=uuid4(),
                name="Test Service",
                price=Decimal("0.00"),
                duration=30,
                category_id=uuid4()
            )
    
    def test_create_service_negative_duration_raises_error(self):
        """Test that negative duration raises ValueError"""
        with pytest.raises(ValueError, match="Service duration must be positive"):
            Service(
                id=uuid4(),
                name="Test Service",
                price=Decimal("25.99"),
                duration=-30,
                category_id=uuid4()
            )
    
    def test_create_service_zero_duration_raises_error(self):
        """Test that zero duration raises ValueError"""
        with pytest.raises(ValueError, match="Service duration must be positive"):
            Service(
                id=uuid4(),
                name="Test Service",
                price=Decimal("25.99"),
                duration=0,
                category_id=uuid4()
            )
    
    def test_mark_popular(self):
        """Test marking service as popular"""
        service = Service(
            id=uuid4(),
            name="Test Service",
            price=Decimal("25.99"),
            duration=30,
            category_id=uuid4()
        )
        
        service.mark_popular()
        assert service.popular is True
    
    def test_unmark_popular(self):
        """Test unmarking service as popular"""
        service = Service(
            id=uuid4(),
            name="Test Service",
            price=Decimal("25.99"),
            duration=30,
            category_id=uuid4(),
            popular=True
        )
        
        service.unmark_popular()
        assert service.popular is False
    
    def test_activate_service(self):
        """Test activating a deactivated service"""
        service = Service(
            id=uuid4(),
            name="Test Service",
            price=Decimal("25.99"),
            duration=30,
            category_id=uuid4(),
            status=ServiceStatus.INACTIVE
        )
        
        service.activate()
        assert service.status == ServiceStatus.ACTIVE
    
    def test_deactivate_service(self):
        """Test deactivating an active service"""
        service = Service(
            id=uuid4(),
            name="Test Service",
            price=Decimal("25.99"),
            duration=30,
            category_id=uuid4()
        )
        
        service.deactivate()
        assert service.status == ServiceStatus.INACTIVE
    
    def test_soft_delete_service(self):
        """Test soft deleting a service"""
        service = Service(
            id=uuid4(),
            name="Test Service",
            price=Decimal("25.99"),
            duration=30,
            category_id=uuid4()
        )
        
        service.soft_delete()
        assert service.status == ServiceStatus.DELETED
    
    def test_is_active(self):
        """Test is_active property"""
        service = Service(
            id=uuid4(),
            name="Test Service",
            price=Decimal("25.99"),
            duration=30,
            category_id=uuid4()
        )
        
        assert service.is_active is True
        
        service.deactivate()
        assert service.is_active is False
        
        service.soft_delete()
        assert service.is_active is False
    
    def test_is_deleted(self):
        """Test is_deleted property"""
        service = Service(
            id=uuid4(),
            name="Test Service",
            price=Decimal("25.99"),
            duration=30,
            category_id=uuid4()
        )
        
        assert service.is_deleted is False
        
        service.soft_delete()
        assert service.is_deleted is True
    
    def test_update_details(self):
        """Test updating service details"""
        category_id = uuid4()
        new_category_id = uuid4()
        
        service = Service(
            id=uuid4(),
            name="Old Name",
            price=Decimal("25.99"),
            duration=30,
            category_id=category_id,
            description="Old description",
            point_description=["Old point"]
        )
        
        old_updated_at = service.updated_at
        
        # Sleep a bit to ensure timestamp difference
        import time
        time.sleep(0.001)
        
        service.update_details(
            name="New Name",
            price=Decimal("35.99"),
            duration=45,
            category_id=new_category_id,
            description="New description",
            point_description=["New point 1", "New point 2"]
        )
        
        assert service.name == "New Name"
        assert service.price == Decimal("35.99")
        assert service.duration == 45
        assert service.category_id == new_category_id
        assert service.description == "New description"
        assert service.point_description == ["New point 1", "New point 2"]
        assert service.updated_at > old_updated_at
    
    def test_update_details_with_none_values(self):
        """Test updating service details with None values (no change)"""
        category_id = uuid4()
        
        service = Service(
            id=uuid4(),
            name="Original Name",
            price=Decimal("25.99"),
            duration=30,
            category_id=category_id,
            description="Original description"
        )
        
        service.update_details(
            name=None,
            price=None,
            duration=None,
            category_id=None,
            description=None,
            point_description=None
        )
        
        # Values should remain unchanged
        assert service.name == "Original Name"
        assert service.price == Decimal("25.99")
        assert service.duration == 30
        assert service.category_id == category_id
        assert service.description == "Original description"