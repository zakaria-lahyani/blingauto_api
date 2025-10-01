"""Integration tests for wash bay capacity management."""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestWashBayCapacityManagement:
    """Test wash bay capacity allocation and management."""

    @pytest.mark.asyncio
    async def test_single_booking_allocates_wash_bay(
        self, client: AsyncClient, admin_headers: dict, test_db: AsyncSession
    ):
        """Test that a single booking allocates a wash bay."""
        # Create a wash bay
        wash_bay_response = await client.post(
            "/api/v1/facilities/wash-bays",
            headers=admin_headers,
            json={
                "bay_number": "BAY-001",
                "max_vehicle_size": "standard",
                "equipment_types": ["pressure_washer", "vacuum"],
                "status": "active",
            },
        )
        assert wash_bay_response.status_code == 201
        wash_bay_id = wash_bay_response.json()["id"]

        # Create customer, vehicle, and service
        customer = await self._create_customer(client)
        vehicle = await self._create_vehicle(client, customer["id"], admin_headers)
        service = await self._create_service(client, admin_headers)

        # Create a booking
        scheduled_at = datetime.utcnow() + timedelta(hours=2)
        booking_response = await client.post(
            "/api/v1/bookings",
            headers=admin_headers,
            json={
                "customer_id": customer["id"],
                "vehicle_id": vehicle["id"],
                "service_ids": [service["id"]],
                "scheduled_at": scheduled_at.isoformat(),
                "booking_type": "stationary",
            },
        )
        assert booking_response.status_code == 201
        booking = booking_response.json()

        # Verify wash bay was allocated
        assert booking["wash_bay_id"] == wash_bay_id
        assert booking["mobile_team_id"] is None

    @pytest.mark.asyncio
    async def test_multiple_bookings_same_time_use_different_bays(
        self, client: AsyncClient, admin_headers: dict, test_db: AsyncSession
    ):
        """Test that multiple bookings at same time use different wash bays."""
        # Create 3 wash bays
        bay_ids = []
        for i in range(3):
            bay_response = await client.post(
                "/api/v1/facilities/wash-bays",
                headers=admin_headers,
                json={
                    "bay_number": f"BAY-00{i+1}",
                    "max_vehicle_size": "standard",
                    "equipment_types": ["pressure_washer"],
                    "status": "active",
                },
            )
            assert bay_response.status_code == 201
            bay_ids.append(bay_response.json()["id"])

        # Create test data
        service = await self._create_service(client, admin_headers)
        scheduled_at = datetime.utcnow() + timedelta(hours=2)

        # Create 3 bookings at the same time
        booking_bay_ids = []
        for i in range(3):
            customer = await self._create_customer(client, email=f"customer{i}@example.com")
            vehicle = await self._create_vehicle(client, customer["id"], admin_headers)

            booking_response = await client.post(
                "/api/v1/bookings",
                headers=admin_headers,
                json={
                    "customer_id": customer["id"],
                    "vehicle_id": vehicle["id"],
                    "service_ids": [service["id"]],
                    "scheduled_at": scheduled_at.isoformat(),
                    "booking_type": "stationary",
                },
            )
            assert booking_response.status_code == 201
            booking = booking_response.json()
            booking_bay_ids.append(booking["wash_bay_id"])

        # Verify all bookings got different wash bays
        assert len(set(booking_bay_ids)) == 3  # All different bays
        assert all(bay_id in bay_ids for bay_id in booking_bay_ids)

    @pytest.mark.asyncio
    async def test_booking_rejected_when_no_capacity(
        self, client: AsyncClient, admin_headers: dict, test_db: AsyncSession
    ):
        """Test that booking is rejected when all wash bays are booked."""
        # Create only 2 wash bays
        for i in range(2):
            await client.post(
                "/api/v1/facilities/wash-bays",
                headers=admin_headers,
                json={
                    "bay_number": f"BAY-00{i+1}",
                    "max_vehicle_size": "standard",
                    "equipment_types": ["pressure_washer"],
                    "status": "active",
                },
            )

        # Create test data
        service = await self._create_service(client, admin_headers)
        scheduled_at = datetime.utcnow() + timedelta(hours=2)

        # Create 2 successful bookings
        for i in range(2):
            customer = await self._create_customer(client, email=f"customer{i}@example.com")
            vehicle = await self._create_vehicle(client, customer["id"], admin_headers)

            booking_response = await client.post(
                "/api/v1/bookings",
                headers=admin_headers,
                json={
                    "customer_id": customer["id"],
                    "vehicle_id": vehicle["id"],
                    "service_ids": [service["id"]],
                    "scheduled_at": scheduled_at.isoformat(),
                    "booking_type": "stationary",
                },
            )
            assert booking_response.status_code == 201

        # Try to create a 3rd booking - should fail
        customer3 = await self._create_customer(client, email="customer3@example.com")
        vehicle3 = await self._create_vehicle(client, customer3["id"], admin_headers)

        booking_response = await client.post(
            "/api/v1/bookings",
            headers=admin_headers,
            json={
                "customer_id": customer3["id"],
                "vehicle_id": vehicle3["id"],
                "service_ids": [service["id"]],
                "scheduled_at": scheduled_at.isoformat(),
                "booking_type": "stationary",
            },
        )
        assert booking_response.status_code == 400
        assert "No available wash bay" in booking_response.json()["detail"]

    @pytest.mark.asyncio
    async def test_staggered_bookings_free_up_capacity(
        self, client: AsyncClient, admin_headers: dict, test_db: AsyncSession
    ):
        """Test that capacity becomes available when earlier bookings end."""
        # Create 1 wash bay
        await client.post(
            "/api/v1/facilities/wash-bays",
            headers=admin_headers,
            json={
                "bay_number": "BAY-001",
                "max_vehicle_size": "standard",
                "equipment_types": ["pressure_washer"],
                "status": "active",
            },
        )

        # Create test data
        service = await self._create_service(client, admin_headers, duration=30)

        # Book 10:00 - 10:30
        customer1 = await self._create_customer(client, email="customer1@example.com")
        vehicle1 = await self._create_vehicle(client, customer1["id"], admin_headers)

        booking1_time = datetime.utcnow() + timedelta(hours=2)
        booking1_response = await client.post(
            "/api/v1/bookings",
            headers=admin_headers,
            json={
                "customer_id": customer1["id"],
                "vehicle_id": vehicle1["id"],
                "service_ids": [service["id"]],
                "scheduled_at": booking1_time.isoformat(),
                "booking_type": "stationary",
            },
        )
        assert booking1_response.status_code == 201

        # Try to book 10:15 - 10:45 (overlaps) - should fail
        customer2 = await self._create_customer(client, email="customer2@example.com")
        vehicle2 = await self._create_vehicle(client, customer2["id"], admin_headers)

        booking2_time = booking1_time + timedelta(minutes=15)
        booking2_response = await client.post(
            "/api/v1/bookings",
            headers=admin_headers,
            json={
                "customer_id": customer2["id"],
                "vehicle_id": vehicle2["id"],
                "service_ids": [service["id"]],
                "scheduled_at": booking2_time.isoformat(),
                "booking_type": "stationary",
            },
        )
        assert booking2_response.status_code == 400

        # Book 10:30 - 11:00 (no overlap) - should succeed
        customer3 = await self._create_customer(client, email="customer3@example.com")
        vehicle3 = await self._create_vehicle(client, customer3["id"], admin_headers)

        booking3_time = booking1_time + timedelta(minutes=30)
        booking3_response = await client.post(
            "/api/v1/bookings",
            headers=admin_headers,
            json={
                "customer_id": customer3["id"],
                "vehicle_id": vehicle3["id"],
                "service_ids": [service["id"]],
                "scheduled_at": booking3_time.isoformat(),
                "booking_type": "stationary",
            },
        )
        assert booking3_response.status_code == 201

    @pytest.mark.asyncio
    async def test_vehicle_size_compatibility(
        self, client: AsyncClient, admin_headers: dict, test_db: AsyncSession
    ):
        """Test that vehicle size is matched to appropriate wash bay."""
        # Create compact and large wash bays
        compact_bay_response = await client.post(
            "/api/v1/facilities/wash-bays",
            headers=admin_headers,
            json={
                "bay_number": "BAY-COMPACT",
                "max_vehicle_size": "compact",
                "equipment_types": ["pressure_washer"],
                "status": "active",
            },
        )
        assert compact_bay_response.status_code == 201
        compact_bay_id = compact_bay_response.json()["id"]

        large_bay_response = await client.post(
            "/api/v1/facilities/wash-bays",
            headers=admin_headers,
            json={
                "bay_number": "BAY-LARGE",
                "max_vehicle_size": "large",
                "equipment_types": ["pressure_washer"],
                "status": "active",
            },
        )
        assert large_bay_response.status_code == 201
        large_bay_id = large_bay_response.json()["id"]

        # Create test data
        customer = await self._create_customer(client)
        service = await self._create_service(client, admin_headers)
        scheduled_at = datetime.utcnow() + timedelta(hours=2)

        # Create compact vehicle - should get compact bay (or large if compatible)
        compact_vehicle = await self._create_vehicle(
            client, customer["id"], admin_headers, size="compact"
        )
        compact_booking = await client.post(
            "/api/v1/bookings",
            headers=admin_headers,
            json={
                "customer_id": customer["id"],
                "vehicle_id": compact_vehicle["id"],
                "service_ids": [service["id"]],
                "scheduled_at": scheduled_at.isoformat(),
                "booking_type": "stationary",
            },
        )
        assert compact_booking.status_code == 201
        # Compact vehicle can use any bay
        assert compact_booking.json()["wash_bay_id"] in [compact_bay_id, large_bay_id]

    @pytest.mark.asyncio
    async def test_cancelled_booking_frees_wash_bay(
        self, client: AsyncClient, admin_headers: dict, test_db: AsyncSession
    ):
        """Test that cancelling a booking frees up the wash bay."""
        # Create 1 wash bay
        await client.post(
            "/api/v1/facilities/wash-bays",
            headers=admin_headers,
            json={
                "bay_number": "BAY-001",
                "max_vehicle_size": "standard",
                "equipment_types": ["pressure_washer"],
                "status": "active",
            },
        )

        # Create test data
        service = await self._create_service(client, admin_headers)
        scheduled_at = datetime.utcnow() + timedelta(hours=2)

        # Create first booking
        customer1 = await self._create_customer(client, email="customer1@example.com")
        vehicle1 = await self._create_vehicle(client, customer1["id"], admin_headers)

        booking1_response = await client.post(
            "/api/v1/bookings",
            headers=admin_headers,
            json={
                "customer_id": customer1["id"],
                "vehicle_id": vehicle1["id"],
                "service_ids": [service["id"]],
                "scheduled_at": scheduled_at.isoformat(),
                "booking_type": "stationary",
            },
        )
        assert booking1_response.status_code == 201
        booking1_id = booking1_response.json()["booking_id"]

        # Try second booking at same time - should fail
        customer2 = await self._create_customer(client, email="customer2@example.com")
        vehicle2 = await self._create_vehicle(client, customer2["id"], admin_headers)

        booking2_response = await client.post(
            "/api/v1/bookings",
            headers=admin_headers,
            json={
                "customer_id": customer2["id"],
                "vehicle_id": vehicle2["id"],
                "service_ids": [service["id"]],
                "scheduled_at": scheduled_at.isoformat(),
                "booking_type": "stationary",
            },
        )
        assert booking2_response.status_code == 400

        # Cancel first booking
        cancel_response = await client.post(
            f"/api/v1/bookings/{booking1_id}/cancel",
            headers=admin_headers,
            json={"reason": "customer_request"},
        )
        assert cancel_response.status_code == 200

        # Try second booking again - should now succeed
        booking3_response = await client.post(
            "/api/v1/bookings",
            headers=admin_headers,
            json={
                "customer_id": customer2["id"],
                "vehicle_id": vehicle2["id"],
                "service_ids": [service["id"]],
                "scheduled_at": scheduled_at.isoformat(),
                "booking_type": "stationary",
            },
        )
        assert booking3_response.status_code == 201

    # Helper methods

    async def _create_customer(self, client: AsyncClient, email: str = "test@example.com"):
        """Create a test customer."""
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "TestPass123!",
                "full_name": "Test Customer",
            },
        )
        assert register_response.status_code == 201
        return register_response.json()

    async def _create_vehicle(
        self,
        client: AsyncClient,
        customer_id: str,
        admin_headers: dict,
        size: str = "standard",
    ):
        """Create a test vehicle."""
        vehicle_response = await client.post(
            "/api/v1/vehicles",
            headers=admin_headers,
            json={
                "customer_id": customer_id,
                "make": "Toyota",
                "model": "Camry",
                "year": 2020,
                "color": "Blue",
                "license_plate": f"ABC{customer_id[:3]}",
                "size": size,
            },
        )
        assert vehicle_response.status_code == 201
        return vehicle_response.json()

    async def _create_service(
        self, client: AsyncClient, admin_headers: dict, duration: int = 30
    ):
        """Create a test service."""
        # Create category first
        category_response = await client.post(
            "/api/v1/services/categories",
            headers=admin_headers,
            json={
                "name": "Basic Wash",
                "description": "Basic car wash services",
            },
        )
        category_id = category_response.json()["id"]

        # Create service
        service_response = await client.post(
            "/api/v1/services",
            headers=admin_headers,
            json={
                "category_id": category_id,
                "name": "Express Wash",
                "description": "Quick exterior wash",
                "base_price": 25.00,
                "duration_minutes": duration,
            },
        )
        assert service_response.status_code == 201
        return service_response.json()
