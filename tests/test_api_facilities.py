"""
API Integration Tests for Facilities Feature

Tests all facilities endpoints including:
- Wash bays CRUD operations
- Mobile teams CRUD operations
- RBAC (admin/manager can manage, staff can view)
- Validation rules
"""

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
class TestWashBayCreation:
    """Test wash bay creation endpoints."""

    async def test_create_wash_bay_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test admin creating a wash bay."""
        response = await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=admin_headers,
            json={
                "bay_number": "BAY-001",
                "max_vehicle_size": "standard",
                "equipment_types": ["pressure_washer", "foam_cannon"],
                "latitude": 40.7128,
                "longitude": -74.0060
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["bay_number"] == "BAY-001"
        assert data["status"] == "active"
        assert "id" in data

    async def test_create_wash_bay_as_manager(self, client: AsyncClient, manager_headers: dict):
        """Test manager creating a wash bay."""
        response = await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=manager_headers,
            json={
                "bay_number": "BAY-002",
                "max_vehicle_size": "large",
                "equipment_types": ["pressure_washer", "vacuum"]
            }
        )
        assert response.status_code == status.HTTP_201_CREATED

    async def test_create_wash_bay_as_client_fails(self, client: AsyncClient, auth_headers: dict):
        """Test client cannot create wash bays."""
        response = await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=auth_headers,
            json={
                "bay_number": "BAY-003",
                "max_vehicle_size": "standard",
                "equipment_types": []
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_create_wash_bay_duplicate_number_fails(self, client: AsyncClient, admin_headers: dict):
        """Test creating wash bay with duplicate bay number fails."""
        # Create first bay
        await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=admin_headers,
            json={
                "bay_number": "BAY-DUP",
                "max_vehicle_size": "standard",
                "equipment_types": []
            }
        )

        # Try to create duplicate
        response = await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=admin_headers,
            json={
                "bay_number": "BAY-DUP",
                "max_vehicle_size": "large",
                "equipment_types": []
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
class TestWashBayRetrieval:
    """Test wash bay retrieval endpoints."""

    async def test_list_wash_bays_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test admin listing wash bays."""
        # Create a wash bay first
        await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=admin_headers,
            json={
                "bay_number": "BAY-LIST-1",
                "max_vehicle_size": "standard",
                "equipment_types": []
            }
        )

        response = await client.get(
            "/api/v1/facilities/wash-bays/",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    async def test_list_wash_bays_as_client(self, client: AsyncClient, auth_headers: dict):
        """Test client can list wash bays (read-only)."""
        response = await client.get(
            "/api/v1/facilities/wash-bays/",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_filter_wash_bays_by_status(self, client: AsyncClient, admin_headers: dict):
        """Test filtering wash bays by status."""
        response = await client.get(
            "/api/v1/facilities/wash-bays/?status=active",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for bay in data["items"]:
            assert bay["status"] == "active"

    async def test_get_wash_bay_details(self, client: AsyncClient, admin_headers: dict):
        """Test getting specific wash bay details."""
        # Create wash bay
        create_response = await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=admin_headers,
            json={
                "bay_number": "BAY-DETAIL",
                "max_vehicle_size": "standard",
                "equipment_types": ["pressure_washer"]
            }
        )
        bay_id = create_response.json()["id"]

        # Get details
        response = await client.get(
            f"/api/v1/facilities/wash-bays/{bay_id}",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["bay_number"] == "BAY-DETAIL"


@pytest.mark.asyncio
class TestWashBayUpdate:
    """Test wash bay update endpoints."""

    async def test_update_wash_bay_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test admin updating wash bay."""
        # Create wash bay
        create_response = await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=admin_headers,
            json={
                "bay_number": "BAY-UPDATE",
                "max_vehicle_size": "standard",
                "equipment_types": []
            }
        )
        bay_id = create_response.json()["id"]

        # Update wash bay
        response = await client.put(
            f"/api/v1/facilities/wash-bays/{bay_id}",
            headers=admin_headers,
            json={
                "max_vehicle_size": "large",
                "equipment_types": ["pressure_washer", "foam_cannon"],
                "status": "maintenance"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["max_vehicle_size"] == "large"
        assert data["status"] == "maintenance"

    async def test_update_wash_bay_as_client_fails(self, client: AsyncClient, auth_headers: dict, admin_headers: dict):
        """Test client cannot update wash bays."""
        # Create wash bay as admin
        create_response = await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=admin_headers,
            json={
                "bay_number": "BAY-NO-UPDATE",
                "max_vehicle_size": "standard",
                "equipment_types": []
            }
        )
        bay_id = create_response.json()["id"]

        # Try to update as client
        response = await client.put(
            f"/api/v1/facilities/wash-bays/{bay_id}",
            headers=auth_headers,
            json={"status": "inactive"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
class TestWashBayDeletion:
    """Test wash bay deletion endpoints."""

    async def test_delete_wash_bay_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test admin deleting wash bay (soft delete)."""
        # Create wash bay
        create_response = await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=admin_headers,
            json={
                "bay_number": "BAY-DELETE",
                "max_vehicle_size": "standard",
                "equipment_types": []
            }
        )
        bay_id = create_response.json()["id"]

        # Delete wash bay
        response = await client.delete(
            f"/api/v1/facilities/wash-bays/{bay_id}",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_delete_wash_bay_as_manager_fails(self, client: AsyncClient, manager_headers: dict, admin_headers: dict):
        """Test manager cannot delete wash bays (admin only)."""
        # Create wash bay as admin
        create_response = await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=admin_headers,
            json={
                "bay_number": "BAY-NO-DEL",
                "max_vehicle_size": "standard",
                "equipment_types": []
            }
        )
        bay_id = create_response.json()["id"]

        # Try to delete as manager
        response = await client.delete(
            f"/api/v1/facilities/wash-bays/{bay_id}",
            headers=manager_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
class TestMobileTeamCreation:
    """Test mobile team creation endpoints."""

    async def test_create_mobile_team_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test admin creating a mobile team."""
        response = await client.post(
            "/api/v1/facilities/mobile-teams/",
            headers=admin_headers,
            json={
                "team_name": "Team Alpha",
                "base_latitude": 40.7128,
                "base_longitude": -74.0060,
                "service_radius_km": 50.0,
                "daily_capacity": 8,
                "equipment_types": ["pressure_washer", "vacuum", "detailing_kit"]
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["team_name"] == "Team Alpha"
        assert data["status"] == "active"
        assert data["daily_capacity"] == 8

    async def test_create_mobile_team_as_manager(self, client: AsyncClient, manager_headers: dict):
        """Test manager creating a mobile team."""
        response = await client.post(
            "/api/v1/facilities/mobile-teams/",
            headers=manager_headers,
            json={
                "team_name": "Team Beta",
                "base_latitude": 34.0522,
                "base_longitude": -118.2437,
                "service_radius_km": 30.0,
                "daily_capacity": 6,
                "equipment_types": []
            }
        )
        assert response.status_code == status.HTTP_201_CREATED

    async def test_create_mobile_team_duplicate_name_fails(self, client: AsyncClient, admin_headers: dict):
        """Test creating mobile team with duplicate name fails."""
        # Create first team
        await client.post(
            "/api/v1/facilities/mobile-teams/",
            headers=admin_headers,
            json={
                "team_name": "Team Duplicate",
                "base_latitude": 40.7128,
                "base_longitude": -74.0060,
                "service_radius_km": 50.0,
                "daily_capacity": 8,
                "equipment_types": []
            }
        )

        # Try to create duplicate
        response = await client.post(
            "/api/v1/facilities/mobile-teams/",
            headers=admin_headers,
            json={
                "team_name": "Team Duplicate",
                "base_latitude": 34.0522,
                "base_longitude": -118.2437,
                "service_radius_km": 30.0,
                "daily_capacity": 6,
                "equipment_types": []
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_create_mobile_team_invalid_capacity_fails(self, client: AsyncClient, admin_headers: dict):
        """Test creating mobile team with invalid capacity fails."""
        response = await client.post(
            "/api/v1/facilities/mobile-teams/",
            headers=admin_headers,
            json={
                "team_name": "Team Invalid",
                "base_latitude": 40.7128,
                "base_longitude": -74.0060,
                "service_radius_km": 50.0,
                "daily_capacity": -5,  # Invalid negative capacity
                "equipment_types": []
            }
        )
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


@pytest.mark.asyncio
class TestMobileTeamRetrieval:
    """Test mobile team retrieval endpoints."""

    async def test_list_mobile_teams(self, client: AsyncClient, admin_headers: dict):
        """Test listing mobile teams."""
        # Create a mobile team first
        await client.post(
            "/api/v1/facilities/mobile-teams/",
            headers=admin_headers,
            json={
                "team_name": "Team List",
                "base_latitude": 40.7128,
                "base_longitude": -74.0060,
                "service_radius_km": 50.0,
                "daily_capacity": 8,
                "equipment_types": []
            }
        )

        response = await client.get(
            "/api/v1/facilities/mobile-teams/",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    async def test_filter_mobile_teams_by_status(self, client: AsyncClient, admin_headers: dict):
        """Test filtering mobile teams by status."""
        response = await client.get(
            "/api/v1/facilities/mobile-teams/?status=active",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for team in data["items"]:
            assert team["status"] == "active"

    async def test_get_mobile_team_details(self, client: AsyncClient, admin_headers: dict):
        """Test getting specific mobile team details."""
        # Create mobile team
        create_response = await client.post(
            "/api/v1/facilities/mobile-teams/",
            headers=admin_headers,
            json={
                "team_name": "Team Detail",
                "base_latitude": 40.7128,
                "base_longitude": -74.0060,
                "service_radius_km": 50.0,
                "daily_capacity": 8,
                "equipment_types": ["pressure_washer"]
            }
        )
        team_id = create_response.json()["id"]

        # Get details
        response = await client.get(
            f"/api/v1/facilities/mobile-teams/{team_id}",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["team_name"] == "Team Detail"


@pytest.mark.asyncio
class TestMobileTeamUpdate:
    """Test mobile team update endpoints."""

    async def test_update_mobile_team(self, client: AsyncClient, admin_headers: dict):
        """Test updating mobile team."""
        # Create mobile team
        create_response = await client.post(
            "/api/v1/facilities/mobile-teams/",
            headers=admin_headers,
            json={
                "team_name": "Team Update",
                "base_latitude": 40.7128,
                "base_longitude": -74.0060,
                "service_radius_km": 50.0,
                "daily_capacity": 8,
                "equipment_types": []
            }
        )
        team_id = create_response.json()["id"]

        # Update mobile team
        response = await client.put(
            f"/api/v1/facilities/mobile-teams/{team_id}",
            headers=admin_headers,
            json={
                "service_radius_km": 75.0,
                "daily_capacity": 10,
                "equipment_types": ["pressure_washer", "vacuum"]
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["service_radius_km"] == "75.00"
        assert data["daily_capacity"] == 10


@pytest.mark.asyncio
class TestMobileTeamDeletion:
    """Test mobile team deletion endpoints."""

    async def test_delete_mobile_team_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test admin deleting mobile team (soft delete)."""
        # Create mobile team
        create_response = await client.post(
            "/api/v1/facilities/mobile-teams/",
            headers=admin_headers,
            json={
                "team_name": "Team Delete",
                "base_latitude": 40.7128,
                "base_longitude": -74.0060,
                "service_radius_km": 50.0,
                "daily_capacity": 8,
                "equipment_types": []
            }
        )
        team_id = create_response.json()["id"]

        # Delete mobile team
        response = await client.delete(
            f"/api/v1/facilities/mobile-teams/{team_id}",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestFacilitiesRBAC:
    """Test RBAC for facilities endpoints."""

    async def test_client_cannot_create_facilities(self, client: AsyncClient, auth_headers: dict):
        """Test client cannot create facilities."""
        # Try wash bay
        response = await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=auth_headers,
            json={
                "bay_number": "BAY-FORBIDDEN",
                "max_vehicle_size": "standard",
                "equipment_types": []
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Try mobile team
        response = await client.post(
            "/api/v1/facilities/mobile-teams/",
            headers=auth_headers,
            json={
                "team_name": "Team Forbidden",
                "base_latitude": 40.7128,
                "base_longitude": -74.0060,
                "service_radius_km": 50.0,
                "daily_capacity": 8,
                "equipment_types": []
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_client_can_view_facilities(self, client: AsyncClient, auth_headers: dict):
        """Test client can view facilities (read-only)."""
        # View wash bays
        response = await client.get(
            "/api/v1/facilities/wash-bays/",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

        # View mobile teams
        response = await client.get(
            "/api/v1/facilities/mobile-teams/",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_manager_can_create_and_update(self, client: AsyncClient, manager_headers: dict):
        """Test manager can create and update facilities."""
        # Create wash bay
        create_response = await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=manager_headers,
            json={
                "bay_number": "BAY-MGR",
                "max_vehicle_size": "standard",
                "equipment_types": []
            }
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        bay_id = create_response.json()["id"]

        # Update wash bay
        update_response = await client.put(
            f"/api/v1/facilities/wash-bays/{bay_id}",
            headers=manager_headers,
            json={"status": "maintenance"}
        )
        assert update_response.status_code == status.HTTP_200_OK

    async def test_only_admin_can_delete(self, client: AsyncClient, manager_headers: dict, admin_headers: dict):
        """Test only admin can delete facilities."""
        # Create wash bay as admin
        create_response = await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=admin_headers,
            json={
                "bay_number": "BAY-ADMIN-DEL",
                "max_vehicle_size": "standard",
                "equipment_types": []
            }
        )
        bay_id = create_response.json()["id"]

        # Manager cannot delete
        response = await client.delete(
            f"/api/v1/facilities/wash-bays/{bay_id}",
            headers=manager_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Admin can delete
        response = await client.delete(
            f"/api/v1/facilities/wash-bays/{bay_id}",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
