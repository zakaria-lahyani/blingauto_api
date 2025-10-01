#!/usr/bin/env python3
"""
Architecture enforcement script.
Validates NON-NEGOTIABLE architecture rules.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: str) -> tuple[int, str, str]:
    """Run shell command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True
    )
    return result.returncode, result.stdout, result.stderr


def check_cross_feature_imports():
    """Check for cross-feature imports."""
    print("🔍 Checking for cross-feature imports...")
    
    features = ["auth", "bookings", "services", "vehicles"]
    violations = []
    
    for feature in features:
        other_features = [f for f in features if f != feature]
        pattern = f"from app\\.features\\.({'|'.join(other_features)})"
        
        cmd = f'find app/features/{feature} -name "*.py" -exec grep -l "{pattern}" {{}} \\;'
        exit_code, stdout, stderr = run_command(cmd)
        
        if stdout.strip():
            violations.extend(stdout.strip().split('\n'))
    
    if violations:
        print("❌ Cross-feature import violations found:")
        for violation in violations:
            print(f"  - {violation}")
        return False
    
    print("✅ No cross-feature imports found")
    return True


def check_business_logic_location():
    """Check for business logic outside domain/use_cases."""
    print("🔍 Checking for business logic in wrong layers...")
    
    # Check API layer for business logic patterns
    cmd = 'find app/features -path "*/api/*.py" -exec grep -l "if.*\\.(price\\|amount\\|status\\|role\\|permission)" {} \\;'
    exit_code, stdout, stderr = run_command(cmd)
    
    violations = []
    if stdout.strip():
        violations.extend(stdout.strip().split('\n'))
    
    # Check adapters for business logic
    cmd = 'find app/features -path "*/adapters/*.py" -exec grep -l "(def|class).*\\b(validate\\|calculate\\|process\\|execute\\|handle)\\b" {} \\;'
    exit_code, stdout, stderr = run_command(cmd)
    
    if stdout.strip():
        violations.extend(stdout.strip().split('\n'))
    
    if violations:
        print("❌ Business logic found outside domain/use_cases:")
        for violation in violations:
            print(f"  - {violation}")
        return False
    
    print("✅ Business logic properly contained in domain/use_cases")
    return True


def check_domain_purity():
    """Check domain layers have no framework dependencies."""
    print("🔍 Checking domain layer purity...")
    
    cmd = 'find app/features -path "*/domain/*.py" -exec grep -l "(fastapi\\|pydantic\\|sqlalchemy)" {} \\;'
    exit_code, stdout, stderr = run_command(cmd)
    
    if stdout.strip():
        violations = stdout.strip().split('\n')
        print("❌ Framework dependencies found in domain layers:")
        for violation in violations:
            print(f"  - {violation}")
        return False
    
    print("✅ Domain layers are pure (no framework dependencies)")
    return True


def check_layered_architecture():
    """Check proper layering api → use_cases → domain."""
    print("🔍 Checking layered architecture...")
    
    violations = []
    
    # Check use_cases don't import from api
    cmd = 'find app/features -path "*/use_cases/*.py" -exec grep -l "from.*\\.api\\." {} \\;'
    exit_code, stdout, stderr = run_command(cmd)
    if stdout.strip():
        violations.extend(["use_cases importing from api: " + f for f in stdout.strip().split('\n')])
    
    # Check domain doesn't import from adapters
    cmd = 'find app/features -path "*/domain/*.py" -exec grep -l "from.*\\.adapters\\." {} \\;'
    exit_code, stdout, stderr = run_command(cmd)
    if stdout.strip():
        violations.extend(["domain importing from adapters: " + f for f in stdout.strip().split('\n')])
    
    if violations:
        print("❌ Architecture layering violations:")
        for violation in violations:
            print(f"  - {violation}")
        return False
    
    print("✅ Architecture layering is correct")
    return True


def main():
    """Run all architecture checks."""
    print("🏗️  ENFORCING NON-NEGOTIABLE ARCHITECTURE RULES")
    print("=" * 50)
    
    checks = [
        check_cross_feature_imports,
        check_business_logic_location,
        check_domain_purity,
        check_layered_architecture,
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 ALL ARCHITECTURE RULES ENFORCED SUCCESSFULLY!")
        return 0
    else:
        print("💥 ARCHITECTURE VIOLATIONS FOUND - MUST BE FIXED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())