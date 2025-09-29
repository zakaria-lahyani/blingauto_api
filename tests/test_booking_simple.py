"""
Simple Booking Creation Test
Debug the 500 error in booking creation
"""

import requests
import json
from datetime import datetime, timedelta


def test_booking_creation_debug():
    """Simple test to debug booking creation 500 error"""
    base_url = "http://localhost:8000"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    # 1. Login as admin
    admin_credentials = {"email": "admin@carwash.com", "password": "AdminSecure123!@#"}
    
    login_response = requests.post(
        f"{base_url}/auth/login",
        json=admin_credentials,
        headers=headers
    )
    
    if login_response.status_code != 200:
        print(f"[ERROR] Admin login failed: {login_response.status_code}")
        return
    
    admin_token = login_response.json()["access_token"]
    auth_headers = headers.copy()
    auth_headers["Authorization"] = f"Bearer {admin_token}"
    
    print("[OK] Admin logged in successfully")
    
    # 2. Get existing categories and services
    categories_response = requests.get(f"{base_url}/services/categories", headers=auth_headers)
    services_response = requests.get(f"{base_url}/services/", headers=auth_headers)
    vehicles_response = requests.get(f"{base_url}/vehicles", headers=auth_headers)
    
    if categories_response.status_code != 200:
        print(f"[ERROR] Failed to get categories: {categories_response.status_code}")
        return
    
    if services_response.status_code != 200:
        print(f"[ERROR] Failed to get services: {services_response.status_code}")
        return
    
    if vehicles_response.status_code != 200:
        print(f"[ERROR] Failed to get vehicles: {vehicles_response.status_code}")
        return
    
    categories = categories_response.json().get("categories", [])
    services = services_response.json().get("services", [])
    vehicles = vehicles_response.json().get("vehicles", [])
    
    print(f"[INFO] Found {len(categories)} categories, {len(services)} services, {len(vehicles)} vehicles")
    
    if not services:
        print("[ERROR] No services available for booking")
        return
    
    if not vehicles:
        print("[ERROR] No vehicles available for booking")
        return
    
    # 3. Try to create a booking
    scheduled_time = datetime.utcnow() + timedelta(days=1)
    booking_data = {
        "vehicle_id": vehicles[0]["id"],
        "scheduled_at": scheduled_time.isoformat() + "Z",
        "service_ids": [services[0]["id"]],
        "booking_type": "in_home",
        "vehicle_size": "standard",
        "notes": "Debug test booking"
    }
    
    print(f"[INFO] Creating booking with data: {json.dumps(booking_data, indent=2)}")
    
    booking_response = requests.post(
        f"{base_url}/bookings/",
        json=booking_data,
        headers=auth_headers
    )
    
    print(f"[RESULT] Booking creation response: {booking_response.status_code}")
    
    if booking_response.status_code == 201:
        booking = booking_response.json()
        print(f"[SUCCESS] Booking created: {booking['id']}")
        print(f"[SUCCESS] Status: {booking['status']}, Price: ${booking['total_price']}")
    else:
        print(f"[ERROR] Booking creation failed: {booking_response.text}")
        
        # Check if it's a specific validation error
        try:
            error_data = booking_response.json()
            print(f"[ERROR] Error details: {json.dumps(error_data, indent=2)}")
        except:
            print(f"[ERROR] Raw response: {booking_response.text}")


if __name__ == "__main__":
    test_booking_creation_debug()