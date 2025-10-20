# IC-ML Test Suite

Comprehensive pytest-based unit test suite for the ic-ml multi-use case LLM platform.

## Overview

This test suite provides coverage for:
- **Product Recommendation Engine**: Product scoring, matching, and recommendation generation
- **Health Quiz Use Case**: Input validation, consultation logic, and business rules
- **Model Configuration**: YAML config loading, model resolution, and alias handling
- **LLM Client**: Cost tracking, metadata tagging, and API wrapper logic
- **Web Service**: API endpoints, webhook processing, and email integration

## Installation

### Install Test Dependencies

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Or install individually
pip install pytest pytest-asyncio pytest-mock pytest-cov
```

### Verify Installation

```bash
pytest --version
```

## Running Tests

### Run All Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run all tests excluding web_service tests (if FastAPI not installed)
pytest tests/ --ignore=tests/test_web_service.py -v
```

### Run Specific Test Files

```bash
# Run single test file
pytest tests/test_product_recommendation_engine.py -v

# Run specific test class
pytest tests/test_model_config.py::TestModelConfigManager -v

# Run specific test
pytest tests/test_llm_client.py::TestUsageTracking::test_get_usage_stats_after_calls -v
```

### Run by Test Markers

```bash
# Run only unit tests (default)
pytest tests/ -m unit

# Skip slow tests
pytest tests/ -m "not slow"

# Run tests that mock LLM calls
pytest tests/ -m mock_llm
```

### Run with Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# View HTML coverage report
open htmlcov/index.html
```

## Test Organization

### Test Files

- `conftest.py` - Shared fixtures and test configuration
- `test_product_recommendation_engine.py` - Product recommendation tests (28 tests)
- `test_health_quiz_use_case.py` - Health quiz business logic tests (27 tests)
- `test_model_config.py` - Configuration management tests (21 tests)
- `test_llm_client.py` - LLM client wrapper tests (20 tests)
- `test_web_service.py` - Web API endpoint tests (26 tests)

### Fixtures (conftest.py)

Key fixtures available to all tests:

**Mock Data:**
- `mock_llm_response` - Mock LiteLLM completion response with usage tracking
- `sample_product_catalog` - List of 4 test products with varied attributes
- `sample_health_quiz_input` - Valid HealthQuizInput for testing
- `sample_formbricks_payload` - Mock webhook payload

**Configuration:**
- `test_config` - Mock ModelConfig instance
- `temp_config_yaml` - Temporary YAML config file (auto-cleanup)
- `temp_product_catalog_csv` - Temporary product CSV (auto-cleanup)
- `mock_use_case_config` - Mock use case configuration

**Mocking:**
- `mock_litellm_completion` - Mock synchronous LLM API calls
- `mock_litellm_async_completion` - Mock async LLM API calls
- `mock_completion_cost` - Mock cost calculation
- `mock_resend_api` - Mock Resend email API

**Reset:**
- `reset_config_manager` - Auto-reset global config manager between tests

## Test Structure

Tests follow pytest best practices:

```python
class TestFeatureName:
    """Test specific feature or component."""

    def test_behavior_under_specific_condition(self, fixture_name):
        """Test does X when Y happens."""
        # Arrange
        input_data = ...

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected_value
```

### Parametrized Tests

Many tests use `@pytest.mark.parametrize` for testing multiple scenarios:

```python
@pytest.mark.parametrize("health_area,expected_category", [
    ("immune_support", "immune_support"),
    ("digestive_health", "digestive_health"),
])
def test_category_matching(health_area, expected_category):
    # Test runs once per parameter combination
    ...
```

## Testing Principles

**DO:**
- Mock external APIs (LiteLLM, Resend, HTTP requests)
- Test behavior and outputs, not implementation details
- Use descriptive test names: `test_what_condition_expected`
- Test edge cases (empty inputs, None values, invalid data)
- Use fixtures for reusable test data

**DON'T:**
- Make actual API calls
- Test private method implementation
- Hard-code values that might change
- Test framework behavior (FastAPI routing, Pydantic validation)

## Current Test Statistics

- **Total Tests**: 122 tests
- **Test Files**: 6 files
- **Passing Tests**: 86+ tests
- **Coverage Areas**:
  - Product recommendation logic
  - Health quiz validation
  - Configuration management
  - Cost tracking
  - API endpoints

## Known Issues & Limitations

### Dependencies

Some tests require optional dependencies:

1. **FastAPI tests** (`test_web_service.py`):
   - Requires: `fastapi`, `uvicorn`, `httpx`
   - Skip with: `--ignore=tests/test_web_service.py`

2. **Real config tests** (marked with `@pytest.mark.requires_config`):
   - Require actual `config/models.yaml` file
   - Skip with: `-m "not requires_config"`

### Test Environment

- Tests use temporary files for config/catalog (auto-cleanup)
- Global config manager is reset between tests (via `reset_config_manager` fixture)
- Tests run in isolation (no shared state)

## Debugging Tests

### Verbose Output

```bash
# Show print statements and full tracebacks
pytest tests/ -v -s --tb=long

# Show only failed tests
pytest tests/ --tb=short -ra
```

### Run Specific Failing Test

```bash
# Run single test with full output
pytest tests/test_llm_client.py::TestUsageTracking::test_get_usage_stats_after_calls -vv -s
```

### Use PDB Debugger

```python
# Add breakpoint in test
def test_something():
    result = function()
    import pdb; pdb.set_trace()  # Debugger starts here
    assert result == expected
```

## Continuous Integration

For CI/CD integration:

```bash
# Run with XML output for CI systems
pytest tests/ --junitxml=junit.xml

# Run with minimal output
pytest tests/ --quiet

# Exit on first failure
pytest tests/ -x
```

## Best Practices for Adding Tests

1. **Add test to appropriate file** based on component being tested
2. **Use existing fixtures** from `conftest.py` when possible
3. **Mock external dependencies** using `mocker` fixture
4. **Follow naming convention**: `test_<what>_<condition>_<expected>`
5. **Add docstring** explaining what the test validates
6. **Test one thing** per test function
7. **Use parametrize** for testing multiple similar cases

## Example: Adding a New Test

```python
# tests/test_product_recommendation_engine.py

class TestProductRecommendationEngine:
    """Test ProductRecommendationEngine end-to-end."""

    def test_recommend_products_with_high_threshold(
        self,
        sample_product_catalog,
        mock_use_case_config
    ):
        """Test recommendations respect high minimum score threshold."""
        # Arrange
        engine = ProductRecommendationEngine(
            client_id="test",
            catalog_path=None,
            config=mock_use_case_config
        )
        engine.catalog = sample_product_catalog

        quiz_input = HealthQuizInput(
            health_issue_description="Specific issue",
            primary_health_area="cognitive_support"
        )

        # Act
        recommendations = engine.recommend_products(
            quiz_input,
            max_recommendations=10,
            min_score_threshold=0.9  # Very high threshold
        )

        # Assert
        assert len(recommendations) <= len(sample_product_catalog)
        if recommendations:
            assert all(r.relevance_score >= 0.9 for r in recommendations)
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'src'`:
- Verify `pythonpath = .` is in `pytest.ini`
- Run pytest from project root directory

### Fixture Not Found

If you see `fixture 'xyz' not found`:
- Check fixture is defined in `conftest.py`
- Verify fixture name matches exactly (case-sensitive)

### Async Test Errors

If async tests fail:
- Ensure `pytest-asyncio` is installed
- Use `@pytest.mark.asyncio` decorator
- Check `asyncio_mode = auto` in `pytest.ini`

## Contributing

When adding new features to ic-ml:

1. Write tests first (TDD approach)
2. Ensure all tests pass: `pytest tests/ -v`
3. Add new fixtures to `conftest.py` if reusable
4. Update this README with new test files/features
5. Aim for >80% code coverage

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-mock](https://pytest-mock.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
