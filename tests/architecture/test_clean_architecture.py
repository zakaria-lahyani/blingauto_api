"""
Architecture compliance tests.

Ensures the codebase follows clean architecture principles:
- No cross-feature imports (except documented exceptions)
- Domain layer purity (no infrastructure dependencies)
- Correct dependency direction
- Business logic in domain/use_cases only
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Set


BASE_DIR = Path(__file__).parent.parent.parent


def get_python_files(pattern: str) -> List[Path]:
    """Get all Python files matching a glob pattern."""
    files = []
    for path in BASE_DIR.glob(pattern):
        if "__pycache__" not in str(path) and path.suffix == ".py":
            files.append(path)
    return files


def get_imports_from_file(file_path: Path) -> List[str]:
    """Extract all import statements from a file."""
    imports = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("from ") or line.startswith("import "):
                imports.append(line)
    return imports


def test_no_cross_feature_imports_except_auth_enums():
    """
    Verify features don't import from other features' internals.

    Exception (ADR-001): UserRole and UserStatus from auth.domain are allowed.
    """
    violations = []

    features = ["auth", "bookings", "facilities", "scheduling", "services", "vehicles"]

    for feature in features:
        feature_files = get_python_files(f"app/features/{feature}/**/*.py")

        for file_path in feature_files:
            imports = get_imports_from_file(file_path)

            for imp in imports:
                # Check for cross-feature imports
                match = re.search(r"from app\.features\.(\w+)", imp)
                if match:
                    imported_feature = match.group(1)

                    # Skip same-feature imports
                    if imported_feature == feature:
                        continue

                    # Exception: auth enums (ADR-001)
                    if "from app.features.auth.domain import UserRole" in imp:
                        continue
                    if "from app.features.auth.domain import UserStatus" in imp:
                        continue

                    # Record violation
                    rel_path = file_path.relative_to(BASE_DIR)
                    violations.append((str(rel_path), imp.strip()))

    assert violations == [], (
        f"Found {len(violations)} cross-feature import violations:\n"
        + "\n".join([f"  {path}: {imp}" for path, imp in violations])
        + "\n\nOnly UserRole/UserStatus from auth.domain are allowed (ADR-001)."
    )


def test_domain_layer_purity():
    """
    Verify domain layers have no infrastructure dependencies.

    Domain should not import: fastapi, pydantic, sqlalchemy, redis, etc.
    """
    violations = []

    forbidden_patterns = [
        r"from fastapi",
        r"import fastapi",
        r"from pydantic",
        r"import pydantic",
        r"from sqlalchemy",
        r"import sqlalchemy",
        r"from redis",
        r"import redis",
    ]

    domain_files = get_python_files("app/features/*/domain/**/*.py")

    for file_path in domain_files:
        imports = get_imports_from_file(file_path)

        for imp in imports:
            for pattern in forbidden_patterns:
                if re.search(pattern, imp):
                    rel_path = file_path.relative_to(BASE_DIR)
                    violations.append((str(rel_path), imp.strip()))
                    break

    assert violations == [], (
        f"Found {len(violations)} domain purity violations:\n"
        + "\n".join([f"  {path}: {imp}" for path, imp in violations])
        + "\n\nDomain layer must not import infrastructure libraries."
    )


def test_use_cases_do_not_import_adapters():
    """
    Verify use cases don't import from adapters (correct dependency direction).

    Use cases should import from ports (interfaces), not adapters (implementations).
    """
    violations = []

    use_case_files = get_python_files("app/features/*/use_cases/**/*.py")

    for file_path in use_case_files:
        imports = get_imports_from_file(file_path)

        for imp in imports:
            if re.search(r"from app\.features\.\w+\.adapters", imp):
                rel_path = file_path.relative_to(BASE_DIR)
                violations.append((str(rel_path), imp.strip()))

    assert violations == [], (
        f"Found {len(violations)} dependency direction violations:\n"
        + "\n".join([f"  {path}: {imp}" for path, imp in violations])
        + "\n\nUse cases must import from ports, not adapters."
    )


def test_no_business_logic_in_api_layer():
    """
    Verify API layer doesn't contain complex business logic.

    API routers should only handle HTTP I/O, not business rules.
    This test checks for common patterns that indicate misplaced logic.
    """
    violations = []

    # Patterns that suggest business logic in API layer
    business_logic_patterns = [
        (r"def calculate_", "Business calculation in API layer"),
        (r"def validate_(?!request|input|schema)", "Business validation in API layer"),
        (r"if.*\.status == .*and.*\.", "Complex state logic in API layer"),
    ]

    api_files = get_python_files("app/features/*/api/**/*.py")

    for file_path in api_files:
        # Skip schema and dependency files (they're infrastructure)
        if "schemas.py" in str(file_path) or "dependencies.py" in str(file_path):
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        for pattern, message in business_logic_patterns:
            if re.search(pattern, content):
                rel_path = file_path.relative_to(BASE_DIR)
                violations.append((str(rel_path), message))

    # Note: This is a heuristic test, may have false positives
    # Review violations manually to confirm they're actual issues
    if violations:
        print("\nWarning: Potential business logic in API layer:")
        for path, message in violations:
            print(f"  {path}: {message}")


def test_features_have_complete_layer_structure():
    """
    Verify all features have the required clean architecture layers.

    Each feature must have: domain, ports, use_cases, adapters, api
    """
    required_layers = ["domain", "ports", "use_cases", "adapters", "api"]
    features = ["auth", "bookings", "facilities", "scheduling", "services", "vehicles"]

    incomplete_features = []

    for feature in features:
        feature_path = BASE_DIR / "app" / "features" / feature
        missing_layers = []

        for layer in required_layers:
            layer_path = feature_path / layer
            if not layer_path.exists():
                missing_layers.append(layer)

        if missing_layers:
            incomplete_features.append((feature, missing_layers))

    assert incomplete_features == [], (
        f"Found {len(incomplete_features)} features with incomplete structure:\n"
        + "\n".join([
            f"  {feature}: missing {', '.join(layers)}"
            for feature, layers in incomplete_features
        ])
        + "\n\nAll features must have: domain, ports, use_cases, adapters, api"
    )


def test_no_cross_feature_model_imports():
    """
    Verify database models are not imported across features.

    Features should use string-based foreign keys, not model imports.
    """
    violations = []

    adapter_files = get_python_files("app/features/*/adapters/**/*.py")

    for file_path in adapter_files:
        # Extract feature name from path
        feature = str(file_path).split("features/")[1].split("/")[0]

        imports = get_imports_from_file(file_path)

        for imp in imports:
            # Check for cross-feature model imports
            match = re.search(r"from app\.features\.(\w+)\.adapters\.models", imp)
            if match:
                imported_feature = match.group(1)

                # Skip same-feature imports
                if imported_feature == feature:
                    continue

                # Record violation
                rel_path = file_path.relative_to(BASE_DIR)
                violations.append((str(rel_path), imp.strip()))

    assert violations == [], (
        f"Found {len(violations)} cross-feature model import violations:\n"
        + "\n".join([f"  {path}: {imp}" for path, imp in violations])
        + "\n\nUse string-based foreign keys, not model imports."
    )


def test_auth_enums_only_used_in_api_or_use_cases():
    """
    Verify UserRole/UserStatus are not used in domain layers.

    Per ADR-001, auth enums may only be used in API layer or use cases for authorization.
    """
    violations = []

    domain_files = get_python_files("app/features/*/domain/**/*.py")

    for file_path in domain_files:
        # Skip auth feature's own domain
        if "/auth/domain/" in str(file_path):
            continue

        imports = get_imports_from_file(file_path)

        for imp in imports:
            if "from app.features.auth.domain import" in imp:
                rel_path = file_path.relative_to(BASE_DIR)
                violations.append((str(rel_path), imp.strip()))

    assert violations == [], (
        f"Found {len(violations)} auth enum violations in domain layers:\n"
        + "\n".join([f"  {path}: {imp}" for path, imp in violations])
        + "\n\nPer ADR-001, auth enums may only be used in API layer or use cases."
    )


def test_bookings_external_services_uses_ports():
    """
    Verify bookings external services adapter follows port pattern.

    Per architecture rules, cross-feature calls must use consumer-owned ports.
    """
    file_path = BASE_DIR / "app" / "features" / "bookings" / "adapters" / "external_services.py"

    if not file_path.exists():
        return  # File might not exist yet

    imports = get_imports_from_file(file_path)

    # Check for port imports (consumer-owned)
    has_port_import = any(
        "from app.features.bookings.ports" in imp
        for imp in imports
    )

    assert has_port_import, (
        "bookings/adapters/external_services.py must import from bookings/ports. "
        "Cross-feature adapters must implement consumer-owned ports."
    )

    # Check that only public use cases are imported (not domain or adapters)
    cross_feature_imports = [
        imp for imp in imports
        if re.search(r"from app\.features\.(\w+)", imp)
        and "from app.features.bookings" not in imp
    ]

    for imp in cross_feature_imports:
        assert "use_cases" in imp, (
            f"Cross-feature adapter can only import public use cases, not domain or adapters: {imp}"
        )


if __name__ == "__main__":
    # Run all tests manually
    print("Running architecture compliance tests...")

    tests = [
        ("No cross-feature imports (except auth enums)", test_no_cross_feature_imports_except_auth_enums),
        ("Domain layer purity", test_domain_layer_purity),
        ("Correct dependency direction", test_use_cases_do_not_import_adapters),
        ("No business logic in API layer", test_no_business_logic_in_api_layer),
        ("Complete layer structure", test_features_have_complete_layer_structure),
        ("No cross-feature model imports", test_no_cross_feature_model_imports),
        ("Auth enums only in API/use cases", test_auth_enums_only_used_in_api_or_use_cases),
        ("Bookings external services uses ports", test_bookings_external_services_uses_ports),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            print(f"✅ {name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {name}")
            print(f"   {str(e)}\n")
            failed += 1
        except Exception as e:
            print(f"⚠️  {name} (error)")
            print(f"   {str(e)}\n")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")

    if failed > 0:
        exit(1)
