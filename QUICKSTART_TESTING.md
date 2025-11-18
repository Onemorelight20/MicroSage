# Quick Start: Testing Guide

Get up and running with the NanoSage test suite in 5 minutes!

## 🚀 Quick Start (3 Steps)

### 1. Install Test Dependencies

```bash
# Install all development dependencies
pip install -r requirements-dev.txt
```

**What's installed**:
- pytest (testing framework)
- pytest-asyncio (async test support)
- pytest-cov (coverage reports)
- pytest-mock (mocking utilities)
- faker, freezegun (test helpers)

---

### 2. Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=backend --cov-report=term-missing
```

**Expected output**:
```
======================== test session starts =========================
collected 225 items

tests/test_validators.py ........................................  [ 18%]
tests/test_models.py ................................................  [ 40%]
tests/test_export_service.py ....................................  [ 56%]
tests/test_history_service.py ...................................  [ 69%]
tests/test_file_upload_service.py ...............................  [ 87%]
tests/test_websocket.py .........................................  [100%]

========================= 225 passed in 5.23s ========================
```

---

### 3. View Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=backend --cov-report=html

# Open in your browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

## 📋 Common Commands

### Run Specific Tests

```bash
# Run tests for a specific module
pytest tests/test_validators.py
pytest tests/test_export_service.py
pytest tests/test_websocket.py

# Run a specific test class
pytest tests/test_validators.py::TestValidateQueryParameters

# Run a specific test function
pytest tests/test_validators.py::TestValidateQueryParameters::test_valid_parameters
```

### Run by Category

```bash
# Run only unit tests
pytest -m unit

# Run only service tests
pytest -m services

# Run only validator tests
pytest -m validators

# Run only WebSocket tests
pytest -m websocket

# Exclude slow tests
pytest -m "not slow"
```

### Debug Tests

```bash
# Show print statements
pytest -s

# Stop at first failure
pytest -x

# Show local variables on failure
pytest --showlocals

# Drop into debugger on failure
pytest --pdb
```

---

## 🎯 What's Tested?

### ✅ Backend Components (225+ tests)

| Component | Tests | Coverage |
|-----------|-------|----------|
| **Validators** | ~40 | Input validation, sanitization |
| **API Models** | ~50 | Pydantic models, enums |
| **Export Service** | ~35 | MD, TXT, PDF export |
| **History Service** | ~30 | Query history, CRUD |
| **File Upload** | ~40 | Upload, delete, cleanup |
| **WebSocket** | ~30 | Connections, messaging |

---

## 🔍 Quick Examples

### Example 1: Run Validators Tests

```bash
pytest tests/test_validators.py -v
```

**Output**:
```
tests/test_validators.py::TestValidateQueryParameters::test_valid_parameters PASSED
tests/test_validators.py::TestValidateQueryParameters::test_empty_query_text_raises_error PASSED
tests/test_validators.py::TestSanitizeInput::test_removes_angle_brackets PASSED
...
```

### Example 2: Check Coverage for Export Service

```bash
pytest tests/test_export_service.py --cov=backend/services/export_service --cov-report=term-missing
```

**Output**:
```
Name                                      Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------
backend/services/export_service.py          150      5    97%   224-225
-----------------------------------------------------------------------
TOTAL                                       150      5    97%
```

### Example 3: Run Only Fast Unit Tests

```bash
pytest -m "unit and not slow" -v
```

---

## 📁 Project Structure

```
NanoSage/
├── backend/                    # Source code
│   ├── api/
│   │   ├── models.py          # ✅ Tested (50+ tests)
│   │   └── websocket.py       # ✅ Tested (30+ tests)
│   ├── services/
│   │   ├── export_service.py  # ✅ Tested (35+ tests)
│   │   ├── history_service.py # ✅ Tested (30+ tests)
│   │   └── file_upload_service.py # ✅ Tested (40+ tests)
│   └── utils/
│       └── validators.py      # ✅ Tested (40+ tests)
│
├── tests/                     # Test suite
│   ├── conftest.py           # Shared fixtures
│   ├── test_validators.py
│   ├── test_models.py
│   ├── test_export_service.py
│   ├── test_history_service.py
│   ├── test_file_upload_service.py
│   └── test_websocket.py
│
├── pytest.ini                # Pytest config
├── requirements-dev.txt      # Test dependencies
└── TESTING.md               # Full documentation
```

---

## 🛠️ Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'backend'"

**Solution**: Run tests from the project root directory:
```bash
cd /path/to/NanoSage
pytest
```

### Issue: "No module named pytest"

**Solution**: Install test dependencies:
```bash
pip install -r requirements-dev.txt
```

### Issue: Tests failing with import errors

**Solution**: Ensure main dependencies are installed:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Issue: Coverage report shows 0%

**Solution**: Specify the correct source path:
```bash
pytest --cov=backend --cov-report=term
```

---

## 📚 Next Steps

1. **Read full documentation**: [TESTING.md](TESTING.md)
2. **View test summary**: [TEST_SUITE_SUMMARY.md](TEST_SUITE_SUMMARY.md)
3. **Write your own tests**: Use examples in existing test files
4. **Set up CI/CD**: See [.github/workflows/tests.yml](.github/workflows/tests.yml)

---

## 💡 Pro Tips

### Tip 1: Run tests on file change

```bash
# Install pytest-watch
pip install pytest-watch

# Auto-run tests on file changes
ptw
```

### Tip 2: Generate coverage badge

```bash
# Install coverage-badge
pip install coverage-badge

# Generate badge
pytest --cov=backend --cov-report=json
coverage-badge -o coverage.svg
```

### Tip 3: Parallel test execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 CPUs)
pytest -n 4
```

### Tip 4: HTML test report

```bash
# Install pytest-html
pip install pytest-html

# Generate HTML report
pytest --html=report.html --self-contained-html
```

---

## ✅ Success Checklist

- [ ] Test dependencies installed (`pip install -r requirements-dev.txt`)
- [ ] All tests passing (`pytest`)
- [ ] Coverage > 70% (`pytest --cov=backend`)
- [ ] No failing tests
- [ ] Tests run in < 10 seconds
- [ ] Coverage report accessible

---

## 📞 Need Help?

1. **Full Documentation**: [TESTING.md](TESTING.md)
2. **Test Summary**: [TEST_SUITE_SUMMARY.md](TEST_SUITE_SUMMARY.md)
3. **Examples**: Check existing test files in `tests/`
4. **Pytest Docs**: https://docs.pytest.org/

---

**Happy Testing! 🎉**

*Last updated: 2025-01-18*
