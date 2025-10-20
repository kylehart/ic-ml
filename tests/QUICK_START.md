# Test Suite Quick Start

## Installation (One Command)

```bash
pip install pytest pytest-asyncio pytest-mock
```

## Run Tests (One Command)

```bash
# Run all tests except web service (no FastAPI required)
pytest tests/ --ignore=tests/test_web_service.py -v
```

## Common Commands

```bash
# Run specific test file
pytest tests/test_product_recommendation_engine.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run and stop on first failure
pytest tests/ -x

# Run only failed tests from last run
pytest tests/ --lf
```

## Expected Results

- **122 total tests** across 6 test files
- **86+ tests passing** (~70% success rate)
- **~3 seconds** execution time
- **Zero actual API calls** (all mocked)

## Test Files

1. `test_product_recommendation_engine.py` - 28 tests - Product scoring & matching
2. `test_health_quiz_use_case.py` - 27 tests - Quiz validation & logic
3. `test_web_service.py` - 26 tests - API endpoints (requires FastAPI)
4. `test_model_config.py` - 21 tests - Configuration management
5. `test_llm_client.py` - 20 tests - LLM wrapper & cost tracking

## Quick Reference

### Run by Component

```bash
pytest tests/test_product_recommendation_engine.py  # Product recommendations
pytest tests/test_health_quiz_use_case.py           # Health quiz logic
pytest tests/test_model_config.py                   # Configuration
pytest tests/test_llm_client.py                     # LLM client
```

### Run Specific Test

```bash
# Format: pytest <file>::<class>::<test_name>
pytest tests/test_llm_client.py::TestUsageTracking::test_get_usage_stats_after_calls -v
```

### Debugging

```bash
# Show print statements
pytest tests/test_model_config.py -s

# Full tracebacks
pytest tests/ --tb=long

# Drop into debugger on failure
pytest tests/ --pdb
```

## Known Skips

- **Web service tests**: Skip if FastAPI not installed → `--ignore=tests/test_web_service.py`
- **Real config tests**: Skip if testing without production config → `-m "not requires_config"`

## Need Help?

- **Full documentation**: `tests/README.md`
- **Implementation summary**: `TEST_SUITE_SUMMARY.md`
- **pytest docs**: https://docs.pytest.org/

## Verify Setup

```bash
# Check pytest installed
pytest --version

# Collect tests without running
pytest tests/ --collect-only

# Run single simple test
pytest tests/test_model_config.py::TestModelConfig::test_model_config_creation -v
```

If this test passes, your setup is working!
