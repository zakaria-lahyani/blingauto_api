"""
API Integration Tests for Services Feature

Tests all service endpoints including:
- Service categories CRUD
- Services CRUD
- Service pricing
- RBAC
"""

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
class TestServiceCategoryOperations:
    """Test service category CRUD operations."""

    async def test_create_category_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test admin creating service category."""
        response = await client.post(
            "/api/v1/services/categories/",
            headers=admin_headers,
            json={
                "name": "Premium Wash",
                "description": "Premium washing services",
                "display_order": 1
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Premium Wash"
        assert "id" in data

    async def test_list_categories(self, client: AsyncClient, auth_headers: dict):
        """Test listing service categories (public)."""
        response = await client.get(
            "/api/v1/services/categories/",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data

    async def test_update_category_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test admin updating category."""
        # Create category
        create_response = await client.post(
            "/api/v1/services/categories/",
            headers=admin_headers,
            json={
                "name": "Basic Wash",
                "description": "Basic washing services"
            }
        )
        category_id = create_response.json()["id"]

        # Update category
        response = await client.put(
            f"/api/v1/services/categories/{category_id}",
            headers=admin_headers,
            json={
                "name": "Basic Wash Updated",
                "description": "Updated description"
            }
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_delete_category_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test admin deleting category."""
        # Create category
        create_response = await client.post(
            "/api/v1/services/categories/",
            headers=admin_headers,
            json={"name": "Delete Me", "description": "To be deleted"}
        )
        category_id = create_response.json()["id"]

        # Delete category
        response = await client.delete(
            f"/api/v1/services/categories/{category_id}",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_client_cannot_create_category(self, client: AsyncClient, auth_headers: dict):
        """Test client cannot create categories."""
        response = await client.post(
            "/api/v1/services/categories/",
            headers=auth_headers,
            json={"name": "Forbidden", "description": "Should fail"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
class TestServiceOperations:
    """Test service CRUD operations."""

    async def test_create_service_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test admin creating service."""
        # Create category first
        cat_response = await client.post(
            "/api/v1/services/categories/",
            headers=admin_headers,
            json={"name": "Wash Category", "description": "Test"}
        )
        category_id = cat_response.json()["id"]

        # Create service
        response = await client.post(
            "/api/v1/services/",
            headers=admin_headers,
            json={
                "name": "Exterior Wash",
                "description": "Complete exterior wash",
                "category_id": category_id,
                "base_price": 25.00,
                "duration_minutes": 30,
                "vehicle_size": "standard"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Exterior Wash"
        assert float(data["base_price"]) == 25.00

    async def test_list_services(self, client: AsyncClient, auth_headers: dict):
        """Test listing services (public)."""
        response = await client.get(
            "/api/v1/services/",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data

    async def test_filter_services_by_category(self, client: AsyncClient, admin_headers: dict, auth_headers: dict):
        """Test filtering services by category."""
        # Create category and service
        cat_response = await client.post(
            "/api/v1/services/categories/",
            headers=admin_headers,
            json={"name": "Filter Test", "description": "Test"}
        )
        category_id = cat_response.json()["id"]

        await client.post(
            "/api/v1/services/",
            headers=admin_headers,
            json={
                "name": "Service in category",
                "description": "Test",
                "category_id": category_id,
                "base_price": 30.00,
                "duration_minutes": 45,
                "vehicle_size": "standard"
            }
        )

        # Filter by category
        response = await client.get(
            f"/api/v1/services/?category_id={category_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for service in data["items"]:
            assert service["category_id"] == category_id

    async def test_get_service_details(self, client: AsyncClient, admin_headers: dict):
        """Test getting service details."""
        # Create category and service
        cat_response = await client.post(
            "/api/v1/services/categories/",
            headers=admin_headers,
            json={"name": "Detail Cat", "description": "Test"}
        )
        category_id = cat_response.json()["id"]

        create_response = await client.post(
            "/api/v1/services/",
            headers=admin_headers,
            json={
                "name": "Detail Service",
                "description": "Detailed",
                "category_id": category_id,
                "base_price": 40.00,
                "duration_minutes": 60,
                "vehicle_size": "large"
            }
        )
        service_id = create_response.json()["id"]

        # Get details
        response = await client.get(
            f"/api/v1/services/{service_id}",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Detail Service"

    async def test_update_service_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test admin updating service."""
        # Create service
        cat_response = await client.post(
            "/api/v1/services/categories/",
            headers=admin_headers,
            json={"name": "Update Cat", "description": "Test"}
        )
        category_id = cat_response.json()["id"]

        create_response = await client.post(
            "/api/v1/services/",
            headers=admin_headers,
            json={
                "name": "Update Service",
                "description": "To be updated",
                "category_id": category_id,
                "base_price": 20.00,
                "duration_minutes": 30,
                "vehicle_size": "standard"
            }
        )
        service_id = create_response.json()["id"]

        # Update service
        response = await client.put(
            f"/api/v1/services/{service_id}",
            headers=admin_headers,
            json={
                "name": "Updated Service",
                "base_price": 25.00,
                "duration_minutes": 40
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Service"
        assert float(data["base_price"]) == 25.00

    async def test_delete_service_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test admin deleting service."""
        # Create service
        cat_response = await client.post(
            "/api/v1/services/categories/",
            headers=admin_headers,
            json={"name": "Delete Cat", "description": "Test"}
        )
        category_id = cat_response.json()["id"]

        create_response = await client.post(
            "/api/v1/services/",
            headers=admin_headers,
            json={
                "name": "Delete Service",
                "description": "To be deleted",
                "category_id": category_id,
                "base_price": 15.00,
                "duration_minutes": 20,
                "vehicle_size": "compact"
            }
        )
        service_id = create_response.json()["id"]

        # Delete service
        response = await client.delete(
            f"/api/v1/services/{service_id}",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestServiceValidation:
    """Test service validation rules."""

    async def test_service_requires_positive_price(self, client: AsyncClient, admin_headers: dict):
        """Test service requires positive price."""
        cat_response = await client.post(
            "/api/v1/services/categories/",
            headers=admin_headers,
            json={"name": "Price Test", "description": "Test"}
        )
        category_id = cat_response.json()["id"]

        response = await client.post(
            "/api/v1/services/",
            headers=admin_headers,
            json={
                "name": "Invalid Price",
                "description": "Test",
                "category_id": category_id,
                "base_price": -10.00,  # Invalid
                "duration_minutes": 30,
                "vehicle_size": "standard"
            }
        )
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_service_requires_positive_duration(self, client: AsyncClient, admin_headers: dict):
        """Test service requires positive duration."""
        cat_response = await client.post(
            "/api/v1/services/categories/",
            headers=admin_headers,
            json={"name": "Duration Test", "description": "Test"}
        )
        category_id = cat_response.json()["id"]

        response = await client.post(
            "/api/v1/services/",
            headers=admin_headers,
            json={
                "name": "Invalid Duration",
                "description": "Test",
                "category_id": category_id,
                "base_price": 20.00,
                "duration_minutes": 0,  # Invalid
                "vehicle_size": "standard"
            }
        )
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


@pytest.mark.asyncio
class TestServiceRBAC:
    """Test RBAC for service endpoints."""

    async def test_client_can_view_services(self, client: AsyncClient, auth_headers: dict):
        """Test client can view services."""
        response = await client.get("/api/v1/services/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

        response = await client.get("/api/v1/services/categories/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

    async def test_client_cannot_modify_services(self, client: AsyncClient, auth_headers: dict):
        """Test client cannot modify services."""
        response = await client.post(
            "/api/v1/services/categories/",
            headers=auth_headers,
            json={"name": "Forbidden", "description": "Test"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_manager_can_manage_services(self, client: AsyncClient, manager_headers: dict):
        """Test manager can manage services."""
        # Create category
        response = await client.post(
            "/api/v1/services/categories/",
            headers=manager_headers,
            json={"name": "Manager Category", "description": "Test"}
        )
        assert response.status_code == status.HTTP_201_CREATED
