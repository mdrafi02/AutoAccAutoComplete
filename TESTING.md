# Testing Guide

This document describes how to run tests for the Robot Framework Keyword Predictor project.

## 📋 Overview

The project includes comprehensive unit tests covering:
- **Prediction Functions**: `predict_next_keyword`, `predict_next_keyword_with_depth`
- **Keyword Extraction**: `extract_keywords_from_output`, `normalize_keyword`
- **API Endpoints**: FastAPI endpoints for prediction and health checks
- **Model Loading**: Model and tokenizer loading functionality

## 🚀 Quick Start

### 1. Install Test Dependencies

```bash
pip install -r requirements_test.txt
```

### 2. Run All Tests

```bash
pytest
```

### 3. Run Tests with Coverage

```bash
pytest --cov=. --cov-report=html --cov-report=term
```

View coverage report:
```bash
# Open htmlcov/index.html in browser
```

## 📁 Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_prediction.py       # Prediction function tests
├── test_extraction.py        # Keyword extraction tests
└── test_api.py              # API endpoint tests
```

## 🧪 Running Specific Tests

### Run a Single Test File

```bash
pytest tests/test_prediction.py
```

### Run a Specific Test Class

```bash
pytest tests/test_prediction.py::TestPredictNextKeyword
```

### Run a Specific Test Function

```bash
pytest tests/test_prediction.py::TestPredictNextKeyword::test_predict_with_valid_context
```

### Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## 📊 Test Coverage

### Generate Coverage Report

```bash
# Terminal report
pytest --cov=. --cov-report=term

# HTML report
pytest --cov=. --cov-report=html

# XML report (for CI/CD)
pytest --cov=. --cov-report=xml
```

### View Coverage

```bash
# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## 🔧 Test Configuration

Test configuration is in `pytest.ini`:

```ini
[pytest]
testpaths = tests
addopts = -v --cov=. --cov-report=html
```

## 🎯 Test Categories

### Unit Tests

Fast, isolated tests for individual functions:
- `test_prediction.py` - Prediction logic
- `test_extraction.py` - Extraction logic

### Integration Tests

Tests that verify component interactions:
- `test_api.py` - API endpoints with model loading

## 📝 Writing New Tests

### Example: Testing a New Function

```python
# tests/test_new_feature.py
import pytest
from my_module import my_function

class TestMyFunction:
    def test_basic_usage(self):
        result = my_function("input")
        assert result == "expected"
    
    def test_edge_case(self):
        with pytest.raises(ValueError):
            my_function("")
```

### Using Fixtures

```python
def test_with_fixture(mock_model, sample_tokenizer):
    # Use fixtures from conftest.py
    result = predict_next_keyword(mock_model, sample_tokenizer, ["kw1", "kw2"])
    assert result is not None
```

## 🐛 Debugging Tests

### Run Tests with Verbose Output

```bash
pytest -vv
```

### Run Tests with Print Statements

```bash
pytest -s
```

### Run Tests and Drop into Debugger on Failure

```bash
pytest --pdb
```

### Show Local Variables on Failure

```bash
pytest -l
```

## 🔍 Common Test Patterns

### Testing Exceptions

```python
def test_raises_error():
    with pytest.raises(ValueError, match="error message"):
        function_that_raises()
```

### Testing with Mocks

```python
from unittest.mock import Mock, patch

def test_with_mock():
    mock_model = Mock()
    mock_model.predict.return_value = [[0.1, 0.9]]
    # Test with mock
```

### Testing File Operations

```python
def test_file_operation(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    # Test file operations
```

## 🚨 Troubleshooting

### Issue: Tests Fail with Import Errors

```bash
# Ensure you're in the project root
cd /path/to/robot_keyword_model2

# Install dependencies
pip install -r requirements_test.txt
```

### Issue: Model Files Not Found

Tests use temporary model files created by fixtures. If you see model file errors:
1. Check that `conftest.py` fixtures are working
2. Ensure TensorFlow is installed
3. Check test logs for specific error messages

### Issue: API Tests Fail

API tests require the model to be loaded. Ensure:
1. `client_with_model` fixture is used
2. Model files are created by fixtures
3. API module is imported correctly

## 📈 Continuous Integration

Tests are automatically run in Jenkins on:
- Every commit/PR
- Weekly training runs
- Manual triggers

See `JENKINS_SETUP.md` for CI/CD configuration.

## 🎓 Best Practices

1. **Write Descriptive Test Names**: `test_predict_with_valid_context` not `test1`
2. **Use Fixtures**: Share common setup via `conftest.py`
3. **Test Edge Cases**: Empty inputs, None values, boundary conditions
4. **Keep Tests Fast**: Unit tests should run in milliseconds
5. **Isolate Tests**: Each test should be independent
6. **Assert Clearly**: Use descriptive assertion messages
7. **Mock External Dependencies**: Don't rely on external services

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Python Testing Best Practices](https://realpython.com/python-testing/)

---

**Questions?** Check test logs or review `conftest.py` for fixture definitions.

