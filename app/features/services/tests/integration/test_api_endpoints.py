import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from app.features.services.domain import Category, Service, CategoryStatus, ServiceStatus
from app.features.services.api.router import service_router


@pytest.fixture
def test_client():
    """Test client for services API."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(service_router)
    return TestClient(app)


@pytest.fixture
def mock_admin_user():
    """Mock admin user for authentication."""
    user = Mock()
    user.id = "admin_123"
    user.email = "admin@test.com"
    user.role = "admin"
    return user


@pytest.fixture
def mock_manager_user():
    """Mock manager user for authentication."""
    user = Mock()
    user.id = "manager_123"
    user.email = "manager@test.com"
    user.role = "manager"
    return user


@pytest.fixture
def mock_regular_user():
    """Mock regular user for authentication."""
    user = Mock()
    user.id = "user_123"
    user.email = "user@test.com"
    user.role = "customer"
    return user


class TestCategoryEndpoints:
    """Test category API endpoints."""
    
    @patch("app.features.services.api.router.require_admin")
    @patch("app.features.services.api.router.CreateCategoryUseCase")
    def test_create_category_success(self, mock_use_case_dep, mock_auth, test_client, mock_admin_user):
        """Test successful category creation via API."""
        # Setup
        mock_auth.return_value = mock_admin_user
        
        mock_use_case = AsyncMock()
        category = Category.create(
            name="Exterior Cleaning",
            description="External car wash services",
            display_order=1,
        )
        mock_use_case.execute.return_value = category
        mock_use_case_dep.return_value = mock_use_case
        
        # Execute
        response = test_client.post(
            "/services/categories",
            json={
                "name": "Exterior Cleaning",
                "description": "External car wash services",
                "display_order": 1,
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Exterior Cleaning"
        assert data["description"] == "External car wash services"
        assert data["display_order"] == 1
        assert data["status"] == "ACTIVE"
        mock_use_case.execute.assert_called_once()
    
    @patch("app.features.services.api.router.require_admin")
    @patch("app.features.services.api.router.CreateCategoryUseCase")
    def test_create_category_validation_error(self, mock_use_case_dep, mock_auth, test_client, mock_admin_user):
        """Test category creation with validation error."""
        # Setup
        mock_auth.return_value = mock_admin_user
        
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ValidationError("Category name cannot be empty")
        mock_use_case_dep.return_value = mock_use_case
        
        # Execute
        response = test_client.post(
            "/services/categories",
            json={
                "name": "",  # Invalid empty name
                "description": "Description",
                "display_order": 1,
            }
        )
        
        # Assert
        assert response.status_code == 400
        assert "Category name cannot be empty" in response.json()["detail"]
    
    @patch("app.features.services.api.router.get_current_user")
    @patch("app.features.services.api.router.ListCategoriesUseCase")
    def test_list_categories_success(self, mock_use_case_dep, mock_auth, test_client, mock_regular_user):
        """Test successful category listing via API."""
        # Setup
        mock_auth.return_value = mock_regular_user
        
        mock_use_case = AsyncMock()
        category = Category.create(
            name="Exterior Cleaning",
            description="External services",
            display_order=1,
        )
        mock_use_case.execute.return_value = {
            "categories": [category],
            "total_count": 1,
            "service_counts": {category.id: 5},
        }
        mock_use_case_dep.return_value = mock_use_case
        
        # Execute
        response = test_client.get("/services/categories")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["categories"]) == 1
        assert data["categories"][0]["name"] == "Exterior Cleaning"
        assert data["categories"][0]["service_count"] == 5


class TestServiceEndpoints:
    """Test service API endpoints."""
    
    @patch("app.features.services.api.router.require_manager_or_admin")
    @patch("app.features.services.api.router.CreateServiceUseCase")
    def test_create_service_success(self, mock_use_case_dep, mock_auth, test_client, mock_manager_user):
        """Test successful service creation via API."""
        # Setup
        mock_auth.return_value = mock_manager_user
        
        mock_use_case = AsyncMock()
        service = Service.create(
            category_id="cat_123",
            name="Basic Wash",
            description="Standard exterior wash",
            price=Decimal("25.00"),
            duration_minutes=30,
        )
        mock_use_case.execute.return_value = service
        mock_use_case_dep.return_value = mock_use_case
        
        # Execute
        response = test_client.post(
            "/services/categories/cat_123/services",
            json={
                "category_id": "cat_123",
                "name": "Basic Wash",
                "description": "Standard exterior wash",
                "price": "25.00",
                "duration_minutes": 30,
                "is_popular": False,
                "display_order": 0,
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Basic Wash"
        assert data["price"] == "25.00"
        assert data["duration_minutes"] == 30
        assert data["is_popular"] is False
        mock_use_case.execute.assert_called_once()
    
    @patch("app.features.services.api.router.require_manager_or_admin")
    @patch("app.features.services.api.router.CreateServiceUseCase")
    def test_create_service_invalid_duration(self, mock_use_case_dep, mock_auth, test_client, mock_manager_user):
        """Test service creation with invalid duration."""
        # Setup
        mock_auth.return_value = mock_manager_user
        
        # Execute - duration not multiple of 15
        response = test_client.post(
            "/services/categories/cat_123/services",
            json={
                "category_id": "cat_123",
                "name": "Basic Wash",
                "description": "Standard wash",
                "price": "25.00",
                "duration_minutes": 20,  # Invalid - not multiple of 15
                "is_popular": False,
                "display_order": 0,
            }
        )
        
        # Assert
        assert response.status_code == 422  # Validation error
        assert "Duration must be in 15-minute increments" in str(response.json())
    
    @patch("app.features.services.api.router.get_current_user")
    @patch("app.features.services.api.router.ListServicesUseCase")
    def test_list_services_success(self, mock_use_case_dep, mock_auth, test_client, mock_regular_user):
        """Test successful service listing via API."""
        # Setup
        mock_auth.return_value = mock_regular_user
        
        mock_use_case = AsyncMock()
        service = Service.create(
            category_id="cat_123",
            name="Basic Wash",
            description="Standard wash",
            price=Decimal("25.00"),
            duration_minutes=30,
        )
        mock_use_case.execute.return_value = {
            "services": [service],
            "total_count": 1,
            "has_next": False,
            "category_names": {service.category_id: "Exterior Cleaning"},
        }
        mock_use_case_dep.return_value = mock_use_case
        
        # Execute
        response = test_client.get("/services/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["services"]) == 1
        assert data["services"][0]["name"] == "Basic Wash"
        assert data["services"][0]["category_name"] == "Exterior Cleaning"
        assert data["has_next"] is False
    
    @patch("app.features.services.api.router.get_current_user")
    @patch("app.features.services.api.router.ListServicesUseCase")
    def test_list_services_with_filters(self, mock_use_case_dep, mock_auth, test_client, mock_regular_user):
        """Test service listing with filters via API."""
        # Setup
        mock_auth.return_value = mock_regular_user
        
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = {
            "services": [],
            "total_count": 0,
            "has_next": False,
            "category_names": {},
        }
        mock_use_case_dep.return_value = mock_use_case
        
        # Execute
        response = test_client.get(
            "/services/?category_id=cat_123&min_price=20.00&max_price=50.00&page=1&limit=10"
        )
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()
        call_args = mock_use_case.execute.call_args[1]
        assert call_args["filters"]["category_id"] == "cat_123"
        assert call_args["filters"]["min_price"] == Decimal("20.00")
        assert call_args["filters"]["max_price"] == Decimal("50.00")
        assert call_args["page"] == 1
        assert call_args["limit"] == 10
    
    @patch("app.features.services.api.router.get_current_user")
    @patch("app.features.services.api.router.GetServiceUseCase")
    def test_get_service_success(self, mock_use_case_dep, mock_auth, test_client, mock_regular_user):
        """Test successful service retrieval via API."""
        # Setup
        mock_auth.return_value = mock_regular_user
        
        mock_use_case = AsyncMock()
        service = Service.create(
            category_id="cat_123",
            name="Basic Wash",
            description="Standard wash",
            price=Decimal("25.00"),
            duration_minutes=30,
        )
        service.id = "srv_123"
        mock_use_case.execute.return_value = service
        mock_use_case_dep.return_value = mock_use_case
        
        # Execute
        response = test_client.get("/services/srv_123")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "srv_123"
        assert data["name"] == "Basic Wash"
        assert data["price"] == "25.00"
        mock_use_case.execute.assert_called_once_with(
            service_id="srv_123",
            requesting_user_id="user_123",
        )
    
    @patch("app.features.services.api.router.get_current_user")
    @patch("app.features.services.api.router.GetServiceUseCase")
    def test_get_service_not_found(self, mock_use_case_dep, mock_auth, test_client, mock_regular_user):
        """Test service retrieval when not found."""
        # Setup
        mock_auth.return_value = mock_regular_user
        
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = ResourceNotFoundError("Service not found")
        mock_use_case_dep.return_value = mock_use_case
        
        # Execute
        response = test_client.get("/services/nonexistent")
        
        # Assert
        assert response.status_code == 404
        assert "Service not found" in response.json()["detail"]
    
    @patch("app.features.services.api.router.require_manager_or_admin")
    @patch("app.features.services.api.router.UpdateServicePriceUseCase")
    def test_update_service_price_success(self, mock_use_case_dep, mock_auth, test_client, mock_manager_user):
        """Test successful service price update via API."""
        # Setup
        mock_auth.return_value = mock_manager_user
        
        mock_use_case = AsyncMock()
        service = Service.create(
            category_id="cat_123",
            name="Basic Wash",
            description="Standard wash",
            price=Decimal("30.00"),  # Updated price
            duration_minutes=30,
        )
        service.id = "srv_123"
        
        mock_use_case.execute.return_value = {
            "service": service,
            "old_price": Decimal("25.00"),
            "new_price": Decimal("30.00"),
            "price_change_percent": Decimal("20.00"),
            "affected_bookings": 3,
            "customers_notified": 5,
        }
        mock_use_case_dep.return_value = mock_use_case
        
        # Execute
        response = test_client.patch(
            "/services/srv_123/price",
            json={
                "new_price": "30.00",
                "notify_customers": True,
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["service_id"] == "srv_123"
        assert data["old_price"] == "25.00"
        assert data["new_price"] == "30.00"
        assert data["affected_future_bookings"] == 3
        assert data["customers_notified"] == 5
    
    @patch("app.features.services.api.router.require_manager_or_admin")
    @patch("app.features.services.api.router.SetServicePopularUseCase")
    def test_set_service_popular_success(self, mock_use_case_dep, mock_auth, test_client, mock_manager_user):
        """Test setting service as popular via API."""
        # Setup
        mock_auth.return_value = mock_manager_user
        
        mock_use_case = AsyncMock()
        service = Service.create(
            category_id="cat_123",
            name="Premium Wash",
            description="Premium wash",
            price=Decimal("45.00"),
            duration_minutes=60,
            is_popular=True,
        )
        service.id = "srv_123"
        
        mock_use_case.execute.return_value = {
            "service": service,
            "category_popular_count": 3,
        }
        mock_use_case_dep.return_value = mock_use_case
        
        # Execute
        response = test_client.patch(
            "/services/srv_123/popular",
            json={"is_popular": True}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["service_id"] == "srv_123"
        assert data["name"] == "Premium Wash"
        assert data["is_popular"] is True
        assert data["category_popular_count"] == 3
        assert "popular" in data["message"]
    
    @patch("app.features.services.api.router.get_current_user")
    @patch("app.features.services.api.router.GetPopularServicesUseCase")
    def test_get_popular_services_success(self, mock_use_case_dep, mock_auth, test_client, mock_regular_user):
        """Test getting popular services via API."""
        # Setup
        mock_auth.return_value = mock_regular_user
        
        mock_use_case = AsyncMock()
        service = Service.create(
            category_id="cat_123",
            name="Premium Wash",
            description="Premium wash",
            price=Decimal("45.00"),
            duration_minutes=60,
            is_popular=True,
        )
        
        mock_use_case.execute.return_value = {
            "services": [service],
            "category_names": {service.category_id: "Exterior Cleaning"},
        }
        mock_use_case_dep.return_value = mock_use_case
        
        # Execute
        response = test_client.get("/services/popular?limit=5")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert len(data["services"]) == 1
        assert data["services"][0]["name"] == "Premium Wash"
        assert data["services"][0]["is_popular"] is True
        mock_use_case.execute.assert_called_once_with(
            limit=5,
            requesting_user_id="user_123",
        )
    
    @patch("app.features.services.api.router.get_current_user")
    @patch("app.features.services.api.router.SearchServicesUseCase")
    def test_search_services_success(self, mock_use_case_dep, mock_auth, test_client, mock_regular_user):
        """Test service search via API."""
        # Setup
        mock_auth.return_value = mock_regular_user
        
        mock_use_case = AsyncMock()
        service = Service.create(
            category_id="cat_123",
            name="Basic Wash",
            description="Standard car wash",
            price=Decimal("25.00"),
            duration_minutes=30,
        )
        
        mock_use_case.execute.return_value = {
            "services": [service],
            "category_names": {service.category_id: "Exterior Cleaning"},
        }
        mock_use_case_dep.return_value = mock_use_case
        
        # Execute
        response = test_client.get("/services/search?q=wash&limit=10")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["services"]) == 1
        assert data["services"][0]["name"] == "Basic Wash"
        assert data["filters_applied"]["search_query"] == "wash"
        mock_use_case.execute.assert_called_once_with(
            query="wash",
            category_id=None,
            limit=10,
            requesting_user_id="user_123",
        )
    
    @patch("app.features.services.api.router.require_admin")
    @patch("app.features.services.api.router.DeactivateServiceUseCase")
    def test_deactivate_service_success(self, mock_use_case_dep, mock_auth, test_client, mock_admin_user):
        """Test service deactivation via API."""
        # Setup
        mock_auth.return_value = mock_admin_user
        
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = None
        mock_use_case_dep.return_value = mock_use_case
        
        # Execute
        response = test_client.delete(
            "/services/srv_123?reason=No longer offered due to equipment issues"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Service deactivated successfully"
        mock_use_case.execute.assert_called_once_with(
            service_id="srv_123",
            reason="No longer offered due to equipment issues",
            deactivated_by="admin_123",
        )