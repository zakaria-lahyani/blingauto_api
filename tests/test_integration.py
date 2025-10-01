"""
Integration tests for the complete car wash application.
Tests the full flow from user registration to booking completion.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db.base import Base
from app.interfaces.http_api import create_app


class TestCarWashIntegration:
    """Integration tests for complete car wash workflow."""
    
    @pytest.fixture(scope="class")
    def app(self):
        """Create test application."""
        return create_app()
    
    @pytest.fixture(scope="class")
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    def test_complete_booking_workflow(self, client):
        """Test complete booking workflow from registration to completion."""
        
        # Step 1: Register customer
        customer_data = {
            "email": "customer@test.com",
            "password": "CustomerPass123!",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890"
        }
        
        register_response = client.post("/api/v1/auth/register", json=customer_data)
        assert register_response.status_code == 201
        customer_id = register_response.json()["user_id"]
        
        # Step 2: Login customer
        login_response = client.post("/api/v1/auth/login", json={
            "email": customer_data["email"],
            "password": customer_data["password"]
        })
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Step 3: Add vehicle
        vehicle_data = {
            "make": "Toyota",
            "model": "Camry",
            "year": 2020,
            "color": "Silver",
            "license_plate": "ABC123",
            "vehicle_type": "car"
        }
        
        vehicle_response = client.post("/api/v1/vehicles", json=vehicle_data, headers=headers)
        assert vehicle_response.status_code == 201
        vehicle_id = vehicle_response.json()["id"]
        
        # Step 4: Browse services
        services_response = client.get("/api/v1/services")
        assert services_response.status_code == 200
        services = services_response.json()["services"]
        assert len(services) > 0
        
        service_id = services[0]["id"]
        
        # Step 5: Check availability
        future_time = datetime.utcnow() + timedelta(hours=24)
        availability_data = {
            "requested_time": future_time.isoformat(),
            "duration_minutes": 60,
            "vehicle_size": "standard",
            "service_type": "wash_bay"
        }
        
        availability_response = client.post(
            "/api/v1/scheduling/check-availability",
            json=availability_data,
            headers=headers
        )
        assert availability_response.status_code == 200
        availability = availability_response.json()
        assert availability["available"] == True
        
        # Step 6: Create booking
        booking_data = {
            "vehicle_id": vehicle_id,
            "service_ids": [service_id],
            "scheduled_at": future_time.isoformat(),
            "booking_type": "stationary",
            "notes": "Test booking",
            "phone_number": "+1234567890"
        }
        
        booking_response = client.post("/api/v1/bookings", json=booking_data, headers=headers)
        assert booking_response.status_code == 201
        booking_id = booking_response.json()["id"]
        
        # Step 7: View booking
        view_booking_response = client.get(f"/api/bookings/{booking_id}", headers=headers)
        assert view_booking_response.status_code == 200
        booking = view_booking_response.json()
        assert booking["status"] == "pending"
        
        # Step 8: Update booking
        update_data = {
            "notes": "Updated booking notes"
        }
        
        update_response = client.put(f"/api/bookings/{booking_id}", json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        # Step 9: List bookings
        list_response = client.get("/api/v1/bookings", headers=headers)
        assert list_response.status_code == 200
        bookings = list_response.json()["bookings"]
        assert len(bookings) == 1
        assert bookings[0]["id"] == booking_id
        
        # Step 10: Cancel booking (optional)
        # Uncomment to test cancellation
        # cancel_response = client.delete(f"/api/bookings/{booking_id}", headers=headers)
        # assert cancel_response.status_code == 200
    
    def test_admin_workflow(self, client):
        """Test admin workflow for managing resources and services."""
        
        # Step 1: Register admin
        admin_data = {
            "email": "admin@test.com",
            "password": "AdminPass123!",
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin"
        }
        
        register_response = client.post("/api/v1/auth/register", json=admin_data)
        assert register_response.status_code == 201
        
        # Step 2: Login admin
        login_response = client.post("/api/v1/auth/login", json={
            "email": admin_data["email"],
            "password": admin_data["password"]
        })
        assert login_response.status_code == 200
        admin_token = login_response.json()["access_token"]
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Step 3: Create service category
        category_data = {
            "name": "Test Category",
            "description": "Test category description",
            "icon": "test-icon"
        }
        
        category_response = client.post("/api/services/categories", json=category_data, headers=admin_headers)
        assert category_response.status_code == 201
        category_id = category_response.json()["id"]
        
        # Step 4: Create service
        service_data = {
            "category_id": category_id,
            "name": "Test Service",
            "description": "Test service description",
            "price": 30.00,
            "duration_minutes": 45,
            "is_popular": True
        }
        
        service_response = client.post("/api/v1/services", json=service_data, headers=admin_headers)
        assert service_response.status_code == 201
        service_id = service_response.json()["id"]
        
        # Step 5: View all bookings (admin)
        all_bookings_response = client.get("/api/v1/bookings", headers=admin_headers)
        assert all_bookings_response.status_code == 200
        
        # Step 6: View resources
        resources_response = client.get("/api/v1/scheduling/resources", headers=admin_headers)
        assert resources_response.status_code == 200
        resources = resources_response.json()
        assert "wash_bays" in resources
        assert "mobile_teams" in resources
    
    def test_error_handling(self, client):
        """Test error handling across different scenarios."""
        
        # Test unauthorized access
        unauthorized_response = client.get("/api/v1/bookings")
        assert unauthorized_response.status_code == 401
        
        # Test invalid login
        invalid_login_response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        })
        assert invalid_login_response.status_code == 401
        
        # Test invalid vehicle data
        invalid_vehicle_response = client.post("/api/v1/vehicles", json={
            "make": "",  # Invalid: empty make
            "model": "Test",
            "year": 1800,  # Invalid: too old
            "color": "Blue",
            "license_plate": "ABC123"
        })
        assert invalid_vehicle_response.status_code == 422
        
        # Test booking in the past
        past_time = datetime.utcnow() - timedelta(hours=1)
        invalid_booking_response = client.post("/api/v1/bookings", json={
            "vehicle_id": "test-vehicle",
            "service_ids": ["test-service"],
            "scheduled_at": past_time.isoformat(),
            "booking_type": "stationary"
        })
        assert invalid_booking_response.status_code == 401  # Unauthorized first
    
    def test_business_rules_validation(self, client):
        """Test business rules validation across features."""
        
        # Register and login customer for testing
        customer_data = {
            "email": "rules_test@test.com",
            "password": "TestPass123!",
            "first_name": "Rules",
            "last_name": "Test"
        }
        
        client.post("/api/v1/auth/register", json=customer_data)
        login_response = client.post("/api/v1/auth/login", json={
            "email": customer_data["email"],
            "password": customer_data["password"]
        })
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test vehicle year validation
        future_year = datetime.now().year + 5
        future_vehicle_response = client.post("/api/v1/vehicles", json={
            "make": "Tesla",
            "model": "Model S",
            "year": future_year,  # Too far in future
            "color": "Red",
            "license_plate": "FUTURE1",
            "vehicle_type": "car"
        }, headers=headers)
        assert future_vehicle_response.status_code == 422
        
        # Test minimum advance booking time
        too_soon = datetime.utcnow() + timedelta(minutes=30)  # Less than 2 hours
        early_booking_response = client.post("/api/v1/scheduling/check-availability", json={
            "requested_time": too_soon.isoformat(),
            "duration_minutes": 60,
            "vehicle_size": "standard",
            "service_type": "wash_bay"
        }, headers=headers)
        assert early_booking_response.status_code == 400
        
        # Test maximum advance booking time
        too_far = datetime.utcnow() + timedelta(days=95)  # More than 90 days
        far_booking_response = client.post("/api/v1/scheduling/check-availability", json={
            "requested_time": too_far.isoformat(),
            "duration_minutes": 60,
            "vehicle_size": "standard",
            "service_type": "wash_bay"
        }, headers=headers)
        assert far_booking_response.status_code == 400
    
    def test_concurrent_bookings(self, client):
        """Test handling of concurrent booking attempts."""
        
        # This would test race conditions and booking conflicts
        # Implementation would require more complex setup with threading
        pass
    
    def test_data_consistency(self, client):
        """Test data consistency across features."""
        
        # Register customer
        customer_data = {
            "email": "consistency@test.com",
            "password": "TestPass123!",
            "first_name": "Consistency",
            "last_name": "Test"
        }
        
        client.post("/api/v1/auth/register", json=customer_data)
        login_response = client.post("/api/v1/auth/login", json={
            "email": customer_data["email"],
            "password": customer_data["password"]
        })
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Add vehicle
        vehicle_data = {
            "make": "Honda",
            "model": "Civic",
            "year": 2019,
            "color": "White",
            "license_plate": "CONSIST1",
            "vehicle_type": "car"
        }
        
        vehicle_response = client.post("/api/v1/vehicles", json=vehicle_data, headers=headers)
        vehicle_id = vehicle_response.json()["id"]
        
        # Create booking
        future_time = datetime.utcnow() + timedelta(hours=48)
        booking_data = {
            "vehicle_id": vehicle_id,
            "service_ids": [],  # Will need actual service IDs
            "scheduled_at": future_time.isoformat(),
            "booking_type": "stationary"
        }
        
        # This would fail due to no services, but tests validation
        booking_response = client.post("/api/v1/bookings", json=booking_data, headers=headers)
        assert booking_response.status_code == 422  # Should validate service requirement
        
        # Test deleting vehicle with active booking (should fail)
        # Implementation would depend on business rules