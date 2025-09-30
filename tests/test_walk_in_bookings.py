"""
Walk-in Booking System Tests
Tests for walk-in customer registration, booking creation, and automatic schedule adjustment.

Test Coverage:
1. Walk-in customer registration by washers
2. Vehicle registration on-the-spot
3. Walk-in booking creation with schedule adjustment
4. Work tracking and completion
5. Accounting integration
6. Washer dashboard functionality
"""

import requests
import json
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Dict, Any, Optional


class WalkInBookingTests:
    """Test walk-in booking functionality"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.tokens = {
            "admin": None,
            "manager": None,
            "washer": None,
            "client": None
        }
        self.test_data = {
            "customers": [],
            "vehicles": [],
            "bookings": [],
            "work_sessions": []
        }
        
    def setup_test_users(self):
        """Setup test users with different roles"""
        print("\n" + "="*70)
        print("SETTING UP TEST USERS FOR WALK-IN BOOKING TESTS")
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
            self.tokens["manager"] = self.tokens["admin"]
            print("[INFO] Manager not found, using admin token")
            
        # Create washer user
        self.create_washer_user()
        
        # Create client user for comparison tests
        self.create_client_user()
        
    def create_washer_user(self):
        """Create a washer user for testing"""
        washer_data = {
            "email": f"washer_test_{uuid4().hex[:8]}@test.com",
            "password": "WasherTest123!@#",
            "full_name": "Test Washer Employee",
            "phone_number": "+1234567890",
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
            
    def create_client_user(self):
        """Create a client user for comparison tests"""
        client_data = {
            "email": f"client_walkin_{uuid4().hex[:8]}@test.com",
            "password": "ClientTest123!@#",
            "full_name": "Test Client User",
            "phone_number": "+1234567891"
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

    # ====================================================================
    # WALK-IN CUSTOMER REGISTRATION TESTS
    # ====================================================================
    
    def test_walk_in_customer_registration_authorization(self):
        """Test that only washers, managers, and admins can register walk-in customers"""
        print("\n" + "="*70)
        print("TESTING WALK-IN CUSTOMER REGISTRATION AUTHORIZATION")
        print("="*70)
        
        customer_data = {
            "first_name": "John",
            "last_name": "WalkIn",
            "phone": "+1555123456",
            "email": "john.walkin@temp.com"
        }
        
        # Test client cannot register walk-in customers
        print("\n--- Testing Client Access (Should Fail) ---")
        client_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['client']}"}
        response = requests.post(f"{self.base_url}/walk-in/register-customer", 
                               json=customer_data, headers=client_headers)
        
        if response.status_code == 403:
            print("[OK] Client correctly denied access to register walk-in customers")
        else:
            print(f"[FAIL] Client should be denied access, got status: {response.status_code}")
            
        # Test washer can register walk-in customers
        print("\n--- Testing Washer Access (Should Succeed) ---")
        washer_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washer']}"}
        response = requests.post(f"{self.base_url}/walk-in/register-customer", 
                               json=customer_data, headers=washer_headers)
        
        if response.status_code in [200, 201]:
            customer = response.json()
            self.test_data["customers"].append(customer)
            print(f"[OK] Washer successfully registered walk-in customer: {customer.get('customer_id')}")
            print(f"    Customer name: {customer['customer_info']['name']}")
            print(f"    Registered by: {customer['registered_by']['washer_name']}")
        else:
            print(f"[FAIL] Washer should be able to register customers, got status: {response.status_code}")
            print(f"Response: {response.text}")
            
        # Test admin can register walk-in customers
        print("\n--- Testing Admin Access (Should Succeed) ---")
        admin_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['admin']}"}
        admin_customer_data = {**customer_data, "first_name": "Jane", "email": "jane.admin.walkin@temp.com"}
        response = requests.post(f"{self.base_url}/walk-in/register-customer", 
                               json=admin_customer_data, headers=admin_headers)
        
        if response.status_code in [200, 201]:
            customer = response.json()
            self.test_data["customers"].append(customer)
            print(f"[OK] Admin successfully registered walk-in customer: {customer.get('customer_id')}")
        else:
            print(f"[FAIL] Admin should be able to register customers, got status: {response.status_code}")

    def test_walk_in_customer_registration_workflow(self):
        """Test the complete walk-in customer registration workflow"""
        print("\n" + "="*70)
        print("TESTING WALK-IN CUSTOMER REGISTRATION WORKFLOW")
        print("="*70)
        
        washer_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washer']}"}
        
        # Test 1: Register customer with minimal information
        print("\n--- Testing Minimal Customer Registration ---")
        minimal_customer = {
            "first_name": "Quick",
            "last_name": "Service",
            "phone": "+1555999888"
        }
        
        response = requests.post(f"{self.base_url}/walk-in/register-customer", 
                               json=minimal_customer, headers=washer_headers)
        
        if response.status_code in [200, 201]:
            customer = response.json()
            print(f"[OK] Minimal customer registered: {customer['customer_info']['name']}")
            print(f"    Auto-generated email: {customer['customer_info']['email']}")
            print(f"    Walk-in flag: {customer['customer_info']['is_walk_in']}")
            self.test_data["customers"].append(customer)
        else:
            print(f"[FAIL] Minimal customer registration failed: {response.status_code}")
            
        # Test 2: Register customer with complete information
        print("\n--- Testing Complete Customer Registration ---")
        complete_customer = {
            "first_name": "Complete",
            "last_name": "Customer",
            "phone": "+1555777666",
            "email": "complete.customer@example.com"
        }
        
        response = requests.post(f"{self.base_url}/walk-in/register-customer", 
                               json=complete_customer, headers=washer_headers)
        
        if response.status_code in [200, 201]:
            customer = response.json()
            print(f"[OK] Complete customer registered: {customer['customer_info']['name']}")
            print(f"    Email: {customer['customer_info']['email']}")
            print(f"    Next step: {customer['next_step']}")
            self.test_data["customers"].append(customer)
        else:
            print(f"[FAIL] Complete customer registration failed: {response.status_code}")

    # ====================================================================
    # VEHICLE REGISTRATION TESTS
    # ====================================================================
    
    def test_vehicle_registration_on_the_spot(self):
        """Test registering vehicles for walk-in customers"""
        print("\n" + "="*70)
        print("TESTING VEHICLE REGISTRATION ON-THE-SPOT")
        print("="*70)
        
        if not self.test_data["customers"]:
            print("[SKIP] No customers available for vehicle registration")
            return
            
        washer_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washer']}"}
        customer = self.test_data["customers"][0]
        
        # Test vehicle registration
        print(f"\n--- Registering Vehicle for Customer {customer['customer_id']} ---")
        vehicle_data = {
            "customer_id": str(customer["customer_id"]),
            "make": "Toyota",
            "model": "Camry",
            "year": 2022,
            "color": "Silver",
            "license_plate": f"WI{uuid4().hex[:4].upper()}"
        }
        
        response = requests.post(f"{self.base_url}/walk-in/register-vehicle", 
                               json=vehicle_data, headers=washer_headers)
        
        if response.status_code in [200, 201]:
            vehicle = response.json()
            self.test_data["vehicles"].append(vehicle)
            print(f"[OK] Vehicle registered: {vehicle['vehicle_info']['year']} {vehicle['vehicle_info']['make']} {vehicle['vehicle_info']['model']}")
            print(f"    License plate: {vehicle['vehicle_info']['license_plate']}")
            print(f"    Customer ID: {vehicle['customer_id']}")
            print(f"    Registered by: {vehicle['registered_by']['washer_name']}")
            print(f"    Next step: {vehicle['next_step']}")
        else:
            print(f"[FAIL] Vehicle registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            
        # Test registration of second vehicle for same customer
        print(f"\n--- Registering Second Vehicle for Same Customer ---")
        vehicle_data_2 = {
            "customer_id": str(customer["customer_id"]),
            "make": "Honda",
            "model": "Civic",
            "year": 2023,
            "color": "Blue",
            "license_plate": f"WI{uuid4().hex[:4].upper()}"
        }
        
        response = requests.post(f"{self.base_url}/walk-in/register-vehicle", 
                               json=vehicle_data_2, headers=washer_headers)
        
        if response.status_code in [200, 201]:
            vehicle = response.json()
            self.test_data["vehicles"].append(vehicle)
            print(f"[OK] Second vehicle registered: {vehicle['vehicle_info']['year']} {vehicle['vehicle_info']['make']} {vehicle['vehicle_info']['model']}")
        else:
            print(f"[FAIL] Second vehicle registration failed: {response.status_code}")

    def test_vehicle_registration_validation(self):
        """Test vehicle registration validation"""
        print("\n" + "="*70)
        print("TESTING VEHICLE REGISTRATION VALIDATION")
        print("="*70)
        
        if not self.test_data["customers"]:
            print("[SKIP] No customers available for validation testing")
            return
            
        washer_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washer']}"}
        customer = self.test_data["customers"][0]
        
        # Test missing required fields
        print("\n--- Testing Missing Required Fields ---")
        invalid_vehicle_data = {
            "customer_id": str(customer["customer_id"]),
            "make": "Tesla",
            # Missing model, year, color, license_plate
        }
        
        response = requests.post(f"{self.base_url}/walk-in/register-vehicle", 
                               json=invalid_vehicle_data, headers=washer_headers)
        
        if response.status_code == 400:
            print("[OK] Validation correctly rejected missing fields")
        else:
            print(f"[FAIL] Should have rejected missing fields, got: {response.status_code}")
            
        # Test invalid customer ID
        print("\n--- Testing Invalid Customer ID ---")
        invalid_customer_data = {
            "customer_id": "invalid-uuid",
            "make": "Tesla",
            "model": "Model 3",
            "year": 2023,
            "color": "Red",
            "license_plate": "INVALID"
        }
        
        response = requests.post(f"{self.base_url}/walk-in/register-vehicle", 
                               json=invalid_customer_data, headers=washer_headers)
        
        if response.status_code in [400, 404]:
            print("[OK] Validation correctly rejected invalid customer ID")
        else:
            print(f"[FAIL] Should have rejected invalid customer ID, got: {response.status_code}")

    # ====================================================================
    # WALK-IN BOOKING CREATION TESTS
    # ====================================================================
    
    def test_walk_in_booking_creation(self):
        """Test creating walk-in bookings with automatic schedule adjustment"""
        print("\n" + "="*70)
        print("TESTING WALK-IN BOOKING CREATION WITH SCHEDULE ADJUSTMENT")
        print("="*70)
        
        if not self.test_data["vehicles"]:
            print("[SKIP] No vehicles available for booking creation")
            return
            
        washer_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washer']}"}
        vehicle = self.test_data["vehicles"][0]
        
        # Get available services first
        print("\n--- Getting Available Services ---")
        response = requests.get(f"{self.base_url}/services", headers=washer_headers)
        if response.status_code == 200:
            services = response.json()
            if services:
                print(f"[OK] Found {len(services)} available services")
                selected_services = services[:2]  # Select first 2 services
            else:
                print("[WARNING] No services found, using dummy service IDs")
                selected_services = [{"id": str(uuid4())}]
        else:
            print(f"[WARNING] Could not get services: {response.status_code}")
            selected_services = [{"id": str(uuid4())}]
        
        # Create walk-in booking
        print(f"\n--- Creating Walk-in Booking for Vehicle {vehicle['vehicle_id']} ---")
        booking_data = {
            "customer_id": str(vehicle["customer_id"]),
            "vehicle_id": str(vehicle["vehicle_id"]),
            "service_ids": [service["id"] for service in selected_services],
            "notes": "Walk-in customer - immediate service required"
        }
        
        response = requests.post(f"{self.base_url}/walk-in/create-booking", 
                               json=booking_data, headers=washer_headers)
        
        if response.status_code in [200, 201]:
            booking = response.json()
            self.test_data["bookings"].append(booking)
            
            print(f"[OK] Walk-in booking created successfully")
            print(f"    Booking ID: {booking['booking']['id']}")
            print(f"    Confirmation: {booking['booking']['confirmation_number']}")
            print(f"    Status: {booking['booking']['status']}")
            print(f"    Total Price: ${booking['booking']['total_price']}")
            print(f"    Duration: {booking['booking']['total_duration']} minutes")
            print(f"    Started at: {booking['booking']['started_at']}")
            print(f"    Estimated completion: {booking['booking']['estimated_completion']}")
            
            # Schedule info
            schedule = booking['schedule_info']
            print(f"    Assigned bay: {schedule['assigned_bay_name']}")
            print(f"    Washer assigned: {schedule['washer_assigned']['name']}")
            print(f"    Schedule adjusted: {schedule['schedule_automatically_adjusted']}")
            
            # Pricing details
            pricing = booking['pricing_details']
            print(f"    Base price: ${pricing['base_price']}")
            print(f"    Walk-in premium: {pricing['walk_in_premium']}")
            
            # Work tracking
            work = booking['work_tracking']
            print(f"    Work session: {work['work_session_id']}")
            print(f"    Tracking started: {work['tracking_started']}")
            
        else:
            print(f"[FAIL] Walk-in booking creation failed: {response.status_code}")
            print(f"Response: {response.text}")

    def test_walk_in_booking_with_bay_specification(self):
        """Test walk-in booking with specific bay assignment"""
        print("\n" + "="*70)
        print("TESTING WALK-IN BOOKING WITH BAY SPECIFICATION")
        print("="*70)
        
        if not self.test_data["vehicles"] or len(self.test_data["vehicles"]) < 2:
            print("[SKIP] Need at least 2 vehicles for bay specification test")
            return
            
        washer_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washer']}"}
        vehicle = self.test_data["vehicles"][1]  # Use second vehicle
        
        # Test with specific bay assignment
        booking_data = {
            "customer_id": str(vehicle["customer_id"]),
            "vehicle_id": str(vehicle["vehicle_id"]),
            "service_ids": [str(uuid4())],  # Dummy service ID
            "bay_id": str(uuid4()),  # Specific bay assignment
            "notes": "Walk-in with specific bay request"
        }
        
        response = requests.post(f"{self.base_url}/walk-in/create-booking", 
                               json=booking_data, headers=washer_headers)
        
        if response.status_code in [200, 201]:
            booking = response.json()
            print(f"[OK] Walk-in booking with bay specification created")
            print(f"    Assigned bay: {booking['schedule_info']['assigned_bay_name']}")
        elif response.status_code == 409:
            print(f"[OK] Correctly handled bay conflict: {response.status_code}")
            conflict_data = response.json()
            print(f"    Conflict message: {conflict_data.get('detail', 'Bay not available')}")
        else:
            print(f"[INFO] Bay specification test result: {response.status_code}")

    # ====================================================================
    # WORK TRACKING TESTS
    # ====================================================================
    
    def test_work_session_management(self):
        """Test work session tracking and management"""
        print("\n" + "="*70)
        print("TESTING WORK SESSION MANAGEMENT")
        print("="*70)
        
        washer_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washer']}"}
        
        # Get active work sessions
        print("\n--- Getting Active Work Sessions ---")
        response = requests.get(f"{self.base_url}/walk-in/work-sessions/active", headers=washer_headers)
        
        if response.status_code == 200:
            sessions = response.json()
            print(f"[OK] Retrieved active work sessions")
            print(f"    Total active: {sessions['total_active']}")
            print(f"    Washer ID: {sessions['washer_id']}")
            
            for session in sessions['active_sessions']:
                print(f"    Session: {session['work_session_id'][:8]}...")
                print(f"      Vehicle: {session['vehicle_info']}")
                print(f"      Customer: {session['customer_name']}")
                print(f"      Bay: {session['bay_name']}")
                print(f"      Status: {session['status']}")
                print(f"      Elapsed: {session['elapsed_time_minutes']} minutes")
                print(f"      Completed: {session['services_completed']}")
                print(f"      Remaining: {session['services_remaining']}")
                
        else:
            print(f"[FAIL] Failed to get active work sessions: {response.status_code}")

    def test_service_completion_tracking(self):
        """Test marking individual services as completed"""
        print("\n" + "="*70)
        print("TESTING SERVICE COMPLETION TRACKING")
        print("="*70)
        
        washer_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washer']}"}
        
        # Simulate work session ID
        work_session_id = uuid4()
        
        # Complete first service
        print(f"\n--- Completing First Service in Session {str(work_session_id)[:8]}... ---")
        service_completion_data = {
            "service_id": str(uuid4()),
            "service_name": "Exterior Wash",
            "quality_rating": 5,
            "notes": "Excellent work, customer very satisfied",
            "actual_duration_minutes": 28,
            "total_services": 2,
            "completed_count": 0
        }
        
        response = requests.post(
            f"{self.base_url}/walk-in/work-sessions/{work_session_id}/complete-service", 
            json=service_completion_data, 
            headers=washer_headers
        )
        
        if response.status_code == 200:
            completion = response.json()
            print(f"[OK] Service completed successfully")
            print(f"    Service: {completion['service_completed']['service_name']}")
            print(f"    Completed at: {completion['service_completed']['completed_at']}")
            print(f"    Quality rating: {completion['service_completed']['quality_rating']}/5")
            print(f"    Duration: {completion['service_completed']['actual_duration_minutes']} minutes")
            print(f"    Progress: {completion['session_status']['overall_progress']}")
            print(f"    Labor cost: {completion['accounting']['labor_cost_this_service']}")
        else:
            print(f"[FAIL] Service completion failed: {response.status_code}")
            
        # Complete second service
        print(f"\n--- Completing Second Service ---")
        service_completion_data_2 = {
            "service_id": str(uuid4()),
            "service_name": "Interior Clean",
            "quality_rating": 4,
            "notes": "Good work, minor touch-ups needed",
            "actual_duration_minutes": 35,
            "total_services": 2,
            "completed_count": 1
        }
        
        response = requests.post(
            f"{self.base_url}/walk-in/work-sessions/{work_session_id}/complete-service", 
            json=service_completion_data_2, 
            headers=washer_headers
        )
        
        if response.status_code == 200:
            completion = response.json()
            print(f"[OK] Second service completed")
            print(f"    Overall progress: {completion['session_status']['overall_progress']}")
            print(f"    Remaining services: {completion['session_status']['remaining_services']}")
        else:
            print(f"[FAIL] Second service completion failed: {response.status_code}")

    def test_work_session_completion(self):
        """Test completing entire work session"""
        print("\n" + "="*70)
        print("TESTING WORK SESSION COMPLETION")
        print("="*70)
        
        washer_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washer']}"}
        work_session_id = uuid4()
        
        # Complete work session
        print(f"\n--- Completing Work Session {str(work_session_id)[:8]}... ---")
        completion_data = {
            "total_actual_duration_minutes": 65,
            "quality_notes": "Customer very satisfied with the service quality",
            "customer_satisfaction": 5
        }
        
        response = requests.post(
            f"{self.base_url}/walk-in/work-sessions/{work_session_id}/complete", 
            json=completion_data, 
            headers=washer_headers
        )
        
        if response.status_code == 200:
            completion = response.json()
            self.test_data["work_sessions"].append(completion)
            
            print(f"[OK] Work session completed successfully")
            print(f"    Session ID: {completion['work_session_id']}")
            print(f"    Booking ID: {completion['booking_id']}")
            
            # Completion summary
            summary = completion['completion_summary']
            print(f"    Completed at: {summary['completed_at']}")
            print(f"    Total duration: {summary['total_duration']}")
            print(f"    Customer satisfaction: {summary['customer_satisfaction']}")
            
            # Accounting details
            accounting = completion['accounting']
            print(f"    Labor hours: {accounting['labor_hours']}")
            print(f"    Hourly rate: {accounting['hourly_rate']}")
            print(f"    Total labor cost: {accounting['total_labor_cost']}")
            print(f"    Service revenue: {accounting['service_revenue']}")
            print(f"    Net revenue: {accounting['net_revenue']}")
            
            # Performance metrics
            performance = completion['performance_metrics']
            print(f"    Efficiency score: {performance['efficiency_score']}")
            print(f"    Quality score: {performance['quality_score']}")
            print(f"    Time vs estimate: {performance['time_vs_estimate']}")
            
        else:
            print(f"[FAIL] Work session completion failed: {response.status_code}")
            print(f"Response: {response.text}")

    # ====================================================================
    # WASHER DASHBOARD TESTS
    # ====================================================================
    
    def test_washer_dashboard(self):
        """Test washer dashboard functionality"""
        print("\n" + "="*70)
        print("TESTING WASHER DASHBOARD")
        print("="*70)
        
        washer_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washer']}"}
        
        # Get washer dashboard
        print("\n--- Getting Washer Dashboard ---")
        response = requests.get(f"{self.base_url}/walk-in/dashboard", headers=washer_headers)
        
        if response.status_code == 200:
            dashboard = response.json()
            
            print(f"[OK] Washer dashboard retrieved")
            
            # Washer info
            washer_info = dashboard['washer_info']
            print(f"    Washer: {washer_info['name']} ({washer_info['role']})")
            print(f"    Shift: {washer_info['shift_start']} - {washer_info['shift_end']}")
            
            # Daily summary
            daily = dashboard['daily_summary']
            print(f"    Services completed today: {daily['services_completed']}")
            print(f"    Walk-ins processed: {daily['walk_ins_processed']}")
            print(f"    Revenue generated: ${daily['total_revenue_generated']}")
            print(f"    Labor hours: {daily['total_labor_hours']}")
            print(f"    Average service time: {daily['average_service_time']} minutes")
            print(f"    Customer satisfaction: {daily['customer_satisfaction_avg']}/5")
            
            # Current status
            current = dashboard['current_status']
            print(f"    Current bay: {current['current_bay']}")
            print(f"    Status: {current['status']}")
            if current['current_booking']:
                booking = current['current_booking']
                print(f"    Current booking: {booking['vehicle']} ({booking['type']})")
                print(f"    Progress: {booking['progress']}")
            
            # Performance metrics
            performance = dashboard['performance_metrics']
            print(f"    Efficiency rating: {performance['efficiency_rating']}")
            print(f"    Quality score: {performance['quality_score']}/5")
            print(f"    This week earnings: ${performance['this_week_earnings']}")
            print(f"    Productivity trend: {performance['productivity_trend']}")
            
            # Available actions
            actions = dashboard['available_actions']
            print(f"    Available actions: {len(actions)}")
            for action in actions:
                print(f"      - {action}")
                
        else:
            print(f"[FAIL] Failed to get washer dashboard: {response.status_code}")

    # ====================================================================
    # ACCOUNTING INTEGRATION TESTS
    # ====================================================================
    
    def test_daily_accounting(self):
        """Test daily accounting for washer"""
        print("\n" + "="*70)
        print("TESTING DAILY ACCOUNTING")
        print("="*70)
        
        washer_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washer']}"}
        
        # Get today's accounting
        print("\n--- Getting Daily Accounting ---")
        today = datetime.now().strftime('%Y-%m-%d')
        response = requests.get(
            f"{self.base_url}/walk-in/accounting/daily",
            params={"date": today},
            headers=washer_headers
        )
        
        if response.status_code == 200:
            accounting = response.json()
            
            print(f"[OK] Daily accounting retrieved for {accounting['date']}")
            print(f"    Washer: {accounting['washer_name']}")
            
            # Summary
            summary = accounting['summary']
            print(f"    Total services: {summary['total_services']}")
            print(f"    Walk-in services: {summary['walk_in_services']}")
            print(f"    Total work hours: {summary['total_work_hours']}")
            print(f"    Total labor cost: ${summary['total_labor_cost']}")
            print(f"    Revenue generated: ${summary['total_revenue_generated']}")
            print(f"    Labor efficiency: {summary['labor_efficiency']}")
            
            # Service breakdown
            print("    Service breakdown:")
            for service in accounting['service_breakdown']:
                print(f"      {service['service_type']}: {service['count']} services")
                print(f"        Time: {service['total_time_minutes']} min")
                print(f"        Revenue: ${service['total_revenue']}")
                print(f"        Labor: ${service['labor_cost']}")
            
            # Earnings
            earnings = accounting['earnings']
            print(f"    Base pay: ${earnings['base_hourly_rate']}/hr × {earnings['total_base_pay']}")
            print(f"    Performance bonus: ${earnings['performance_bonus']}")
            print(f"    Walk-in bonus: ${earnings['walk_in_bonus']}")
            print(f"    Total daily earnings: ${earnings['total_daily_earnings']}")
            
        else:
            print(f"[FAIL] Failed to get daily accounting: {response.status_code}")

    def test_weekly_accounting(self):
        """Test weekly accounting summary"""
        print("\n" + "="*70)
        print("TESTING WEEKLY ACCOUNTING")
        print("="*70)
        
        washer_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washer']}"}
        
        # Get weekly accounting
        print("\n--- Getting Weekly Accounting ---")
        response = requests.get(f"{self.base_url}/walk-in/accounting/weekly", headers=washer_headers)
        
        if response.status_code == 200:
            weekly = response.json()
            
            print(f"[OK] Weekly accounting retrieved")
            print(f"    Week ending: {weekly['week_ending']}")
            
            # Summary
            summary = weekly['summary']
            print(f"    Days worked: {summary['total_days_worked']}")
            print(f"    Total services: {summary['total_services']}")
            print(f"    Total hours: {summary['total_work_hours']}")
            print(f"    Total earnings: ${summary['total_earnings']}")
            print(f"    Average daily earnings: ${summary['average_daily_earnings']}")
            print(f"    Revenue generated: ${summary['total_revenue_generated']}")
            print(f"    Labor efficiency: {summary['labor_efficiency']}")
            
            # Daily breakdown
            print("    Daily breakdown:")
            for day in weekly['daily_breakdown']:
                print(f"      {day['day']}: {day['services']} services, {day['hours']}h, ${day['earnings']}")
            
            # Performance trends
            trends = weekly['performance_trends']
            print(f"    Services per hour: {trends['services_per_hour']}")
            print(f"    Revenue per service: ${trends['revenue_per_service']}")
            print(f"    Efficiency trend: {trends['efficiency_trend']}")
            
            # Bonuses
            bonuses = weekly['bonuses_earned']
            print(f"    Performance bonus: ${bonuses['performance_bonus']}")
            print(f"    Walk-in bonus: ${bonuses['walk_in_bonus']}")
            print(f"    Quality bonus: ${bonuses['quality_bonus']}")
            print(f"    Total bonuses: ${bonuses['total_bonuses']}")
            
        else:
            print(f"[FAIL] Failed to get weekly accounting: {response.status_code}")

    # ====================================================================
    # AUTHORIZATION EDGE CASES
    # ====================================================================
    
    def test_client_access_restrictions(self):
        """Test that clients cannot access walk-in functionality"""
        print("\n" + "="*70)
        print("TESTING CLIENT ACCESS RESTRICTIONS")
        print("="*70)
        
        client_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['client']}"}
        
        # Test endpoints that clients should not access
        restricted_endpoints = [
            ("POST", "/walk-in/register-customer", {}),
            ("POST", "/walk-in/register-vehicle", {}),
            ("POST", "/walk-in/create-booking", {}),
            ("GET", "/walk-in/work-sessions/active", None),
            ("GET", "/walk-in/dashboard", None),
            ("GET", "/walk-in/accounting/daily", None)
        ]
        
        for method, endpoint, data in restricted_endpoints:
            print(f"\n--- Testing {method} {endpoint} ---")
            
            if method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}", json=data, headers=client_headers)
            else:
                response = requests.get(f"{self.base_url}{endpoint}", headers=client_headers)
            
            if response.status_code == 403:
                print(f"[OK] Client correctly denied access to {endpoint}")
            else:
                print(f"[FAIL] Client should be denied access to {endpoint}, got: {response.status_code}")

    def run_all_tests(self):
        """Run all walk-in booking tests"""
        print("\n" + "="*80)
        print("STARTING COMPREHENSIVE WALK-IN BOOKING TESTS")
        print("="*80)
        
        try:
            # Setup
            self.setup_test_users()
            
            # Authorization tests
            self.test_walk_in_customer_registration_authorization()
            
            # Customer registration workflow
            self.test_walk_in_customer_registration_workflow()
            
            # Vehicle registration
            self.test_vehicle_registration_on_the_spot()
            self.test_vehicle_registration_validation()
            
            # Walk-in booking creation
            self.test_walk_in_booking_creation()
            self.test_walk_in_booking_with_bay_specification()
            
            # Work tracking
            self.test_work_session_management()
            self.test_service_completion_tracking()
            self.test_work_session_completion()
            
            # Dashboard and analytics
            self.test_washer_dashboard()
            
            # Accounting integration
            self.test_daily_accounting()
            self.test_weekly_accounting()
            
            # Access control
            self.test_client_access_restrictions()
            
            print("\n" + "="*80)
            print("WALK-IN BOOKING TESTS COMPLETED")
            print("="*80)
            
        except Exception as e:
            print(f"\n[ERROR] Test execution failed: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    tests = WalkInBookingTests()
    tests.run_all_tests()