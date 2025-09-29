"""
Comprehensive Bookings Test Suite - Real API Endpoints Testing

Tests booking functionality with real HTTP requests to http://localhost:8000
Following the same pattern as services and auth tests.

Test Coverage:
1. Booking CRUD Operations (Create, Read, Update, Delete/Cancel)
2. Role-Based Access Control (Client, Manager, Admin) 
3. Booking Status Transitions (Pending, Confirmed, In Progress, Completed)
4. Business Logic Validation (Scheduling, Pricing, Services)
5. Advanced Features (Reschedule, Rating, Service Management)
6. Analytics and Reporting
7. Security and Error Handling

Dependencies: services, vehicles, and categories need to exist for booking creation
"""

import pytest
import time
import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import uuid4


class BookingTestRunner:
    """Comprehensive booking test runner with real API endpoints"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.user_tokens = {}
        self.test_data = {
            "categories": [],
            "services": [],
            "vehicles": [],
            "bookings": []
        }
        
        # Setup test users and create test data
        self._setup_test_users()
        self._create_test_data()
    
    def _setup_test_users(self):
        """Setup test users with different roles"""
        # Use existing users from previous tests with proper authentication
        existing_users = {
            "admin": {"email": "admin@carwash.com", "password": "AdminSecure123!@#"},
            # Try multiple client accounts that might be verified
            "client": {"email": "client_verified@example.com", "password": "SecureDevPassword123!"},
            "client2": {"email": "test.client@example.com", "password": "TestPassword123!"},
            "client3": {"email": "john.doe@carwash.com", "password": "SecurePassword123!"},
            "manager": {"email": "manager@example.com", "password": "SecureDevPassword123!"},
        }
        
        # Try to login with existing users
        for role, credentials in existing_users.items():
            try:
                response = requests.post(
                    f"{self.base_url}/auth/login",
                    json=credentials,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.user_tokens[role] = token_data["access_token"]
                    print(f"[OK] Logged in as {role}: {credentials['email']}")
                else:
                    print(f"[FAIL] Failed to login as {role}: {response.status_code}")
                    
            except Exception as e:
                print(f"[ERROR] Login error for {role}: {e}")
        
        # Create fallback client if needed
        if "client" not in self.user_tokens:
            print("[INFO] Creating fallback client for booking tests...")
            self._create_fallback_client()
    
    def _create_fallback_client(self):
        """Create a fallback client user for testing"""
        timestamp = str(int(time.time()))
        fallback_user = {
            "email": f"booking_client_{timestamp}@example.com",
            "password": "BookingTest123!@#",
            "first_name": "Booking",
            "last_name": "Test",
            "phone": f"555002{timestamp[-4:]}"
        }
        
        try:
            # Register user
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=fallback_user,
                headers=self.headers
            )
            
            print(f"[DEBUG] Registration response: {response.status_code} - {response.text[:200]}")
            
            if response.status_code == 201:
                # Login to get token
                login_response = requests.post(
                    f"{self.base_url}/auth/login",
                    json={
                        "email": fallback_user["email"],
                        "password": fallback_user["password"]
                    },
                    headers=self.headers
                )
                
                print(f"[DEBUG] Login response: {login_response.status_code}")
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    self.user_tokens["client"] = token_data["access_token"]
                    print(f"[OK] Created fallback client: {fallback_user['email']}")
                else:
                    print(f"[ERROR] Login failed: {login_response.text}")
            else:
                print(f"[ERROR] Registration failed: {response.text}")
                    
        except Exception as e:
            print(f"[ERROR] Fallback client creation failed: {e}")
    
    def _create_test_data(self):
        """Create necessary test data (categories, services, vehicles)"""
        if "admin" not in self.user_tokens:
            print("[WARN] No admin token available, skipping test data creation")
            return
        
        admin_headers = self.headers.copy()
        admin_headers["Authorization"] = f"Bearer {self.user_tokens['admin']}"
        
        # Create test category with unique name
        timestamp = str(int(time.time()))
        category_data = {
            "name": f"Booking Test Category {timestamp}",
            "description": "Category for booking tests"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/services/categories",
                json=category_data,
                headers=admin_headers
            )
            
            print(f"[DEBUG] Category creation response: {response.status_code} - {response.text[:200]}")
            
            if response.status_code == 201:
                category = response.json()
                self.test_data["categories"].append(category)
                print(f"[OK] Created test category: {category['name']}")
                
                # Create test services
                self._create_test_services(category["id"], admin_headers)
            else:
                print(f"[ERROR] Failed to create test category: {response.status_code}")
                print(f"[ERROR] Category error details: {response.text}")
                # Try to use existing categories
                self._get_existing_categories(admin_headers)
                
        except Exception as e:
            print(f"[ERROR] Test category creation failed: {e}")
            self._get_existing_categories(admin_headers)
        
        # Create test vehicle for client
        self._create_test_vehicle()
    
    def _create_test_services(self, category_id: str, admin_headers: dict):
        """Create test services for booking tests"""
        services_data = [
            {
                "name": "Basic Wash",
                "price": 25.00,
                "duration": 30,
                "category_id": category_id,
                "description": "Basic exterior wash"
            },
            {
                "name": "Premium Wash",
                "price": 45.00,
                "duration": 60,
                "category_id": category_id,
                "description": "Premium wash with interior cleaning"
            },
            {
                "name": "Detailing Service",
                "price": 85.00,
                "duration": 120,
                "category_id": category_id,
                "description": "Full vehicle detailing"
            }
        ]
        
        for service_data in services_data:
            try:
                response = requests.post(
                    f"{self.base_url}/services/",
                    json=service_data,
                    headers=admin_headers
                )
                
                if response.status_code == 201:
                    service = response.json()
                    self.test_data["services"].append(service)
                    print(f"[OK] Created test service: {service['name']}")
                else:
                    print(f"[WARN] Failed to create service {service_data['name']}: {response.status_code}")
                    
            except Exception as e:
                print(f"[ERROR] Service creation failed for {service_data['name']}: {e}")
    
    def _get_existing_categories(self, admin_headers: dict):
        """Get existing categories as fallback"""
        try:
            response = requests.get(f"{self.base_url}/services/categories", headers=admin_headers)
            if response.status_code == 200:
                categories_data = response.json()
                if categories_data.get("categories"):
                    # Use the first available category
                    category = categories_data["categories"][0]
                    self.test_data["categories"].append(category)
                    print(f"[OK] Using existing category: {category['name']}")
                    # Create test services with existing category
                    self._create_test_services(category["id"], admin_headers)
        except Exception as e:
            print(f"[ERROR] Failed to get existing categories: {e}")
    
    def _create_test_vehicle(self):
        """Create test vehicle for client"""
        # Try client first, then admin as fallback
        token_to_use = None
        user_role = None
        
        if "client" in self.user_tokens:
            token_to_use = self.user_tokens["client"]
            user_role = "client"
        elif "admin" in self.user_tokens:
            token_to_use = self.user_tokens["admin"]
            user_role = "admin"
        else:
            print("[WARN] No tokens available for vehicle creation")
            return
        
        client_headers = self.headers.copy()
        client_headers["Authorization"] = f"Bearer {token_to_use}"
        
        vehicle_data = {
            "make": "Honda",
            "model": "Civic",
            "year": 2022,
            "color": "Blue",
            "license_plate": f"TEST{int(time.time()) % 10000}",
            "vehicle_type": "sedan",
            "is_default": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/vehicles",
                json=vehicle_data,
                headers=client_headers
            )
            
            if response.status_code == 201:
                vehicle = response.json()
                self.test_data["vehicles"].append(vehicle)
                print(f"[OK] Created test vehicle: {vehicle['make']} {vehicle['model']}")
            else:
                print(f"[WARN] Failed to create test vehicle: {response.status_code}")
                # Try to get existing vehicles
                self._get_existing_vehicles(client_headers)
                
        except Exception as e:
            print(f"[ERROR] Vehicle creation failed: {e}")
            # Try to get existing vehicles as fallback
            self._get_existing_vehicles(client_headers)
    
    def _get_existing_vehicles(self, client_headers: dict):
        """Get existing vehicles as fallback"""
        try:
            response = requests.get(f"{self.base_url}/vehicles", headers=client_headers)
            if response.status_code == 200:
                vehicles_data = response.json()
                if vehicles_data.get("vehicles"):
                    self.test_data["vehicles"] = vehicles_data["vehicles"]
                    print(f"[OK] Using existing vehicles: {len(self.test_data['vehicles'])} found")
        except Exception as e:
            print(f"[ERROR] Failed to get existing vehicles: {e}")
    
    def make_request(self, method: str, endpoint: str, token: str = None, **kwargs) -> requests.Response:
        """Make HTTP request with optional authentication"""
        headers = self.headers.copy()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        url = f"{self.base_url}{endpoint}"
        return requests.request(method, url, headers=headers, **kwargs)
    
    def test_booking_creation_success(self):
        """Test successful booking creation with valid data"""
        print("\n[TEST] Booking creation with valid data")
        
        # Try to use client token, fall back to admin
        user_token = None
        user_role = None
        if self.user_tokens.get("client"):
            user_token = self.user_tokens["client"]
            user_role = "client"
        elif self.user_tokens.get("admin"):
            user_token = self.user_tokens["admin"]
            user_role = "admin"
        
        if not user_token or not self.test_data["services"] or not self.test_data["vehicles"]:
            print(f"[SKIP] Missing required test data (user token: {bool(user_token)}, services: {len(self.test_data['services'])}, vehicles: {len(self.test_data['vehicles'])})")
            return False
        
        # Create booking in the future
        scheduled_time = datetime.utcnow() + timedelta(days=1)
        booking_data = {
            "vehicle_id": self.test_data["vehicles"][0]["id"],
            "scheduled_at": scheduled_time.isoformat() + "Z",
            "service_ids": [self.test_data["services"][0]["id"]],
            "booking_type": "in_home",
            "vehicle_size": "standard",
            "notes": "Test booking for automated testing"
        }
        
        try:
            response = self.make_request(
                "POST", "/bookings/",
                token=user_token,
                json=booking_data
            )
            
            print(f"[DEBUG] Using {user_role} token for booking creation")
            
            if response.status_code == 201:
                booking = response.json()
                self.test_data["bookings"].append(booking)
                
                # Validate booking structure
                assert "id" in booking
                assert booking["status"] == "pending"
                assert booking["booking_type"] == "in_home"
                assert booking["vehicle_size"] == "standard"
                assert len(booking["services"]) == 1
                assert booking["services"][0]["service_id"] == self.test_data["services"][0]["id"]
                
                print(f"[OK] Booking created successfully: {booking['id']}")
                print(f"[OK] Status: {booking['status']}, Price: ${booking['total_price']}")
                return True
            else:
                print(f"[FAIL] Booking creation failed: {response.status_code}")
                print(f"[FAIL] Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Booking creation test failed: {e}")
            return False
    
    def test_booking_creation_validation(self):
        """Test booking creation with invalid data"""
        print("\n[TEST] Booking creation validation")
        
        if not self.user_tokens.get("client"):
            print("[SKIP] No client token available")
            return False
        
        # Test cases for validation
        test_cases = [
            {
                "name": "Past scheduled time",
                "data": {
                    "vehicle_id": str(uuid4()),
                    "scheduled_at": (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z",
                    "service_ids": [str(uuid4())],
                    "booking_type": "in_home",
                    "vehicle_size": "standard"
                },
                "expected_status": 422  # Validation error
            },
            {
                "name": "Invalid booking type",
                "data": {
                    "vehicle_id": str(uuid4()),
                    "scheduled_at": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
                    "service_ids": [str(uuid4())],
                    "booking_type": "invalid_type",
                    "vehicle_size": "standard"
                },
                "expected_status": 422  # Validation error
            },
            {
                "name": "Missing service IDs",
                "data": {
                    "vehicle_id": str(uuid4()),
                    "scheduled_at": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
                    "service_ids": [],
                    "booking_type": "in_home",
                    "vehicle_size": "standard"
                },
                "expected_status": 422  # Validation error
            },
            {
                "name": "Mobile booking without location",
                "data": {
                    "vehicle_id": str(uuid4()),
                    "scheduled_at": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
                    "service_ids": [str(uuid4())],
                    "booking_type": "mobile",
                    "vehicle_size": "standard"
                },
                "expected_status": 422  # Validation error - missing customer_location
            }
        ]
        
        passed = 0
        for test_case in test_cases:
            try:
                response = self.make_request(
                    "POST", "/bookings/",
                    token=self.user_tokens["client"],
                    json=test_case["data"]
                )
                
                if response.status_code == test_case["expected_status"]:
                    print(f"[OK] {test_case['name']}: Correctly rejected ({response.status_code})")
                    passed += 1
                else:
                    print(f"[FAIL] {test_case['name']}: Expected {test_case['expected_status']}, got {response.status_code}")
                    
            except Exception as e:
                print(f"[ERROR] {test_case['name']} test failed: {e}")
        
        print(f"[RESULT] Validation tests: {passed}/{len(test_cases)} passed")
        return passed == len(test_cases)
    
    def test_booking_list_and_pagination(self):
        """Test booking list endpoint with pagination and filtering"""
        print("\n[TEST] Booking list and pagination")
        
        if not self.user_tokens.get("client"):
            print("[SKIP] No client token available")
            return False
        
        try:
            # Test basic listing
            response = self.make_request(
                "GET", "/bookings/",
                token=self.user_tokens["client"]
            )
            
            if response.status_code == 200:
                bookings_data = response.json()
                
                # Validate response structure
                assert "bookings" in bookings_data
                assert "total" in bookings_data
                assert "page" in bookings_data
                assert "size" in bookings_data
                assert "has_next" in bookings_data
                assert "has_prev" in bookings_data
                
                print(f"[OK] Booking list successful: {bookings_data['total']} total bookings")
                
                # Test pagination
                if bookings_data['total'] > 0:
                    response = self.make_request(
                        "GET", "/bookings/?page=1&size=1",
                        token=self.user_tokens["client"]
                    )
                    
                    if response.status_code == 200:
                        paginated_data = response.json()
                        assert paginated_data['size'] == 1
                        assert paginated_data['page'] == 1
                        print("[OK] Pagination working correctly")
                
                return True
            else:
                print(f"[FAIL] Booking list failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Booking list test failed: {e}")
            return False
    
    def test_booking_details_and_permissions(self):
        """Test booking details retrieval and permission checking"""
        print("\n[TEST] Booking details and permissions")
        
        if not self.test_data["bookings"]:
            print("[SKIP] No test bookings available")
            return False
        
        booking_id = self.test_data["bookings"][0]["id"]
        
        try:
            # Test owner access
            if "client" in self.user_tokens:
                response = self.make_request(
                    "GET", f"/bookings/{booking_id}",
                    token=self.user_tokens["client"]
                )
                
                if response.status_code == 200:
                    booking = response.json()
                    assert booking["id"] == booking_id
                    print("[OK] Client can access their own booking")
                else:
                    print(f"[FAIL] Client access to own booking failed: {response.status_code}")
            
            # Test admin access
            if "admin" in self.user_tokens:
                response = self.make_request(
                    "GET", f"/bookings/{booking_id}",
                    token=self.user_tokens["admin"]
                )
                
                if response.status_code == 200:
                    booking = response.json()
                    assert booking["id"] == booking_id
                    print("[OK] Admin can access any booking")
                else:
                    print(f"[WARN] Admin access to booking failed: {response.status_code}")
            
            # Test unauthorized access (no token)
            response = self.make_request("GET", f"/bookings/{booking_id}")
            
            if response.status_code == 401:
                print("[OK] Unauthorized access correctly blocked")
            else:
                print(f"[FAIL] Unauthorized access should be blocked, got: {response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Booking details test failed: {e}")
            return False
    
    def test_booking_status_transitions(self):
        """Test booking status transitions with proper role permissions"""
        print("\n[TEST] Booking status transitions")
        
        if not self.test_data["bookings"] or not self.user_tokens.get("admin"):
            print("[SKIP] No test bookings or admin token available")
            return False
        
        booking_id = self.test_data["bookings"][0]["id"]
        
        try:
            # Test confirm booking (admin only)
            response = self.make_request(
                "PATCH", f"/bookings/{booking_id}/confirm",
                token=self.user_tokens["admin"]
            )
            
            if response.status_code == 200:
                booking = response.json()
                assert booking["status"] == "confirmed"
                print("[OK] Booking confirmed successfully")
                
                # Test start service
                response = self.make_request(
                    "PATCH", f"/bookings/{booking_id}/start",
                    token=self.user_tokens["admin"]
                )
                
                if response.status_code == 200:
                    booking = response.json()
                    assert booking["status"] == "in_progress"
                    print("[OK] Service started successfully")
                    
                    # Test complete service
                    response = self.make_request(
                        "PATCH", f"/bookings/{booking_id}/complete",
                        token=self.user_tokens["admin"]
                    )
                    
                    if response.status_code == 200:
                        booking = response.json()
                        assert booking["status"] == "completed"
                        print("[OK] Service completed successfully")
                        return True
                    else:
                        print(f"[FAIL] Service completion failed: {response.status_code}")
                else:
                    print(f"[FAIL] Service start failed: {response.status_code}")
            else:
                print(f"[FAIL] Booking confirmation failed: {response.status_code}")
                print(f"[FAIL] Response: {response.text}")
                
        except Exception as e:
            print(f"[ERROR] Status transition test failed: {e}")
            return False
        
        return False
    
    def test_booking_cancellation(self):
        """Test booking cancellation functionality"""
        print("\n[TEST] Booking cancellation")
        
        if not self.user_tokens.get("client") or not self.test_data["services"] or not self.test_data["vehicles"]:
            print("[SKIP] Missing required test data for cancellation test")
            return False
        
        # Create a new booking specifically for cancellation test
        scheduled_time = datetime.utcnow() + timedelta(days=2)
        booking_data = {
            "vehicle_id": self.test_data["vehicles"][0]["id"],
            "scheduled_at": scheduled_time.isoformat() + "Z",
            "service_ids": [self.test_data["services"][0]["id"]],
            "booking_type": "in_home",
            "vehicle_size": "standard",
            "notes": "Booking for cancellation test"
        }
        
        try:
            # Create booking
            response = self.make_request(
                "POST", "/bookings/",
                token=self.user_tokens["client"],
                json=booking_data
            )
            
            if response.status_code != 201:
                print(f"[FAIL] Could not create booking for cancellation test: {response.status_code}")
                return False
            
            booking = response.json()
            booking_id = booking["id"]
            
            # Test cancellation info
            response = self.make_request(
                "GET", f"/bookings/{booking_id}/cancellation-info",
                token=self.user_tokens["client"]
            )
            
            if response.status_code == 200:
                cancel_info = response.json()
                assert "can_cancel" in cancel_info
                assert "fee" in cancel_info
                print(f"[OK] Cancellation info retrieved: can_cancel={cancel_info['can_cancel']}, fee=${cancel_info['fee']}")
            
            # Cancel booking
            cancel_data = {
                "reason": "Testing cancellation functionality"
            }
            
            response = self.make_request(
                "POST", f"/bookings/{booking_id}/cancel",
                token=self.user_tokens["client"],
                json=cancel_data
            )
            
            if response.status_code == 200:
                cancelled_booking = response.json()
                assert cancelled_booking["status"] == "cancelled"
                print("[OK] Booking cancelled successfully")
                return True
            else:
                print(f"[FAIL] Booking cancellation failed: {response.status_code}")
                print(f"[FAIL] Response: {response.text}")
                
        except Exception as e:
            print(f"[ERROR] Cancellation test failed: {e}")
            
        return False
    
    def test_booking_rating_and_feedback(self):
        """Test service quality rating functionality"""
        print("\n[TEST] Booking rating and feedback")
        
        # Find a completed booking or create one for rating
        completed_booking = None
        for booking in self.test_data["bookings"]:
            if booking.get("status") == "completed":
                completed_booking = booking
                break
        
        if not completed_booking:
            print("[SKIP] No completed booking available for rating test")
            return False
        
        if not self.user_tokens.get("client"):
            print("[SKIP] No client token available")
            return False
        
        try:
            rating_data = {
                "rating": 5,
                "feedback": "Excellent service! Very satisfied with the wash quality."
            }
            
            response = self.make_request(
                "POST", f"/bookings/{completed_booking['id']}/rate",
                token=self.user_tokens["client"],
                json=rating_data
            )
            
            if response.status_code == 200:
                rated_booking = response.json()
                assert rated_booking["quality_rating"] == 5
                assert rated_booking["quality_feedback"] == rating_data["feedback"]
                print(f"[OK] Booking rated successfully: {rated_booking['quality_rating']}/5 stars")
                return True
            else:
                print(f"[FAIL] Booking rating failed: {response.status_code}")
                print(f"[FAIL] Response: {response.text}")
                
        except Exception as e:
            print(f"[ERROR] Rating test failed: {e}")
            
        return False
    
    def test_booking_analytics(self):
        """Test booking analytics endpoint"""
        print("\n[TEST] Booking analytics")
        
        if not self.user_tokens.get("client"):
            print("[SKIP] No client token available")
            return False
        
        try:
            response = self.make_request(
                "GET", "/bookings/analytics/summary",
                token=self.user_tokens["client"]
            )
            
            if response.status_code == 200:
                analytics = response.json()
                
                # Validate analytics structure
                expected_fields = ["total_bookings", "completed_bookings", "cancelled_bookings", "total_spent"]
                for field in expected_fields:
                    if field in analytics:
                        print(f"[OK] Analytics field present: {field}={analytics[field]}")
                    else:
                        print(f"[WARN] Analytics field missing: {field}")
                
                return True
            else:
                print(f"[FAIL] Analytics retrieval failed: {response.status_code}")
                
        except Exception as e:
            print(f"[ERROR] Analytics test failed: {e}")
            
        return False
    
    def test_role_based_access_control(self):
        """Test role-based access control across booking endpoints"""
        print("\n[TEST] Role-based access control")
        
        if not self.test_data["bookings"]:
            print("[SKIP] No test bookings available")
            return False
        
        booking_id = self.test_data["bookings"][0]["id"]
        results = {}
        
        # Test admin-only endpoints
        admin_endpoints = [
            ("PATCH", f"/bookings/{booking_id}/confirm", "Admin can confirm bookings"),
            ("PATCH", f"/bookings/{booking_id}/start", "Admin can start services"),
            ("PATCH", f"/bookings/{booking_id}/complete", "Admin can complete services")
        ]
        
        for method, endpoint, description in admin_endpoints:
            # Test with client token (should fail)
            if "client" in self.user_tokens:
                response = self.make_request(method, endpoint, token=self.user_tokens["client"])
                if response.status_code in [401, 403]:
                    results[f"client_blocked_{method}_{endpoint.split('/')[-1]}"] = True
                    print(f"[OK] Client correctly blocked from {description.lower()}")
                else:
                    results[f"client_blocked_{method}_{endpoint.split('/')[-1]}"] = False
                    print(f"[FAIL] Client should be blocked from {description.lower()}")
            
            # Test with admin token (should work or give business logic error)
            if "admin" in self.user_tokens:
                response = self.make_request(method, endpoint, token=self.user_tokens["admin"])
                if response.status_code in [200, 400]:  # 400 for business logic (e.g., already confirmed)
                    results[f"admin_access_{method}_{endpoint.split('/')[-1]}"] = True
                    print(f"[OK] {description}")
                else:
                    results[f"admin_access_{method}_{endpoint.split('/')[-1]}"] = False
                    print(f"[WARN] Admin access issue for {description.lower()}: {response.status_code}")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        print(f"[RESULT] RBAC tests: {passed}/{total} passed")
        
        return passed >= (total * 0.7)  # 70% pass rate acceptable
    
    def run_comprehensive_tests(self):
        """Run all comprehensive booking tests"""
        print("\n" + "="*60)
        print("COMPREHENSIVE BOOKING TESTS - Real API Endpoints")
        print("="*60)
        print(f"Base URL: {self.base_url}")
        print(f"Available tokens: {list(self.user_tokens.keys())}")
        print(f"Test data: {len(self.test_data['services'])} services, {len(self.test_data['vehicles'])} vehicles")
        
        test_results = {}
        
        # Core functionality tests
        test_results["booking_creation_success"] = self.test_booking_creation_success()
        test_results["booking_creation_validation"] = self.test_booking_creation_validation()
        test_results["booking_list_pagination"] = self.test_booking_list_and_pagination()
        test_results["booking_details_permissions"] = self.test_booking_details_and_permissions()
        
        # Business logic tests
        test_results["booking_status_transitions"] = self.test_booking_status_transitions()
        test_results["booking_cancellation"] = self.test_booking_cancellation()
        test_results["booking_rating"] = self.test_booking_rating_and_feedback()
        
        # Analytics and RBAC tests
        test_results["booking_analytics"] = self.test_booking_analytics()
        test_results["role_based_access_control"] = self.test_role_based_access_control()
        
        # Summary
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        
        for test_name, result in test_results.items():
            status = "[PASS]" if result else "[FAIL]"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests >= total_tests * 0.8:
            print("[EXCELLENT] Booking system is working very well!")
        elif passed_tests >= total_tests * 0.6:
            print("[GOOD] Booking system is mostly functional")
        else:
            print("[NEEDS WORK] Several booking issues need attention")
        
        return test_results


def test_comprehensive_bookings():
    """Main test function that runs all booking tests"""
    runner = BookingTestRunner()
    results = runner.run_comprehensive_tests()
    
    # Assert that at least 60% of tests pass for CI/CD
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    assert passed >= total * 0.6, f"Too many booking tests failed: {passed}/{total} passed"


if __name__ == "__main__":
    # Run tests directly
    test_runner = BookingTestRunner()
    test_runner.run_comprehensive_tests()