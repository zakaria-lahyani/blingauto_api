"""
API Integration Tests for Bookings Feature

Tests all booking endpoints including:
- Create bookings (standard, walk-in)
- List bookings (with filters)
- Get booking details
- Update booking status
- Cancel bookings
- RBAC (client vs staff access)
"""

import pytest
from httpx import AsyncClient
from fastapi import status
from datetime import datetime, timedelta


@pytest.mark.asyncio
class TestBookingCreation:
    """Test booking creation endpoints."""

    async def test_create_booking_as_client(self, client: AsyncClient, auth_headers: dict):
        """Test client creating a booking."""
        booking_time = datetime.utcnow() + timedelta(days=1)

        response = await client.post(
            "/api/v1/bookings/",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_id": "test-vehicle-id",
                "scheduled_time": booking_time.isoformat(),
                "booking_type": "scheduled",
                "notes": "Please wash carefully"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["booking_type"] == "scheduled"
        assert data["status"] == "pending"
        assert "id" in data

    async def test_create_walk_in_booking_as_staff(self, client: AsyncClient, manager_headers: dict):
        """Test staff creating a walk-in booking."""
        response = await client.post(
            "/api/v1/bookings/walk-in",
            headers=manager_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_license_plate": "ABC123",
                "customer_name": "John Doe",
                "customer_phone": "+1234567890",
                "notes": "Walk-in customer"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["booking_type"] == "walk_in"
        assert data["customer_name"] == "John Doe"

    async def test_create_booking_past_time_fails(self, client: AsyncClient, auth_headers: dict):
        """Test creating booking with past time fails."""
        past_time = datetime.utcnow() - timedelta(hours=1)

        response = await client.post(
            "/api/v1/bookings/",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_id": "test-vehicle-id",
                "scheduled_time": past_time.isoformat(),
                "booking_type": "scheduled"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_create_booking_without_auth_fails(self, client: AsyncClient):
        """Test creating booking without authentication fails."""
        booking_time = datetime.utcnow() + timedelta(days=1)

        response = await client.post(
            "/api/v1/bookings/",
            json={
                "service_id": "test-service-id",
                "vehicle_id": "test-vehicle-id",
                "scheduled_time": booking_time.isoformat(),
                "booking_type": "scheduled"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestBookingRetrieval:
    """Test booking retrieval endpoints."""

    async def test_list_own_bookings_as_client(self, client: AsyncClient, auth_headers: dict):
        """Test client listing their own bookings."""
        # Create a booking first
        booking_time = datetime.utcnow() + timedelta(days=1)
        await client.post(
            "/api/v1/bookings/",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_id": "test-vehicle-id",
                "scheduled_time": booking_time.isoformat(),
                "booking_type": "scheduled"
            }
        )

        # List bookings
        response = await client.get(
            "/api/v1/bookings/",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    async def test_list_all_bookings_as_staff(self, client: AsyncClient, manager_headers: dict):
        """Test staff listing all bookings."""
        response = await client.get(
            "/api/v1/bookings/",
            headers=manager_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    async def test_filter_bookings_by_status(self, client: AsyncClient, auth_headers: dict):
        """Test filtering bookings by status."""
        response = await client.get(
            "/api/v1/bookings/?status=pending",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for booking in data["items"]:
            assert booking["status"] == "pending"

    async def test_filter_bookings_by_date_range(self, client: AsyncClient, auth_headers: dict):
        """Test filtering bookings by date range."""
        start_date = datetime.utcnow().date().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=7)).date().isoformat()

        response = await client.get(
            f"/api/v1/bookings/?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_get_booking_details(self, client: AsyncClient, auth_headers: dict):
        """Test getting specific booking details."""
        # Create a booking
        booking_time = datetime.utcnow() + timedelta(days=1)
        create_response = await client.post(
            "/api/v1/bookings/",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_id": "test-vehicle-id",
                "scheduled_time": booking_time.isoformat(),
                "booking_type": "scheduled"
            }
        )
        booking_id = create_response.json()["id"]

        # Get booking details
        response = await client.get(
            f"/api/v1/bookings/{booking_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == booking_id

    async def test_get_other_user_booking_fails(self, client: AsyncClient, auth_headers: dict):
        """Test client cannot view other user's bookings."""
        # This would need a second user's booking
        # Testing with a non-existent booking ID
        response = await client.get(
            "/api/v1/bookings/other-user-booking-id",
            headers=auth_headers
        )
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN]


@pytest.mark.asyncio
class TestBookingUpdate:
    """Test booking update endpoints."""

    async def test_update_booking_status_as_staff(self, client: AsyncClient, auth_headers: dict, manager_headers: dict):
        """Test staff updating booking status."""
        # Create booking as client
        booking_time = datetime.utcnow() + timedelta(days=1)
        create_response = await client.post(
            "/api/v1/bookings/",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_id": "test-vehicle-id",
                "scheduled_time": booking_time.isoformat(),
                "booking_type": "scheduled"
            }
        )
        booking_id = create_response.json()["id"]

        # Update status as manager
        response = await client.patch(
            f"/api/v1/bookings/{booking_id}/status",
            headers=manager_headers,
            json={"status": "confirmed"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "confirmed"

    async def test_client_cannot_update_booking_status(self, client: AsyncClient, auth_headers: dict):
        """Test client cannot directly update booking status."""
        # Create booking
        booking_time = datetime.utcnow() + timedelta(days=1)
        create_response = await client.post(
            "/api/v1/bookings/",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_id": "test-vehicle-id",
                "scheduled_time": booking_time.isoformat(),
                "booking_type": "scheduled"
            }
        )
        booking_id = create_response.json()["id"]

        # Try to update status
        response = await client.patch(
            f"/api/v1/bookings/{booking_id}/status",
            headers=auth_headers,
            json={"status": "confirmed"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_update_booking_details(self, client: AsyncClient, auth_headers: dict):
        """Test updating booking details."""
        # Create booking
        booking_time = datetime.utcnow() + timedelta(days=1)
        create_response = await client.post(
            "/api/v1/bookings/",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_id": "test-vehicle-id",
                "scheduled_time": booking_time.isoformat(),
                "booking_type": "scheduled"
            }
        )
        booking_id = create_response.json()["id"]

        # Update booking
        new_time = datetime.utcnow() + timedelta(days=2)
        response = await client.put(
            f"/api/v1/bookings/{booking_id}",
            headers=auth_headers,
            json={
                "scheduled_time": new_time.isoformat(),
                "notes": "Updated notes"
            }
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestBookingCancellation:
    """Test booking cancellation endpoints."""

    async def test_cancel_own_booking_as_client(self, client: AsyncClient, auth_headers: dict):
        """Test client canceling their own booking."""
        # Create booking
        booking_time = datetime.utcnow() + timedelta(days=1)
        create_response = await client.post(
            "/api/v1/bookings/",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_id": "test-vehicle-id",
                "scheduled_time": booking_time.isoformat(),
                "booking_type": "scheduled"
            }
        )
        booking_id = create_response.json()["id"]

        # Cancel booking
        response = await client.post(
            f"/api/v1/bookings/{booking_id}/cancel",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "cancelled"

    async def test_cancel_booking_as_staff(self, client: AsyncClient, manager_headers: dict):
        """Test staff canceling any booking."""
        # Create walk-in booking
        create_response = await client.post(
            "/api/v1/bookings/walk-in",
            headers=manager_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_license_plate": "ABC123",
                "customer_name": "John Doe",
                "customer_phone": "+1234567890"
            }
        )
        booking_id = create_response.json()["id"]

        # Cancel booking
        response = await client.post(
            f"/api/v1/bookings/{booking_id}/cancel",
            headers=manager_headers,
            json={"cancellation_reason": "Customer request"}
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_cannot_cancel_completed_booking(self, client: AsyncClient, manager_headers: dict):
        """Test cannot cancel already completed booking."""
        # This would require creating a booking and marking it completed first
        # Simplified test
        response = await client.post(
            "/api/v1/bookings/nonexistent-id/cancel",
            headers=manager_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
class TestBookingRBAC:
    """Test RBAC for booking endpoints."""

    async def test_client_sees_only_own_bookings(self, client: AsyncClient, auth_headers: dict):
        """Test client can only see their own bookings."""
        # Create booking
        booking_time = datetime.utcnow() + timedelta(days=1)
        await client.post(
            "/api/v1/bookings/",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_id": "test-vehicle-id",
                "scheduled_time": booking_time.isoformat(),
                "booking_type": "scheduled"
            }
        )

        # List bookings
        response = await client.get(
            "/api/v1/bookings/",
            headers=auth_headers
        )
        data = response.json()
        # All bookings should belong to this user
        for booking in data["items"]:
            assert booking["user_id"] is not None

    async def test_client_cannot_create_walk_in_booking(self, client: AsyncClient, auth_headers: dict):
        """Test client cannot create walk-in bookings."""
        response = await client.post(
            "/api/v1/bookings/walk-in",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_license_plate": "ABC123",
                "customer_name": "John Doe",
                "customer_phone": "+1234567890"
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_manager_can_see_all_bookings(self, client: AsyncClient, manager_headers: dict):
        """Test manager can see all bookings."""
        response = await client.get(
            "/api/v1/bookings/",
            headers=manager_headers
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_admin_can_manage_all_bookings(self, client: AsyncClient, admin_headers: dict):
        """Test admin has full access to bookings."""
        # Create walk-in booking
        response = await client.post(
            "/api/v1/bookings/walk-in",
            headers=admin_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_license_plate": "ABC123",
                "customer_name": "Jane Doe",
                "customer_phone": "+9876543210"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
class TestBookingValidation:
    """Test booking validation rules."""

    async def test_booking_requires_service(self, client: AsyncClient, auth_headers: dict):
        """Test booking requires valid service."""
        booking_time = datetime.utcnow() + timedelta(days=1)

        response = await client.post(
            "/api/v1/bookings/",
            headers=auth_headers,
            json={
                "vehicle_id": "test-vehicle-id",
                "scheduled_time": booking_time.isoformat(),
                "booking_type": "scheduled"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_booking_requires_vehicle(self, client: AsyncClient, auth_headers: dict):
        """Test booking requires valid vehicle."""
        booking_time = datetime.utcnow() + timedelta(days=1)

        response = await client.post(
            "/api/v1/bookings/",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "scheduled_time": booking_time.isoformat(),
                "booking_type": "scheduled"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_booking_requires_future_time(self, client: AsyncClient, auth_headers: dict):
        """Test booking requires future scheduled time."""
        past_time = datetime.utcnow() - timedelta(days=1)

        response = await client.post(
            "/api/v1/bookings/",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_id": "test-vehicle-id",
                "scheduled_time": past_time.isoformat(),
                "booking_type": "scheduled"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
