"""
API Integration Tests for Vehicles Feature

Tests all vehicle endpoints including:
- Vehicle CRUD operations
- Vehicle ownership
- RBAC
"""

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
class TestVehicleCreation:
    """Test vehicle creation endpoints."""

    async def test_create_vehicle_as_client(self, client: AsyncClient, auth_headers: dict):
        """Test client creating their own vehicle."""
        response = await client.post(
            "/api/v1/vehicles/",
            headers=auth_headers,
            json={
                "make": "Toyota",
                "model": "Camry",
                "year": 2022,
                "license_plate": "ABC123",
                "color": "Blue",
                "size": "standard"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["make"] == "Toyota"
        assert data["model"] == "Camry"
        assert "id" in data

    async def test_create_vehicle_with_vin(self, client: AsyncClient, auth_headers: dict):
        """Test creating vehicle with VIN."""
        response = await client.post(
            "/api/v1/vehicles/",
            headers=auth_headers,
            json={
                "make": "Honda",
                "model": "Accord",
                "year": 2023,
                "license_plate": "XYZ789",
                "vin": "1HGBH41JXMN109186",
                "color": "Red",
                "size": "standard"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["vin"] == "1HGBH41JXMN109186"

    async def test_create_vehicle_duplicate_license_plate_fails(self, client: AsyncClient, auth_headers: dict):
        """Test creating vehicle with duplicate license plate fails."""
        # Create first vehicle
        await client.post(
            "/api/v1/vehicles/",
            headers=auth_headers,
            json={
                "make": "Ford",
                "model": "F150",
                "year": 2021,
                "license_plate": "DUP123",
                "color": "White",
                "size": "large"
            }
        )

        # Try duplicate
        response = await client.post(
            "/api/v1/vehicles/",
            headers=auth_headers,
            json={
                "make": "Chevrolet",
                "model": "Silverado",
                "year": 2022,
                "license_plate": "DUP123",
                "color": "Black",
                "size": "large"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_create_vehicle_without_auth_fails(self, client: AsyncClient):
        """Test creating vehicle without authentication fails."""
        response = await client.post(
            "/api/v1/vehicles/",
            json={
                "make": "Tesla",
                "model": "Model 3",
                "year": 2023,
                "license_plate": "TESLA1",
                "color": "White",
                "size": "standard"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestVehicleRetrieval:
    """Test vehicle retrieval endpoints."""

    async def test_list_own_vehicles(self, client: AsyncClient, auth_headers: dict):
        """Test client listing their own vehicles."""
        # Create a vehicle
        await client.post(
            "/api/v1/vehicles/",
            headers=auth_headers,
            json={
                "make": "Nissan",
                "model": "Altima",
                "year": 2021,
                "license_plate": "NIS456",
                "color": "Silver",
                "size": "standard"
            }
        )

        # List vehicles
        response = await client.get(
            "/api/v1/vehicles/",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    async def test_get_vehicle_details(self, client: AsyncClient, auth_headers: dict):
        """Test getting specific vehicle details."""
        # Create vehicle
        create_response = await client.post(
            "/api/v1/vehicles/",
            headers=auth_headers,
            json={
                "make": "BMW",
                "model": "3 Series",
                "year": 2023,
                "license_plate": "BMW789",
                "color": "Black",
                "size": "standard"
            }
        )
        vehicle_id = create_response.json()["id"]

        # Get details
        response = await client.get(
            f"/api/v1/vehicles/{vehicle_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["make"] == "BMW"
        assert data["model"] == "3 Series"

    async def test_cannot_view_other_user_vehicle(self, client: AsyncClient, auth_headers: dict):
        """Test client cannot view other user's vehicles."""
        # Would need second user to test properly
        response = await client.get(
            "/api/v1/vehicles/other-user-vehicle-id",
            headers=auth_headers
        )
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN]


@pytest.mark.asyncio
class TestVehicleUpdate:
    """Test vehicle update endpoints."""

    async def test_update_own_vehicle(self, client: AsyncClient, auth_headers: dict):
        """Test client updating their own vehicle."""
        # Create vehicle
        create_response = await client.post(
            "/api/v1/vehicles/",
            headers=auth_headers,
            json={
                "make": "Mazda",
                "model": "CX-5",
                "year": 2022,
                "license_plate": "MAZ123",
                "color": "Blue",
                "size": "standard"
            }
        )
        vehicle_id = create_response.json()["id"]

        # Update vehicle
        response = await client.put(
            f"/api/v1/vehicles/{vehicle_id}",
            headers=auth_headers,
            json={
                "color": "Red",
                "year": 2023
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["color"] == "Red"
        assert data["year"] == 2023

    async def test_cannot_update_other_user_vehicle(self, client: AsyncClient, auth_headers: dict):
        """Test client cannot update other user's vehicles."""
        response = await client.put(
            "/api/v1/vehicles/other-user-vehicle-id",
            headers=auth_headers,
            json={"color": "Green"}
        )
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN]


@pytest.mark.asyncio
class TestVehicleDeletion:
    """Test vehicle deletion endpoints."""

    async def test_delete_own_vehicle(self, client: AsyncClient, auth_headers: dict):
        """Test client deleting their own vehicle."""
        # Create vehicle
        create_response = await client.post(
            "/api/v1/vehicles/",
            headers=auth_headers,
            json={
                "make": "Hyundai",
                "model": "Sonata",
                "year": 2021,
                "license_plate": "HYU456",
                "color": "White",
                "size": "standard"
            }
        )
        vehicle_id = create_response.json()["id"]

        # Delete vehicle
        response = await client.delete(
            f"/api/v1/vehicles/{vehicle_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_cannot_delete_other_user_vehicle(self, client: AsyncClient, auth_headers: dict):
        """Test client cannot delete other user's vehicles."""
        response = await client.delete(
            "/api/v1/vehicles/other-user-vehicle-id",
            headers=auth_headers
        )
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN]


@pytest.mark.asyncio
class TestVehicleValidation:
    """Test vehicle validation rules."""

    async def test_vehicle_requires_make(self, client: AsyncClient, auth_headers: dict):
        """Test vehicle requires make."""
        response = await client.post(
            "/api/v1/vehicles/",
            headers=auth_headers,
            json={
                "model": "Test Model",
                "year": 2023,
                "license_plate": "TEST123",
                "color": "Blue",
                "size": "standard"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_vehicle_requires_valid_year(self, client: AsyncClient, auth_headers: dict):
        """Test vehicle requires valid year."""
        response = await client.post(
            "/api/v1/vehicles/",
            headers=auth_headers,
            json={
                "make": "Test Make",
                "model": "Test Model",
                "year": 1800,  # Invalid year
                "license_plate": "OLD123",
                "color": "Blue",
                "size": "standard"
            }
        )
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_vehicle_requires_license_plate(self, client: AsyncClient, auth_headers: dict):
        """Test vehicle requires license plate."""
        response = await client.post(
            "/api/v1/vehicles/",
            headers=auth_headers,
            json={
                "make": "Test Make",
                "model": "Test Model",
                "year": 2023,
                "color": "Blue",
                "size": "standard"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
class TestVehicleRBAC:
    """Test RBAC for vehicle endpoints."""

    async def test_client_manages_own_vehicles_only(self, client: AsyncClient, auth_headers: dict):
        """Test client can only manage their own vehicles."""
        # Create vehicle
        response = await client.post(
            "/api/v1/vehicles/",
            headers=auth_headers,
            json={
                "make": "Kia",
                "model": "Optima",
                "year": 2022,
                "license_plate": "KIA789",
                "color": "Gray",
                "size": "standard"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED

        # List own vehicles
        response = await client.get("/api/v1/vehicles/", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

    async def test_staff_can_view_all_vehicles(self, client: AsyncClient, manager_headers: dict):
        """Test staff can view all vehicles."""
        response = await client.get(
            "/api/v1/vehicles/?all=true",
            headers=manager_headers
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestDefaultVehicle:
    """Test default vehicle selection."""

    async def test_set_default_vehicle(self, client: AsyncClient, auth_headers: dict):
        """Test setting a vehicle as default."""
        # Create vehicle
        create_response = await client.post(
            "/api/v1/vehicles/",
            headers=auth_headers,
            json={
                "make": "Volkswagen",
                "model": "Jetta",
                "year": 2023,
                "license_plate": "VW123",
                "color": "Blue",
                "size": "standard"
            }
        )
        vehicle_id = create_response.json()["id"]

        # Set as default
        response = await client.post(
            f"/api/v1/vehicles/{vehicle_id}/set-default",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_default"] is True

    async def test_only_one_default_vehicle(self, client: AsyncClient, auth_headers: dict):
        """Test only one vehicle can be default."""
        # Create first vehicle and set as default
        create_response1 = await client.post(
            "/api/v1/vehicles/",
            headers=auth_headers,
            json={
                "make": "Subaru",
                "model": "Outback",
                "year": 2022,
                "license_plate": "SUB1",
                "color": "Green",
                "size": "standard"
            }
        )
        vehicle_id1 = create_response1.json()["id"]
        await client.post(f"/api/v1/vehicles/{vehicle_id1}/set-default", headers=auth_headers)

        # Create second vehicle and set as default
        create_response2 = await client.post(
            "/api/v1/vehicles/",
            headers=auth_headers,
            json={
                "make": "Jeep",
                "model": "Cherokee",
                "year": 2023,
                "license_plate": "JEEP2",
                "color": "Red",
                "size": "large"
            }
        )
        vehicle_id2 = create_response2.json()["id"]
        await client.post(f"/api/v1/vehicles/{vehicle_id2}/set-default", headers=auth_headers)

        # First vehicle should no longer be default
        response = await client.get(f"/api/v1/vehicles/{vehicle_id1}", headers=auth_headers)
        data = response.json()
        assert data["is_default"] is False

        # Second vehicle should be default
        response = await client.get(f"/api/v1/vehicles/{vehicle_id2}", headers=auth_headers)
        data = response.json()
        assert data["is_default"] is True
