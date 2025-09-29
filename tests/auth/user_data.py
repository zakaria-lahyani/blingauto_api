import os
import time
import json
import requests

BASE_URL = "http://localhost:8000"

test_users = {
            "superadmin": {
                "email": "admin@carwash.com",  # Use existing admin
                "password": "AdminSecure123!@#",  # Use existing admin password
                "first_name": "System",
                "last_name": "Administrator",
                "phone": "0000000001",
                "skip_registration": True  # Don't register, already exists
            },
            "admin": {
                "email": f"admin_1@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Admin",
                "last_name": "Admin",
                "phone": "0000000002"
            },
            "supermanager": {
                "email": f"supermanager_1@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Super",
                "last_name": "Manager",
                "phone": "0000000003"
            },
            "manager": {
                "email": f"manager_2@example.com",
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
                "email": f"washer2_@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Washer",
                "last_name": "Two",
                "phone": "0000000006"
            },
            "washer_3": {
                "email": f"washer3_@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Washer",
                "last_name": "Three",
                "phone": "0000000007"
            },
            "client_verified": {
                "email": f"client_verified_@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Client",
                "last_name": "Verified",
                "phone": "0000000008"
            },
            "client_unverified": {
                "email": f"client_unverified_@example.com",
                "password": "SecureDevPassword123!",
                "first_name": "Client",
                "last_name": "Unverified",
                "phone": "0000000009"
            }
        }