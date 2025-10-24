# Testing Quick Reference Card

## 🚀 Quick Start

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific file
pytest tests/test_sample.py -v

# Run without coverage (faster)
pytest --no-cov
```

## 📁 Project Structure

```
tests/
├── conftest.py       # Fixtures (9 available)
├── factories.py      # Data factories (5 classes)
├── test_sample.py    # Verification tests (14 passing ✅)
├── models/           # Model tests (write here)
├── views/            # View tests (write here)
├── forms/            # Form tests (write here)
├── utils/            # Utility tests (write here)
├── templatetags/     # Template tag tests (write here)
└── integration/      # Integration tests (write here)
```

## 🏷️ Test Markers

```bash
pytest -m unit           # Unit tests
pytest -m integration    # Integration tests
pytest -m models         # Model tests
pytest -m views          # View tests
pytest -m forms          # Form tests
pytest -m utils          # Utility tests
pytest -m "not slow"     # Skip slow tests
```

## 🔧 Makefile Commands

```bash
make test              # Run all tests
make test-coverage     # Run with coverage report
make test-fast         # Skip slow tests
make test-models       # Run model tests only
make test-views        # Run view tests only
make test-forms        # Run form tests only
make test-utils        # Run utility tests only
make clean             # Clean generated files
```

## 📊 Coverage

```bash
# Generate coverage report
pytest --cov

# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Check coverage threshold
pytest --cov --cov-fail-under=80
```

## ✍️ Writing Tests

### Basic Test Template

```python
import pytest
from tests.factories import MeetingRequestFactory

@pytest.mark.unit
@pytest.mark.models
class TestMeetingRequest:
    """Test MeetingRequest model."""
    
    def test_create_meeting(self, db):
        """Test creating a meeting request."""
        meeting = MeetingRequestFactory(title="Test")
        assert meeting.id is not None
        assert meeting.title == "Test"
```

### Available Fixtures

```python
# In your test functions:
def test_with_client(client):
    """Use Django test client."""
    response = client.get('/')
    
def test_with_auth(authenticated_client):
    """Use client with session."""
    response = authenticated_client.get('/dashboard/')
    
def test_with_timezone(tz_vietnam, tz_utc):
    """Use timezone objects."""
    assert tz_vietnam.zone == 'Asia/Ho_Chi_Minh'
    
def test_mock_time(mock_now, tz_utc):
    """Mock current time."""
    from django.utils import timezone
    fake_time = timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=tz_utc)
    mock_now(fake_time)
```

### Available Factories

```python
from tests.factories import (
    MeetingRequestFactory,
    ParticipantFactory,
    ParticipantWithoutEmailFactory,
    BusySlotFactory,
    SuggestedSlotFactory,
    create_meeting_with_participants
)

# Create meeting request
meeting = MeetingRequestFactory(title="My Meeting")

# Create participant with email
participant = ParticipantFactory(meeting_request=meeting)

# Create participant without email
anonymous = ParticipantWithoutEmailFactory(meeting_request=meeting)

# Create busy slot
busy = BusySlotFactory(participant=participant)

# Create suggested slot
suggestion = SuggestedSlotFactory(meeting_request=meeting)

# Create complete setup
meeting, participants = create_meeting_with_participants(
    num_participants=5,
    num_responded=2,
    include_busy_slots=True
)
```

## 🐛 Debugging

```bash
# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Drop into debugger
pytest --pdb

# Run last failed
pytest --lf

# Run tests matching pattern
pytest -k "test_meeting"
```

## 📈 Test Priority Order

### High Priority (Start Here)
1. ✅ Infrastructure setup (DONE)
2. 📝 `tests/utils/test_time_slots.py` - Time slot generation
3. 📝 `tests/utils/test_availability.py` - Availability checking
4. 📝 `tests/models/test_meeting_request.py` - Meeting model
5. 📝 `tests/forms/test_meeting_request_form.py` - Form validation

### Medium Priority
6. 📝 View tests (creation, response, API)
7. 📝 Remaining model tests
8. 📝 Template tag tests

### Integration
9. 📝 End-to-end workflow tests
10. 📝 Timezone handling tests

## 📚 Documentation

- **TESTING_GUIDE.md** - Comprehensive guide
- **TESTING_SETUP_SUMMARY.md** - Setup completion report
- **tests/README.md** - Test directory guide
- **UNIT_TEST_ANALYSIS.md** - Function analysis

## 🎯 Current Status

- **Tests Passing**: 14/14 ✅
- **Coverage**: 12.30% (baseline)
- **Target**: 80%+
- **Status**: Ready for development

## ⚠️ Common Issues

### Tests not found
```bash
# Make sure you're in project root
cd /home/ubuntu/code/time-manager
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Database errors
```bash
# Tests use SQLite in-memory, no setup needed
# Just run pytest
```

### Coverage too low warning
```bash
# Run without coverage check
pytest --no-cov
```

## 🔗 Useful Links

- pytest docs: https://docs.pytest.org/
- pytest-django docs: https://pytest-django.readthedocs.io/
- factory-boy docs: https://factoryboy.readthedocs.io/
- Django testing docs: https://docs.djangoproject.com/en/stable/topics/testing/

---

**Remember**: Write tests as you develop features. Aim for 80%+ coverage!
