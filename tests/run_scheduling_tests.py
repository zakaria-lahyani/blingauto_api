"""
Scheduling Test Runner
Executes all scheduling and advanced features tests in sequence.
"""

import sys
import subprocess
from datetime import datetime


def run_test_file(test_file, description):
    """Run a specific test file"""
    print(f"\n{'='*80}")
    print(f"RUNNING: {description}")
    print(f"File: {test_file}")
    print(f"{'='*80}")
    
    try:
        # Run the test file directly
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=300)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"\n[SUCCESS] {description} completed successfully")
        else:
            print(f"\n[ERROR] {description} failed with return code {result.returncode}")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"\n[TIMEOUT] {description} timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"\n[ERROR] Failed to run {description}: {str(e)}")
        return False


def main():
    """Run all scheduling tests"""
    print("SCHEDULING SYSTEM TEST SUITE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    tests = [
        ("test_scheduling_management.py", "Core Scheduling Management Tests"),
        ("test_advanced_features.py", "Advanced Features Tests")
    ]
    
    results = []
    
    for test_file, description in tests:
        success = run_test_file(test_file, description)
        results.append((description, success))
    
    # Summary
    print("\n" + "="*80)
    print("TEST EXECUTION SUMMARY")
    print("="*80)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    for description, success in results:
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {description}")
    
    print(f"\nTotal: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print(f"\n❌ {failed_tests} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)