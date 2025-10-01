import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
from fastapi.testclient import TestClient
from fastapi import FastAPI, status

from app.features.bookings.api import booking_router
from app.features.bookings.use_cases import (
    CreateBookingResponse,
    CancelBookingResponse,
    UpdateBookingResponse,
    GetBookingResponse,
    ListBookingsResponse,
    BookingSummary,
)
from app.features.bookings.domain import BookingStatus, BookingType


@pytest.mark.api
class TestBookingEndpoints:
    """Test booking API endpoints."""
    
    @pytest.fixture
    def test_app(self):
        """Create test FastAPI app with booking router."""
        app = FastAPI()
        app.include_router(booking_router)
        return app
    
    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return TestClient(test_app)
    
    @pytest.fixture
    def mock_current_user(self):
        """Mock current user for authentication."""
        return {
            "id": "customer_123",
            "email": "customer@example.com",
            "role": "client",
        }
    
    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user for testing admin endpoints."""
        return {
            "id": "admin_123",
            "email": "admin@example.com",
            "role": "admin",
        }
    
    @pytest.fixture
    def valid_booking_data(self):
        """Valid booking creation data."""
        return {
            "customer_id": "customer_123",
            "vehicle_id": "vehicle_123",
            "service_ids": ["service_1", "service_2"],
            "scheduled_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "booking_type": "SCHEDULED",
            "notes": "Test booking",
            "phone_number": "+1234567890",
        }
    
    def test_create_booking_success(self, client, mocker, mock_current_user, valid_booking_data):
        """Test successful booking creation."""
        # Mock dependencies
        mock_get_current_user = mocker.patch("app.features.bookings.api.router.get_current_user")
        mock_get_current_user.return_value = mock_current_user
        
        mock_use_case = mocker.patch("app.features.bookings.api.router.get_create_booking_use_case")
        mock_use_case_instance = Mock()
        mock_use_case.return_value = mock_use_case_instance
        
        # Mock use case response
        mock_response = CreateBookingResponse(
            booking_id="booking_123",
            status=BookingStatus.PENDING.value,
            total_price=40.0,
            estimated_duration=50,
            scheduled_at=datetime.fromisoformat(valid_booking_data["scheduled_at"]),
            services=[
                {
                    "id": "service_1",
                    "name": "Basic Wash",
                    "price": 25.0,
                    "duration_minutes": 30,
                },
                {
                    "id": "service_2",
                    "name": "Interior Clean",
                    "price": 15.0,
                    "duration_minutes": 20,
                },
            ],
        )
        mock_use_case_instance.execute = AsyncMock(return_value=mock_response)
        
        # Make request
        response = client.post("/bookings", json=valid_booking_data)
        
        # Verify response
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["booking_id"] == "booking_123"
        assert data["status"] == BookingStatus.PENDING.value
        assert data["total_price"] == 40.0
        assert len(data["services"]) == 2
    
    def test_create_booking_forbidden_other_customer(
        self, client, mocker, mock_current_user, valid_booking_data
    ):
        """Test booking creation forbidden for other customers."""
        mock_get_current_user = mocker.patch("app.features.bookings.api.router.get_current_user")
        mock_get_current_user.return_value = mock_current_user
        
        # Try to create booking for different customer
        valid_booking_data["customer_id"] = "other_customer_456"
        
        response = client.post("/bookings", json=valid_booking_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "only create bookings for yourself" in response.json()["detail"]
    
    def test_create_booking_admin_can_create_for_others(
        self, client, mocker, mock_admin_user, valid_booking_data
    ):
        """Test admin can create bookings for other customers."""
        mock_get_current_user = mocker.patch("app.features.bookings.api.router.get_current_user")
        mock_get_current_user.return_value = mock_admin_user
        
        mock_use_case = mocker.patch("app.features.bookings.api.router.get_create_booking_use_case")
        mock_use_case_instance = Mock()
        mock_use_case.return_value = mock_use_case_instance
        
        mock_response = CreateBookingResponse(
            booking_id="booking_123",
            status=BookingStatus.PENDING.value,
            total_price=40.0,
            estimated_duration=50,
            scheduled_at=datetime.fromisoformat(valid_booking_data["scheduled_at"]),
            services=[],
        )
        mock_use_case_instance.execute = AsyncMock(return_value=mock_response)
        
        # Create booking for different customer
        valid_booking_data["customer_id"] = "other_customer_456"
        
        response = client.post("/bookings", json=valid_booking_data)
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_create_booking_validation_error(
        self, client, mocker, mock_current_user, valid_booking_data
    ):
        """Test booking creation with validation errors."""
        mock_get_current_user = mocker.patch("app.features.bookings.api.router.get_current_user")
        mock_get_current_user.return_value = mock_current_user
        
        mock_use_case = mocker.patch("app.features.bookings.api.router.get_create_booking_use_case")
        mock_use_case_instance = Mock()
        mock_use_case.return_value = mock_use_case_instance
        
        from app.core.errors import ValidationError
        mock_use_case_instance.execute = AsyncMock(side_effect=ValidationError("Invalid data"))
        
        response = client.post("/bookings", json=valid_booking_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid data" in response.json()["detail"]
    
    def test_create_booking_business_rule_violation(
        self, client, mocker, mock_current_user, valid_booking_data
    ):
        """Test booking creation with business rule violation."""
        mock_get_current_user = mocker.patch("app.features.bookings.api.router.get_current_user")
        mock_get_current_user.return_value = mock_current_user
        
        mock_use_case = mocker.patch("app.features.bookings.api.router.get_create_booking_use_case")
        mock_use_case_instance = Mock()
        mock_use_case.return_value = mock_use_case_instance
        
        from app.core.errors import BusinessRuleViolationError
        mock_use_case_instance.execute = AsyncMock(
            side_effect=BusinessRuleViolationError("Time slot conflicts")
        )
        
        response = client.post("/bookings", json=valid_booking_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Time slot conflicts" in response.json()["detail"]
    
    def test_get_booking_success(self, client, mocker, mock_current_user):
        """Test successful booking retrieval."""
        mock_get_current_user = mocker.patch("app.features.bookings.api.router.get_current_user")
        mock_get_current_user.return_value = mock_current_user
        
        mock_use_case = mocker.patch("app.features.bookings.api.router.get_get_booking_use_case")
        mock_use_case_instance = Mock()
        mock_use_case.return_value = mock_use_case_instance
        
        mock_response = GetBookingResponse(
            id="booking_123",
            customer_id="customer_123",
            vehicle_id="vehicle_123",
            status=BookingStatus.PENDING.value,
            scheduled_at=datetime.now() + timedelta(hours=24),
            booking_type=BookingType.SCHEDULED.value,
            services=[],
            total_price=40.0,
            estimated_duration=50,
            notes="Test booking",
            phone_number="+1234567890",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        mock_use_case_instance.execute = AsyncMock(return_value=mock_response)
        
        response = client.get("/bookings/booking_123")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == "booking_123"
        assert data["customer_id"] == "customer_123"
        assert data["status"] == BookingStatus.PENDING.value
    
    def test_get_booking_not_found(self, client, mocker, mock_current_user):
        """Test booking retrieval when booking not found."""
        mock_get_current_user = mocker.patch("app.features.bookings.api.router.get_current_user")
        mock_get_current_user.return_value = mock_current_user
        
        mock_use_case = mocker.patch("app.features.bookings.api.router.get_get_booking_use_case")
        mock_use_case_instance = Mock()
        mock_use_case.return_value = mock_use_case_instance
        
        from app.core.errors import NotFoundError
        mock_use_case_instance.execute = AsyncMock(side_effect=NotFoundError("Booking not found"))
        
        response = client.get("/bookings/nonexistent_123")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Booking not found" in response.json()["detail"]
    
    def test_get_booking_forbidden(self, client, mocker, mock_current_user):
        """Test booking retrieval forbidden for other customers."""
        mock_get_current_user = mocker.patch("app.features.bookings.api.router.get_current_user")
        mock_get_current_user.return_value = mock_current_user
        
        mock_use_case = mocker.patch("app.features.bookings.api.router.get_get_booking_use_case")
        mock_use_case_instance = Mock()
        mock_use_case.return_value = mock_use_case_instance
        
        from app.core.errors import BusinessRuleViolationError
        mock_use_case_instance.execute = AsyncMock(
            side_effect=BusinessRuleViolationError("You can only view your own bookings")
        )
        
        response = client.get("/bookings/other_booking_123")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "only view your own bookings" in response.json()["detail"]
    
    def test_list_bookings_success(self, client, mocker, mock_current_user):
        """Test successful booking listing."""
        mock_get_current_user = mocker.patch("app.features.bookings.api.router.get_current_user")
        mock_get_current_user.return_value = mock_current_user
        
        mock_use_case = mocker.patch("app.features.bookings.api.router.get_list_bookings_use_case")
        mock_use_case_instance = Mock()
        mock_use_case.return_value = mock_use_case_instance
        
        mock_response = ListBookingsResponse(
            bookings=[
                BookingSummary(
                    id="booking_123",
                    customer_id="customer_123",
                    vehicle_id="vehicle_123",
                    status=BookingStatus.PENDING.value,
                    scheduled_at=datetime.now() + timedelta(hours=24),
                    total_price=40.0,
                    estimated_duration=50,
                    services_count=2,
                    booking_type=BookingType.SCHEDULED.value,
                    created_at=datetime.now(),
                )
            ],
            total_count=1,
            page=1,
            limit=20,
            has_next=False,
        )
        mock_use_case_instance.execute = AsyncMock(return_value=mock_response)
        
        response = client.get("/bookings")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["bookings"]) == 1
        assert data["total_count"] == 1
        assert data["page"] == 1
        assert not data["has_next"]
    
    def test_list_bookings_with_filters(self, client, mocker, mock_current_user):
        """Test booking listing with filters."""
        mock_get_current_user = mocker.patch("app.features.bookings.api.router.get_current_user")
        mock_get_current_user.return_value = mock_current_user
        
        mock_use_case = mocker.patch("app.features.bookings.api.router.get_list_bookings_use_case")
        mock_use_case_instance = Mock()
        mock_use_case.return_value = mock_use_case_instance
        
        mock_response = ListBookingsResponse(
            bookings=[],
            total_count=0,
            page=1,
            limit=10,
            has_next=False,
        )
        mock_use_case_instance.execute = AsyncMock(return_value=mock_response)
        
        response = client.get("/bookings?status=pending&page=1&limit=10")
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify the use case was called with correct filters
        call_args = mock_use_case_instance.execute.call_args[0][0]
        assert call_args.status == "pending"
        assert call_args.page == 1
        assert call_args.limit == 10
        assert call_args.customer_id == "customer_123"  # Auto-set for non-admin
    
    def test_update_booking_success(self, client, mocker, mock_current_user):
        """Test successful booking update."""
        mock_get_current_user = mocker.patch("app.features.bookings.api.router.get_current_user")
        mock_get_current_user.return_value = mock_current_user
        
        mock_use_case = mocker.patch("app.features.bookings.api.router.get_update_booking_use_case")
        mock_use_case_instance = Mock()
        mock_use_case.return_value = mock_use_case_instance
        
        mock_response = UpdateBookingResponse(
            booking_id="booking_123",
            status=BookingStatus.PENDING.value,
            total_price=40.0,
            estimated_duration=50,
            scheduled_at=datetime.now() + timedelta(hours=48),
            services=[],
            changes_made=["scheduled_at", "notes"],
        )
        mock_use_case_instance.execute = AsyncMock(return_value=mock_response)
        
        update_data = {
            "scheduled_at": (datetime.now() + timedelta(hours=48)).isoformat(),
            "notes": "Updated booking notes",
        }
        
        response = client.put("/bookings/booking_123", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["booking_id"] == "booking_123"
        assert "scheduled_at" in data["changes_made"]
        assert "notes" in data["changes_made"]
    
    def test_cancel_booking_success(self, client, mocker, mock_current_user):
        """Test successful booking cancellation."""
        mock_get_current_user = mocker.patch("app.features.bookings.api.router.get_current_user")
        mock_get_current_user.return_value = mock_current_user
        
        mock_use_case = mocker.patch("app.features.bookings.api.router.get_cancel_booking_use_case")
        mock_use_case_instance = Mock()
        mock_use_case.return_value = mock_use_case_instance
        
        mock_response = CancelBookingResponse(
            booking_id="booking_123",
            status=BookingStatus.CANCELLED.value,
            refund_amount=40.0,
            refund_status="succeeded",
        )
        mock_use_case_instance.execute = AsyncMock(return_value=mock_response)
        
        cancel_data = {"reason": "Customer request"}
        
        response = client.post("/bookings/booking_123/cancel", json=cancel_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["booking_id"] == "booking_123"
        assert data["status"] == BookingStatus.CANCELLED.value
        assert data["refund_amount"] == 40.0
        assert data["refund_status"] == "succeeded"
    
    def test_admin_endpoints_require_admin_role(self, client, mocker, mock_current_user):
        """Test admin endpoints require admin role."""
        mock_get_current_user = mocker.patch("app.features.bookings.api.router.get_current_user")
        mock_get_current_user.return_value = mock_current_user
        
        mock_require_roles = mocker.patch("app.features.bookings.api.router.require_roles")
        mock_require_roles.side_effect = Exception("Insufficient permissions")
        
        # Test admin stats endpoint
        response = client.get("/bookings/admin/stats")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Test confirm booking endpoint
        response = client.post("/bookings/booking_123/confirm")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Test complete booking endpoint
        response = client.post("/bookings/booking_123/complete")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_admin_can_access_admin_endpoints(self, client, mocker, mock_admin_user):
        """Test admin can access admin endpoints."""
        mock_get_current_user = mocker.patch("app.features.bookings.api.router.get_current_user")
        mock_get_current_user.return_value = mock_admin_user
        
        mock_require_roles = mocker.patch("app.features.bookings.api.router.require_roles")
        mock_require_roles.return_value = lambda: None  # Allow access
        
        # Test admin stats endpoint
        response = client.get("/bookings/admin/stats")
        assert response.status_code == status.HTTP_200_OK
        
        # Test confirm booking endpoint
        response = client.post("/bookings/booking_123/confirm")
        assert response.status_code == status.HTTP_200_OK
        
        # Test complete booking endpoint
        response = client.post("/bookings/booking_123/complete")
        assert response.status_code == status.HTTP_200_OK
    
    def test_request_validation(self, client, mocker, mock_current_user):
        """Test request data validation."""
        mock_get_current_user = mocker.patch("app.features.bookings.api.router.get_current_user")
        mock_get_current_user.return_value = mock_current_user
        
        # Test invalid booking data
        invalid_data = {
            "customer_id": "",  # Empty customer ID
            "vehicle_id": "vehicle_123",
            "service_ids": [],  # Empty services
            "scheduled_at": "invalid-datetime",  # Invalid datetime
            "booking_type": "INVALID_TYPE",  # Invalid type
        }
        
        response = client.post("/bookings", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test invalid update data
        invalid_update = {
            "scheduled_at": "2020-01-01T10:00:00",  # Past date
        }
        
        response = client.put("/bookings/booking_123", json=invalid_update)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY