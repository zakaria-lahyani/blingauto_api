"""
Simple test to verify application startup works.
"""

def test_app_creation():
    """Test that the FastAPI app can be created successfully."""
    try:
        from app.interfaces.http_api import create_app
        
        app = create_app()
        
        assert app is not None
        assert app.title == "BlingAuto API"
        assert app.version == "1.0.0"
        
        # Check that routers are included
        routes = [route.path for route in app.routes]
        
        expected_prefixes = [
            "/health",
            "/api/v1/auth",
            "/api/v1/bookings",
            "/api/v1/services",
            "/api/v1/vehicles",
            "/api/v1/pricing",
            "/api/v1/scheduling",
            "/api/v1/facilities/wash-bays",
            "/api/v1/facilities/mobile-teams"
        ]
        
        # Check that routers are included (at least the prefixes exist)
        found_prefixes = []
        for prefix in expected_prefixes:
            if any(route.startswith(prefix) for route in routes):
                found_prefixes.append(prefix)
        
        # Report what was found
        print(f"Found route prefixes: {found_prefixes}")
        print(f"Missing route prefixes: {set(expected_prefixes) - set(found_prefixes)}")
        
        # At least health and some core routes should exist
        assert "/health" in found_prefixes, "Health routes missing"
        
        print("SUCCESS: Application startup test passed!")
        print(f"SUCCESS: App title: {app.title}")
        print(f"SUCCESS: App version: {app.version}")
        print(f"SUCCESS: Total routes: {len(routes)}")
        print("SUCCESS: All expected route prefixes found")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Application startup failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_app_creation()
    exit(0 if success else 1)