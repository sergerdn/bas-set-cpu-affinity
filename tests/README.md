# Test Implementation for bas-set-cpu-affinity

This directory contains tests for the bas-set-cpu-affinity package.

The tests have been organized into unit tests and functional tests, with a focus on comprehensive coverage of the
application's functionality.

## Test Structure

The test suite is organized as follows:

```
tests/
├── unit/                  # Unit tests for individual components
│   ├── __init__.py        # Package marker
│   ├── test_core.py       # Tests for core.py module
│   └── test_cli.py        # Tests for cli.py module
├── functional/            # Functional tests for the application as a whole
│   ├── __init__.py        # Package marker
│   └── test_affinity_management.py  # Tests for affinity management functionality
├── __init__.py            # Package marker
├── conftest.py            # Shared pytest fixtures
└── README.md              # This file
```

## Running Tests

To run all tests:

```bash
pytest
```

To run only unit tests:

```bash
pytest tests/unit/
```

To run only functional tests:

```bash
pytest tests/functional/
```

To run a specific test file:

```bash
pytest tests/unit/test_core.py
```

To run a specific test:

```bash
pytest tests/unit/test_core.py::TestParseCorString::test_valid_core_string
```

## Test Coverage

### Unit Tests

Unit tests focus on testing individual functions in isolation, mocking external dependencies where necessary.

- **Core Module Tests** (`test_core.py`): Tests for the core functionality of the CPU affinity manager, including
  parsing core strings, validating cores, handling processes, and setting affinities.

- **CLI Module Tests** (`test_cli.py`): Tests for the command-line interface functionality, including calculating
  default cores, validating core specifications, and managing affinities.

### Functional Tests

Functional tests focus on testing the application as a whole, ensuring that different components work together
correctly.

- **Affinity Management Tests** (`test_affinity_management.py`): Tests for the CLI entry point, process affinity
  setting, and continuous monitoring functionality.

## Test Fixtures

The `conftest.py` file contains shared fixtures that can be used across multiple test files:

- `mock_process`: A mock psutil.Process object with customizable attributes.
- `mock_process_iter`: A mock for psutil.process_iter that returns a list of mock processes.
- `mock_cpu_count`: A mock for psutil.cpu_count that returns a configurable number of CPUs.
- `mock_win32_api`: Mocks for Windows API functions used in the application.

## Mocking Strategy

Since the application interacts with the operating system and running processes, many tests use mocking to avoid
interacting with the actual system:

- **psutil**: Mocked to avoid interacting with real processes.
- **win32api, win32event, win32ui**: Mocked to avoid interacting with the Windows API.
- **time**: Mocked to avoid waiting during tests.

## Platform-Specific Considerations

Some tests are platform-specific and will only run on Windows. These tests are marked with
`@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")`.

## Test Execution with Makefile

The project includes Makefile targets for running tests:

```bash
# Run all tests
make tests

# Run tests with coverage report
make tests_coverage
```
