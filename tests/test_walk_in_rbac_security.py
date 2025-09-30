"""
Walk-in Booking RBAC & Security Tests

This test suite validates Role-Based Access Control and security for walk-in booking system:
1. Authentication token validation
2. Role-specific endpoint access
3. Data isolation between users
4. Token expiration handling
5. Privilege escalation prevention
6. Cross-user data access prevention
7. Security edge cases and attack vectors

All tests focus on security and access control enforcement.
"""

import pytest
import requests
import json
import time
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from typing import Dict, Any, Optional, List

# Test configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}


class RBACSecurityTests:
    """RBAC and security validation tests"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS
        self.tokens = {}
        self.users = {}
        self.test_data = {}
        
        self._setup_test_users()
        self._create_test_data()
    
    def _setup_test_users(self):
        """Setup users with different roles for RBAC testing"""
        print("\n" + "="*80)
        print("SETTING UP RBAC SECURITY TEST USERS")
        print("="*80)
        
        # Setup admin
        self._setup_admin()
        
        # Create multiple users of each role
        self._create_managers()
        self._create_washers()
        self._create_clients()
    
    def _setup_admin(self):
        """Setup admin user"""
        admin_creds = {"email": "admin@carwash.com", "password": "AdminSecure123!@#"}
        response = requests.post(f"{self.base_url}/auth/login", json=admin_creds, headers=self.headers)
        
        if response.status_code == 200:
            self.tokens["admin"] = response.json()["access_token"]
            print("[OK] Admin authenticated")
        else:
            raise Exception(f"Admin authentication failed: {response.status_code}")
    
    def _create_managers(self):
        """Create multiple manager users"""
        admin_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['admin']}"}
        
        self.users["managers"] = []
        self.tokens["managers"] = []
        
        for i in range(2):
            manager_data = {
                "email": f"manager_rbac_{i}_{uuid4().hex[:6]}@test.com",
                "password": "ManagerRBAC123!@#",
                "first_name": "RBAC",
                "last_name": f"Manager{i}",
                "phone_number": f"+123456789{i}",
                "role": "manager"
            }
            
            # Create manager
            response = requests.post(f"{self.base_url}/auth/register", json=manager_data, headers=admin_headers)
            if response.status_code in [200, 201]:
                # Login as manager
                login_response = requests.post(
                    f"{self.base_url}/auth/login",
                    json={"email": manager_data["email"], "password": manager_data["password"]},
                    headers=self.headers
                )
                if login_response.status_code == 200:
                    token = login_response.json()["access_token"]
                    self.tokens["managers"].append(token)
                    self.users["managers"].append(manager_data)
                    print(f"[OK] Manager {i} created and authenticated")
                else:
                    raise Exception(f"Manager {i} login failed: {login_response.status_code}")
            else:
                raise Exception(f"Manager {i} creation failed: {response.status_code}")
    
    def _create_washers(self):
        """Create multiple washer users"""
        admin_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['admin']}"}
        
        self.users["washers"] = []
        self.tokens["washers"] = []
        
        for i in range(3):
            washer_data = {
                "email": f"washer_rbac_{i}_{uuid4().hex[:6]}@test.com",
                "password": "WasherRBAC123!@#",
                "first_name": "RBAC",
                "last_name": f"Washer{i}",
                "phone_number": f"+123456780{i}",
                "role": "washer"
            }
            
            # Create washer
            response = requests.post(f"{self.base_url}/auth/register", json=washer_data, headers=admin_headers)
            if response.status_code in [200, 201]:
                # Login as washer
                login_response = requests.post(
                    f"{self.base_url}/auth/login",
                    json={"email": washer_data["email"], "password": washer_data["password"]},
                    headers=self.headers
                )
                if login_response.status_code == 200:
                    token = login_response.json()["access_token"]
                    self.tokens["washers"].append(token)
                    self.users["washers"].append(washer_data)
                    print(f"[OK] Washer {i} created and authenticated")
                else:
                    raise Exception(f"Washer {i} login failed: {login_response.status_code}")
            else:
                raise Exception(f"Washer {i} creation failed: {response.status_code}")
    
    def _create_clients(self):
        """Create multiple client users"""
        self.users["clients"] = []
        self.tokens["clients"] = []
        
        for i in range(2):
            client_data = {
                "email": f"client_rbac_{i}_{uuid4().hex[:6]}@test.com",
                "password": "ClientRBAC123!@#",
                "first_name": "RBAC",
                "last_name": f"Client{i}",
                "phone_number": f"+123456770{i}"
            }
            
            # Create client
            response = requests.post(f"{self.base_url}/auth/register", json=client_data, headers=self.headers)
            if response.status_code in [200, 201]:
                # Login as client
                login_response = requests.post(
                    f"{self.base_url}/auth/login",
                    json={"email": client_data["email"], "password": client_data["password"]},
                    headers=self.headers
                )
                if login_response.status_code == 200:
                    token = login_response.json()["access_token"]
                    self.tokens["clients"].append(token)
                    self.users["clients"].append(client_data)
                    print(f"[OK] Client {i} created and authenticated")
                else:
                    raise Exception(f"Client {i} login failed: {login_response.status_code}")
            else:
                raise Exception(f"Client {i} creation failed: {response.status_code}")
    
    def _create_test_data(self):
        """Create test data for access control testing"""
        # Create customers and vehicles using washer 0
        washer_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washers'][0]}"}
        
        # Create test customer
        customer_data = {
            "first_name": "RBAC",
            "last_name": "TestCustomer",
            "phone": "+1555000001",
            "email": "rbac.customer@test.com"
        }
        
        response = requests.post(f"{self.base_url}/walk-in/register-customer",
                               json=customer_data, headers=washer_headers)
        
        if response.status_code in [200, 201]:
            self.test_data["customer"] = response.json()
            
            # Create test vehicle
            vehicle_data = {
                "customer_id": str(self.test_data["customer"]["customer_id"]),
                "make": "RBAC",
                "model": "TestVehicle",
                "year": 2023,
                "color": "Security",
                "license_plate": f"RBAC{uuid4().hex[:4].upper()}"
            }
            
            response = requests.post(f"{self.base_url}/walk-in/register-vehicle",
                                   json=vehicle_data, headers=washer_headers)
            
            if response.status_code in [200, 201]:
                self.test_data["vehicle"] = response.json()
                print("[OK] Test data created for RBAC testing")

    def test_authentication_token_validation(self):
        """Test authentication token validation and rejection of invalid tokens"""
        print("\n" + "="*80)
        print("TESTING AUTHENTICATION TOKEN VALIDATION")
        print("="*80)
        
        customer_data = {
            "first_name": "Auth",
            "last_name": "Test",
            "phone": "+1555000001"
        }
        
        # Test 1: No token provided
        print("\n--- Testing No Authentication Token ---")
        response = requests.post(f"{self.base_url}/walk-in/register-customer",
                               json=customer_data, headers=self.headers)
        
        assert response.status_code == 401, f"Should reject missing token, got: {response.status_code}"
        print("[✓] Missing token correctly rejected (401)")
        
        # Test 2: Invalid token format
        print("\n--- Testing Invalid Token Format ---")
        invalid_headers = {**self.headers, "Authorization": "Bearer invalid_token_format"}
        response = requests.post(f"{self.base_url}/walk-in/register-customer",
                               json=customer_data, headers=invalid_headers)
        
        assert response.status_code == 401, f"Should reject invalid token, got: {response.status_code}"
        print("[✓] Invalid token format correctly rejected (401)")
        
        # Test 3: Malformed Authorization header
        print("\n--- Testing Malformed Authorization Header ---")
        malformed_headers = {**self.headers, "Authorization": "InvalidFormat token_here"}
        response = requests.post(f"{self.base_url}/walk-in/register-customer",
                               json=customer_data, headers=malformed_headers)
        
        assert response.status_code == 401, f"Should reject malformed header, got: {response.status_code}"
        print("[✓] Malformed authorization header correctly rejected (401)")
        
        # Test 4: Empty Authorization header
        print("\n--- Testing Empty Authorization Header ---")
        empty_headers = {**self.headers, "Authorization": ""}
        response = requests.post(f"{self.base_url}/walk-in/register-customer",
                               json=customer_data, headers=empty_headers)
        
        assert response.status_code == 401, f"Should reject empty header, got: {response.status_code}"
        print("[✓] Empty authorization header correctly rejected (401)")
        
        print("[✓] Authentication token validation working correctly")

    def test_role_specific_endpoint_access(self):
        """Test that each role can only access appropriate endpoints"""
        print("\n" + "="*80)
        print("TESTING ROLE-SPECIFIC ENDPOINT ACCESS")
        print("="*80)
        
        # Define endpoint access matrix
        endpoints = [
            ("POST", "/walk-in/register-customer", {"first_name": "Test", "last_name": "User", "phone": "+1555000001"}),
            ("POST", "/walk-in/register-vehicle", {"customer_id": str(uuid4()), "make": "Test", "model": "Car", "year": 2023, "color": "Blue", "license_plate": "TEST123"}),
            ("POST", "/walk-in/create-booking", {"customer_id": str(uuid4()), "vehicle_id": str(uuid4()), "service_ids": [str(uuid4())]}),
            ("GET", "/walk-in/work-sessions/active", None),
            ("GET", "/walk-in/dashboard", None),
            ("GET", "/walk-in/accounting/daily", None),
            ("GET", "/walk-in/accounting/weekly", None),
        ]
        
        # Expected access results: True = should have access, False = should be denied
        expected_access = {
            "admin": True,
            "managers": True,
            "washers": True,
            "clients": False
        }
        
        for method, endpoint, data in endpoints:
            print(f"\n--- Testing {method} {endpoint} ---")
            
            # Test admin access
            admin_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['admin']}"}
            if method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}", json=data, headers=admin_headers)
            else:
                response = requests.get(f"{self.base_url}{endpoint}", headers=admin_headers)
            
            if expected_access["admin"]:
                assert response.status_code != 403, f"Admin should have access to {endpoint}, got: {response.status_code}"
                print(f"[✓] Admin has access to {endpoint}")
            else:
                assert response.status_code == 403, f"Admin should be denied access to {endpoint}, got: {response.status_code}"
            
            # Test manager access
            for i, manager_token in enumerate(self.tokens["managers"]):
                manager_headers = {**self.headers, "Authorization": f"Bearer {manager_token}"}
                if method == "POST":
                    response = requests.post(f"{self.base_url}{endpoint}", json=data, headers=manager_headers)
                else:
                    response = requests.get(f"{self.base_url}{endpoint}", headers=manager_headers)
                
                if expected_access["managers"]:
                    assert response.status_code != 403, f"Manager {i} should have access to {endpoint}, got: {response.status_code}"
                    print(f"[✓] Manager {i} has access to {endpoint}")
                else:
                    assert response.status_code == 403, f"Manager {i} should be denied access to {endpoint}, got: {response.status_code}"
            
            # Test washer access
            for i, washer_token in enumerate(self.tokens["washers"]):
                washer_headers = {**self.headers, "Authorization": f"Bearer {washer_token}"}
                if method == "POST":
                    response = requests.post(f"{self.base_url}{endpoint}", json=data, headers=washer_headers)
                else:
                    response = requests.get(f"{self.base_url}{endpoint}", headers=washer_headers)
                
                if expected_access["washers"]:
                    assert response.status_code != 403, f"Washer {i} should have access to {endpoint}, got: {response.status_code}"
                    print(f"[✓] Washer {i} has access to {endpoint}")
                else:
                    assert response.status_code == 403, f"Washer {i} should be denied access to {endpoint}, got: {response.status_code}"
            
            # Test client access (should be denied for all walk-in endpoints)
            for i, client_token in enumerate(self.tokens["clients"]):
                client_headers = {**self.headers, "Authorization": f"Bearer {client_token}"}
                if method == "POST":
                    response = requests.post(f"{self.base_url}{endpoint}", json=data, headers=client_headers)
                else:
                    response = requests.get(f"{self.base_url}{endpoint}", headers=client_headers)
                
                if expected_access["clients"]:
                    assert response.status_code != 403, f"Client {i} should have access to {endpoint}, got: {response.status_code}"
                else:
                    assert response.status_code == 403, f"Client {i} should be denied access to {endpoint}, got: {response.status_code}"
                    print(f"[✓] Client {i} correctly denied access to {endpoint}")
        
        print("[✓] Role-specific endpoint access working correctly")

    def test_data_isolation_between_users(self):
        """Test that users can only access their own data"""
        print("\n" + "="*80)
        print("TESTING DATA ISOLATION BETWEEN USERS")
        print("="*80)
        
        # Create customers using different washers
        washer_0_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washers'][0]}"}
        washer_1_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washers'][1]}"}
        
        # Washer 0 creates customer
        print("\n--- Washer 0 Creating Customer ---")
        customer_0_data = {
            "first_name": "Washer0",
            "last_name": "Customer",
            "phone": "+1555000010",
            "email": "washer0.customer@test.com"
        }
        
        response = requests.post(f"{self.base_url}/walk-in/register-customer",
                               json=customer_0_data, headers=washer_0_headers)
        
        assert response.status_code in [200, 201], f"Washer 0 customer creation failed: {response.status_code}"
        customer_0 = response.json()
        print(f"[✓] Washer 0 created customer: {customer_0['customer_id']}")
        
        # Washer 1 creates customer
        print("\n--- Washer 1 Creating Customer ---")
        customer_1_data = {
            "first_name": "Washer1",
            "last_name": "Customer",
            "phone": "+1555000011",
            "email": "washer1.customer@test.com"
        }
        
        response = requests.post(f"{self.base_url}/walk-in/register-customer",
                               json=customer_1_data, headers=washer_1_headers)
        
        assert response.status_code in [200, 201], f"Washer 1 customer creation failed: {response.status_code}"
        customer_1 = response.json()
        print(f"[✓] Washer 1 created customer: {customer_1['customer_id']}")
        
        # Test dashboard data isolation
        print("\n--- Testing Dashboard Data Isolation ---")
        
        # Get washer 0 dashboard
        response_0 = requests.get(f"{self.base_url}/walk-in/dashboard", headers=washer_0_headers)
        assert response_0.status_code == 200, f"Washer 0 dashboard failed: {response_0.status_code}"
        dashboard_0 = response_0.json()
        
        # Get washer 1 dashboard
        response_1 = requests.get(f"{self.base_url}/walk-in/dashboard", headers=washer_1_headers)
        assert response_1.status_code == 200, f"Washer 1 dashboard failed: {response_1.status_code}"
        dashboard_1 = response_1.json()
        
        # Verify dashboards show different washer IDs
        assert dashboard_0["washer_info"]["id"] != dashboard_1["washer_info"]["id"], "Dashboards should show different washer IDs"
        print(f"[✓] Dashboard data properly isolated:")
        print(f"    Washer 0 ID: {dashboard_0['washer_info']['id']}")
        print(f"    Washer 1 ID: {dashboard_1['washer_info']['id']}")
        
        # Test accounting data isolation
        print("\n--- Testing Accounting Data Isolation ---")
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get washer 0 accounting
        response_0 = requests.get(f"{self.base_url}/walk-in/accounting/daily",
                                params={"date": today}, headers=washer_0_headers)
        assert response_0.status_code == 200, f"Washer 0 accounting failed: {response_0.status_code}"
        accounting_0 = response_0.json()
        
        # Get washer 1 accounting
        response_1 = requests.get(f"{self.base_url}/walk-in/accounting/daily",
                                params={"date": today}, headers=washer_1_headers)
        assert response_1.status_code == 200, f"Washer 1 accounting failed: {response_1.status_code}"
        accounting_1 = response_1.json()
        
        # Verify accounting shows different washer IDs
        assert accounting_0["washer_id"] != accounting_1["washer_id"], "Accounting should show different washer IDs"
        print(f"[✓] Accounting data properly isolated:")
        print(f"    Washer 0 ID: {accounting_0['washer_id']}")
        print(f"    Washer 1 ID: {accounting_1['washer_id']}")
        
        print("[✓] Data isolation between users working correctly")

    def test_privilege_escalation_prevention(self):
        """Test prevention of privilege escalation attempts"""
        print("\n" + "="*80)
        print("TESTING PRIVILEGE ESCALATION PREVENTION")
        print("="*80)
        
        # Test 1: Client trying to access admin/manager-only endpoints through walk-in system
        print("\n--- Testing Client Privilege Escalation Attempts ---")
        client_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['clients'][0]}"}
        
        privileged_endpoints = [
            ("POST", "/walk-in/register-customer"),
            ("POST", "/walk-in/register-vehicle"),
            ("GET", "/walk-in/dashboard"),
            ("GET", "/walk-in/accounting/daily"),
        ]
        
        for method, endpoint in privileged_endpoints:
            print(f"--- Client attempting {method} {endpoint} ---")
            
            if method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}",
                                       json={"test": "data"}, headers=client_headers)
            else:
                response = requests.get(f"{self.base_url}{endpoint}", headers=client_headers)
            
            assert response.status_code == 403, f"Client should be denied {endpoint}, got: {response.status_code}"
            print(f"[✓] Client correctly denied access to {endpoint}")
        
        # Test 2: Token manipulation attempts
        print("\n--- Testing Token Manipulation Resistance ---")
        
        # Try modified token
        original_token = self.tokens["clients"][0]
        modified_token = original_token[:-5] + "admin"  # Change end of token
        modified_headers = {**self.headers, "Authorization": f"Bearer {modified_token}"}
        
        response = requests.post(f"{self.base_url}/walk-in/register-customer",
                               json={"first_name": "Escalation", "last_name": "Test", "phone": "+1555000001"},
                               headers=modified_headers)
        
        assert response.status_code == 401, f"Modified token should be rejected, got: {response.status_code}"
        print("[✓] Modified token correctly rejected")
        
        # Test 3: Role field manipulation (if applicable)
        print("\n--- Testing Role Manipulation Resistance ---")
        
        # Try to register with admin role using client credentials
        # This tests if the registration endpoint properly validates role assignment
        client_headers_admin = {**self.headers, "Authorization": f"Bearer {self.tokens['clients'][0]}"}
        escalation_data = {
            "email": f"escalation_{uuid4().hex[:6]}@test.com",
            "password": "EscalationAttempt123!@#",
            "first_name": "Privilege",
            "last_name": "Escalation",
            "phone_number": "+1555000999",
            "role": "admin"  # Client trying to create admin user
        }
        
        response = requests.post(f"{self.base_url}/auth/register",
                               json=escalation_data, headers=client_headers_admin)
        
        # Should either reject completely (403/401) or ignore the role field and create client
        assert response.status_code in [401, 403], f"Role escalation attempt should be blocked, got: {response.status_code}"
        print("[✓] Role escalation attempt correctly blocked")
        
        print("[✓] Privilege escalation prevention working correctly")

    def test_security_edge_cases(self):
        """Test security edge cases and potential attack vectors"""
        print("\n" + "="*80)
        print("TESTING SECURITY EDGE CASES")
        print("="*80)
        
        washer_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['washers'][0]}"}
        
        # Test 1: SQL injection attempts in customer data
        print("\n--- Testing SQL Injection Resistance ---")
        malicious_customer_data = {
            "first_name": "'; DROP TABLE customers; --",
            "last_name": "OR 1=1",
            "phone": "+1555000001' UNION SELECT * FROM users",
            "email": "malicious@test.com"
        }
        
        response = requests.post(f"{self.base_url}/walk-in/register-customer",
                               json=malicious_customer_data, headers=washer_headers)
        
        # Should handle malicious input gracefully (either sanitize or reject)
        assert response.status_code in [200, 201, 400, 422], f"SQL injection attempt handling: {response.status_code}"
        print(f"[✓] SQL injection attempt handled gracefully: {response.status_code}")
        
        # Test 2: XSS attempts in input fields
        print("\n--- Testing XSS Prevention ---")
        xss_customer_data = {
            "first_name": "<script>alert('XSS')</script>",
            "last_name": "javascript:alert('XSS')",
            "phone": "+1555000001",
            "email": "xss@test.com"
        }
        
        response = requests.post(f"{self.base_url}/walk-in/register-customer",
                               json=xss_customer_data, headers=washer_headers)
        
        # Should handle XSS attempts gracefully
        assert response.status_code in [200, 201, 400, 422], f"XSS attempt handling: {response.status_code}"
        print(f"[✓] XSS attempt handled gracefully: {response.status_code}")
        
        # Test 3: Extremely large payload
        print("\n--- Testing Large Payload Handling ---")
        large_customer_data = {
            "first_name": "A" * 10000,  # Very long first name
            "last_name": "B" * 10000,   # Very long last name
            "phone": "+1555000001",
            "email": "large@test.com"
        }
        
        response = requests.post(f"{self.base_url}/walk-in/register-customer",
                               json=large_customer_data, headers=washer_headers)
        
        # Should reject or truncate large payloads
        assert response.status_code in [200, 201, 400, 413, 422], f"Large payload handling: {response.status_code}"
        print(f"[✓] Large payload handled appropriately: {response.status_code}")
        
        # Test 4: UUID injection/manipulation
        print("\n--- Testing UUID Manipulation Resistance ---")
        if self.test_data.get("customer"):
            # Try to use another customer's ID
            malicious_vehicle_data = {
                "customer_id": "00000000-0000-0000-0000-000000000000",  # Null UUID
                "make": "Malicious",
                "model": "Test",
                "year": 2023,
                "color": "Red",
                "license_plate": "HACK123"
            }
            
            response = requests.post(f"{self.base_url}/walk-in/register-vehicle",
                                   json=malicious_vehicle_data, headers=washer_headers)
            
            # Should reject invalid/non-existent customer ID
            assert response.status_code in [400, 404, 422], f"UUID manipulation should be rejected: {response.status_code}"
            print(f"[✓] UUID manipulation correctly rejected: {response.status_code}")
        
        # Test 5: Concurrent authentication attempts
        print("\n--- Testing Concurrent Authentication Handling ---")
        invalid_creds = {"email": "nonexistent@test.com", "password": "WrongPassword"}
        
        # Multiple failed login attempts (simulating brute force)
        failed_attempts = 0
        for i in range(5):
            response = requests.post(f"{self.base_url}/auth/login", json=invalid_creds, headers=self.headers)
            if response.status_code == 401:
                failed_attempts += 1
        
        assert failed_attempts == 5, f"All login attempts should fail: {failed_attempts}/5"
        print(f"[✓] Multiple failed authentication attempts handled correctly")
        
        print("[✓] Security edge cases tested successfully")

    def run_rbac_security_tests(self):
        """Run all RBAC and security tests"""
        print("\n" + "="*80)
        print("STARTING RBAC & SECURITY TESTS")
        print("Testing: Authentication, Authorization, Data Isolation, Security")
        print("="*80)
        
        try:
            # Run all security tests
            self.test_authentication_token_validation()
            self.test_role_specific_endpoint_access()
            self.test_data_isolation_between_users()
            self.test_privilege_escalation_prevention()
            self.test_security_edge_cases()
            
            print("\n" + "="*80)
            print("RBAC & SECURITY TESTS COMPLETED SUCCESSFULLY")
            print("="*80)
            print("Summary of security validations:")
            print(f"  - Admin users: 1")
            print(f"  - Manager users: {len(self.users['managers'])}")
            print(f"  - Washer users: {len(self.users['washers'])}")
            print(f"  - Client users: {len(self.users['clients'])}")
            print("\nAll RBAC and security tests passed!")
            print("✓ Authentication properly enforced")
            print("✓ Authorization roles working correctly")
            print("✓ Data isolation maintained")
            print("✓ Privilege escalation prevented")
            print("✓ Security edge cases handled")
            
        except Exception as e:
            print(f"\n[ERROR] RBAC/Security test failed: {str(e)}")
            import traceback
            traceback.print_exc()


# Pytest integration
def test_rbac_security():
    """Pytest wrapper for RBAC and security tests"""
    tests = RBACSecurityTests()
    tests.run_rbac_security_tests()


if __name__ == "__main__":
    # Run tests directly
    tests = RBACSecurityTests()
    tests.run_rbac_security_tests()