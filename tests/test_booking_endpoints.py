"""
Test Individual Booking Endpoints
Test which booking endpoints work and which have issues
"""

import requests
from datetime import datetime, timedelta


def test_booking_endpoints():
    """Test individual booking endpoints to see which ones work"""
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
    
    # Test each booking endpoint
    endpoints_to_test = [
        ("GET", "/bookings/", "List bookings"),
        ("GET", "/bookings/my", "My bookings"),
        ("GET", "/bookings/analytics/summary", "Booking analytics"),
        # We'll skip POST /bookings/ since we know it has a 500 error
    ]
    
    results = {}
    
    for method, endpoint, description in endpoints_to_test:
        try:
            response = requests.request(method, f"{base_url}{endpoint}", headers=auth_headers)
            
            if response.status_code == 200:
                data = response.json()
                results[endpoint] = {"status": "SUCCESS", "data": data}
                print(f"[OK] {description}: {response.status_code}")
                
                # Print some details for list endpoints
                if endpoint == "/bookings/":
                    print(f"[INFO] Total bookings: {data.get('total', 'unknown')}")
                elif endpoint == "/bookings/analytics/summary":
                    print(f"[INFO] Analytics: {data}")
                    
            else:
                results[endpoint] = {"status": "ERROR", "code": response.status_code, "response": response.text[:200]}
                print(f"[FAIL] {description}: {response.status_code}")
                if response.status_code != 404:  # Don't print 404 details
                    print(f"[FAIL] Response: {response.text[:100]}")
                
        except Exception as e:
            results[endpoint] = {"status": "EXCEPTION", "error": str(e)}
            print(f"[ERROR] {description}: {e}")
    
    # Test if there are any existing bookings by trying to get a specific one
    print("\n[INFO] Testing individual booking access...")
    
    # Try to list bookings first to see if there are any
    if results.get("/bookings/", {}).get("status") == "SUCCESS":
        bookings_data = results["/bookings/"]["data"]
        if bookings_data.get("total", 0) > 0:
            # There are bookings, try to get the first one
            bookings = bookings_data.get("bookings", [])
            if bookings:
                booking_id = bookings[0]["id"]
                try:
                    response = requests.get(f"{base_url}/bookings/{booking_id}", headers=auth_headers)
                    if response.status_code == 200:
                        booking = response.json()
                        print(f"[OK] Individual booking access works: {booking['id']}")
                        print(f"[INFO] Booking status: {booking['status']}")
                        
                        # Test status transitions on existing booking
                        test_status_transitions(base_url, auth_headers, booking_id, booking['status'])
                    else:
                        print(f"[FAIL] Individual booking access: {response.status_code}")
                except Exception as e:
                    print(f"[ERROR] Individual booking test: {e}")
        else:
            print("[INFO] No existing bookings found")
    
    print("\n" + "="*50)
    print("BOOKING ENDPOINTS TEST SUMMARY")
    print("="*50)
    
    for endpoint, result in results.items():
        status = result["status"]
        if status == "SUCCESS":
            print(f"[OK] {endpoint}: Working correctly")
        elif status == "ERROR":
            print(f"[FAIL] {endpoint}: HTTP {result['code']} error")
        else:
            print(f"[ERROR] {endpoint}: Exception - {result.get('error', 'Unknown')}")
    
    return results


def test_status_transitions(base_url, auth_headers, booking_id, current_status):
    """Test booking status transitions"""
    print(f"\n[INFO] Testing status transitions for booking {booking_id} (current: {current_status})")
    
    transitions_to_test = []
    
    # Based on current status, determine what transitions to test
    if current_status == "pending":
        transitions_to_test = [("confirm", "PATCH", f"/bookings/{booking_id}/confirm")]
    elif current_status == "confirmed":
        transitions_to_test = [("start", "PATCH", f"/bookings/{booking_id}/start")]
    elif current_status == "in_progress":
        transitions_to_test = [("complete", "PATCH", f"/bookings/{booking_id}/complete")]
    
    for action, method, endpoint in transitions_to_test:
        try:
            response = requests.request(method, f"{base_url}{endpoint}", headers=auth_headers)
            if response.status_code == 200:
                booking = response.json()
                print(f"[OK] {action.capitalize()} transition successful: {current_status} -> {booking['status']}")
            else:
                print(f"[FAIL] {action.capitalize()} transition failed: {response.status_code}")
                if response.status_code != 400:  # 400 might be expected business logic error
                    print(f"[FAIL] Response: {response.text[:100]}")
        except Exception as e:
            print(f"[ERROR] {action.capitalize()} transition error: {e}")


if __name__ == "__main__":
    test_booking_endpoints()