# Testing Infrastructure Setup Guide

## Overview

This document describes the complete testing infrastructure for the Time Manager project. The setup follows industry best practices for Django testing with pytest.

## Architecture

### Technology Stack

- **pytest**: Modern Python testing framework
- **pytest-django**: Django integration for pytest
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities
- **factory-boy**: Test data generation
- **freezegun**: Time/date mocking
- **faker**: Realistic fake data generation

### Directory Structure

```
tests/
├── conftest.py              # Global fixtures and configuration
├── factories.py             # Factory Boy factories for models
├── test_sample.py           # Infrastructure verification tests
├── models/                  # Model layer tests
├── views/                   # View layer tests
├── forms/                   # Form validation tests
├── utils/                   # Utility function tests
├── templatetags/            # Template tag tests
└── integration/             # End-to-end integration tests
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Core dependencies (Django, PyMySQL, pytz, etc.)
- Testing dependencies (pytest, pytest-django, etc.)

### 2. Verify Installation

Run the sample tests to verify everything is working:

```bash
pytest tests/test_sample.py -v
```

Expected output: All tests should pass, demonstrating that:
- pytest is working
- Django test client is available
- Database access works
- Factories create valid objects
- Fixtures load correctly
- Mocking works

## Configuration Files

### pytest.ini

Main pytest configuration:
- Sets Django settings module
- Defines test discovery patterns
- Configures coverage reporting
- Defines custom markers
- Optimizes test execution with `--reuse-db`

### .coveragerc

Coverage tool configuration:
- Specifies source code to measure
- Excludes migrations, tests, and config files
- Sets minimum coverage threshold (80%)
- Configures HTML and XML report generation

### Makefile

Convenient commands for common tasks:
- `make test` - Run all tests
- `make test-coverage` - Run with coverage report
- `make test-fast` - Skip slow tests
- `make test-unit` - Run only unit tests
- `make clean` - Clean generated files

## Core Components

### 1. Fixtures (conftest.py)

Reusable test utilities available to all tests:

- **client**: Django test client
- **request_factory**: Create request objects
- **authenticated_client**: Client with session
- **tz_vietnam**: Vietnam timezone object
- **tz_utc**: UTC timezone object
- **mock_now**: Function to mock current time
- **sample_datetime_vietnam**: Sample datetime in Vietnam timezone
- **sample_datetime_utc**: Sample datetime in UTC
- **api_client**: JSON API test client

### 2. Factories (factories.py)

Factory classes for creating test data:

- **MeetingRequestFactory**: Creates meeting requests with sensible defaults
- **ParticipantFactory**: Creates participants with email
- **ParticipantWithoutEmailFactory**: Creates participants without email (NULL)
- **BusySlotFactory**: Creates busy time slots
- **SuggestedSlotFactory**: Creates suggested meeting slots
- **create_meeting_with_participants()**: Helper to create complete meeting setup

### 3. Test Markers

Custom markers for organizing tests:

- `@pytest.mark.unit` - Unit tests (isolated functions)
- `@pytest.mark.integration` - Integration tests (multiple components)
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.models` - Model layer tests
- `@pytest.mark.views` - View layer tests
- `@pytest.mark.forms` - Form validation tests
- `@pytest.mark.utils` - Utility function tests
- `@pytest.mark.api` - API endpoint tests

## Writing Tests

### Basic Test Structure

```python
import pytest
from tests.factories import MeetingRequestFactory

@pytest.mark.unit
class TestMeetingRequest:
    """Test MeetingRequest model."""
    
    def test_create_meeting_request(self, db):
        """Test creating a meeting request."""
        meeting = MeetingRequestFactory(title="Test Meeting")
        
        assert meeting.id is not None
        assert meeting.title == "Test Meeting"
        assert meeting.token is not None
```

### Using Factories

```python
def test_with_participants(self, db):
    """Test with multiple participants."""
    from tests.factories import create_meeting_with_participants
    
    meeting, participants = create_meeting_with_participants(
        num_participants=5,
        num_responded=2,
        include_busy_slots=True
    )
    
    assert len(participants) == 5
    assert meeting.participants.count() == 5
```

### Testing Views

```python
def test_home_view(self, client):
    """Test home page renders."""
    response = client.get('/')
    
    assert response.status_code == 200
    assert 'meetings/home.html' in [t.name for t in response.templates]
```

### Testing with Sessions

```python
def test_with_session(self, authenticated_client):
    """Test view that requires session data."""
    response = authenticated_client.get('/dashboard/')
    
    assert response.status_code == 200
    assert 'creator_id' in authenticated_client.session
```

### Mocking Time

```python
from freezegun import freeze_time

@freeze_time("2025-01-15 10:00:00")
def test_time_dependent_function():
    """Test with frozen time."""
    from django.utils import timezone
    
    now = timezone.now()
    assert now.day == 15
    assert now.month == 1
```

### Testing API Endpoints

```python
def test_api_endpoint(self, api_client):
    """Test JSON API endpoint."""
    response = api_client.get('/api/suggestions/some-id/')
    
    assert response.status_code == 200
    data = response.json()
    assert 'suggestions' in data
```

### Parametrized Tests

```python
@pytest.mark.parametrize("availability,expected_level", [
    (0, 0),
    (15, 1),
    (25, 2),
    (45, 3),
    (65, 4),
    (85, 5),
])
def test_heatmap_levels(availability, expected_level):
    """Test heatmap level calculation."""
    # Test implementation
    pass
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v
pytest -vv  # Extra verbose

# Run specific file
pytest tests/test_sample.py

# Run specific test class
pytest tests/test_sample.py::TestInfrastructure

# Run specific test function
pytest tests/test_sample.py::TestInfrastructure::test_pytest_working
```

### With Coverage

```bash
# Run with coverage
pytest --cov

# Generate HTML coverage report
pytest --cov --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Using Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run model tests
pytest -m models

# Combine markers
pytest -m "unit and models"
```

### Debugging

```bash
# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb

# Run last failed tests
pytest --lf

# Run failed tests first, then others
pytest --ff
```

### Using Makefile

```bash
# Run tests
make test

# Run with coverage
make test-coverage

# Run fast tests (skip slow)
make test-fast

# Run specific module tests
make test-models
make test-views
make test-forms
make test-utils

# Clean generated files
make clean
```

## Coverage Goals

### Minimum Coverage Targets

- **Overall**: 80% minimum
- **Critical business logic**: 90%+ target
- **Pure utility functions**: 100% target
- **Views**: 85%+ target
- **Models**: 90%+ target

### Checking Coverage

```bash
# Generate coverage report
pytest --cov --cov-report=term-missing

# Check if meets threshold
pytest --cov --cov-fail-under=80
```

### Viewing Coverage Reports

1. **Terminal**: Shows summary after test run
2. **HTML**: Detailed line-by-line coverage
   ```bash
   pytest --cov --cov-report=html
   open htmlcov/index.html
   ```
3. **XML**: For CI/CD integration
   ```bash
   pytest --cov --cov-report=xml
   ```

## Best Practices

### 1. Test Organization

- Group related tests in classes
- Use descriptive test names
- One assertion concept per test
- Keep tests simple and focused

### 2. Test Independence

- Each test should be independent
- Use factories instead of fixtures for test data
- Don't rely on test execution order
- Clean up after tests (Django does this automatically)

### 3. Test Naming

```python
# Good test names
def test_meeting_request_generates_token_on_save()
def test_participant_without_email_is_valid()
def test_busy_slot_validation_fails_when_end_before_start()

# Poor test names
def test_save()
def test_participant()
def test_validation()
```

### 4. Mocking Guidelines

- Mock external dependencies (APIs, time, random)
- Don't mock what you're testing
- Use pytest-mock for simple mocks
- Use factories for database objects

### 5. Performance

- Use `--reuse-db` for faster test runs
- Mark slow tests with `@pytest.mark.slow`
- Use `pytest-xdist` for parallel execution (optional)
- Keep database queries minimal

## Continuous Integration

### GitHub Actions

The `.github/workflows/test.yml` file configures:
- Runs tests on push/PR
- Tests against multiple Python versions
- Sets up MySQL service
- Generates coverage reports
- Uploads to Codecov (if configured)
- Checks coverage threshold

### Running CI Locally

```bash
# Simulate CI environment
pytest --cov --cov-fail-under=80 --tb=short
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure dependencies installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Database errors**: Check database configuration
   ```bash
   python manage.py migrate
   ```

3. **Timezone issues**: Use timezone-aware datetimes
   ```python
   from django.utils import timezone
   now = timezone.now()  # Timezone-aware
   ```

4. **Factory errors**: Check model constraints
   ```python
   # Provide required fields explicitly
   meeting = MeetingRequestFactory(
       start_date=future_date,
       end_date=future_date + timedelta(days=1)
   )
   ```

### Debug Mode

Add print statements and use `-s` flag:
```bash
pytest -s tests/test_sample.py
```

Use debugger:
```bash
pytest --pdb tests/test_sample.py
```

## Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Verify setup**: `pytest tests/test_sample.py -v`
3. **Review factories**: Check `tests/factories.py`
4. **Review fixtures**: Check `tests/conftest.py`
5. **Start writing tests**: Follow priority order from UNIT_TEST_ANALYSIS.md
6. **Monitor coverage**: `make test-coverage`
7. **Set up CI/CD**: Configure GitHub Actions

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-django documentation](https://pytest-django.readthedocs.io/)
- [factory-boy documentation](https://factoryboy.readthedocs.io/)
- [Django testing documentation](https://docs.djangoproject.com/en/stable/topics/testing/)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review test examples in `tests/test_sample.py`
3. Consult the UNIT_TEST_ANALYSIS.md document
4. Review pytest documentation
