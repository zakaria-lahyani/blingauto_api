"""
Scheduling Management Tests
Tests for business hours, wash bays, and smart booking engine functionality.

Test Coverage:
1. Business Hours CRUD (Manager/Admin only)
2. Wash Bays CRUD (Manager/Admin only) 
3. Smart Booking Engine with time slot validation
4. Booking confirmation schedule updates
5. Wash bay availability logic for multiple bays
"""

import requests
import json
from datetime import datetime, timedelta, time
from uuid import uuid4
from typing import Dict, Any, Optional, List


class SchedulingManagementTests:
    """Test scheduling management functionality"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.tokens = {
            "admin": None,
            "manager": None,
            "client": None,
            "washer": None
        }
        self.test_data = {
            "business_hours": [],
            "wash_bays": [],
            "services": [],
            "vehicles": [],
            "bookings": []
        }
        
    def setup_test_users(self):
        """Setup test users with different roles"""
        print("\n" + "="*70)
        print("SETTING UP TEST USERS FOR SCHEDULING TESTS")
        print("="*70)
        
        # Admin login
        admin_creds = {"email": "admin@carwash.com", "password": "AdminSecure123!@#"}
        response = requests.post(f"{self.base_url}/auth/login", json=admin_creds, headers=self.headers)
        if response.status_code == 200:
            self.tokens["admin"] = response.json()["access_token"]
            print("[OK] Admin logged in")
        else:
            print(f"[FAIL] Admin login failed: {response.status_code}")
            
        # Manager login
        manager_creds = {"email": "manager@carwash.com", "password": "ManagerSecure123!@#"}
        response = requests.post(f"{self.base_url}/auth/login", json=manager_creds, headers=self.headers)
        if response.status_code == 200:
            self.tokens["manager"] = response.json()["access_token"]
            print("[OK] Manager logged in")
        else:
            print("[INFO] Manager not found, using admin token")
            self.tokens["manager"] = self.tokens["admin"]
            
        # Create client user
        self.create_client_user()
        
        # Create washer user
        self.create_washer_user()
        
    def create_client_user(self):
        """Create a client user for testing"""
        client_data = {
            "email": f"client_sched_{uuid4().hex[:8]}@test.com",
            "password": "ClientTest123!@#",
            "full_name": "Test Scheduling Client",
            "phone_number": "+1234567890"
        }
        
        response = requests.post(f"{self.base_url}/auth/register", json=client_data, headers=self.headers)
        if response.status_code in [200, 201]:
            print(f"[OK] Client registered: {client_data['email']}")
            
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
            
    def create_washer_user(self):
        """Create a washer user for testing"""
        washer_data = {
            "email": f"washer_sched_{uuid4().hex[:8]}@test.com",
            "password": "WasherTest123!@#",
            "full_name": "Test Washer",
            "phone_number": "+1234567891",
            "role": "washer"
        }
        
        # Use admin token to create washer
        admin_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['admin']}"}
        response = requests.post(f"{self.base_url}/auth/register", json=washer_data, headers=admin_headers)
        if response.status_code in [200, 201]:
            print(f"[OK] Washer registered: {washer_data['email']}")
            
            login_response = requests.post(
                f"{self.base_url}/auth/login",
                json={"email": washer_data["email"], "password": washer_data["password"]},
                headers=self.headers
            )
            if login_response.status_code == 200:
                self.tokens["washer"] = login_response.json()["access_token"]
                print("[OK] Washer logged in")
            else:
                print(f"[FAIL] Washer login failed: {login_response.status_code}")
        else:
            print(f"[FAIL] Washer registration failed: {response.status_code}")

    # ====================================================================
    # BUSINESS HOURS CRUD TESTS (Manager/Admin Only)
    # ====================================================================
    
    def test_business_hours_crud_authorization(self):
        """Test that only managers and admins can CRUD business hours"""
        print("\n" + "="*70)
        print("TESTING BUSINESS HOURS CRUD AUTHORIZATION")
        print("="*70)
        
        business_hours_data = {
            "day_of_week": "monday",
            "open_time": "08:00:00",
            "close_time": "18:00:00",
            "is_closed": False,
            "break_periods": [
                {"start": "12:00:00", "end": "13:00:00"}
            ]
        }
        
        # Test client cannot create business hours
        print("\n--- Testing Client Access (Should Fail) ---")
        client_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['client']}"}
        response = requests.post(f"{self.base_url}/scheduling/business-hours", 
                               json=business_hours_data, headers=client_headers)
        
        if response.status_code == 403:
            print("[OK] Client correctly denied access to create business hours")
        else:
            print(f"[FAIL] Client should be denied access, got status: {response.status_code}")
            
        # Test washer cannot create business hours
        print("\n--- Testing Washer Access (Should Fail) ---")
        washer_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washer']}"}
        response = requests.post(f"{self.base_url}/scheduling/business-hours", 
                               json=business_hours_data, headers=washer_headers)
        
        if response.status_code == 403:
            print("[OK] Washer correctly denied access to create business hours")
        else:
            print(f"[FAIL] Washer should be denied access, got status: {response.status_code}")
            
        # Test manager can create business hours
        print("\n--- Testing Manager Access (Should Succeed) ---")
        manager_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['manager']}"}
        response = requests.post(f"{self.base_url}/scheduling/business-hours", 
                               json=business_hours_data, headers=manager_headers)
        
        if response.status_code in [200, 201]:
            business_hours = response.json()
            self.test_data["business_hours"].append(business_hours)
            print(f"[OK] Manager successfully created business hours: {business_hours.get('id')}")
        else:
            print(f"[FAIL] Manager should be able to create business hours, got status: {response.status_code}")
            print(f"Response: {response.text}")
            
        # Test admin can create business hours
        print("\n--- Testing Admin Access (Should Succeed) ---")
        admin_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['admin']}"}
        tuesday_hours = {**business_hours_data, "day_of_week": "tuesday"}
        response = requests.post(f"{self.base_url}/scheduling/business-hours", 
                               json=tuesday_hours, headers=admin_headers)
        
        if response.status_code in [200, 201]:
            business_hours = response.json()
            self.test_data["business_hours"].append(business_hours)
            print(f"[OK] Admin successfully created business hours: {business_hours.get('id')}")
        else:
            print(f"[FAIL] Admin should be able to create business hours, got status: {response.status_code}")
            print(f"Response: {response.text}")
            
    def test_business_hours_crud_operations(self):
        """Test full CRUD operations for business hours"""
        print("\n" + "="*70)
        print("TESTING BUSINESS HOURS CRUD OPERATIONS")
        print("="*70)
        
        admin_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['admin']}"}
        
        # CREATE
        print("\n--- Testing CREATE ---")
        create_data = {
            "day_of_week": "wednesday",
            "open_time": "09:00:00",
            "close_time": "17:00:00",
            "is_closed": False,
            "break_periods": [
                {"start": "12:30:00", "end": "13:30:00"}
            ]
        }
        
        response = requests.post(f"{self.base_url}/scheduling/business-hours", 
                               json=create_data, headers=admin_headers)
        
        if response.status_code in [200, 201]:
            created_hours = response.json()
            business_hours_id = created_hours.get('id')
            print(f"[OK] Created business hours: {business_hours_id}")
            self.test_data["business_hours"].append(created_hours)
        else:
            print(f"[FAIL] Create failed: {response.status_code} - {response.text}")
            return
            
        # READ
        print("\n--- Testing READ ---")
        response = requests.get(f"{self.base_url}/scheduling/business-hours/{business_hours_id}", 
                              headers=admin_headers)
        
        if response.status_code == 200:
            hours_data = response.json()
            print(f"[OK] Retrieved business hours: {hours_data.get('day_of_week')}")
        else:
            print(f"[FAIL] Read failed: {response.status_code} - {response.text}")
            
        # UPDATE
        print("\n--- Testing UPDATE ---")
        update_data = {
            "open_time": "08:30:00",
            "close_time": "18:30:00",
            "break_periods": [
                {"start": "12:00:00", "end": "13:00:00"},
                {"start": "15:00:00", "end": "15:15:00"}
            ]
        }
        
        response = requests.put(f"{self.base_url}/scheduling/business-hours/{business_hours_id}", 
                              json=update_data, headers=admin_headers)
        
        if response.status_code == 200:
            updated_hours = response.json()
            print(f"[OK] Updated business hours: {updated_hours.get('open_time')} - {updated_hours.get('close_time')}")
        else:
            print(f"[FAIL] Update failed: {response.status_code} - {response.text}")
            
        # LIST
        print("\n--- Testing LIST ---")
        response = requests.get(f"{self.base_url}/scheduling/business-hours", headers=admin_headers)
        
        if response.status_code == 200:
            hours_list = response.json()
            print(f"[OK] Listed {len(hours_list)} business hours")
        else:
            print(f"[FAIL] List failed: {response.status_code} - {response.text}")

    # ====================================================================
    # WASH BAYS CRUD TESTS (Manager/Admin Only)
    # ====================================================================
    
    def test_wash_bays_crud_authorization(self):
        """Test that only managers and admins can CRUD wash bays"""
        print("\n" + "="*70)
        print("TESTING WASH BAYS CRUD AUTHORIZATION")
        print("="*70)
        
        wash_bay_data = {
            "name": "Test Bay 1",
            "bay_number": 101,
            "is_active": True,
            "equipment_types": ["pressure_washer", "foam_cannon", "vacuum"],
            "max_vehicle_size": "standard",
            "has_covered_area": True,
            "has_power_supply": True,
            "notes": "Test bay for automated testing"
        }
        
        # Test client cannot create wash bays
        print("\n--- Testing Client Access (Should Fail) ---")
        client_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['client']}"}
        response = requests.post(f"{self.base_url}/scheduling/wash-bays", 
                               json=wash_bay_data, headers=client_headers)
        
        if response.status_code == 403:
            print("[OK] Client correctly denied access to create wash bays")
        else:
            print(f"[FAIL] Client should be denied access, got status: {response.status_code}")
            
        # Test washer cannot create wash bays
        print("\n--- Testing Washer Access (Should Fail) ---")
        washer_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washer']}"}
        response = requests.post(f"{self.base_url}/scheduling/wash-bays", 
                               json=wash_bay_data, headers=washer_headers)
        
        if response.status_code == 403:
            print("[OK] Washer correctly denied access to create wash bays")
        else:
            print(f"[FAIL] Washer should be denied access, got status: {response.status_code}")
            
        # Test manager can create wash bays
        print("\n--- Testing Manager Access (Should Succeed) ---")
        manager_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['manager']}"}
        response = requests.post(f"{self.base_url}/scheduling/wash-bays", 
                               json=wash_bay_data, headers=manager_headers)
        
        if response.status_code in [200, 201]:
            wash_bay = response.json()
            self.test_data["wash_bays"].append(wash_bay)
            print(f"[OK] Manager successfully created wash bay: {wash_bay.get('id')}")
        else:
            print(f"[FAIL] Manager should be able to create wash bay, got status: {response.status_code}")
            print(f"Response: {response.text}")
            
        # Test admin can create wash bays
        print("\n--- Testing Admin Access (Should Succeed) ---")
        admin_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['admin']}"}
        bay_2_data = {**wash_bay_data, "name": "Test Bay 2", "bay_number": 102}
        response = requests.post(f"{self.base_url}/scheduling/wash-bays", 
                               json=bay_2_data, headers=admin_headers)
        
        if response.status_code in [200, 201]:
            wash_bay = response.json()
            self.test_data["wash_bays"].append(wash_bay)
            print(f"[OK] Admin successfully created wash bay: {wash_bay.get('id')}")
        else:
            print(f"[FAIL] Admin should be able to create wash bay, got status: {response.status_code}")
            print(f"Response: {response.text}")

    def test_wash_bays_crud_operations(self):
        """Test full CRUD operations for wash bays"""
        print("\n" + "="*70)
        print("TESTING WASH BAYS CRUD OPERATIONS")
        print("="*70)
        
        admin_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['admin']}"}
        
        # CREATE
        print("\n--- Testing CREATE ---")
        create_data = {
            "name": "Premium Detailing Bay",
            "bay_number": 201,
            "is_active": True,
            "equipment_types": ["pressure_washer", "foam_cannon", "vacuum", "steam_cleaner", "hot_water"],
            "max_vehicle_size": "large",
            "has_covered_area": True,
            "has_power_supply": True,
            "notes": "Specialized bay for premium detailing services"
        }
        
        response = requests.post(f"{self.base_url}/scheduling/wash-bays", 
                               json=create_data, headers=admin_headers)
        
        if response.status_code in [200, 201]:
            created_bay = response.json()
            bay_id = created_bay.get('id')
            print(f"[OK] Created wash bay: {bay_id}")
            self.test_data["wash_bays"].append(created_bay)
        else:
            print(f"[FAIL] Create failed: {response.status_code} - {response.text}")
            return
            
        # READ
        print("\n--- Testing READ ---")
        response = requests.get(f"{self.base_url}/scheduling/wash-bays/{bay_id}", 
                              headers=admin_headers)
        
        if response.status_code == 200:
            bay_data = response.json()
            print(f"[OK] Retrieved wash bay: {bay_data.get('name')}")
        else:
            print(f"[FAIL] Read failed: {response.status_code} - {response.text}")
            
        # UPDATE
        print("\n--- Testing UPDATE ---")
        update_data = {
            "is_active": False,
            "notes": "Temporarily closed for maintenance",
            "equipment_types": ["pressure_washer", "foam_cannon", "vacuum", "steam_cleaner"]
        }
        
        response = requests.put(f"{self.base_url}/scheduling/wash-bays/{bay_id}", 
                              json=update_data, headers=admin_headers)
        
        if response.status_code == 200:
            updated_bay = response.json()
            print(f"[OK] Updated wash bay: Active={updated_bay.get('is_active')}")
        else:
            print(f"[FAIL] Update failed: {response.status_code} - {response.text}")
            
        # LIST
        print("\n--- Testing LIST ---")
        response = requests.get(f"{self.base_url}/scheduling/wash-bays", headers=admin_headers)
        
        if response.status_code == 200:
            bays_list = response.json()
            print(f"[OK] Listed {len(bays_list)} wash bays")
        else:
            print(f"[FAIL] List failed: {response.status_code} - {response.text}")

    # ====================================================================
    # SMART BOOKING ENGINE TESTS
    # ====================================================================
    
    def test_time_slot_availability_based_on_business_hours(self):
        """Test that available time slots respect business hours"""
        print("\n" + "="*70)
        print("TESTING TIME SLOT AVAILABILITY BASED ON BUSINESS HOURS")
        print("="*70)
        
        client_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['client']}"}
        
        # Get available time slots for booking
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"\n--- Getting Available Slots for {tomorrow} ---")
        response = requests.get(
            f"{self.base_url}/scheduling/available-slots",
            params={
                "date": tomorrow,
                "service_duration": 60,  # 1 hour service
                "service_type": "exterior_wash"
            },
            headers=client_headers
        )
        
        if response.status_code == 200:
            available_slots = response.json()
            print(f"[OK] Found {len(available_slots)} available slots")
            
            # Validate slots are within business hours
            for slot in available_slots:
                slot_time = datetime.fromisoformat(slot['start_time'].replace('Z', '+00:00')).time()
                print(f"  Available slot: {slot_time}")
                
                # Check if slot is within reasonable business hours (8 AM - 6 PM)
                if time(8, 0) <= slot_time <= time(18, 0):
                    print(f"    [OK] Slot {slot_time} is within business hours")
                else:
                    print(f"    [WARNING] Slot {slot_time} might be outside business hours")
                    
        else:
            print(f"[FAIL] Failed to get available slots: {response.status_code} - {response.text}")

    def test_wash_bay_availability_logic(self):
        """Test that multiple wash bays can handle concurrent bookings"""
        print("\n" + "="*70)
        print("TESTING WASH BAY AVAILABILITY LOGIC")
        print("="*70)
        
        client_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['client']}"}
        
        # Ensure we have at least 2 active wash bays
        admin_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['admin']}"}
        
        # Create additional wash bays for testing
        bay_data_1 = {
            "name": "Concurrent Test Bay 1",
            "bay_number": 301,
            "is_active": True,
            "equipment_types": ["pressure_washer", "foam_cannon"],
            "max_vehicle_size": "standard",
            "has_covered_area": True,
            "has_power_supply": True
        }
        
        bay_data_2 = {
            "name": "Concurrent Test Bay 2", 
            "bay_number": 302,
            "is_active": True,
            "equipment_types": ["pressure_washer", "foam_cannon"],
            "max_vehicle_size": "standard",
            "has_covered_area": True,
            "has_power_supply": True
        }
        
        # Create bays
        for bay_data in [bay_data_1, bay_data_2]:
            response = requests.post(f"{self.base_url}/scheduling/wash-bays", 
                                   json=bay_data, headers=admin_headers)
            if response.status_code in [200, 201]:
                self.test_data["wash_bays"].append(response.json())
                print(f"[OK] Created test bay: {bay_data['name']}")
        
        # Test concurrent availability
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"\n--- Testing Concurrent Bookings for {tomorrow} ---")
        
        # Get available slots
        response = requests.get(
            f"{self.base_url}/scheduling/available-slots",
            params={
                "date": tomorrow,
                "service_duration": 30,
                "service_type": "exterior_wash"
            },
            headers=client_headers
        )
        
        if response.status_code == 200:
            available_slots = response.json()
            print(f"[OK] Found {len(available_slots)} available slots")
            
            if len(available_slots) >= 2:
                # Test that same time slot can be booked on different bays
                first_slot = available_slots[0]
                print(f"  Testing slot: {first_slot['start_time']}")
                
                # Count how many bays can accommodate this time slot
                concurrent_capacity = sum(1 for slot in available_slots 
                                        if slot['start_time'] == first_slot['start_time'])
                
                print(f"  [OK] {concurrent_capacity} bays available for same time slot")
                
                if concurrent_capacity >= 2:
                    print("  [OK] Multiple bays can handle concurrent bookings")
                else:
                    print("  [INFO] Only one bay available - may need more bays for concurrency")
            else:
                print("  [WARNING] Not enough available slots to test concurrency")
        else:
            print(f"[FAIL] Failed to get available slots: {response.status_code}")

    def test_booking_confirmation_updates_schedule(self):
        """Test that confirming a booking updates the schedule and reduces availability"""
        print("\n" + "="*70)
        print("TESTING BOOKING CONFIRMATION SCHEDULE UPDATES")
        print("="*70)
        
        # Setup: Create a vehicle and get available services
        self.setup_test_vehicle_and_service()
        
        client_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['client']}"}
        
        # Get initial available slots
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"\n--- Getting Initial Available Slots for {tomorrow} ---")
        response = requests.get(
            f"{self.base_url}/scheduling/available-slots",
            params={
                "date": tomorrow,
                "service_duration": 60,
                "service_type": "exterior_wash"
            },
            headers=client_headers
        )
        
        if response.status_code != 200:
            print(f"[FAIL] Failed to get initial slots: {response.status_code}")
            return
            
        initial_slots = response.json()
        initial_count = len(initial_slots)
        print(f"[OK] Initial available slots: {initial_count}")
        
        if not initial_slots:
            print("[SKIP] No available slots to test booking")
            return
            
        # Create a booking for the first available slot
        selected_slot = initial_slots[0]
        booking_data = {
            "vehicle_id": self.test_data["vehicles"][0]["id"],
            "service_ids": [self.test_data["services"][0]["id"]],
            "scheduled_at": selected_slot["start_time"],
            "booking_type": "stationary",
            "notes": "Test booking for schedule update validation"
        }
        
        print(f"\n--- Creating Booking for {selected_slot['start_time']} ---")
        response = requests.post(f"{self.base_url}/bookings", 
                               json=booking_data, headers=client_headers)
        
        if response.status_code in [200, 201]:
            booking = response.json()
            self.test_data["bookings"].append(booking)
            print(f"[OK] Created booking: {booking.get('id')}")
            
            # Confirm the booking (if it's not auto-confirmed)
            if booking.get('status') == 'pending':
                print("\n--- Confirming Booking ---")
                confirm_response = requests.post(
                    f"{self.base_url}/bookings/{booking['id']}/confirm",
                    headers=client_headers
                )
                
                if confirm_response.status_code == 200:
                    print("[OK] Booking confirmed")
                else:
                    print(f"[WARNING] Booking confirmation failed: {confirm_response.status_code}")
            
            # Check that available slots are reduced
            print(f"\n--- Checking Updated Available Slots ---")
            response = requests.get(
                f"{self.base_url}/scheduling/available-slots",
                params={
                    "date": tomorrow,
                    "service_duration": 60,
                    "service_type": "exterior_wash"
                },
                headers=client_headers
            )
            
            if response.status_code == 200:
                updated_slots = response.json()
                updated_count = len(updated_slots)
                print(f"[OK] Updated available slots: {updated_count}")
                
                # Verify the booked slot is no longer available (at least on the same bay)
                booked_time = selected_slot["start_time"]
                same_time_slots = [slot for slot in updated_slots 
                                 if slot["start_time"] == booked_time]
                
                if len(same_time_slots) < len([slot for slot in initial_slots 
                                             if slot["start_time"] == booked_time]):
                    print("[OK] Booking reduced availability for the same time slot")
                else:
                    print("[INFO] Same time slot still available (different bay)")
                    
            else:
                print(f"[FAIL] Failed to get updated slots: {response.status_code}")
                
        else:
            print(f"[FAIL] Failed to create booking: {response.status_code} - {response.text}")

    def setup_test_vehicle_and_service(self):
        """Setup test vehicle and service for booking tests"""
        if not self.test_data["vehicles"] or not self.test_data["services"]:
            client_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['client']}"}
            
            # Create test vehicle
            vehicle_data = {
                "make": "Toyota",
                "model": "Camry",
                "year": 2022,
                "color": "Silver",
                "license_plate": f"TEST{uuid4().hex[:4].upper()}",
                "is_default": True
            }
            
            response = requests.post(f"{self.base_url}/vehicles", 
                                   json=vehicle_data, headers=client_headers)
            
            if response.status_code in [200, 201]:
                self.test_data["vehicles"].append(response.json())
                print("[OK] Created test vehicle")
                
            # Get available services
            response = requests.get(f"{self.base_url}/services", headers=client_headers)
            if response.status_code == 200:
                services = response.json()
                if services:
                    self.test_data["services"] = services[:1]  # Take first service
                    print("[OK] Got test service")

    def test_smart_booking_suggestions(self):
        """Test smart booking engine suggestions based on service type and availability"""
        print("\n" + "="*70)
        print("TESTING SMART BOOKING SUGGESTIONS")
        print("="*70)
        
        client_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['client']}"}
        
        # Test suggestions for different service types
        service_types = ["exterior_wash", "full_detail", "interior_clean"]
        
        for service_type in service_types:
            print(f"\n--- Testing Suggestions for {service_type} ---")
            
            response = requests.get(
                f"{self.base_url}/scheduling/smart-suggestions",
                params={
                    "service_type": service_type,
                    "preferred_time": "morning",  # morning, afternoon, evening
                    "days_ahead": 7
                },
                headers=client_headers
            )
            
            if response.status_code == 200:
                suggestions = response.json()
                print(f"[OK] Got {len(suggestions)} suggestions for {service_type}")
                
                for suggestion in suggestions[:3]:  # Show first 3
                    print(f"  Suggestion: {suggestion.get('date')} at {suggestion.get('time')}")
                    print(f"    Bay: {suggestion.get('bay_name')}")
                    print(f"    Confidence: {suggestion.get('confidence_score', 'N/A')}")
                    
            else:
                print(f"[FAIL] Failed to get suggestions for {service_type}: {response.status_code}")

    def run_all_tests(self):
        """Run all scheduling management tests"""
        print("\n" + "="*80)
        print("STARTING COMPREHENSIVE SCHEDULING MANAGEMENT TESTS")
        print("="*80)
        
        try:
            # Setup
            self.setup_test_users()
            
            # Business Hours Tests
            self.test_business_hours_crud_authorization()
            self.test_business_hours_crud_operations()
            
            # Wash Bays Tests
            self.test_wash_bays_crud_authorization()
            self.test_wash_bays_crud_operations()
            
            # Smart Booking Engine Tests
            self.test_time_slot_availability_based_on_business_hours()
            self.test_wash_bay_availability_logic()
            self.test_booking_confirmation_updates_schedule()
            self.test_smart_booking_suggestions()
            
            print("\n" + "="*80)
            print("SCHEDULING MANAGEMENT TESTS COMPLETED")
            print("="*80)
            
        except Exception as e:
            print(f"\n[ERROR] Test execution failed: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    tests = SchedulingManagementTests()
    tests.run_all_tests()