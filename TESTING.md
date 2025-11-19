# NanoSage Testing Guide

This document provides comprehensive information about the NanoSage testing infrastructure, including how to run tests, write new tests, and interpret test results.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Installation](#installation)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Writing Tests](#writing-tests)
- [Test Markers](#test-markers)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting](#troubleshooting)

---

## Overview

NanoSage uses **pytest** as its testing framework, providing comprehensive unit tests for the backend services, API models, validators, and WebSocket functionality. The test suite ensures code quality, prevents regressions, and validates business logic.

### Test Statistics

- **Total Test Files**: 7
- **Test Coverage**: Backend services, API models, validators, WebSocket
- **Test Types**: Unit tests, integration tests
- **Test Framework**: pytest with asyncio support

---

## Test Structure

```
NanoSage/
├── tests/                          # Test directory
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures and configuration
│   ├── test_validators.py          # Tests for validators
│   ├── test_models.py              # Tests for API models
│   ├── test_export_service.py      # Tests for export service
│   ├── test_history_service.py     # Tests for history service
│   ├── test_file_upload_service.py # Tests for file upload service
│   └── test_websocket.py           # Tests for WebSocket manager
├── pytest.ini                      # Pytest configuration
├── requirements-dev.txt            # Development dependencies
└── TESTING.md                      # This file
```

### Test Coverage by Module

| Module | Test File | Test Count | Coverage |
|--------|-----------|------------|----------|
| `backend/utils/validators.py` | `test_validators.py` | 40+ tests | Validation logic, sanitization |
| `backend/api/models.py` | `test_models.py` | 50+ tests | Pydantic models, enums |
| `backend/services/export_service.py` | `test_export_service.py` | 35+ tests | Export formats, content |
| `backend/services/history_service.py` | `test_history_service.py` | 30+ tests | History management |
| `backend/services/file_upload_service.py` | `test_file_upload_service.py` | 40+ tests | File handling |
| `backend/api/websocket.py` | `test_websocket.py` | 30+ tests | WebSocket lifecycle |

---

## Installation

### Install Development Dependencies

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Or install specific packages
pip install pytest pytest-asyncio pytest-cov pytest-mock faker freezegun
```

### Verify Installation

```bash
pytest --version
```

---

## Running Tests

### Run All Tests

```bash
# Run all tests with coverage report
pytest

# Run with verbose output
pytest -v

# Run with detailed output
pytest -vv
```

### Run Specific Test Files

```bash
# Run tests for validators
pytest tests/test_validators.py

# Run tests for export service
pytest tests/test_export_service.py

# Run tests for WebSocket
pytest tests/test_websocket.py
```

### Run Specific Test Classes or Functions

```bash
# Run specific test class
pytest tests/test_validators.py::TestValidateQueryParameters

# Run specific test function
pytest tests/test_validators.py::TestValidateQueryParameters::test_valid_parameters

# Run tests matching a keyword
pytest -k "export"
pytest -k "websocket"
```

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only service tests
pytest -m services

# Run only validator tests
pytest -m validators

# Run only WebSocket tests
pytest -m websocket

# Run integration tests (when available)
pytest -m integration

# Exclude slow tests
pytest -m "not slow"
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=backend --cov-report=html

# View coverage in terminal
pytest --cov=backend --cov-report=term-missing

# Generate coverage with branch coverage
pytest --cov=backend --cov-branch --cov-report=html

# Open HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

## Test Coverage

### Current Coverage Areas

✅ **Fully Covered**:
- Input validation and sanitization
- Pydantic model validation
- Export service (Markdown, Text, PDF)
- History service (CRUD operations)
- File upload service (upload, delete, cleanup)
- WebSocket connection management

⚠️ **Partially Covered**:
- API routes (integration tests needed)
- Query service (end-to-end tests needed)

❌ **Not Yet Covered**:
- LLM integration
- Web search functionality
- Knowledge base operations
- Frontend components (React/TypeScript)

### Coverage Goals

- **Target Coverage**: 80%+ for backend services
- **Critical Paths**: 100% for validators and models
- **Integration Tests**: Coming soon

---

## Writing Tests

### Test File Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>` or `Test<Functionality>`
- Test functions: `test_<what_is_being_tested>`

### Basic Test Structure

```python
import pytest
from backend.services.example_service import ExampleService

@pytest.mark.unit
@pytest.mark.services
class TestExampleService:
    """Tests for ExampleService class"""

    @pytest.fixture
    def service(self, temp_dir):
        """Create ExampleService instance"""
        return ExampleService(data_dir=temp_dir)

    def test_basic_functionality(self, service):
        """Test basic functionality works"""
        result = service.do_something()
        assert result == expected_value

    @pytest.mark.asyncio
    async def test_async_functionality(self, service):
        """Test async functionality"""
        result = await service.do_async_operation()
        assert result is not None
```

### Using Fixtures

Shared fixtures are available in `tests/conftest.py`:

```python
def test_with_temp_directory(temp_dir):
    """Use temporary directory fixture"""
    file_path = os.path.join(temp_dir, "test.txt")
    # temp_dir is automatically cleaned up

def test_with_mock_query_parameters(mock_query_parameters):
    """Use mock query parameters"""
    assert mock_query_parameters.query == "What is quantum computing?"

def test_with_mock_query_result(mock_query_result):
    """Use complete mock query result"""
    assert mock_query_result.status == QueryStatus.COMPLETED
```

### Parametrized Tests

```python
@pytest.mark.parametrize(
    "input_value,expected_output",
    [
        ("input1", "output1"),
        ("input2", "output2"),
        ("input3", "output3"),
    ]
)
def test_multiple_scenarios(input_value, expected_output):
    """Test multiple scenarios with parametrize"""
    result = function_under_test(input_value)
    assert result == expected_output
```

### Testing Exceptions

```python
def test_validation_error_raised():
    """Test that validation error is raised"""
    with pytest.raises(ValidationError, match="Query text cannot be empty"):
        validate_query_parameters(invalid_params)
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test async operation"""
    result = await async_function()
    assert result is not None
```

---

## Test Markers

Test markers are used to categorize and filter tests:

| Marker | Description | Usage |
|--------|-------------|-------|
| `@pytest.mark.unit` | Unit tests (fast, isolated) | `pytest -m unit` |
| `@pytest.mark.integration` | Integration tests (slower) | `pytest -m integration` |
| `@pytest.mark.slow` | Slow tests (network, I/O) | `pytest -m slow` |
| `@pytest.mark.validators` | Validator tests | `pytest -m validators` |
| `@pytest.mark.models` | Model tests | `pytest -m models` |
| `@pytest.mark.services` | Service layer tests | `pytest -m services` |
| `@pytest.mark.websocket` | WebSocket tests | `pytest -m websocket` |

### Combining Markers

```bash
# Run unit tests for services
pytest -m "unit and services"

# Run all tests except slow ones
pytest -m "not slow"

# Run validators and models tests
pytest -m "validators or models"
```

---

## Continuous Integration

### GitHub Actions (Example)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: pytest --cov=backend --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Run tests before commit
pytest -m "not slow" || exit 1
```

---

## Troubleshooting

### Common Issues

#### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'backend'`

**Solution**: Ensure you're running tests from the project root directory:
```bash
cd /path/to/NanoSage
pytest
```

#### Async Test Warnings

**Problem**: `RuntimeWarning: coroutine was never awaited`

**Solution**: Add `@pytest.mark.asyncio` decorator:
```python
@pytest.mark.asyncio
async def test_async_function():
    await async_operation()
```

#### Fixture Not Found

**Problem**: `fixture 'temp_dir' not found`

**Solution**: Ensure `conftest.py` is in the tests directory and contains the fixture.

#### Coverage Not Working

**Problem**: Coverage report shows 0%

**Solution**: Run from project root with correct source path:
```bash
pytest --cov=backend --cov-report=term
```

### Debug Mode

Run tests with debug output:

```bash
# Show print statements
pytest -s

# Show local variables on failure
pytest --showlocals

# Drop into debugger on failure
pytest --pdb

# Verbose output
pytest -vv
```

---

## Best Practices

### 1. Test Independence

Each test should be independent and not rely on other tests:

```python
# ✅ Good - independent test
def test_addition():
    calculator = Calculator()
    result = calculator.add(2, 3)
    assert result == 5

# ❌ Bad - depends on class state
class TestCalculator:
    calc = Calculator()  # Shared state

    def test_addition(self):
        self.calc.add(2, 3)  # Modifies state
```

### 2. Descriptive Test Names

Use descriptive names that explain what is being tested:

```python
# ✅ Good - clear intent
def test_export_markdown_includes_query_metadata()

# ❌ Bad - unclear
def test_export()
```

### 3. Arrange-Act-Assert Pattern

Structure tests with clear sections:

```python
def test_user_registration():
    # Arrange
    user_data = {"email": "test@example.com", "password": "secure123"}

    # Act
    result = register_user(user_data)

    # Assert
    assert result.success is True
    assert result.user.email == "test@example.com"
```

### 4. Use Fixtures for Setup

Avoid repetitive setup code:

```python
@pytest.fixture
def configured_service():
    service = MyService()
    service.configure({"key": "value"})
    return service

def test_with_fixture(configured_service):
    result = configured_service.do_something()
    assert result is not None
```

### 5. Test Edge Cases

Always test edge cases and error conditions:

```python
def test_divide_by_zero_raises_error():
    calculator = Calculator()
    with pytest.raises(ZeroDivisionError):
        calculator.divide(10, 0)
```

---

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

## Contributing

When adding new features:

1. Write tests first (TDD approach recommended)
2. Ensure all tests pass: `pytest`
3. Check coverage: `pytest --cov=backend`
4. Add appropriate markers
5. Update this documentation if needed

---

**Last Updated**: 2025-01-18
**Maintainers**: NanoSage Development Team
