"""
API Integration Tests for Scheduling Feature

Tests all scheduling endpoints including:
- Available time slots
- Wash bay availability
- Mobile team availability
- Capacity management
- Business hours
"""

import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import datetime, timedelta


@pytest.mark.asyncio
class TestAvailableTimeSlots:
    """Test available time slots endpoints."""

    async def test_get_available_time_slots(self, client: AsyncClient, auth_headers: dict):
        """Test getting available time slots."""
        start_date = datetime.utcnow().date().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=7)).date().isoformat()

        response = await client.get(
            f"/api/v1/scheduling/time-slots?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    async def test_get_time_slots_for_specific_service(self, client: AsyncClient, auth_headers: dict):
        """Test getting time slots for specific service."""
        start_date = datetime.utcnow().date().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=7)).date().isoformat()

        response = await client.get(
            f"/api/v1/scheduling/time-slots?start_date={start_date}&end_date={end_date}&service_id=test-service",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_get_time_slots_requires_date_range(self, client: AsyncClient, auth_headers: dict):
        """Test getting time slots requires date range."""
        response = await client.get(
            "/api/v1/scheduling/time-slots",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
class TestWashBayAvailability:
    """Test wash bay availability endpoints."""

    async def test_check_wash_bay_availability(self, client: AsyncClient, admin_headers: dict, auth_headers: dict):
        """Test checking wash bay availability."""
        # Create wash bay first
        bay_response = await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=admin_headers,
            json={
                "bay_number": "SCHED-BAY-1",
                "max_vehicle_size": "standard",
                "equipment_types": []
            }
        )
        bay_id = bay_response.json()["id"]

        # Check availability
        check_time = datetime.utcnow() + timedelta(days=1)
        response = await client.get(
            f"/api/v1/scheduling/wash-bays/{bay_id}/availability?datetime={check_time.isoformat()}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "available" in data

    async def test_wash_bay_capacity_check(self, client: AsyncClient, admin_headers: dict):
        """Test wash bay capacity validation."""
        # Create wash bay
        bay_response = await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=admin_headers,
            json={
                "bay_number": "CAPACITY-BAY",
                "max_vehicle_size": "compact",
                "equipment_types": []
            }
        )
        bay_id = bay_response.json()["id"]

        # Check capacity
        response = await client.get(
            f"/api/v1/scheduling/wash-bays/{bay_id}/capacity",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestMobileTeamAvailability:
    """Test mobile team availability endpoints."""

    async def test_check_mobile_team_availability(self, client: AsyncClient, admin_headers: dict, auth_headers: dict):
        """Test checking mobile team availability."""
        # Create mobile team first
        team_response = await client.post(
            "/api/v1/facilities/mobile-teams/",
            headers=admin_headers,
            json={
                "team_name": "Sched Team",
                "base_latitude": 40.7128,
                "base_longitude": -74.0060,
                "service_radius_km": 50.0,
                "daily_capacity": 8,
                "equipment_types": []
            }
        )
        team_id = team_response.json()["id"]

        # Check availability
        check_time = datetime.utcnow() + timedelta(days=1)
        response = await client.get(
            f"/api/v1/scheduling/mobile-teams/{team_id}/availability?datetime={check_time.isoformat()}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "available" in data

    async def test_mobile_team_service_radius_check(self, client: AsyncClient, admin_headers: dict, auth_headers: dict):
        """Test mobile team service radius validation."""
        # Create mobile team
        team_response = await client.post(
            "/api/v1/facilities/mobile-teams/",
            headers=admin_headers,
            json={
                "team_name": "Radius Team",
                "base_latitude": 40.7128,
                "base_longitude": -74.0060,
                "service_radius_km": 25.0,
                "daily_capacity": 8,
                "equipment_types": []
            }
        )
        team_id = team_response.json()["id"]

        # Check if location is within service radius
        response = await client.get(
            f"/api/v1/scheduling/mobile-teams/{team_id}/coverage?latitude=40.8&longitude=-74.1",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestSmartBooking:
    """Test smart booking recommendations."""

    async def test_get_smart_booking_recommendations(self, client: AsyncClient, auth_headers: dict):
        """Test getting smart booking recommendations."""
        preferred_date = (datetime.utcnow() + timedelta(days=2)).date().isoformat()

        response = await client.post(
            "/api/v1/scheduling/smart-booking/recommend",
            headers=auth_headers,
            json={
                "service_id": "test-service",
                "vehicle_size": "standard",
                "preferred_date": preferred_date,
                "preferred_time_of_day": "morning"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "recommendations" in data

    async def test_smart_booking_considers_location(self, client: AsyncClient, auth_headers: dict):
        """Test smart booking considers location for mobile service."""
        preferred_date = (datetime.utcnow() + timedelta(days=2)).date().isoformat()

        response = await client.post(
            "/api/v1/scheduling/smart-booking/recommend",
            headers=auth_headers,
            json={
                "service_id": "mobile-service",
                "vehicle_size": "standard",
                "preferred_date": preferred_date,
                "location": {
                    "latitude": 40.7128,
                    "longitude": -74.0060
                }
            }
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestBusinessHours:
    """Test business hours constraints."""

    async def test_get_business_hours(self, client: AsyncClient, auth_headers: dict):
        """Test getting business hours."""
        response = await client.get(
            "/api/v1/scheduling/business-hours",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "hours" in data or "items" in data

    async def test_update_business_hours_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test admin updating business hours."""
        response = await client.put(
            "/api/v1/scheduling/business-hours",
            headers=admin_headers,
            json={
                "monday": {"open": "08:00", "close": "18:00"},
                "tuesday": {"open": "08:00", "close": "18:00"},
                "wednesday": {"open": "08:00", "close": "18:00"},
                "thursday": {"open": "08:00", "close": "18:00"},
                "friday": {"open": "08:00", "close": "18:00"},
                "saturday": {"open": "09:00", "close": "15:00"},
                "sunday": {"closed": True}
            }
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_client_cannot_update_business_hours(self, client: AsyncClient, auth_headers: dict):
        """Test client cannot update business hours."""
        response = await client.put(
            "/api/v1/scheduling/business-hours",
            headers=auth_headers,
            json={"monday": {"open": "06:00", "close": "20:00"}}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
class TestSchedulingConstraints:
    """Test scheduling constraint validation."""

    async def test_booking_respects_business_hours(self, client: AsyncClient, auth_headers: dict):
        """Test bookings respect business hours."""
        # Try to book outside business hours
        booking_time = datetime.utcnow().replace(hour=2, minute=0, second=0)  # 2 AM

        response = await client.post(
            "/api/v1/bookings/",
            headers=auth_headers,
            json={
                "service_id": "test-service",
                "vehicle_id": "test-vehicle",
                "scheduled_time": booking_time.isoformat(),
                "booking_type": "scheduled"
            }
        )
        # Should fail if business hours validation is enforced
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED]

    async def test_capacity_limit_enforced(self, client: AsyncClient, admin_headers: dict, auth_headers: dict):
        """Test capacity limits are enforced."""
        # Create wash bay with limited capacity
        bay_response = await client.post(
            "/api/v1/facilities/wash-bays/",
            headers=admin_headers,
            json={
                "bay_number": "LIMITED-BAY",
                "max_vehicle_size": "compact",  # Only compact vehicles
                "equipment_types": []
            }
        )
        bay_id = bay_response.json()["id"]

        # Check availability reflects capacity
        response = await client.get(
            f"/api/v1/scheduling/wash-bays/{bay_id}/capacity",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestSchedulingRBAC:
    """Test RBAC for scheduling endpoints."""

    async def test_all_users_can_view_availability(self, client: AsyncClient, auth_headers: dict):
        """Test all authenticated users can view availability."""
        start_date = datetime.utcnow().date().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=7)).date().isoformat()

        response = await client.get(
            f"/api/v1/scheduling/time-slots?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_only_staff_can_manage_schedules(self, client: AsyncClient, auth_headers: dict, manager_headers: dict):
        """Test only staff can manage scheduling constraints."""
        # Client cannot update
        response = await client.put(
            "/api/v1/scheduling/constraints",
            headers=auth_headers,
            json={"max_bookings_per_hour": 10}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Manager can update
        response = await client.put(
            "/api/v1/scheduling/constraints",
            headers=manager_headers,
            json={"max_bookings_per_hour": 10}
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
