#!/usr/bin/env python3
"""
Auth Feature Test Runner

Runs all tests for the auth feature including unit, integration, and API tests.
This script demonstrates the comprehensive test coverage for the auth feature.
"""

import sys
import subprocess
from pathlib import Path


def run_command(command: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            cwd=Path(__file__).parent.parent.parent.parent.parent,  # Project root
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✓ {description} completed successfully")
            return True
        else:
            print(f"✗ {description} failed with return code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ {description} timed out")
        return False
    except Exception as e:
        print(f"✗ {description} failed with error: {e}")
        return False


def main():
    """Run all auth feature tests."""
    print("Auth Feature Test Suite")
    print("Testing authentication, authorization, and user management")
    
    # Test commands
    tests = [
        {
            "command": [
                "python", "-m", "pytest", 
                "app/features/auth/tests/unit/",
                "-v", "--tb=short", "--no-header"
            ],
            "description": "Unit Tests (Domain Entities & Policies)"
        },
        {
            "command": [
                "python", "-m", "pytest", 
                "app/features/auth/tests/integration/",
                "-v", "--tb=short", "--no-header"
            ],
            "description": "Integration Tests (Repository & Database)"
        },
        {
            "command": [
                "python", "-m", "pytest", 
                "app/features/auth/tests/api/",
                "-v", "--tb=short", "--no-header"
            ],
            "description": "API Tests (HTTP Endpoints)"
        }
    ]
    
    # Run all tests
    results = []
    for test in tests:
        success = run_command(test["command"], test["description"])
        results.append((test["description"], success))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    for description, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {description}")
    
    print(f"\nTotal: {total_tests}, Passed: {passed_tests}, Failed: {failed_tests}")
    
    if failed_tests > 0:
        print("\nSome tests failed. Please check the output above for details.")
        return 1
    else:
        print("\nAll auth feature tests passed!")
        print("\nFeature coverage includes:")
        print("- User registration with email verification")
        print("- Login with account lockout protection") 
        print("- JWT token management with refresh")
        print("- Password reset workflow")
        print("- Role-based access control (RBAC)")
        print("- User profile management")
        print("- Admin user management")
        print("- Comprehensive input validation")
        print("- Security policy enforcement")
        return 0


if __name__ == "__main__":
    sys.exit(main())