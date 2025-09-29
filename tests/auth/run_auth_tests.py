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
                "email": f"admin_{timestamp}@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Admin",
                "last_name": "Admin",
                "phone": "0000000002"
            },
            "supermanager": {
                "email": f"supermanager_{timestamp}@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Super",
                "last_name": "Manager",
                "phone": "0000000003"
            },
            "manager": {
                "email": f"manager_{timestamp}@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Manager",
                "last_name": "Manager",
                "phone": "0000000004"
            },
            "washer_1": {
                "email": f"washer1_{timestamp}@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Washer",
                "last_name": "One",
                "phone": "0000000005"
            },
            "washer_2": {
                "email": f"washer2_{timestamp}@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Washer",
                "last_name": "Two",
                "phone": "0000000006"
            },
            "washer_3": {
                "email": f"washer3_{timestamp}@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Washer",
                "last_name": "Three",
                "phone": "0000000007"
            },
            "client_verified": {
                "email": f"client_verified_{timestamp}@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Client",
                "last_name": "Verified",
                "phone": "0000000008"
            },
            "client_unverified": {
                "email": f"client_unverified_{timestamp}@example.com",
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
                
                # Test promoting users to different roles
                print("\n--- Happy Path: Role Promotions ---")
                
                # Promote manager to manager role
                if "manager" in self.users:
                    result = self.change_user_role(
                        self.users["manager"]["id"],
                        "manager",
                        admin_token
                    )
                    if result["status"] == 200:
                        self.log_result("Promote manager", "PASS", "Manager role assigned")
                    else:
                        self.log_result("Promote manager", "FAIL", f"Status {result['status']}")
                
                # Promote washers
                for washer in ["washer_1", "washer_2", "washer_3"]:
                    if washer in self.users:
                        result = self.change_user_role(
                            self.users[washer]["id"],
                            "washer",
                            admin_token
                        )
                        if result["status"] == 200:
                            self.log_result(f"Promote {washer}", "PASS", "Washer role assigned")
                        else:
                            self.log_result(f"Promote {washer}", "FAIL", f"Status {result['status']}")
                
                print("\n--- Negative Tests: Should Fail ---")
                
                # Test washer trying to promote self (should fail)
                if "washer_2" in self.users:
                    # First login as washer
                    washer_login = self.make_request("POST", "/auth/login", json={
                        "email": self.users["washer_2"]["email"],
                        "password": self.users["washer_2"]["password"]
                    })
                    
                    if washer_login.status_code == 200:
                        washer_token = washer_login.json()["access_token"]
                        
                        # Try to promote self
                        result = self.change_user_role(
                            self.users["washer_2"]["id"],
                            "manager",
                            washer_token
                        )
                        if result["status"] in [403, 401]:
                            self.log_result("Washer self-promotion", "PASS", "Correctly denied")
                        else:
                            self.log_result("Washer self-promotion", "FAIL", "Should be denied")
                        
                        # Try to promote another washer
                        if "washer_3" in self.users:
                            result = self.change_user_role(
                                self.users["washer_3"]["id"],
                                "manager",
                                washer_token
                            )
                            if result["status"] in [403, 401]:
                                self.log_result("Washer promote other", "PASS", "Correctly denied")
                            else:
                                self.log_result("Washer promote other", "FAIL", "Should be denied")
            else:
                self.log_result("Admin login", "FAIL", f"Status {response.status_code}")
                self.log_result("Role tests", "SKIP", "Cannot proceed without admin")
                
        except Exception as e:
            self.log_result("Role validation", "FAIL", str(e))
    
    def change_user_role(self, user_id: str, new_role: str, admin_token: str) -> dict:
        """Helper method to change user role"""
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {admin_token}"
        
        response = requests.put(
            f"{self.base_url}/auth/users/{user_id}/role",
            json={"role": new_role},
            headers=headers
        )
        return {"status": response.status_code, "data": response.json() if response.status_code < 400 else response.text}
    
    def test_4_email_verification(self):
        """Test 4: Email verification scenarios"""
        print("\n" + "="*60)
        print("TEST 4: EMAIL VERIFICATION")
        print("="*60)
        
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
                
                # Note: Actual verification would need the token from email
                print("\nNote: Email verification confirmation requires token from email")
            else:
                self.log_result(
                    "Request email verification",
                    "FAIL",
                    f"Status {response.status_code}"
                )
        except Exception as e:
            self.log_result("Email verification", "FAIL", str(e))
    
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
    """Main test execution"""
    print("Starting Auth Endpoint Tests")
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now()}")
    
    runner = AuthTestRunner()
    
    try:
        # Run all test suites
        # runner.test_1_registration()
        runner.test_2_login_and_me()
        # runner.test_3_role_validation()
        # runner.test_4_email_verification()
        #
        # # Print summary
        # success = runner.print_summary()
        
        # if success:

        #     print("\nALL TESTS PASSED!")
        #     return 0
        # else:
        #     print("\nSOME TESTS FAILED!")
        #     return 1
            
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        runner.print_summary()
        return 2
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        runner.print_summary()
        return 3


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)