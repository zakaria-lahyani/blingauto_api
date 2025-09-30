#!/usr/bin/env python3
"""
Walk-in Booking System Test Runner

This script provides multiple ways to run the walk-in booking system tests:
1. Run all tests with comprehensive validation
2. Run specific test categories
3. Run individual test files
4. Generate detailed reports

Usage:
    python run_walk_in_tests.py --all                 # Run all tests
    python run_walk_in_tests.py --comprehensive       # Run comprehensive tests only
    python run_walk_in_tests.py --persistence         # Run persistence tests only
    python run_walk_in_tests.py --security            # Run RBAC/security tests only
    python run_walk_in_tests.py --report              # Generate test report only
"""

import sys
import argparse
import time
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.test_walk_in_comprehensive import WalkInComprehensiveTests
from tests.test_walk_in_database_persistence import DatabasePersistenceTests
from tests.test_walk_in_rbac_security import RBACSecurityTests
from tests.test_walk_in_complete_validation import WalkInCompleteValidation


class WalkInTestRunner:
    """Test runner for walk-in booking system"""
    
    def __init__(self):
        self.start_time = None
        self.results = {}
    
    def run_comprehensive_tests(self):
        """Run comprehensive functionality tests"""
        print("\nRunning Comprehensive Walk-in Tests...")
        try:
            tests = WalkInComprehensiveTests()
            tests.run_all_tests()
            self.results["comprehensive"] = "PASSED"
            print("[OK] Comprehensive tests completed successfully")
            return True
        except Exception as e:
            print(f"[FAIL] Comprehensive tests failed: {e}")
            self.results["comprehensive"] = f"FAILED: {e}"
            return False
    
    def run_persistence_tests(self):
        """Run database persistence tests"""
        print("\nRunning Database Persistence Tests...")
        try:
            tests = DatabasePersistenceTests()
            tests.run_persistence_tests()
            self.results["persistence"] = "PASSED"
            print("[OK] Database persistence tests completed successfully")
            return True
        except Exception as e:
            print(f"[FAIL] Database persistence tests failed: {e}")
            self.results["persistence"] = f"FAILED: {e}"
            return False
    
    def run_security_tests(self):
        """Run RBAC and security tests"""
        print("\nRunning RBAC & Security Tests...")
        try:
            tests = RBACSecurityTests()
            tests.run_rbac_security_tests()
            self.results["security"] = "PASSED"
            print("[OK] RBAC & Security tests completed successfully")
            return True
        except Exception as e:
            print(f"[FAIL] RBAC & Security tests failed: {e}")
            self.results["security"] = f"FAILED: {e}"
            return False
    
    def run_complete_validation(self):
        """Run complete validation suite"""
        print("\nRunning Complete Validation Suite...")
        try:
            validator = WalkInCompleteValidation()
            success = validator.run_complete_validation()
            if success:
                self.results["complete"] = "PASSED"
                print("[OK] Complete validation passed")
                return True
            else:
                self.results["complete"] = "FAILED: Some tests failed"
                print("[FAIL] Complete validation failed")
                return False
        except Exception as e:
            print(f"[FAIL] Complete validation failed: {e}")
            self.results["complete"] = f"FAILED: {e}"
            return False
    
    def generate_summary_report(self):
        """Generate summary test report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print(f"\n{'='*80}")
        print("WALK-IN BOOKING SYSTEM TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Execution Time: {duration:.2f} seconds")
        print(f"Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nTest Results:")
        print(f"{'-'*80}")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result == "PASSED")
        
        for test_name, result in self.results.items():
            status_icon = "[OK]" if result == "PASSED" else "[FAIL]"
            print(f"{status_icon} {test_name.upper():<20} {result}")
        
        print(f"{'-'*80}")
        print(f"Total: {total_tests} | Passed: {passed_tests} | Failed: {total_tests - passed_tests}")
        
        if passed_tests == total_tests:
            print("\nALL TESTS PASSED - WALK-IN SYSTEM READY!")
        else:
            print(f"\n{total_tests - passed_tests} TEST(S) FAILED - REVIEW REQUIRED")
        
        print(f"{'='*80}")
        
        return passed_tests == total_tests


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Walk-in Booking System Test Runner")
    parser.add_argument("--all", action="store_true", help="Run all tests with complete validation")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive tests only")
    parser.add_argument("--persistence", action="store_true", help="Run database persistence tests only")
    parser.add_argument("--security", action="store_true", help="Run RBAC/security tests only")
    parser.add_argument("--report", action="store_true", help="Show test categories and exit")
    
    args = parser.parse_args()
    
    runner = WalkInTestRunner()
    runner.start_time = datetime.now()
    
    print("Walk-in Booking System Test Runner")
    print(f"Started: {runner.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.report:
        print("\nAvailable Test Categories:")
        print("  --comprehensive  : Core functionality, workflows, RBAC basics")
        print("  --persistence    : Database integrity, data relationships")
        print("  --security       : Advanced RBAC, authentication, security")
        print("  --all           : Complete validation with all tests")
        return
    
    success = True
    
    if args.all:
        print("\nRunning Complete Validation Suite (All Tests)")
        success = runner.run_complete_validation()
    else:
        if args.comprehensive:
            success &= runner.run_comprehensive_tests()
        
        if args.persistence:
            success &= runner.run_persistence_tests()
        
        if args.security:
            success &= runner.run_security_tests()
        
        # If no specific test type selected, run all individual tests
        if not (args.comprehensive or args.persistence or args.security):
            print("\nNo specific test selected, running all test categories...")
            success &= runner.run_comprehensive_tests()
            success &= runner.run_persistence_tests()
            success &= runner.run_security_tests()
    
    # Generate summary report
    overall_success = runner.generate_summary_report()
    
    # Exit with appropriate code
    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()