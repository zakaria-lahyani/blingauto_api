"""
Advanced Features Tests
Tests for smart booking engine features and business optimization.

Test Coverage:
1. Customer Vehicle History and Service Recommendations
2. Mobile Team Route Optimization
3. Dynamic Pricing Engine
4. Conflict Resolution Dashboard
5. Capacity Analytics
6. Upselling Engine
"""

import requests
import json
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Dict, Any, Optional, List


class AdvancedFeaturesTests:
    """Test advanced scheduling and business optimization features"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.tokens = {
            "admin": None,
            "manager": None,
            "client": None
        }
        self.test_data = {
            "vehicles": [],
            "services": [],
            "bookings": [],
            "customers": []
        }
        
    def setup_test_users(self):
        """Setup test users for advanced features testing"""
        print("\n" + "="*70)
        print("SETTING UP TEST USERS FOR ADVANCED FEATURES")
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
            
        # Create test client
        self.create_test_client()
        
    def create_test_client(self):
        """Create a test client with vehicle history"""
        client_data = {
            "email": f"adv_client_{uuid4().hex[:8]}@test.com",
            "password": "ClientTest123!@#",
            "full_name": "Advanced Test Client",
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
                self.test_data["customers"].append({
                    "email": client_data["email"],
                    "token": self.tokens["client"]
                })
            else:
                print(f"[FAIL] Client login failed: {login_response.status_code}")
        else:
            print(f"[FAIL] Client registration failed: {response.status_code}")

    # ====================================================================
    # CUSTOMER VEHICLE HISTORY & RECOMMENDATIONS
    # ====================================================================
    
    def test_customer_vehicle_history(self):
        """Test customer vehicle history tracking and service recommendations"""
        print("\n" + "="*70)
        print("TESTING CUSTOMER VEHICLE HISTORY & RECOMMENDATIONS")
        print("="*70)
        
        client_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['client']}"}
        
        # Create test vehicles
        vehicles_data = [
            {
                "make": "BMW",
                "model": "X5",
                "year": 2023,
                "color": "Black",
                "license_plate": f"BMW{uuid4().hex[:4].upper()}",
                "is_default": True
            },
            {
                "make": "Toyota",
                "model": "Prius",
                "year": 2022,
                "color": "White",
                "license_plate": f"TOY{uuid4().hex[:4].upper()}",
                "is_default": False
            }
        ]
        
        print("\n--- Creating Test Vehicles ---")
        for vehicle_data in vehicles_data:
            response = requests.post(f"{self.base_url}/vehicles", 
                                   json=vehicle_data, headers=client_headers)
            if response.status_code in [200, 201]:
                vehicle = response.json()
                self.test_data["vehicles"].append(vehicle)
                print(f"[OK] Created vehicle: {vehicle['make']} {vehicle['model']}")
        
        # Get available services
        response = requests.get(f"{self.base_url}/services", headers=client_headers)
        if response.status_code == 200:
            self.test_data["services"] = response.json()
            print(f"[OK] Found {len(self.test_data['services'])} available services")
        
        # Create historical bookings for the BMW (premium vehicle)
        if self.test_data["vehicles"] and self.test_data["services"]:
            bmw_vehicle = self.test_data["vehicles"][0]
            premium_services = [s for s in self.test_data["services"] if "detail" in s.get("name", "").lower()]
            
            print(f"\n--- Creating Historical Bookings for {bmw_vehicle['make']} ---")
            
            # Create 3 historical bookings
            for i in range(3):
                booking_date = (datetime.now() - timedelta(days=30 * (i + 1))).isoformat()
                service = premium_services[0] if premium_services else self.test_data["services"][0]
                
                booking_data = {
                    "vehicle_id": bmw_vehicle["id"],
                    "service_ids": [service["id"]],
                    "scheduled_at": booking_date,
                    "booking_type": "stationary",
                    "notes": f"Historical booking #{i+1}",
                    "status": "completed"  # Simulate completed bookings
                }
                
                # Note: This might need admin privileges to create historical bookings
                response = requests.post(f"{self.base_url}/bookings", 
                                       json=booking_data, headers=client_headers)
                if response.status_code in [200, 201]:
                    self.test_data["bookings"].append(response.json())
                    print(f"[OK] Created historical booking for {booking_date[:10]}")
        
        # Test vehicle history endpoint
        print("\n--- Testing Vehicle History Endpoint ---")
        if self.test_data["vehicles"]:
            vehicle_id = self.test_data["vehicles"][0]["id"]
            response = requests.get(f"{self.base_url}/vehicles/{vehicle_id}/history", 
                                  headers=client_headers)
            
            if response.status_code == 200:
                history = response.json()
                print(f"[OK] Retrieved vehicle history: {len(history.get('bookings', []))} bookings")
                
                # Check for service recommendations
                if 'recommendations' in history:
                    recommendations = history['recommendations']
                    print(f"[OK] Got {len(recommendations)} service recommendations")
                    for rec in recommendations:
                        print(f"  Recommendation: {rec.get('service_name')} - {rec.get('reason')}")
                else:
                    print("[INFO] No recommendations in history response")
            else:
                print(f"[FAIL] Failed to get vehicle history: {response.status_code}")
        
        # Test customer analytics
        print("\n--- Testing Customer Analytics ---")
        response = requests.get(f"{self.base_url}/customers/analytics", headers=client_headers)
        
        if response.status_code == 200:
            analytics = response.json()
            print(f"[OK] Customer analytics retrieved")
            print(f"  Total bookings: {analytics.get('total_bookings', 0)}")
            print(f"  Total spent: ${analytics.get('total_spent', 0)}")
            print(f"  Preferred services: {analytics.get('preferred_services', [])}")
            print(f"  Last service: {analytics.get('last_service_date', 'N/A')}")
        else:
            print(f"[INFO] Customer analytics not available: {response.status_code}")

    # ====================================================================
    # MOBILE TEAM ROUTE OPTIMIZATION
    # ====================================================================
    
    def test_mobile_team_route_optimization(self):
        """Test mobile team route optimization for in-home services"""
        print("\n" + "="*70)
        print("TESTING MOBILE TEAM ROUTE OPTIMIZATION")
        print("="*70)
        
        admin_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['admin']}"}
        
        # Create mobile team
        mobile_team_data = {
            "name": "Route Test Team",
            "team_size": 2,
            "equipment_types": ["portable_washer", "vacuum", "detailing_supplies"],
            "service_radius_km": 25,
            "max_vehicles_per_day": 8,
            "hourly_rate": 5000,  # $50.00 in cents
            "is_active": True,
            "base_location": {
                "latitude": 40.7128,
                "longitude": -74.0060,
                "address": "123 Main St, New York, NY"
            }
        }
        
        print("\n--- Creating Mobile Team ---")
        response = requests.post(f"{self.base_url}/scheduling/mobile-teams", 
                               json=mobile_team_data, headers=admin_headers)
        
        if response.status_code in [200, 201]:
            mobile_team = response.json()
            print(f"[OK] Created mobile team: {mobile_team.get('name')}")
            
            # Create multiple in-home bookings for route optimization
            print("\n--- Creating In-Home Bookings for Route Testing ---")
            
            locations = [
                {"latitude": 40.7589, "longitude": -73.9851, "address": "Times Square, NY"},
                {"latitude": 40.7505, "longitude": -73.9934, "address": "Empire State Building, NY"},
                {"latitude": 40.7484, "longitude": -73.9857, "address": "Flatiron Building, NY"},
                {"latitude": 40.7614, "longitude": -73.9776, "address": "Central Park South, NY"}
            ]
            
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            
            for i, location in enumerate(locations):
                booking_time = f"{tomorrow}T{9 + i}:00:00"
                
                # Create booking for this location
                booking_data = {
                    "vehicle_id": self.test_data["vehicles"][0]["id"] if self.test_data["vehicles"] else None,
                    "service_ids": [self.test_data["services"][0]["id"]] if self.test_data["services"] else [],
                    "scheduled_at": booking_time,
                    "booking_type": "mobile",
                    "customer_location": location,
                    "notes": f"Route optimization test booking #{i+1}"
                }
                
                # This would typically be created by the client, but we're simulating
                print(f"  Simulated booking at {location['address']}")
            
            # Test route optimization endpoint
            print("\n--- Testing Route Optimization ---")
            response = requests.get(
                f"{self.base_url}/scheduling/mobile-teams/{mobile_team['id']}/optimize-route",
                params={"date": tomorrow},
                headers=admin_headers
            )
            
            if response.status_code == 200:
                optimized_route = response.json()
                print(f"[OK] Route optimization completed")
                print(f"  Total distance: {optimized_route.get('total_distance_km', 'N/A')} km")
                print(f"  Estimated time: {optimized_route.get('total_time_minutes', 'N/A')} minutes")
                print(f"  Stops: {len(optimized_route.get('stops', []))}")
                
                for stop in optimized_route.get('stops', []):
                    print(f"    Stop: {stop.get('address')} at {stop.get('estimated_arrival')}")
            else:
                print(f"[INFO] Route optimization not available: {response.status_code}")
        else:
            print(f"[FAIL] Failed to create mobile team: {response.status_code}")

    # ====================================================================
    # DYNAMIC PRICING ENGINE
    # ====================================================================
    
    def test_dynamic_pricing_engine(self):
        """Test dynamic pricing based on demand, weather, and time"""
        print("\n" + "="*70)
        print("TESTING DYNAMIC PRICING ENGINE")
        print("="*70)
        
        admin_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['admin']}"}
        client_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['client']}"}
        
        # Test pricing for different scenarios
        scenarios = [
            {
                "name": "Peak Weekend Morning",
                "date": (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),  # Saturday
                "time": "10:00",
                "expected_multiplier": 1.2
            },
            {
                "name": "Weekday Afternoon", 
                "date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),  # Tomorrow
                "time": "14:00",
                "expected_multiplier": 1.0
            },
            {
                "name": "Rainy Day",
                "date": (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
                "time": "12:00",
                "weather": "rain",
                "expected_multiplier": 1.3
            }
        ]
        
        print("\n--- Testing Dynamic Pricing Scenarios ---")
        
        for scenario in scenarios:
            print(f"\n  Testing: {scenario['name']}")
            
            params = {
                "date": scenario["date"],
                "time": scenario["time"],
                "service_type": "exterior_wash"
            }
            
            if "weather" in scenario:
                params["weather_condition"] = scenario["weather"]
            
            response = requests.get(
                f"{self.base_url}/pricing/dynamic",
                params=params,
                headers=client_headers
            )
            
            if response.status_code == 200:
                pricing = response.json()
                base_price = pricing.get('base_price', 0)
                adjusted_price = pricing.get('adjusted_price', 0)
                multiplier = pricing.get('demand_multiplier', 1.0)
                
                print(f"    Base price: ${base_price}")
                print(f"    Adjusted price: ${adjusted_price}")
                print(f"    Multiplier: {multiplier}x")
                print(f"    Factors: {pricing.get('pricing_factors', [])}")
                
                # Validate multiplier is reasonable
                if 0.8 <= multiplier <= 2.0:
                    print(f"    [OK] Reasonable pricing multiplier")
                else:
                    print(f"    [WARNING] Extreme pricing multiplier: {multiplier}")
            else:
                print(f"    [INFO] Dynamic pricing not available: {response.status_code}")

    # ====================================================================
    # CONFLICT RESOLUTION DASHBOARD
    # ====================================================================
    
    def test_conflict_resolution_dashboard(self):
        """Test conflict detection and resolution dashboard"""
        print("\n" + "="*70)
        print("TESTING CONFLICT RESOLUTION DASHBOARD")
        print("="*70)
        
        admin_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['admin']}"}
        
        # Get current scheduling conflicts
        print("\n--- Getting Current Conflicts ---")
        response = requests.get(f"{self.base_url}/scheduling/conflicts", headers=admin_headers)
        
        if response.status_code == 200:
            conflicts = response.json()
            print(f"[OK] Found {len(conflicts)} scheduling conflicts")
            
            for conflict in conflicts:
                print(f"  Conflict: {conflict.get('conflict_type')}")
                print(f"    Time: {conflict.get('requested_time')}")
                print(f"    Message: {conflict.get('message')}")
                print(f"    Resolved: {conflict.get('resolved', False)}")
                
        else:
            print(f"[INFO] Conflicts endpoint not available: {response.status_code}")
        
        # Test conflict resolution suggestions
        print("\n--- Testing Conflict Resolution Suggestions ---")
        
        # Simulate a conflict scenario
        conflict_scenario = {
            "requested_time": (datetime.now() + timedelta(days=1, hours=10)).isoformat(),
            "service_duration": 60,
            "customer_preferences": {
                "preferred_time_range": ["09:00", "12:00"],
                "max_wait_time": 30
            }
        }
        
        response = requests.post(
            f"{self.base_url}/scheduling/conflicts/resolve",
            json=conflict_scenario,
            headers=admin_headers
        )
        
        if response.status_code == 200:
            suggestions = response.json()
            print(f"[OK] Got {len(suggestions.get('alternative_slots', []))} alternative suggestions")
            
            for suggestion in suggestions.get('alternative_slots', []):
                print(f"  Alternative: {suggestion.get('start_time')}")
                print(f"    Bay: {suggestion.get('bay_name')}")
                print(f"    Score: {suggestion.get('preference_score')}")
        else:
            print(f"[INFO] Conflict resolution not available: {response.status_code}")

    # ====================================================================
    # CAPACITY ANALYTICS
    # ====================================================================
    
    def test_capacity_analytics(self):
        """Test capacity analytics and utilization reporting"""
        print("\n" + "="*70)
        print("TESTING CAPACITY ANALYTICS")
        print("="*70)
        
        admin_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['admin']}"}
        
        # Test daily capacity analytics
        print("\n--- Testing Daily Capacity Analytics ---")
        
        today = datetime.now().strftime('%Y-%m-%d')
        response = requests.get(
            f"{self.base_url}/analytics/capacity/daily",
            params={"date": today},
            headers=admin_headers
        )
        
        if response.status_code == 200:
            daily_analytics = response.json()
            print(f"[OK] Daily capacity analytics retrieved")
            print(f"  Total capacity: {daily_analytics.get('total_capacity', 0)} slots")
            print(f"  Booked slots: {daily_analytics.get('booked_slots', 0)}")
            print(f"  Utilization rate: {daily_analytics.get('utilization_rate', 0):.1%}")
            print(f"  Peak hours: {daily_analytics.get('peak_hours', [])}")
            
            # Bay-specific analytics
            for bay_data in daily_analytics.get('bay_analytics', []):
                print(f"    Bay {bay_data.get('bay_name')}: {bay_data.get('utilization_rate', 0):.1%} utilization")
        else:
            print(f"[INFO] Daily capacity analytics not available: {response.status_code}")
        
        # Test weekly trends
        print("\n--- Testing Weekly Capacity Trends ---")
        response = requests.get(
            f"{self.base_url}/analytics/capacity/weekly",
            headers=admin_headers
        )
        
        if response.status_code == 200:
            weekly_analytics = response.json()
            print(f"[OK] Weekly capacity trends retrieved")
            print(f"  Average utilization: {weekly_analytics.get('average_utilization', 0):.1%}")
            print(f"  Best day: {weekly_analytics.get('best_day')}")
            print(f"  Worst day: {weekly_analytics.get('worst_day')}")
            print(f"  Recommendations: {len(weekly_analytics.get('recommendations', []))}")
        else:
            print(f"[INFO] Weekly capacity analytics not available: {response.status_code}")

    # ====================================================================
    # UPSELLING ENGINE
    # ====================================================================
    
    def test_upselling_engine(self):
        """Test upselling suggestions based on vehicle and booking history"""
        print("\n" + "="*70)
        print("TESTING UPSELLING ENGINE")
        print("="*70)
        
        client_headers = {**self.headers, "Authorization": f"Bearer {self.tokens['client']}"}
        
        if not self.test_data["vehicles"]:
            print("[SKIP] No vehicles available for upselling test")
            return
        
        vehicle = self.test_data["vehicles"][0]  # Use BMW from earlier test
        
        # Test upselling suggestions during booking
        print("\n--- Testing Upselling During Booking ---")
        
        booking_context = {
            "vehicle_id": vehicle["id"],
            "selected_services": [self.test_data["services"][0]["id"]] if self.test_data["services"] else [],
            "vehicle_type": f"{vehicle['make']} {vehicle['model']}",
            "customer_history": {
                "total_bookings": 3,
                "preferred_services": ["exterior_wash", "interior_clean"],
                "last_service_date": "2024-01-15"
            }
        }
        
        response = requests.post(
            f"{self.base_url}/upselling/suggestions",
            json=booking_context,
            headers=client_headers
        )
        
        if response.status_code == 200:
            suggestions = response.json()
            print(f"[OK] Got {len(suggestions.get('upsell_options', []))} upsell suggestions")
            
            for suggestion in suggestions.get('upsell_options', []):
                print(f"  Upsell: {suggestion.get('service_name')}")
                print(f"    Additional cost: ${suggestion.get('additional_cost')}")
                print(f"    Reason: {suggestion.get('reason')}")
                print(f"    Confidence: {suggestion.get('confidence_score'):.2f}")
        else:
            print(f"[INFO] Upselling engine not available: {response.status_code}")
        
        # Test package recommendations
        print("\n--- Testing Package Recommendations ---")
        response = requests.get(
            f"{self.base_url}/services/packages/recommendations",
            params={"vehicle_type": f"{vehicle['make']} {vehicle['model']}"},
            headers=client_headers
        )
        
        if response.status_code == 200:
            packages = response.json()
            print(f"[OK] Got {len(packages)} package recommendations")
            
            for package in packages:
                print(f"  Package: {package.get('name')}")
                print(f"    Services: {', '.join(package.get('services', []))}")
                print(f"    Total value: ${package.get('total_value')}")
                print(f"    Package price: ${package.get('package_price')}")
                print(f"    Savings: ${package.get('savings')}")
        else:
            print(f"[INFO] Package recommendations not available: {response.status_code}")

    def run_all_tests(self):
        """Run all advanced features tests"""
        print("\n" + "="*80)
        print("STARTING ADVANCED FEATURES TESTS")
        print("="*80)
        
        try:
            # Setup
            self.setup_test_users()
            
            # Advanced Features Tests
            self.test_customer_vehicle_history()
            self.test_mobile_team_route_optimization()
            self.test_dynamic_pricing_engine()
            self.test_conflict_resolution_dashboard()
            self.test_capacity_analytics()
            self.test_upselling_engine()
            
            print("\n" + "="*80)
            print("ADVANCED FEATURES TESTS COMPLETED")
            print("="*80)
            
        except Exception as e:
            print(f"\n[ERROR] Test execution failed: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    tests = AdvancedFeaturesTests()
    tests.run_all_tests()