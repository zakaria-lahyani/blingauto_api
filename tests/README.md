# Test Directory Structure

## Overview

This directory contains all tests for the BlingAuto API, organized by test type and feature.

## Structure

```
tests/
├── unit/                 # Fast isolated tests
│   ├── auth/            # Authentication feature tests
│   ├── services/        # Services feature tests  
│   ├── vehicles/        # Vehicles feature tests
│   └── bookings/        # Bookings feature tests
├── integration/         # Component integration tests
│   ├── auth/
│   ├── services/
│   ├── vehicles/
│   └── bookings/
├── e2e/                 # End-to-end workflow tests
│   ├── auth/
│   ├── services/
│   ├── vehicles/
│   └── bookings/
├── performance/         # Performance and load tests
│   ├── auth/
│   ├── services/
│   ├── vehicles/
│   └── bookings/
├── fixtures/            # Shared test data
├── conftest.py         # Pytest configuration
└── README.md           # This file
```

## Test Types

### Unit Tests (`unit/`)
- Test individual functions and classes in isolation
- Mock external dependencies
- Fast execution (< 1ms per test)
- High coverage of business logic

### Integration Tests (`integration/`)
- Test component interactions
- Use real database (test instance)
- Test API endpoints with real adapters
- Moderate execution time (< 100ms per test)

### End-to-End Tests (`e2e/`)
- Test complete user workflows
- Full application stack
- Real external services (or staging equivalents)
- Slower execution (< 5s per test)

### Performance Tests (`performance/`)
- Load testing and benchmarks
- Response time validation
- Resource usage monitoring
- Executed separately from main test suite

## Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only  
pytest tests/integration/

# E2E tests only
pytest tests/e2e/

# Performance tests
pytest tests/performance/

# Specific feature
pytest tests/unit/auth/
pytest tests/integration/bookings/

# With coverage
pytest --cov=app tests/unit/

# Parallel execution
pytest -n auto tests/unit/
```

## Test Configuration

- `conftest.py`: Shared fixtures and pytest configuration
- `fixtures/`: Reusable test data and factory functions
- Each feature has its own `conftest.py` for feature-specific fixtures

## Guidelines

1. **Naming**: Test files should be named `test_*.py`
2. **Functions**: Test functions should be named `test_*`
3. **Classes**: Test classes should be named `Test*`
4. **Isolation**: Each test should be independent
5. **Cleanup**: Use fixtures for setup/teardown
6. **Documentation**: Include docstrings for complex test scenarios