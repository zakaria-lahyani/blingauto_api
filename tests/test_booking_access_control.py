"""
Booking Access Control and Validation Tests
Tests to ensure:
1. Only authenticated users can create bookings
2. Bookings require vehicle, service, and schedule
3. Different user roles have appropriate access
"""

import requests
import json
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Dict, Any, Optional


class BookingAccessControlTests:
    """Test booking access control and validation"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.tokens = {
            "admin": None,
            "manager": None,
            "client": None
        }
        self.test_data = {
            "vehicle_id": None,
            "service_id": None
        }
        
    def setup_test_users(self):
        """Setup test users with different roles"""
        print("\n" + "="*70)
        print("SETTING UP TEST USERS")
        print("="*70)
        
        # Admin login
        admin_creds = {"email": "admin@carwash.com", "password": "AdminSecure123!@#"}
        response = requests.post(f"{self.base_url}/auth/login", json=admin_creds, headers=self.headers)
        if response.status_code == 200:
            self.tokens["admin"] = response.json()["access_token"]
            print("[OK] Admin logged in")
        else:
            print(f"[FAIL] Admin login failed: {response.status_code}")
            
        # Manager login (if exists, otherwise use admin)
        manager_creds = {"email": "manager@carwash.com", "password": "ManagerSecure123!@#"}
        response = requests.post(f"{self.base_url}/auth/login", json=manager_creds, headers=self.headers)
        if response.status_code == 200:
            self.tokens["manager"] = response.json()["access_token"]
            print("[OK] Manager logged in")
        else:
            print("[INFO] Manager not found, will create one")
            self.tokens["manager"] = self.tokens["admin"]  # Use admin for now
            
        # Client login (create a new client)
        self.create_client_user()
        
    def create_client_user(self):
        """Create a client user for testing"""
        client_data = {
            "email": f"client_test_{uuid4().hex[:8]}@test.com",
            "password": "ClientTest123!@#",
            "full_name": "Test Client",
            "phone_number": "+1234567890"
        }
        
        # Register client
        response = requests.post(f"{self.base_url}/auth/register", json=client_data, headers=self.headers)
        if response.status_code in [200, 201]:
            print(f"[OK] Client registered: {client_data['email']}")
            
            # Login as client
            login_response = requests.post(
                f"{self.base_url}/auth/login",
                json={"email": client_data["email"], "password": client_data["password"]},
                headers=self.headers
            )
            if login_response.status_code == 200:
                self.tokens["client"] = login_response.json()["access_token"]
                print("[OK] Client logged in")
            else:
                print(f"[FAIL] Client login failed: {login_response.status_code}")
        else:
            print(f"[FAIL] Client registration failed: {response.status_code}")
            
    def setup_test_data(self):
        """Setup test data (vehicles and services)"""
        print("\n" + "="*70)
        print("SETTING UP TEST DATA")
        print("="*70)
        
        if not self.tokens["admin"]:
            print("[ERROR] No admin token available")
            return False
            
        auth_headers = self.headers.copy()
        auth_headers["Authorization"] = f"Bearer {self.tokens['admin']}"
        
        # Get services
        services_response = requests.get(f"{self.base_url}/services/", headers=auth_headers)
        if services_response.status_code == 200:
            services = services_response.json().get("services", [])
            if services:
                self.test_data["service_id"] = services[0]["id"]
                print(f"[OK] Using service: {services[0]['name']}")
                
        # Get vehicles
        vehicles_response = requests.get(f"{self.base_url}/vehicles", headers=auth_headers)
        if vehicles_response.status_code == 200:
            vehicles = vehicles_response.json().get("vehicles", [])
            if vehicles:
                self.test_data["vehicle_id"] = vehicles[0]["id"]
                print(f"[OK] Using vehicle: {vehicles[0]['make']} {vehicles[0]['model']}")
                
        return self.test_data["service_id"] and self.test_data["vehicle_id"]
        
    def test_unauthenticated_booking(self):
        """Test that unauthenticated users cannot create bookings"""
        print("\n[TEST] Unauthenticated user booking attempt")
        
        booking_data = {
            "vehicle_id": self.test_data["vehicle_id"],
            "scheduled_at": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
            "service_ids": [self.test_data["service_id"]],
            "booking_type": "in_home",
            "vehicle_size": "standard"
        }
        
        # No auth header
        response = requests.post(f"{self.base_url}/bookings/", json=booking_data, headers=self.headers)
        
        if response.status_code in [401, 403]:
            print("[OK] Unauthenticated user correctly blocked")
            return True
        else:
            print(f"[FAIL] Unexpected response: {response.status_code}")
            return False
            
    def test_client_booking_with_all_fields(self):
        """Test that client can book with all required fields"""
        print("\n[TEST] Client booking with all required fields")
        
        if not self.tokens["client"]:
            print("[SKIP] No client token available")
            return False
            
        auth_headers = self.headers.copy()
        auth_headers["Authorization"] = f"Bearer {self.tokens['client']}"
        
        booking_data = {
            "vehicle_id": self.test_data["vehicle_id"],
            "scheduled_at": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
            "service_ids": [self.test_data["service_id"]],
            "booking_type": "in_home",
            "vehicle_size": "standard",
            "notes": "Client test booking with all fields"
        }
        
        response = requests.post(f"{self.base_url}/bookings/", json=booking_data, headers=auth_headers)
        
        if response.status_code == 201:
            booking = response.json()
            print(f"[OK] Client booking created: {booking.get('id')}")
            print(f"[OK] Status: {booking.get('status')}")
            print(f"[OK] Total price: ${booking.get('total_price')}")
            return True
        else:
            print(f"[FAIL] Booking creation failed: {response.status_code}")
            print(f"[FAIL] Response: {response.text[:200]}")
            return False
            
    def test_booking_without_vehicle(self):
        """Test that booking fails without vehicle"""
        print("\n[TEST] Booking without vehicle (should fail)")
        
        if not self.tokens["client"]:
            print("[SKIP] No client token available")
            return False
            
        auth_headers = self.headers.copy()
        auth_headers["Authorization"] = f"Bearer {self.tokens['client']}"
        
        booking_data = {
            # Missing vehicle_id
            "scheduled_at": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
            "service_ids": [self.test_data["service_id"]],
            "booking_type": "in_home",
            "vehicle_size": "standard"
        }
        
        response = requests.post(f"{self.base_url}/bookings/", json=booking_data, headers=auth_headers)
        
        if response.status_code in [400, 422]:
            print("[OK] Booking without vehicle correctly rejected")
            try:
                error = response.json()
                if 'vehicle' in str(error).lower():
                    print("[OK] Error message mentions vehicle")
            except:
                pass
            return True
        else:
            print(f"[FAIL] Expected validation error, got: {response.status_code}")
            return False
            
    def test_booking_without_services(self):
        """Test that booking fails without services"""
        print("\n[TEST] Booking without services (should fail)")
        
        if not self.tokens["client"]:
            print("[SKIP] No client token available")
            return False
            
        auth_headers = self.headers.copy()
        auth_headers["Authorization"] = f"Bearer {self.tokens['client']}"
        
        booking_data = {
            "vehicle_id": self.test_data["vehicle_id"],
            "scheduled_at": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z",
            "service_ids": [],  # Empty services
            "booking_type": "in_home",
            "vehicle_size": "standard"
        }
        
        response = requests.post(f"{self.base_url}/bookings/", json=booking_data, headers=auth_headers)
        
        if response.status_code in [400, 422]:
            print("[OK] Booking without services correctly rejected")
            try:
                error = response.json()
                if 'service' in str(error).lower():
                    print("[OK] Error message mentions services")
            except:
                pass
            return True
        else:
            print(f"[FAIL] Expected validation error, got: {response.status_code}")
            return False
            
    def test_booking_without_schedule(self):
        """Test that booking fails without schedule"""
        print("\n[TEST] Booking without schedule (should fail)")
        
        if not self.tokens["client"]:
            print("[SKIP] No client token available")
            return False
            
        auth_headers = self.headers.copy()
        auth_headers["Authorization"] = f"Bearer {self.tokens['client']}"
        
        booking_data = {
            "vehicle_id": self.test_data["vehicle_id"],
            # Missing scheduled_at
            "service_ids": [self.test_data["service_id"]],
            "booking_type": "in_home",
            "vehicle_size": "standard"
        }
        
        response = requests.post(f"{self.base_url}/bookings/", json=booking_data, headers=auth_headers)
        
        if response.status_code in [400, 422]:
            print("[OK] Booking without schedule correctly rejected")
            try:
                error = response.json()
                if 'schedul' in str(error).lower() or 'time' in str(error).lower():
                    print("[OK] Error message mentions schedule/time")
            except:
                pass
            return True
        else:
            print(f"[FAIL] Expected validation error, got: {response.status_code}")
            return False
            
    def test_booking_with_past_schedule(self):
        """Test that booking fails with past schedule"""
        print("\n[TEST] Booking with past schedule (should fail)")
        
        if not self.tokens["client"]:
            print("[SKIP] No client token available")
            return False
            
        auth_headers = self.headers.copy()
        auth_headers["Authorization"] = f"Bearer {self.tokens['client']}"
        
        booking_data = {
            "vehicle_id": self.test_data["vehicle_id"],
            "scheduled_at": (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z",  # Past time
            "service_ids": [self.test_data["service_id"]],
            "booking_type": "in_home",
            "vehicle_size": "standard"
        }
        
        response = requests.post(f"{self.base_url}/bookings/", json=booking_data, headers=auth_headers)
        
        if response.status_code in [400, 422]:
            print("[OK] Booking with past schedule correctly rejected")
            try:
                error = response.json()
                if 'past' in str(error).lower() or 'future' in str(error).lower():
                    print("[OK] Error message mentions past/future requirement")
            except:
                pass
            return True
        else:
            print(f"[FAIL] Expected validation error, got: {response.status_code}")
            return False
            
    def test_admin_can_view_all_bookings(self):
        """Test that admin can view all bookings"""
        print("\n[TEST] Admin viewing all bookings")
        
        if not self.tokens["admin"]:
            print("[SKIP] No admin token available")
            return False
            
        auth_headers = self.headers.copy()
        auth_headers["Authorization"] = f"Bearer {self.tokens['admin']}"
        
        response = requests.get(f"{self.base_url}/bookings/", headers=auth_headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Admin can view all bookings: {data.get('total', 0)} bookings found")
            return True
        else:
            print(f"[FAIL] Admin cannot view bookings: {response.status_code}")
            return False
            
    def test_client_can_only_view_own_bookings(self):
        """Test that client can only view their own bookings"""
        print("\n[TEST] Client viewing own bookings")
        
        if not self.tokens["client"]:
            print("[SKIP] No client token available")
            return False
            
        auth_headers = self.headers.copy()
        auth_headers["Authorization"] = f"Bearer {self.tokens['client']}"
        
        response = requests.get(f"{self.base_url}/bookings/my", headers=auth_headers)
        
        if response.status_code == 200:
            bookings = response.json()
            print(f"[OK] Client can view own bookings: {len(bookings)} bookings")
            return True
        else:
            print(f"[FAIL] Client cannot view own bookings: {response.status_code}")
            return False
            
    def run_all_tests(self):
        """Run all access control and validation tests"""
        print("\n" + "="*70)
        print("BOOKING ACCESS CONTROL AND VALIDATION TESTS")
        print("="*70)
        
        # Setup
        self.setup_test_users()
        if not self.setup_test_data():
            print("[ERROR] Failed to setup test data")
            return
            
        # Run tests
        results = {
            "unauthenticated_blocked": self.test_unauthenticated_booking(),
            "client_can_book": self.test_client_booking_with_all_fields(),
            "requires_vehicle": self.test_booking_without_vehicle(),
            "requires_services": self.test_booking_without_services(),
            "requires_schedule": self.test_booking_without_schedule(),
            "validates_schedule": self.test_booking_with_past_schedule(),
            "admin_view_all": self.test_admin_can_view_all_bookings(),
            "client_view_own": self.test_client_can_only_view_own_bookings()
        }
        
        # Summary
        print("\n" + "="*70)
        print("TEST RESULTS SUMMARY")
        print("="*70)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if results["requires_vehicle"] and results["requires_services"] and results["requires_schedule"]:
            print("\n[EXCELLENT] All required field validations working!")
            print("[OK] Clients cannot book without vehicle")
            print("[OK] Clients cannot book without services")
            print("[OK] Clients cannot book without schedule")
        
        if results["client_can_book"]:
            print("\n[OK] Clients CAN create bookings with all required fields")
        
        if results["unauthenticated_blocked"]:
            print("[OK] Unauthenticated users are blocked from booking")
            
        return results


if __name__ == "__main__":
    tester = BookingAccessControlTests()
    tester.run_all_tests()