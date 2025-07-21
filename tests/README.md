# Tests Directory

This directory contains test files for the SuperC Termin Bot application.

## Test Structure

- `test_config.py`: Basic configuration and constants tests
- `test_integration.py`: Integration tests for appointment checking functionality  
- `run_tests.py`: Test runner for executing all tests

## Running Tests

### Run All Tests
```bash
python tests/run_tests.py
```

### Run Specific Tests
```bash
python tests/test_config.py
python tests/test_integration.py
```

### Using pytest (if installed)
```bash
pip install pytest
pytest tests/
```

## Test Types

### Unit Tests
Basic tests that validate individual functions and modules in isolation.

### Integration Tests  
Tests that may require network access or external dependencies. These tests validate the interaction between different components of the system.

## Notes

- Some tests use mocking to avoid external dependencies during testing
- Integration tests may require network access to fully validate functionality
- Tests are designed to work with the refactored package structure