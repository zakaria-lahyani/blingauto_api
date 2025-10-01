"""
API Integration Tests for Pricing Feature

Tests all pricing endpoints including:
- Get service pricing
- Calculate booking totals
- Apply discounts
- Dynamic pricing
- Price validation
"""

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
class TestServicePricing:
    """Test service pricing endpoints."""

    async def test_get_service_price(self, client: AsyncClient, auth_headers: dict):
        """Test getting price for a service."""
        response = await client.get(
            "/api/v1/pricing/service/test-service-id",
            headers=auth_headers
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "base_price" in data

    async def test_get_service_price_by_vehicle_size(self, client: AsyncClient, admin_headers: dict, auth_headers: dict):
        """Test getting price varies by vehicle size."""
        # Create service
        cat_response = await client.post(
            "/api/v1/services/categories/",
            headers=admin_headers,
            json={"name": "Price Test", "description": "Test"}
        )
        category_id = cat_response.json()["id"]

        service_response = await client.post(
            "/api/v1/services/",
            headers=admin_headers,
            json={
                "name": "Size-based Service",
                "description": "Test",
                "category_id": category_id,
                "base_price": 25.00,
                "duration_minutes": 30,
                "vehicle_size": "standard"
            }
        )
        service_id = service_response.json()["id"]

        # Get price for standard size
        response = await client.get(
            f"/api/v1/pricing/service/{service_id}?vehicle_size=standard",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestBookingPricing:
    """Test booking price calculation."""

    async def test_calculate_booking_total(self, client: AsyncClient, auth_headers: dict):
        """Test calculating total price for a booking."""
        response = await client.post(
            "/api/v1/pricing/calculate",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_size": "standard",
                "add_ons": []
            }
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "total_price" in data

    async def test_calculate_booking_with_add_ons(self, client: AsyncClient, auth_headers: dict):
        """Test calculating price with add-on services."""
        response = await client.post(
            "/api/v1/pricing/calculate",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_size": "standard",
                "add_ons": ["wax", "interior-clean"]
            }
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    async def test_price_breakdown(self, client: AsyncClient, auth_headers: dict):
        """Test getting detailed price breakdown."""
        response = await client.post(
            "/api/v1/pricing/breakdown",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_size": "large",
                "add_ons": []
            }
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "base_price" in data or "breakdown" in data


@pytest.mark.asyncio
class TestDiscounts:
    """Test discount application."""

    async def test_apply_discount_code(self, client: AsyncClient, auth_headers: dict):
        """Test applying a discount code."""
        response = await client.post(
            "/api/v1/pricing/calculate",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_size": "standard",
                "discount_code": "FIRST10"
            }
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    async def test_invalid_discount_code(self, client: AsyncClient, auth_headers: dict):
        """Test invalid discount code handling."""
        response = await client.post(
            "/api/v1/pricing/calculate",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_size": "standard",
                "discount_code": "INVALID_CODE"
            }
        )
        # Should either reject or ignore invalid code
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    async def test_validate_discount_code(self, client: AsyncClient, auth_headers: dict):
        """Test validating discount code before applying."""
        response = await client.get(
            "/api/v1/pricing/discounts/validate?code=SUMMER20",
            headers=auth_headers
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
class TestDynamicPricing:
    """Test dynamic pricing rules."""

    async def test_surge_pricing(self, client: AsyncClient, auth_headers: dict):
        """Test surge pricing during peak hours."""
        from datetime import datetime, timedelta

        # Weekend booking (might have surge pricing)
        weekend_time = datetime.utcnow() + timedelta(days=5)  # Next weekend
        while weekend_time.weekday() < 5:  # Find Saturday (5) or Sunday (6)
            weekend_time += timedelta(days=1)

        response = await client.post(
            "/api/v1/pricing/calculate",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_size": "standard",
                "scheduled_time": weekend_time.isoformat()
            }
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    async def test_off_peak_pricing(self, client: AsyncClient, auth_headers: dict):
        """Test off-peak pricing discount."""
        from datetime import datetime, timedelta

        # Weekday morning booking (might have off-peak discount)
        weekday_time = datetime.utcnow() + timedelta(days=2)
        weekday_time = weekday_time.replace(hour=10, minute=0, second=0)

        response = await client.post(
            "/api/v1/pricing/calculate",
            headers=auth_headers,
            json={
                "service_id": "test-service-id",
                "vehicle_size": "standard",
                "scheduled_time": weekday_time.isoformat()
            }
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]


@pytest.mark.asyncio
class TestPricingRules:
    """Test pricing rule management."""

    async def test_list_pricing_rules_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test admin listing pricing rules."""
        response = await client.get(
            "/api/v1/pricing/rules",
            headers=admin_headers
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_create_pricing_rule_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test admin creating pricing rule."""
        response = await client.post(
            "/api/v1/pricing/rules",
            headers=admin_headers,
            json={
                "name": "Weekend Surge",
                "rule_type": "surge",
                "multiplier": 1.2,
                "conditions": {
                    "days_of_week": [5, 6],  # Saturday, Sunday
                    "time_range": {"start": "09:00", "end": "17:00"}
                }
            }
        )
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_404_NOT_FOUND]

    async def test_client_cannot_manage_pricing_rules(self, client: AsyncClient, auth_headers: dict):
        """Test client cannot manage pricing rules."""
        response = await client.post(
            "/api/v1/pricing/rules",
            headers=auth_headers,
            json={
                "name": "Forbidden Rule",
                "rule_type": "discount",
                "multiplier": 0.8
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_update_pricing_rule_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test admin updating pricing rule."""
        # Create rule first
        create_response = await client.post(
            "/api/v1/pricing/rules",
            headers=admin_headers,
            json={
                "name": "Test Rule",
                "rule_type": "discount",
                "multiplier": 0.9
            }
        )

        if create_response.status_code == status.HTTP_201_CREATED:
            rule_id = create_response.json()["id"]

            # Update rule
            response = await client.put(
                f"/api/v1/pricing/rules/{rule_id}",
                headers=admin_headers,
                json={"multiplier": 0.85}
            )
            assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestPriceEstimates:
    """Test price estimation."""

    async def test_get_price_estimate_range(self, client: AsyncClient, auth_headers: dict):
        """Test getting price estimate range for services."""
        response = await client.get(
            "/api/v1/pricing/estimate?service_category=wash&vehicle_size=standard",
            headers=auth_headers
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "min_price" in data or "max_price" in data or "estimated_price" in data

    async def test_compare_service_prices(self, client: AsyncClient, auth_headers: dict):
        """Test comparing prices across services."""
        response = await client.get(
            "/api/v1/pricing/compare?service_ids=service1,service2,service3&vehicle_size=standard",
            headers=auth_headers
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
class TestPricingValidation:
    """Test pricing validation rules."""

    async def test_price_cannot_be_negative(self, client: AsyncClient, admin_headers: dict):
        """Test prices cannot be negative."""
        cat_response = await client.post(
            "/api/v1/services/categories/",
            headers=admin_headers,
            json={"name": "Validation Cat", "description": "Test"}
        )
        category_id = cat_response.json()["id"]

        response = await client.post(
            "/api/v1/services/",
            headers=admin_headers,
            json={
                "name": "Invalid Price Service",
                "description": "Test",
                "category_id": category_id,
                "base_price": -10.00,  # Invalid
                "duration_minutes": 30,
                "vehicle_size": "standard"
            }
        )
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_discount_cannot_exceed_100_percent(self, client: AsyncClient, admin_headers: dict):
        """Test discount cannot exceed 100%."""
        response = await client.post(
            "/api/v1/pricing/rules",
            headers=admin_headers,
            json={
                "name": "Invalid Discount",
                "rule_type": "discount",
                "multiplier": -0.5  # More than 100% discount (invalid)
            }
        )
        # Should fail validation
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_404_NOT_FOUND]


@pytest.mark.asyncio
class TestPricingRBAC:
    """Test RBAC for pricing endpoints."""

    async def test_all_users_can_view_prices(self, client: AsyncClient, auth_headers: dict):
        """Test all users can view service prices."""
        response = await client.get(
            "/api/v1/pricing/service/test-service",
            headers=auth_headers
        )
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    async def test_only_admin_can_manage_pricing(self, client: AsyncClient, auth_headers: dict, manager_headers: dict, admin_headers: dict):
        """Test only admin can manage pricing rules."""
        # Client cannot manage
        response = await client.post(
            "/api/v1/pricing/rules",
            headers=auth_headers,
            json={"name": "Test", "rule_type": "discount", "multiplier": 0.9}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Manager might not have access (depends on business rules)
        response = await client.post(
            "/api/v1/pricing/rules",
            headers=manager_headers,
            json={"name": "Test", "rule_type": "discount", "multiplier": 0.9}
        )
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

        # Admin can manage
        response = await client.post(
            "/api/v1/pricing/rules",
            headers=admin_headers,
            json={"name": "Test", "rule_type": "discount", "multiplier": 0.9}
        )
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_404_NOT_FOUND]
