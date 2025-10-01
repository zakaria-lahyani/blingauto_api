#!/usr/bin/env python3
"""
Services Feature Test Runner

This script runs all tests for the services feature including:
- Unit tests for domain entities and business logic
- Unit tests for use cases  
- Integration tests for API endpoints
- Domain policy validation tests

Usage:
    python -m app.features.services.tests.run_services_tests
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and display results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print('='*60)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent.parent
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
        else:
            print(f"❌ {description} - FAILED")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def main():
    """Run all services tests."""
    print("🧪 Starting Services Feature Test Suite")
    print("Testing hexagonal architecture implementation with RG-SVC business rules")
    
    # Test commands for services feature
    test_commands = [
        (
            "python -m pytest app/features/services/tests/unit/test_domain_entities.py -v --tb=short",
            "Services Domain Entities Unit Tests"
        ),
        (
            "python -m pytest app/features/services/tests/unit/test_use_cases.py -v --tb=short", 
            "Services Use Cases Unit Tests"
        ),
        (
            "python -m pytest app/features/services/tests/integration/test_api_endpoints.py -v --tb=short",
            "Services API Integration Tests"
        ),
        (
            "python -m pytest app/features/services/tests/ -v --tb=short",
            "All Services Tests Combined"
        ),
    ]
    
    passed_tests = 0
    total_tests = len(test_commands)
    
    # Run each test command
    for command, description in test_commands:
        success = run_command(command, description)
        if success:
            passed_tests += 1
    
    # Final results
    print(f"\n{'='*60}")
    print("🏁 SERVICES FEATURE TEST RESULTS")
    print(f"{'='*60}")
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 All services tests PASSED!")
        print("\n✅ Services feature implementation is complete with:")
        print("   - Domain entities with RG-SVC business rules validation")
        print("   - Hexagonal architecture (ports/adapters pattern)")
        print("   - Use cases for all business operations")
        print("   - Repository and service adapters")
        print("   - REST API endpoints with proper validation")
        print("   - Comprehensive test coverage")
        return 0
    else:
        print(f"❌ {total_tests - passed_tests} test suite(s) failed")
        print("\n🔧 Issues to fix:")
        print("   - Review failed test output above")
        print("   - Ensure all dependencies are properly injected")
        print("   - Verify RG-SVC business rules implementation")
        print("   - Check API endpoint authentication and authorization")
        return 1


if __name__ == "__main__":
    sys.exit(main())