import pytest
from decimal import Decimal
from unittest.mock import AsyncMock

from app.features.services.domain import Category, Service, CategoryStatus, ServiceStatus
from app.features.services.use_cases import (
    CreateCategoryUseCase,
    CreateServiceUseCase,
    UpdateServicePriceUseCase,
    SetServicePopularUseCase,
    ListCategoriesUseCase,
    ListServicesUseCase,
    GetServiceUseCase,
    DeactivateServiceUseCase,
    GetPopularServicesUseCase,
    SearchServicesUseCase,
)
from app.shared.exceptions.standardized_errors import (
    ValidationError,
    ResourceNotFoundError,
    BusinessRuleViolationError,
)


class TestCreateCategoryUseCase:
    """Test CreateCategoryUseCase."""
    
    async def test_create_category_success(
        self,
        mock_category_repository,
        mock_event_service,
        mock_audit_service,
    ):
        """Test successful category creation."""
        # Setup
        mock_category_repository.exists_by_name.return_value = False
        mock_category_repository.create.return_value = AsyncMock()
        
        use_case = CreateCategoryUseCase(
            category_repository=mock_category_repository,
            event_service=mock_event_service,
            audit_service=mock_audit_service,
        )
        
        # Execute
        result = await use_case.execute(
            name="Exterior Cleaning",
            description="External car wash services",
            display_order=1,
            created_by="admin_123",
        )
        
        # Assert
        mock_category_repository.exists_by_name.assert_called_once_with("Exterior Cleaning")
        mock_category_repository.create.assert_called_once()
        mock_event_service.publish_category_created.assert_called_once()
        mock_audit_service.log_category_creation.assert_called_once()
        assert result is not None
    
    async def test_create_category_with_duplicate_name_fails(
        self,
        mock_category_repository,
        mock_event_service,
        mock_audit_service,
    ):
        """Test category creation fails with duplicate name."""
        # Setup
        mock_category_repository.exists_by_name.return_value = True
        
        use_case = CreateCategoryUseCase(
            category_repository=mock_category_repository,
            event_service=mock_event_service,
            audit_service=mock_audit_service,
        )
        
        # Execute & Assert
        with pytest.raises(BusinessRuleViolationError, match="Category with this name already exists"):
            await use_case.execute(
                name="Duplicate Name",
                description="Description",
                display_order=1,
                created_by="admin_123",
            )
        
        mock_category_repository.create.assert_not_called()


class TestCreateServiceUseCase:
    """Test CreateServiceUseCase."""
    
    async def test_create_service_success(
        self,
        mock_category_repository,
        mock_service_repository,
        mock_event_service,
        mock_audit_service,
        sample_category,
    ):
        """Test successful service creation."""
        # Setup
        mock_category_repository.get_by_id.return_value = sample_category
        mock_service_repository.exists_by_name_in_category.return_value = False
        mock_service_repository.count_popular_in_category.return_value = 1
        mock_service_repository.create.return_value = AsyncMock()
        
        use_case = CreateServiceUseCase(
            category_repository=mock_category_repository,
            service_repository=mock_service_repository,
            event_service=mock_event_service,
            audit_service=mock_audit_service,
        )
        
        # Execute
        result = await use_case.execute(
            category_id="cat_123",
            name="Basic Wash",
            description="Standard exterior wash",
            price=Decimal("25.00"),
            duration_minutes=30,
            is_popular=False,
            display_order=1,
            created_by="admin_123",
        )
        
        # Assert
        mock_category_repository.get_by_id.assert_called_once_with("cat_123")
        mock_service_repository.exists_by_name_in_category.assert_called_once()
        mock_service_repository.create.assert_called_once()
        mock_event_service.publish_service_created.assert_called_once()
        mock_audit_service.log_service_creation.assert_called_once()
        assert result is not None
    
    async def test_create_service_with_nonexistent_category_fails(
        self,
        mock_category_repository,
        mock_service_repository,
        mock_event_service,
        mock_audit_service,
    ):
        """Test service creation fails with non-existent category."""
        # Setup
        mock_category_repository.get_by_id.return_value = None
        
        use_case = CreateServiceUseCase(
            category_repository=mock_category_repository,
            service_repository=mock_service_repository,
            event_service=mock_event_service,
            audit_service=mock_audit_service,
        )
        
        # Execute & Assert
        with pytest.raises(ResourceNotFoundError, match="Category not found"):
            await use_case.execute(
                category_id="nonexistent",
                name="Basic Wash",
                description="Standard wash",
                price=Decimal("25.00"),
                duration_minutes=30,
                is_popular=False,
                display_order=1,
                created_by="admin_123",
            )
        
        mock_service_repository.create.assert_not_called()
    
    async def test_create_popular_service_exceeding_limit_fails(
        self,
        mock_category_repository,
        mock_service_repository,
        mock_event_service,
        mock_audit_service,
        sample_category,
    ):
        """Test creating popular service when limit exceeded."""
        # Setup
        mock_category_repository.get_by_id.return_value = sample_category
        mock_service_repository.exists_by_name_in_category.return_value = False
        mock_service_repository.count_popular_in_category.return_value = 3  # At limit
        
        use_case = CreateServiceUseCase(
            category_repository=mock_category_repository,
            service_repository=mock_service_repository,
            event_service=mock_event_service,
            audit_service=mock_audit_service,
        )
        
        # Execute & Assert
        with pytest.raises(BusinessRuleViolationError, match="Cannot exceed 3 popular services per category"):
            await use_case.execute(
                category_id="cat_123",
                name="Premium Wash",
                description="Premium wash",
                price=Decimal("45.00"),
                duration_minutes=60,
                is_popular=True,  # Trying to add 4th popular service
                display_order=1,
                created_by="admin_123",
            )


class TestUpdateServicePriceUseCase:
    """Test UpdateServicePriceUseCase."""
    
    async def test_update_service_price_success(
        self,
        mock_service_repository,
        mock_booking_repository,
        mock_event_service,
        mock_notification_service,
        mock_audit_service,
        sample_service,
    ):
        """Test successful service price update."""
        # Setup
        mock_service_repository.get_by_id.return_value = sample_service
        mock_service_repository.update.return_value = sample_service
        mock_booking_repository.count_bookings_for_service.return_value = 5
        
        use_case = UpdateServicePriceUseCase(
            service_repository=mock_service_repository,
            booking_repository=mock_booking_repository,
            event_service=mock_event_service,
            notification_service=mock_notification_service,
            audit_service=mock_audit_service,
        )
        
        # Execute
        result = await use_case.execute(
            service_id="srv_123",
            new_price=Decimal("30.00"),
            notify_customers=True,
            updated_by="admin_123",
        )
        
        # Assert
        mock_service_repository.get_by_id.assert_called_once_with("srv_123")
        mock_service_repository.update.assert_called_once()
        mock_event_service.publish_service_price_changed.assert_called_once()
        mock_audit_service.log_service_price_change.assert_called_once()
        assert result["service"] == sample_service
        assert result["old_price"] == Decimal("25.00")
        assert result["new_price"] == Decimal("30.00")
        assert result["affected_bookings"] == 5
    
    async def test_update_service_price_with_nonexistent_service_fails(
        self,
        mock_service_repository,
        mock_booking_repository,
        mock_event_service,
        mock_notification_service,
        mock_audit_service,
    ):
        """Test price update fails with non-existent service."""
        # Setup
        mock_service_repository.get_by_id.return_value = None
        
        use_case = UpdateServicePriceUseCase(
            service_repository=mock_service_repository,
            booking_repository=mock_booking_repository,
            event_service=mock_event_service,
            notification_service=mock_notification_service,
            audit_service=mock_audit_service,
        )
        
        # Execute & Assert
        with pytest.raises(ResourceNotFoundError, match="Service not found"):
            await use_case.execute(
                service_id="nonexistent",
                new_price=Decimal("30.00"),
                notify_customers=True,
                updated_by="admin_123",
            )


class TestSetServicePopularUseCase:
    """Test SetServicePopularUseCase."""
    
    async def test_set_service_popular_success(
        self,
        mock_service_repository,
        mock_event_service,
        mock_audit_service,
        sample_service,
    ):
        """Test successfully setting service as popular."""
        # Setup
        mock_service_repository.get_by_id.return_value = sample_service
        mock_service_repository.count_popular_in_category.return_value = 2
        mock_service_repository.update.return_value = sample_service
        
        use_case = SetServicePopularUseCase(
            service_repository=mock_service_repository,
            event_service=mock_event_service,
            audit_service=mock_audit_service,
        )
        
        # Execute
        result = await use_case.execute(
            service_id="srv_123",
            is_popular=True,
            updated_by="admin_123",
        )
        
        # Assert
        mock_service_repository.get_by_id.assert_called_once_with("srv_123")
        mock_service_repository.update.assert_called_once()
        mock_event_service.publish_service_marked_popular.assert_called_once()
        assert result["service"] == sample_service
        assert result["category_popular_count"] == 3  # 2 existing + 1 new
    
    async def test_set_service_popular_exceeding_limit_fails(
        self,
        mock_service_repository,
        mock_event_service,
        mock_audit_service,
        sample_service,
    ):
        """Test setting service popular when limit exceeded."""
        # Setup
        mock_service_repository.get_by_id.return_value = sample_service
        mock_service_repository.count_popular_in_category.return_value = 3  # At limit
        
        use_case = SetServicePopularUseCase(
            service_repository=mock_service_repository,
            event_service=mock_event_service,
            audit_service=mock_audit_service,
        )
        
        # Execute & Assert
        with pytest.raises(BusinessRuleViolationError, match="Cannot exceed 3 popular services per category"):
            await use_case.execute(
                service_id="srv_123",
                is_popular=True,
                updated_by="admin_123",
            )


class TestListCategoriesUseCase:
    """Test ListCategoriesUseCase."""
    
    async def test_list_categories_success(
        self,
        mock_category_repository,
        mock_service_repository,
        sample_category,
    ):
        """Test successful category listing."""
        # Setup
        mock_category_repository.list_all.return_value = [sample_category]
        mock_category_repository.count.return_value = 1
        mock_service_repository.count_by_category.return_value = 5
        
        use_case = ListCategoriesUseCase(
            category_repository=mock_category_repository,
            service_repository=mock_service_repository,
        )
        
        # Execute
        result = await use_case.execute(
            include_inactive=False,
            requesting_user_id="user_123",
        )
        
        # Assert
        mock_category_repository.list_all.assert_called_once_with(
            include_inactive=False,
            offset=0,
            limit=50,
        )
        mock_category_repository.count.assert_called_once_with(include_inactive=False)
        assert result["categories"] == [sample_category]
        assert result["total_count"] == 1
        assert result["service_counts"][sample_category.id] == 5


class TestListServicesUseCase:
    """Test ListServicesUseCase."""
    
    async def test_list_services_success(
        self,
        mock_service_repository,
        mock_category_repository,
        sample_service,
        sample_category,
    ):
        """Test successful service listing."""
        # Setup
        mock_service_repository.list_all.return_value = [sample_service]
        mock_category_repository.get_by_id.return_value = sample_category
        
        use_case = ListServicesUseCase(
            service_repository=mock_service_repository,
            category_repository=mock_category_repository,
        )
        
        # Execute
        result = await use_case.execute(
            filters={},
            include_inactive=False,
            page=1,
            limit=20,
            requesting_user_id="user_123",
        )
        
        # Assert
        mock_service_repository.list_all.assert_called_once_with(
            include_inactive=False,
            offset=0,
            limit=20,
        )
        assert result["services"] == [sample_service]
        assert result["has_next"] is False
        assert result["category_names"][sample_service.category_id] == sample_category.name
    
    async def test_list_services_with_filters(
        self,
        mock_service_repository,
        mock_category_repository,
        sample_service,
    ):
        """Test service listing with filters."""
        # Setup
        mock_service_repository.list_by_category.return_value = [sample_service]
        
        use_case = ListServicesUseCase(
            service_repository=mock_service_repository,
            category_repository=mock_category_repository,
        )
        
        # Execute
        result = await use_case.execute(
            filters={"category_id": "cat_123"},
            include_inactive=False,
            page=1,
            limit=20,
            requesting_user_id="user_123",
        )
        
        # Assert
        mock_service_repository.list_by_category.assert_called_once_with(
            category_id="cat_123",
            include_inactive=False,
            offset=0,
            limit=20,
        )


class TestGetServiceUseCase:
    """Test GetServiceUseCase."""
    
    async def test_get_service_success(
        self,
        mock_service_repository,
        sample_service,
    ):
        """Test successful service retrieval."""
        # Setup
        mock_service_repository.get_by_id.return_value = sample_service
        
        use_case = GetServiceUseCase(
            service_repository=mock_service_repository,
        )
        
        # Execute
        result = await use_case.execute(
            service_id="srv_123",
            requesting_user_id="user_123",
        )
        
        # Assert
        mock_service_repository.get_by_id.assert_called_once_with("srv_123")
        assert result == sample_service
    
    async def test_get_service_not_found_fails(
        self,
        mock_service_repository,
    ):
        """Test service retrieval fails when not found."""
        # Setup
        mock_service_repository.get_by_id.return_value = None
        
        use_case = GetServiceUseCase(
            service_repository=mock_service_repository,
        )
        
        # Execute & Assert
        with pytest.raises(ResourceNotFoundError, match="Service not found"):
            await use_case.execute(
                service_id="nonexistent",
                requesting_user_id="user_123",
            )


class TestGetPopularServicesUseCase:
    """Test GetPopularServicesUseCase."""
    
    async def test_get_popular_services_success(
        self,
        mock_service_repository,
        mock_category_repository,
        sample_popular_service,
        sample_category,
    ):
        """Test successful popular services retrieval."""
        # Setup
        mock_service_repository.list_popular.return_value = [sample_popular_service]
        mock_category_repository.get_by_id.return_value = sample_category
        
        use_case = GetPopularServicesUseCase(
            service_repository=mock_service_repository,
            category_repository=mock_category_repository,
        )
        
        # Execute
        result = await use_case.execute(
            limit=10,
            requesting_user_id="user_123",
        )
        
        # Assert
        mock_service_repository.list_popular.assert_called_once_with(limit=10)
        assert result["services"] == [sample_popular_service]
        assert result["category_names"][sample_popular_service.category_id] == sample_category.name


class TestSearchServicesUseCase:
    """Test SearchServicesUseCase."""
    
    async def test_search_services_success(
        self,
        mock_service_repository,
        mock_category_repository,
        sample_service,
        sample_category,
    ):
        """Test successful service search."""
        # Setup
        mock_service_repository.search_services.return_value = [sample_service]
        mock_category_repository.get_by_id.return_value = sample_category
        
        use_case = SearchServicesUseCase(
            service_repository=mock_service_repository,
            category_repository=mock_category_repository,
        )
        
        # Execute
        result = await use_case.execute(
            query="wash",
            category_id=None,
            limit=20,
            requesting_user_id="user_123",
        )
        
        # Assert
        mock_service_repository.search_services.assert_called_once_with(
            query="wash",
            category_id=None,
            limit=20,
        )
        assert result["services"] == [sample_service]
        assert result["category_names"][sample_service.category_id] == sample_category.name


class TestDeactivateServiceUseCase:
    """Test DeactivateServiceUseCase."""
    
    async def test_deactivate_service_success(
        self,
        mock_service_repository,
        mock_event_service,
        mock_audit_service,
        sample_service,
    ):
        """Test successful service deactivation."""
        # Setup
        mock_service_repository.get_by_id.return_value = sample_service
        mock_service_repository.update.return_value = sample_service
        
        use_case = DeactivateServiceUseCase(
            service_repository=mock_service_repository,
            event_service=mock_event_service,
            audit_service=mock_audit_service,
        )
        
        # Execute
        await use_case.execute(
            service_id="srv_123",
            reason="No longer offered",
            deactivated_by="admin_123",
        )
        
        # Assert
        mock_service_repository.get_by_id.assert_called_once_with("srv_123")
        mock_service_repository.update.assert_called_once()
        mock_event_service.publish_service_deactivated.assert_called_once()
        mock_audit_service.log_service_deactivation.assert_called_once()
    
    async def test_deactivate_service_not_found_fails(
        self,
        mock_service_repository,
        mock_event_service,
        mock_audit_service,
    ):
        """Test service deactivation fails when not found."""
        # Setup
        mock_service_repository.get_by_id.return_value = None
        
        use_case = DeactivateServiceUseCase(
            service_repository=mock_service_repository,
            event_service=mock_event_service,
            audit_service=mock_audit_service,
        )
        
        # Execute & Assert
        with pytest.raises(ResourceNotFoundError, match="Service not found"):
            await use_case.execute(
                service_id="nonexistent",
                reason="No longer offered",
                deactivated_by="admin_123",
            )