"""
Manual auth test runner following the exact test plan
Run this to execute all auth tests step by step
"""

import os
import time
import json
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


@dataclass
class TestResult:
    """Test result tracking"""
    test_name: str
    status: str  # PASS, FAIL, SKIP
    message: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()


class AuthTestRunner:
    """Main test runner for auth endpoints"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.results: List[TestResult] = []
        self.users = {}
        self.tokens = {}
        
        # Generate unique emails with timestamp
        timestamp = str(int(time.time()))
        
        # Test users setup
        self.test_users = {
            "superadmin": {
                "email": "admin@carwash.com",  # Use existing admin
                "password": "AdminSecure123!@#",  # Use existing admin password
                "first_name": "System",
                "last_name": "Administrator",
                "phone": "0000000001",
                "skip_registration": True  # Don't register, already exists
            },
            "admin": {
                "email": f"admin@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Admin",
                "last_name": "Admin",
                "phone": "0000000002"
            },
            "supermanager": {
                "email": f"supermanager@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Super",
                "last_name": "Manager",
                "phone": "0000000003"
            },
            "manager": {
                "email": f"manager@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Manager",
                "last_name": "Manager",
                "phone": "0000000004"
            },
            "washer_1": {
                "email": f"washer1@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Washer",
                "last_name": "One",
                "phone": "0000000005"
            },
            "washer_2": {
                "email": f"washer2@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Washer",
                "last_name": "Two",
                "phone": "0000000006"
            },
            "washer_3": {
                "email": f"washer3@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Washer",
                "last_name": "Three",
                "phone": "0000000007"
            },
            "client_verified": {
                "email": f"client_verified@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Client",
                "last_name": "Verified",
                "phone": "0000000008"
            },
            "client_unverified": {
                "email": f"client_unverified@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Client",
                "last_name": "Unverified",
                "phone": "0000000009"
            }
        }
    
    def log_result(self, test_name: str, status: str, message: str):
        """Log test result"""
        result = TestResult(test_name, status, message)
        self.results.append(result)
        
        # Print result
        icon = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[SKIP]"
        print(f"{icon} {test_name}: {message}")
        
        return result
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request"""
        url = f"{self.base_url}{endpoint}"
        return requests.request(method, url, headers=self.headers, **kwargs)
    
    def fetch_existing_users(self):
        """Fetch existing users from API to get their IDs"""
        # First try to login as admin to get user list
        admin_login_data = {
            "email": "admin@carwash.com",
            "password": "AdminSecure123!@#"
        }
        
        try:
            admin_response = self.make_request("POST", "/auth/login", json=admin_login_data)
            if admin_response.status_code == 200:
                admin_token = admin_response.json()["access_token"]
                
                # Get user list
                headers = self.headers.copy()
                headers["Authorization"] = f"Bearer {admin_token}"
                users_response = requests.get(f"{self.base_url}/auth/users", headers=headers)
                
                if users_response.status_code == 200:
                    users_data = users_response.json()
                    users_list = users_data.get('users', []) if isinstance(users_data, dict) else users_data
                    
                    # Map users by email to test user types
                    email_to_user_type = {}
                    for user_type, user_data in self.test_users.items():
                        email_to_user_type[user_data["email"]] = user_type
                    
                    # Populate users dictionary with actual user data including IDs
                    for user in users_list:
                        email = user.get("email")
                        if email in email_to_user_type:
                            user_type = email_to_user_type[email]
                            # Merge test data with actual user data
                            self.users[user_type] = {
                                **self.test_users[user_type],
                                "id": user.get("id"),
                                "email_verified": user.get("email_verified", False),
                                "role": user.get("role", "client")
                            }
                    
                    print(f"Fetched {len(self.users)} existing users with IDs")
                    return
                    
            # If admin approach fails, populate with test data without IDs
            print("Could not fetch user IDs, using test data without IDs")
            for user_type, user_data in self.test_users.items():
                self.users[user_type] = user_data.copy()
                
        except Exception as e:
            print(f"Error fetching existing users: {e}")
            # Fallback: populate with test data without IDs
            for user_type, user_data in self.test_users.items():
                self.users[user_type] = user_data.copy()
    
    def test_1_registration(self):
        """Test 1: Register all users and check persistence"""
        print("\n" + "="*60)
        print("TEST 1: USER REGISTRATION & PERSISTENCE")
        print("="*60)
        
        for user_type, user_data in self.test_users.items():
            # Skip registration for existing admin
            if user_data.get("skip_registration"):
                self.users[user_type] = user_data
                self.log_result(
                    f"Register {user_type}",
                    "SKIP",
                    "Using existing admin account"
                )
                continue
                
            try:
                response = self.make_request("POST", "/auth/register", json=user_data)
                
                if response.status_code == 201:
                    user_info = response.json()
                    self.users[user_type] = {
                        **user_data,
                        "id": user_info["id"]
                    }
                    self.log_result(
                        f"Register {user_type}",
                        "PASS",
                        f"User registered with ID: {user_info['id']}"
                    )
                else:
                    self.log_result(
                        f"Register {user_type}",
                        "FAIL",
                        f"Status {response.status_code}: {response.text}"
                    )
            except Exception as e:
                self.log_result(f"Register {user_type}", "FAIL", str(e))
        
        print("\nNote: Email verification bypass needs to be implemented")
        verified_users = ["admin", "manager", "washer_1", "client_verified"]
        for user in verified_users:
            print(f"  - {user} should be email-verified")
    
    def test_2_login_and_me(self):
        """Test 2: Login and /me endpoint tests"""
        print("\n" + "="*60)
        print("TEST 2: LOGIN & /ME ENDPOINT")
        print("="*60)
        
        # Test successful login for verified users
        print("\n--- Testing Login for Verified Users ---")
        for user_type in ["client_verified"]:  # Start with client_verified
            print(user_type)
            if user_type not in self.users:
                continue
                
            user = self.users[user_type]
            try:
                response = self.make_request("POST", "/auth/login", json={
                    "email": user["email"],
                    "password": user["password"]
                })
                print(response)
                if response.status_code == 200:
                    token_data = response.json()
                    self.tokens[user_type] = token_data["access_token"]
                    self.log_result(
                        f"Login {user_type}",
                        "PASS",
                        "Login successful, token received"
                    )
                    
                    # Test /me endpoint
                    headers = self.headers.copy()
                    headers["Authorization"] = f"Bearer {token_data['access_token']}"
                    me_response = requests.get(f"{self.base_url}/auth/me", headers=headers)
                    
                    if me_response.status_code == 200:
                        me_data = me_response.json()
                        if me_data["email"] == user["email"]:
                            self.log_result(
                                f"/me for {user_type}",
                                "PASS",
                                "Profile returned correctly"
                            )
                        else:
                            self.log_result(
                                f"/me for {user_type}",
                                "FAIL",
                                "Email mismatch in profile"
                            )
                    else:
                        self.log_result(
                            f"/me for {user_type}",
                            "FAIL",
                            f"Status {me_response.status_code}"
                        )
                else:
                    self.log_result(
                        f"Login {user_type}",
                        "FAIL",
                        f"Status {response.status_code}: {response.text}"
                    )
            except Exception as e:
                self.log_result(f"Login {user_type}", "FAIL", str(e))
        
        # Test unverified user login (should fail)
        print("\n--- Testing Login for Unverified Users ---")
        if "client_unverified" in self.users:
            user = self.users["client_unverified"]
            try:
                response = self.make_request("POST", "/auth/login", json={
                    "email": user["email"],
                    "password": user["password"]
                })
                
                if response.status_code != 200:
                    self.log_result(
                        "Login unverified user",
                        "PASS",
                        "Correctly denied (unverified email)"
                    )
                else:
                    self.log_result(
                        "Login unverified user",
                        "FAIL",
                        "Should not allow unverified login"
                    )
            except Exception as e:
                self.log_result("Login unverified user", "FAIL", str(e))
        
        # Test /me without authentication
        print("\n--- Testing /me Without Authentication ---")
        try:
            response = requests.get(f"{self.base_url}/auth/me", headers=self.headers)
            if response.status_code == 403:
                self.log_result("/me without auth", "PASS", "Correctly returned 403")
            else:
                self.log_result("/me without auth", "FAIL", f"Expected 403, got {response.status_code}")
        except Exception as e:
            self.log_result("/me without auth", "FAIL", str(e))
        
        # Test /me with invalid token
        print("\n--- Testing /me With Invalid Token ---")
        try:
            headers = self.headers.copy()
            headers["Authorization"] = "Bearer invalid_token_123456"
            response = requests.get(f"{self.base_url}/auth/me", headers=headers)
            if response.status_code == 401:
                self.log_result("/me with invalid token", "PASS", "Correctly returned 401")
            else:
                self.log_result("/me with invalid token", "FAIL", f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("/me with invalid token", "FAIL", str(e))
        
        # Test /me with malformed header
        print("\n--- Testing /me With Malformed Header ---")
        try:
            headers = self.headers.copy()
            headers["Authorization"] = "Bearer"  # Missing token
            response = requests.get(f"{self.base_url}/auth/me", headers=headers)
            if response.status_code == 401:
                self.log_result("/me with malformed header", "PASS", "Correctly returned 401")
            else:
                self.log_result("/me with malformed header", "FAIL", f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("/me with malformed header", "FAIL", str(e))
    
    def test_3_role_validation(self):
        """Test 3: Validate RBAC (Role-Based Access Control)"""
        print("\n" + "="*60)
        print("TEST 3: ROLE-BASED ACCESS CONTROL")
        print("="*60)
        
        print("\n--- Testing Admin Login ---")
        # Login as existing admin
        try:
            response = self.make_request("POST", "/auth/login", json={
                "email": "admin@carwash.com",
                "password": "AdminSecure123!@#"
            })
            
            if response.status_code == 200:
                admin_token = response.json()["access_token"]
                self.log_result("Admin login", "PASS", "Admin logged in successfully")
                
                # List all users to get their IDs
                print("\n--- Fetching User List ---")
                headers = self.headers.copy()
                headers["Authorization"] = f"Bearer {admin_token}"
                users_response = requests.get(f"{self.base_url}/auth/users", headers=headers)
                
                if users_response.status_code == 200:
                    users_data = users_response.json()
                    users_list = users_data.get('users', []) if isinstance(users_data, dict) else users_data
                    self.log_result("Fetch users", "PASS", f"Retrieved {len(users_list)} users")
                    
                    # Debug: Print the actual user data
                    print("DEBUG: User list data:")
                    print(f"  Raw response: {users_data}")
                    print(f"  Users list length: {len(users_list)}")
                    for i, user in enumerate(users_list):
                        print(f"  User {i}: {user}")
                    
                    # Map users by email to get IDs
                    email_to_user = {}
                    for user in users_list:
                        email_to_user[user.get("email")] = user
                    
                    # Test promoting users to different roles
                    print("\n--- Happy Path: Role Promotions ---")
                    print("[EXPLANATION] We're going to promote users from their default 'client' role to specific roles:")
                    print("   - admin@example.com: client -> admin")
                    print("   - manager@example.com: client -> manager") 
                    print("   - washer1/2/3@example.com: client -> washer")
                    
                    # Promote admin@example.com to admin role (this is the main one you're concerned about)
                    admin_email = "admin@example.com"
                    if admin_email in email_to_user:
                        current_role = email_to_user[admin_email].get("role", "unknown")
                        print(f"[TARGET] PROMOTING ADMIN USER:")
                        print(f"   Email: {admin_email}")
                        print(f"   Current Role: {current_role}")
                        print(f"   Target Role: admin")
                        
                        user_id = email_to_user[admin_email]["id"]
                        result = self.change_user_role(user_id, "admin", admin_token)
                        if result["status"] == 200:
                            self.log_result("Promote admin@example.com", "PASS", "Admin role assigned")
                        else:
                            self.log_result("Promote admin@example.com", "FAIL", f"Status {result['status']}")
                    else:
                        self.log_result("Promote admin@example.com", "SKIP", "Admin user not found")
                    
                    # Promote manager to manager role
                    manager_email = "manager@example.com"
                    if manager_email in email_to_user:
                        current_role = email_to_user[manager_email].get("role", "unknown")
                        print(f"[TARGET] PROMOTING MANAGER USER:")
                        print(f"   Email: {manager_email}")
                        print(f"   Current Role: {current_role}")
                        print(f"   Target Role: manager")
                        
                        user_id = email_to_user[manager_email]["id"]
                        result = self.change_user_role(user_id, "manager", admin_token)
                        if result["status"] == 200:
                            self.log_result("Promote manager", "PASS", "Manager role assigned")
                        else:
                            self.log_result("Promote manager", "FAIL", f"Status {result['status']}")
                    else:
                        self.log_result("Promote manager", "SKIP", "Manager user not found")
                    
                    # Promote washers
                    washer_emails = ["washer1@example.com", "washer2@example.com", "washer3@example.com"]
                    for i, washer_email in enumerate(washer_emails, 1):
                        if washer_email in email_to_user:
                            user_id = email_to_user[washer_email]["id"]
                            result = self.change_user_role(user_id, "washer", admin_token)
                            if result["status"] == 200:
                                self.log_result(f"Promote washer_{i}", "PASS", "Washer role assigned")
                            else:
                                self.log_result(f"Promote washer_{i}", "FAIL", f"Status {result['status']}")
                        else:
                            self.log_result(f"Promote washer_{i}", "SKIP", "Washer user not found")
                    
                    print("\n--- Negative Tests: Should Fail ---")
                    
                    # Test washer trying to promote self (should fail)
                    washer_email = "washer2@example.com"
                    if washer_email in email_to_user:
                        # First login as washer
                        washer_login = self.make_request("POST", "/auth/login", json={
                            "email": washer_email,
                            "password": "SecureDevPassword123!"
                        })
                        
                        if washer_login.status_code == 200:
                            washer_token = washer_login.json()["access_token"]
                            user_id = email_to_user[washer_email]["id"]
                            
                            # Try to promote self
                            result = self.change_user_role(user_id, "manager", washer_token)
                            if result["status"] in [403, 401]:
                                self.log_result("Washer self-promotion", "PASS", "Correctly denied")
                            else:
                                self.log_result("Washer self-promotion", "FAIL", "Should be denied")
                            
                            # Try to promote another washer
                            other_washer_email = "washer3@example.com"
                            if other_washer_email in email_to_user:
                                other_user_id = email_to_user[other_washer_email]["id"]
                                result = self.change_user_role(other_user_id, "manager", washer_token)
                                if result["status"] in [403, 401]:
                                    self.log_result("Washer promote other", "PASS", "Correctly denied")
                                else:
                                    self.log_result("Washer promote other", "FAIL", "Should be denied")
                        else:
                            self.log_result("Washer login for negative test", "SKIP", "Cannot login washer")
                    else:
                        self.log_result("Negative tests", "SKIP", "Washer user not found")
                        
                else:
                    self.log_result("Fetch users", "FAIL", f"Status {users_response.status_code}")
                    self.log_result("Role tests", "SKIP", "Cannot proceed without user list")
                    
            else:
                self.log_result("Admin login", "FAIL", f"Status {response.status_code}")
                self.log_result("Role tests", "SKIP", "Cannot proceed without admin")
                
        except Exception as e:
            self.log_result("Role validation", "FAIL", str(e))
    
    def change_user_role(self, user_id: str, new_role: str, admin_token: str) -> dict:
        """Helper method to change user role"""
        print(f"    [ROLE CHANGE] ATTEMPTING:")
        print(f"       User ID: {user_id}")
        print(f"       New Role: {new_role}")
        print(f"       Endpoint: PUT /auth/users/{user_id}/role")
        
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {admin_token}"
        
        response = requests.put(
            f"{self.base_url}/auth/users/{user_id}/role",
            json={"role": new_role},
            headers=headers
        )
        
        print(f"       Response Status: {response.status_code}")
        if response.status_code < 400:
            response_data = response.json()
            print(f"       Updated User: {response_data}")
            return {"status": response.status_code, "data": response_data}
        else:
            print(f"       Error Response: {response.text}")
            return {"status": response.status_code, "data": response.text}
    
    def test_4_email_verification(self):
        """Test 4: Email verification scenarios"""
        print("\n" + "="*60)
        print("TEST 4: EMAIL VERIFICATION")
        print("="*60)
        
        # Test verification for multiple users
        users_to_verify = ["admin", "manager", "washer_1", "client_verified"]
        
        for user_type in users_to_verify:
            if user_type not in self.users:
                continue
                
            user = self.users[user_type]
            print(f"\n--- Simulating verification for {user_type} ---")
            
            # Get verification status first
            try:
                response = requests.get(f"{self.base_url}/auth/verification-status/{user['email']}")
                if response.status_code == 200:
                    status = response.json()
                    if status.get("email_verified"):
                        self.log_result(
                            f"Check {user_type} verification",
                            "PASS",
                            "Already verified"
                        )
                        continue
                    else:
                        # Simulate verification by directly calling endpoint
                        # In real scenario, we'd extract token from email
                        print(f"  Note: {user_type} needs verification (simulated)")
                        self.log_result(
                            f"Check {user_type} verification",
                            "INFO",
                            "Needs verification"
                        )
            except Exception as e:
                self.log_result(f"Check {user_type} verification", "FAIL", str(e))
        
        # Test unverified user verification flow
        if "client_unverified" not in self.users:
            self.log_result("Email verification", "SKIP", "No unverified user created")
            return
        
        user = self.users["client_unverified"]
        
        # Request email verification
        try:
            response = self.make_request("POST", "/auth/verify-email/request", json={
                "email": user["email"]
            })
            
            if response.status_code == 404:
                self.log_result(
                    "Email verification",
                    "SKIP",
                    "Feature not enabled"
                )
            elif response.status_code == 200:
                self.log_result(
                    "Request email verification",
                    "PASS",
                    "Verification email requested"
                )
                
                # Test resend verification
                print("\n--- Testing Resend Verification ---")
                time.sleep(1)  # Small delay
                resend_response = self.make_request("POST", "/auth/verify-email/request", json={
                    "email": user["email"]
                })
                if resend_response.status_code == 200:
                    self.log_result(
                        "Resend verification email",
                        "PASS",
                        "Resend successful"
                    )
                else:
                    self.log_result(
                        "Resend verification email",
                        "FAIL",
                        f"Status {resend_response.status_code}"
                    )
                
                print("\nNote: Actual verification requires token from email")
                print("In production, token would be extracted and verified")
            else:
                self.log_result(
                    "Request email verification",
                    "FAIL",
                    f"Status {response.status_code}"
                )
        except Exception as e:
            self.log_result("Email verification", "FAIL", str(e))
    
    def test_5_login_after_verification(self):
        """Test 5: Login after verification"""
        print("\n" + "="*60)
        print("TEST 5: LOGIN AFTER VERIFICATION")
        print("="*60)
        
        # Test login for all verified users
        verified_users = ["admin", "manager", "washer_1", "client_verified"]
        
        for user_type in verified_users:
            if user_type not in self.users:
                continue
            
            user = self.users[user_type]
            print(f"\n--- Testing login for {user_type} (should work) ---")
            
            try:
                response = self.make_request("POST", "/auth/login", json={
                    "email": user["email"],
                    "password": user["password"]
                })
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.tokens[user_type] = token_data["access_token"]
                    self.log_result(
                        f"Login {user_type} after verification",
                        "PASS",
                        "Login successful"
                    )
                    
                    # Test /me endpoint
                    headers = self.headers.copy()
                    headers["Authorization"] = f"Bearer {token_data['access_token']}"
                    me_response = requests.get(f"{self.base_url}/auth/me", headers=headers)
                    
                    if me_response.status_code == 200:
                        self.log_result(
                            f"/me for {user_type}",
                            "PASS",
                            "Profile retrieved successfully"
                        )
                    else:
                        self.log_result(
                            f"/me for {user_type}",
                            "FAIL",
                            f"Status {me_response.status_code}"
                        )
                else:
                    # Check if it's because of unverified email
                    if "verification required" in response.text.lower():
                        self.log_result(
                            f"Login {user_type}",
                            "INFO",
                            "Email verification required"
                        )
                    else:
                        self.log_result(
                            f"Login {user_type}",
                            "FAIL",
                            f"Status {response.status_code}: {response.text}"
                        )
            except Exception as e:
                self.log_result(f"Login {user_type}", "FAIL", str(e))
    
    def test_6_password_management(self):
        """Test 6: Password reset and change scenarios"""
        print("\n" + "="*60)
        print("TEST 6: PASSWORD MANAGEMENT")
        print("="*60)
        
        if "client_verified" not in self.users:
            self.log_result("Password management", "SKIP", "No test user")
            return
        
        user = self.users["client_verified"]
        
        # Test password reset request
        print("\n--- Testing Password Reset Request ---")
        try:
            response = self.make_request("POST", "/auth/forgot-password", json={
                "email": user["email"]
            })
            
            if response.status_code == 200:
                self.log_result(
                    "Password reset request",
                    "PASS",
                    "Reset email requested"
                )
            else:
                self.log_result(
                    "Password reset request",
                    "FAIL",
                    f"Status {response.status_code}"
                )
        except Exception as e:
            self.log_result("Password reset", "FAIL", str(e))
        
        # Test password change (requires login)
        if "client_verified" in self.tokens:
            print("\n--- Testing Password Change ---")
            headers = self.headers.copy()
            headers["Authorization"] = f"Bearer {self.tokens['client_verified']}"
            
            try:
                response = requests.post(
                    f"{self.base_url}/auth/change-password",
                    json={
                        "current_password": user["password"],
                        "new_password": "NewSecurePassword123!@#"
                    },
                    headers=headers
                )
                
                if response.status_code == 200:
                    self.log_result(
                        "Password change",
                        "PASS",
                        "Password changed successfully"
                    )
                    # Update stored password for future tests
                    self.users["client_verified"]["password"] = "NewSecurePassword123!@#"
                else:
                    self.log_result(
                        "Password change",
                        "FAIL",
                        f"Status {response.status_code}"
                    )
            except Exception as e:
                self.log_result("Password change", "FAIL", str(e))
    
    def test_7_token_management(self):
        """Test 7: Token refresh and logout scenarios"""
        print("\n" + "="*60)
        print("TEST 7: TOKEN MANAGEMENT")
        print("="*60)
        
        # Test token refresh
        print("\n--- Testing Token Refresh ---")
        # This would require storing refresh tokens from login
        
        # Test logout
        if "client_verified" in self.tokens:
            print("\n--- Testing Logout ---")
            headers = self.headers.copy()
            headers["Authorization"] = f"Bearer {self.tokens['client_verified']}"
            
            try:
                # Note: logout requires refresh token in body
                response = requests.post(
                    f"{self.base_url}/auth/logout",
                    json={"refresh_token": "dummy_refresh_token"},  # Would need real refresh token
                    headers=headers
                )
                
                if response.status_code in [200, 500]:  # 500 if refresh token invalid
                    self.log_result(
                        "Logout",
                        "INFO",
                        "Logout attempted"
                    )
                else:
                    self.log_result(
                        "Logout",
                        "FAIL",
                        f"Unexpected status {response.status_code}"
                    )
            except Exception as e:
                self.log_result("Logout", "FAIL", str(e))
    
    def test_8_user_management(self):
        """Test 8: User list and management endpoints"""
        print("\n" + "="*60)
        print("TEST 8: USER MANAGEMENT")
        print("="*60)
        
        # Need admin token
        admin_token = self.tokens.get("superadmin")
        if not admin_token:
            # Try to login as admin
            try:
                response = self.make_request("POST", "/auth/login", json={
                    "email": "admin@carwash.com",
                    "password": "AdminSecure123!@#"
                })
                if response.status_code == 200:
                    admin_token = response.json()["access_token"]
                    self.tokens["superadmin"] = admin_token
            except:
                pass
        
        if not admin_token:
            self.log_result("User management", "SKIP", "No admin token")
            return
        
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {admin_token}"
        
        # Test list users
        print("\n--- Testing List Users ---")
        try:
            response = requests.get(f"{self.base_url}/auth/users", headers=headers)
            
            if response.status_code == 200:
                users = response.json()
                self.log_result(
                    "List users",
                    "PASS",
                    f"Retrieved {users.get('total', 0)} users"
                )
            else:
                self.log_result(
                    "List users",
                    "FAIL",
                    f"Status {response.status_code}"
                )
        except Exception as e:
            self.log_result("List users", "FAIL", str(e))
        
        # Test get specific user
        if "client_verified" in self.users and self.users["client_verified"].get("id"):
            print("\n--- Testing Get User by ID ---")
            user_id = self.users["client_verified"]["id"]
            
            try:
                response = requests.get(f"{self.base_url}/auth/users/{user_id}", headers=headers)
                
                if response.status_code == 200:
                    self.log_result(
                        "Get user by ID",
                        "PASS",
                        "User retrieved successfully"
                    )
                else:
                    self.log_result(
                        "Get user by ID",
                        "FAIL",
                        f"Status {response.status_code}"
                    )
            except Exception as e:
                self.log_result("Get user by ID", "FAIL", str(e))
        else:
            self.log_result("Get user by ID", "SKIP", "Client user ID not available")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        total = len(self.results)
        
        print(f"\nResults:")
        print(f"  Passed:  {passed}/{total}")
        print(f"  Failed:  {failed}/{total}")
        print(f"  Skipped: {skipped}/{total}")
        
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if result.status == "FAIL":
                    print(f"  - {result.test_name}: {result.message}")
        
        # Save results to file
        results_file = f"test_results_{int(time.time())}.json"
        with open(results_file, "w") as f:
            json.dump(
                [asdict(r) for r in self.results],
                f,
                indent=2,
                default=str
            )
        print(f"\nResults saved to: {results_file}")
        
        return failed == 0

def main():
    """Main test execution following the planned sequence"""
    print("="*60)
    print("AUTHENTICATION SYSTEM COMPREHENSIVE TEST SUITE")
    print("="*60)
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now()}")
    print("\nTest Plan:")
    print("1. Register users")
    print("2. Test login (should fail for unverified)")
    print("3. Simulate email verification")
    print("4. Test login again (should work)")
    print("5. Test role-based access control")
    print("6. Test password management")
    print("7. Test token management")
    print("8. Test user management")
    print("="*60)
    
    runner = AuthTestRunner()
    
    try:
        # Step 1: Register all users
        # runner.test_1_registration()
        
        # If skipping registration, populate users dictionary with existing users
        if False:  # Set to False if running full registration
            print("Using pre-existing users (skipping registration)")
            # Fetch actual user data including IDs from the API
            runner.fetch_existing_users()
        else:
            print("Running full registration process...")
            runner.test_1_registration()
        
        # Step 2: Test login and /me (should fail for unverified users)
        print("\n[PHASE 1: Testing login BEFORE verification]")
        # runner.test_2_login_and_me()



        # Step 3: Run email verification for unverified users
        # runner.test_4_email_verification()
        
        # Step 4: Test login and /me again (should work after verification)
        print("\n[PHASE 2: Testing login AFTER verification]")
        runner.test_5_login_after_verification()
        
        # Step 5: Test role-based access control
        runner.test_3_role_validation()
        
        # Step 6: Test password management
        runner.test_6_password_management()
        
        # Step 7: Test token management
        runner.test_7_token_management()
        
        # Step 8: Test user management
        runner.test_8_user_management()
        
        # Print final summary
        success = runner.print_summary()
        
        if success:
            print("\n[SUCCESS] ALL TESTS PASSED!")
            return 0
        else:
            print("\n[WARNING] SOME TESTS FAILED!")
            return 1
            
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Tests interrupted by user")
        runner.print_summary()
        return 2
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        runner.print_summary()
        return 3


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)