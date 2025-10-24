# Test Directory Structure

This directory contains all tests for the Time Manager application.

## Directory Organization

```
tests/
├── __init__.py                    # Package initialization
├── conftest.py                    # Shared fixtures and configuration
├── factories.py                   # Factory Boy test data factories
├── test_sample.py                 # Sample tests to verify setup
├── models/                        # Model layer tests
│   ├── __init__.py
│   ├── test_meeting_request.py
│   ├── test_participant.py
│   ├── test_busy_slot.py
│   └── test_suggested_slot.py
├── views/                         # View layer tests
│   ├── __init__.py
│   ├── test_dashboard_views.py
│   ├── test_creation_views.py
│   ├── test_response_views.py
│   └── test_api_views.py
├── forms/                         # Form validation tests
│   ├── __init__.py
│   ├── test_meeting_request_form.py
│   └── test_participant_forms.py
├── utils/                         # Utility function tests
│   ├── __init__.py
│   ├── test_time_slots.py
│   ├── test_availability.py
│   └── test_helpers.py
├── templatetags/                  # Template tag tests
│   ├── __init__.py
│   └── test_meeting_filters.py
└── integration/                   # Integration tests
    ├── __init__.py
    ├── test_complete_workflow.py
    └── test_timezone_handling.py
```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run with coverage:
```bash
pytest --cov
```

### Run specific test file:
```bash
pytest tests/test_sample.py
```

### Run tests by marker:
```bash
pytest -m unit          # Run only unit tests
pytest -m integration   # Run only integration tests
pytest -m "not slow"    # Skip slow tests
```

### Run specific test class or function:
```bash
pytest tests/test_sample.py::TestInfrastructure
pytest tests/test_sample.py::TestInfrastructure::test_pytest_working
```

### Verbose output:
```bash
pytest -v
pytest -vv  # Extra verbose
```

### Show print statements:
```bash
pytest -s
```

### Stop on first failure:
```bash
pytest -x
```

### Run last failed tests:
```bash
pytest --lf
```

## Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.models` - Model layer tests
- `@pytest.mark.views` - View layer tests
- `@pytest.mark.forms` - Form tests
- `@pytest.mark.utils` - Utility function tests
- `@pytest.mark.api` - API endpoint tests

## Writing Tests

### Example using factories:
```python
from tests.factories import MeetingRequestFactory, ParticipantFactory

def test_example(db):
    meeting = MeetingRequestFactory(title="Test Meeting")
    participant = ParticipantFactory(meeting_request=meeting)
    
    assert participant.meeting_request == meeting
```

### Example using fixtures:
```python
def test_with_client(client):
    response = client.get('/')
    assert response.status_code == 200
```

### Example with time mocking:
```python
from freezegun import freeze_time

@freeze_time("2025-01-15 10:00:00")
def test_with_frozen_time():
    # Time is frozen at 2025-01-15 10:00:00
    pass
```

## Coverage Reports

After running tests with coverage:
- HTML report: `htmlcov/index.html`
- XML report: `coverage.xml`
- Terminal report: shown automatically

## Continuous Integration

This test suite is designed to run in CI/CD pipelines. The configuration is optimized for:
- Fast execution (using `--reuse-db`)
- Comprehensive coverage
- Clear failure reporting

## Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Run sample tests: `pytest tests/test_sample.py -v`
3. Start writing tests for specific modules
4. Maintain >80% coverage for all new code
