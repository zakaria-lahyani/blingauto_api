import pytest
from decimal import Decimal

from app.features.services.domain import (
    Category,
    Service,
    CategoryStatus,
    ServiceStatus,
)
from app.shared.exceptions.standardized_errors import ValidationError


class TestCategory:
    """Test Category domain entity."""
    
    def test_create_category_success(self):
        """Test successful category creation."""
        category = Category.create(
            name="Exterior Cleaning",
            description="External car wash services",
            display_order=1,
        )
        
        assert category.name == "Exterior Cleaning"
        assert category.description == "External car wash services"
        assert category.display_order == 1
        assert category.status == CategoryStatus.ACTIVE
        assert category.id is not None
        assert category.created_at is not None
        assert category.updated_at is not None
    
    def test_create_category_with_empty_name_fails(self):
        """Test category creation fails with empty name."""
        with pytest.raises(ValidationError, match="Category name cannot be empty"):
            Category.create(
                name="",
                description="Description",
                display_order=1,
            )
    
    def test_create_category_with_long_name_fails(self):
        """Test category creation fails with name too long."""
        long_name = "x" * 101  # Exceeds 100 character limit
        with pytest.raises(ValidationError, match="Category name cannot exceed 100 characters"):
            Category.create(
                name=long_name,
                description="Description",
                display_order=1,
            )
    
    def test_create_category_with_long_description_fails(self):
        """Test category creation fails with description too long."""
        long_description = "x" * 501  # Exceeds 500 character limit
        with pytest.raises(ValidationError, match="Category description cannot exceed 500 characters"):
            Category.create(
                name="Valid Name",
                description=long_description,
                display_order=1,
            )
    
    def test_create_category_with_negative_display_order_fails(self):
        """Test category creation fails with negative display order."""
        with pytest.raises(ValidationError, match="Display order must be non-negative"):
            Category.create(
                name="Valid Name",
                description="Valid description",
                display_order=-1,
            )
    
    def test_deactivate_category(self):
        """Test category deactivation."""
        category = Category.create(
            name="Test Category",
            description="Test description",
            display_order=1,
        )
        
        category.deactivate()
        assert category.status == CategoryStatus.INACTIVE
    
    def test_category_equality(self):
        """Test category equality comparison."""
        category1 = Category.create(
            name="Test Category",
            description="Test description",
            display_order=1,
        )
        category2 = Category.create(
            name="Different Category",
            description="Different description",
            display_order=2,
        )
        category2.id = category1.id  # Same ID
        
        assert category1 == category2
        
        category2.id = "different_id"
        assert category1 != category2


class TestService:
    """Test Service domain entity."""
    
    def test_create_service_success(self):
        """Test successful service creation."""
        service = Service.create(
            category_id="cat_123",
            name="Basic Wash",
            description="Standard exterior wash",
            price=Decimal("25.00"),
            duration_minutes=30,
        )
        
        assert service.category_id == "cat_123"
        assert service.name == "Basic Wash"
        assert service.description == "Standard exterior wash"
        assert service.price == Decimal("25.00")
        assert service.duration_minutes == 30
        assert service.status == ServiceStatus.ACTIVE
        assert service.is_popular is False
        assert service.display_order == 0
        assert service.id is not None
        assert service.created_at is not None
        assert service.updated_at is not None
    
    def test_create_service_with_popular_flag(self):
        """Test service creation with popular flag."""
        service = Service.create(
            category_id="cat_123",
            name="Premium Wash",
            description="Premium service",
            price=Decimal("45.00"),
            duration_minutes=60,
            is_popular=True,
            display_order=5,
        )
        
        assert service.is_popular is True
        assert service.display_order == 5
    
    def test_create_service_with_empty_name_fails(self):
        """Test service creation fails with empty name."""
        with pytest.raises(ValidationError, match="Service name cannot be empty"):
            Service.create(
                category_id="cat_123",
                name="",
                description="Description",
                price=Decimal("25.00"),
                duration_minutes=30,
            )
    
    def test_create_service_with_long_name_fails(self):
        """Test service creation fails with name too long."""
        long_name = "x" * 101
        with pytest.raises(ValidationError, match="Service name cannot exceed 100 characters"):
            Service.create(
                category_id="cat_123",
                name=long_name,
                description="Description",
                price=Decimal("25.00"),
                duration_minutes=30,
            )
    
    def test_create_service_with_zero_price_fails(self):
        """Test service creation fails with zero price."""
        with pytest.raises(ValidationError, match="Service price must be positive"):
            Service.create(
                category_id="cat_123",
                name="Valid Name",
                description="Description",
                price=Decimal("0.00"),
                duration_minutes=30,
            )
    
    def test_create_service_with_negative_price_fails(self):
        """Test service creation fails with negative price."""
        with pytest.raises(ValidationError, match="Service price must be positive"):
            Service.create(
                category_id="cat_123",
                name="Valid Name",
                description="Description",
                price=Decimal("-10.00"),
                duration_minutes=30,
            )
    
    def test_create_service_with_zero_duration_fails(self):
        """Test service creation fails with zero duration."""
        with pytest.raises(ValidationError, match="Service duration must be positive"):
            Service.create(
                category_id="cat_123",
                name="Valid Name",
                description="Description",
                price=Decimal("25.00"),
                duration_minutes=0,
            )
    
    def test_create_service_with_negative_duration_fails(self):
        """Test service creation fails with negative duration."""
        with pytest.raises(ValidationError, match="Service duration must be positive"):
            Service.create(
                category_id="cat_123",
                name="Valid Name",
                description="Description",
                price=Decimal("25.00"),
                duration_minutes=-15,
            )
    
    def test_create_service_with_invalid_duration_increment_fails(self):
        """Test service creation fails with invalid duration increment."""
        with pytest.raises(ValidationError, match="Service duration must be in 15-minute increments"):
            Service.create(
                category_id="cat_123",
                name="Valid Name",
                description="Description",
                price=Decimal("25.00"),
                duration_minutes=20,  # Not multiple of 15
            )
    
    def test_create_service_with_negative_display_order_fails(self):
        """Test service creation fails with negative display order."""
        with pytest.raises(ValidationError, match="Display order must be non-negative"):
            Service.create(
                category_id="cat_123",
                name="Valid Name",
                description="Description",
                price=Decimal("25.00"),
                duration_minutes=30,
                display_order=-1,
            )
    
    def test_update_service_price(self):
        """Test service price update."""
        service = Service.create(
            category_id="cat_123",
            name="Basic Wash",
            description="Standard wash",
            price=Decimal("25.00"),
            duration_minutes=30,
        )
        
        old_price = service.price
        service.update_price(Decimal("30.00"))
        
        assert service.price == Decimal("30.00")
        assert service.price != old_price
    
    def test_update_service_price_with_zero_fails(self):
        """Test service price update fails with zero."""
        service = Service.create(
            category_id="cat_123",
            name="Basic Wash",
            description="Standard wash",
            price=Decimal("25.00"),
            duration_minutes=30,
        )
        
        with pytest.raises(ValidationError, match="Service price must be positive"):
            service.update_price(Decimal("0.00"))
    
    def test_set_service_popular(self):
        """Test setting service as popular."""
        service = Service.create(
            category_id="cat_123",
            name="Basic Wash",
            description="Standard wash",
            price=Decimal("25.00"),
            duration_minutes=30,
        )
        
        assert service.is_popular is False
        service.set_popular(True)
        assert service.is_popular is True
        
        service.set_popular(False)
        assert service.is_popular is False
    
    def test_deactivate_service(self):
        """Test service deactivation."""
        service = Service.create(
            category_id="cat_123",
            name="Basic Wash",
            description="Standard wash",
            price=Decimal("25.00"),
            duration_minutes=30,
        )
        
        service.deactivate()
        assert service.status == ServiceStatus.INACTIVE
    
    def test_archive_service(self):
        """Test service archival."""
        service = Service.create(
            category_id="cat_123",
            name="Basic Wash",
            description="Standard wash",
            price=Decimal("25.00"),
            duration_minutes=30,
        )
        
        service.archive()
        assert service.status == ServiceStatus.ARCHIVED
    
    def test_service_price_display(self):
        """Test service price display formatting."""
        service = Service.create(
            category_id="cat_123",
            name="Basic Wash",
            description="Standard wash",
            price=Decimal("25.00"),
            duration_minutes=30,
        )
        
        assert service.price_display == "$25.00"
        
        service.update_price(Decimal("125.50"))
        assert service.price_display == "$125.50"
    
    def test_service_duration_display(self):
        """Test service duration display formatting."""
        service = Service.create(
            category_id="cat_123",
            name="Basic Wash",
            description="Standard wash",
            price=Decimal("25.00"),
            duration_minutes=30,
        )
        
        assert service.duration_display == "30 minutes"
        
        service = Service.create(
            category_id="cat_123",
            name="Extended Wash",
            description="Extended wash",
            price=Decimal("45.00"),
            duration_minutes=90,
        )
        
        assert service.duration_display == "1 hour 30 minutes"
        
        service = Service.create(
            category_id="cat_123",
            name="Quick Wash",
            description="Quick wash",
            price=Decimal("15.00"),
            duration_minutes=15,
        )
        
        assert service.duration_display == "15 minutes"
    
    def test_service_equality(self):
        """Test service equality comparison."""
        service1 = Service.create(
            category_id="cat_123",
            name="Basic Wash",
            description="Standard wash",
            price=Decimal("25.00"),
            duration_minutes=30,
        )
        service2 = Service.create(
            category_id="cat_456",
            name="Different Wash",
            description="Different wash",
            price=Decimal("35.00"),
            duration_minutes=45,
        )
        service2.id = service1.id  # Same ID
        
        assert service1 == service2
        
        service2.id = "different_id"
        assert service1 != service2