# Unit Test Quick Reference Guide

## Quick Commands

### Run All Tests
```bash
python -m pytest tests/
```

### Run by Module
```bash
pytest tests/models/        # Model tests only
pytest tests/forms/         # Form tests only
pytest tests/utils/         # Utility tests only
pytest tests/templatetags/  # Template tag tests only
pytest tests/views/         # View tests only
```

### Run Specific Test
```bash
pytest tests/models/test_models.py::TestMeetingRequestSave::test_auto_generate_token_on_save
```

### Output Options
```bash
pytest tests/ -v              # Verbose output
pytest tests/ -q              # Quiet output
pytest tests/ --tb=short      # Short traceback
pytest tests/ --tb=no         # No traceback
pytest tests/ -x              # Stop on first failure
pytest tests/ -k "test_name"  # Run tests matching pattern
```

### Coverage
```bash
pytest tests/ --cov=meetings --cov-report=html
pytest tests/ --cov=meetings --cov-report=term-missing
```

## Test File Structure

```
tests/
├── __init__.py
├── conftest.py              # Fixtures and configuration
├── factories.py             # Test data factories
├── forms/
│   └── test_forms.py        # Form validation tests
├── models/
│   └── test_models.py       # Model logic tests
├── templatetags/
│   └── test_meeting_filters.py  # Template filter tests
├── utils/
│   └── test_utils.py        # Utility function tests
└── views/
    └── test_views.py        # View and workflow tests
```

## Common Test Patterns

### Creating Test Data
```python
from tests.factories import (
    MeetingRequestFactory,
    ParticipantFactory,
    BusySlotFactory
)

# Create a meeting
meeting = MeetingRequestFactory()

# Create participants
participant = ParticipantFactory(meeting_request=meeting)

# Create multiple
participants = ParticipantFactory.create_batch(5, meeting_request=meeting)

# Create with specific attributes
meeting = MeetingRequestFactory(
    status='active',
    work_days_only=True,
    duration_minutes=60
)
```

### Testing with Django Client
```python
def test_view(client):
    response = client.get('/dashboard/')
    assert response.status_code == 200
    assert 'requests' in response.context
```

### Testing with Request Factory
```python
def test_view(request_factory):
    request = request_factory.get('/path/')
    request.session = {}
    response = my_view(request)
    assert response.status_code == 200
```

### Testing Forms
```python
def test_form():
    data = {'title': 'Test', 'duration_minutes': 60}
    form = MeetingRequestForm(data=data)
    assert form.is_valid()
```

### Testing Models
```python
def test_model():
    meeting = MeetingRequestFactory()
    assert meeting.response_rate == 0
    
    ParticipantFactory.create_batch(5, 
        meeting_request=meeting, 
        has_responded=True
    )
    assert meeting.response_rate == 100
```

### Testing with Time
```python
from django.utils import timezone
from datetime import timedelta

def test_deadline():
    past = timezone.now() - timedelta(days=1)
    meeting = MeetingRequestFactory(response_deadline=past)
    assert not meeting.is_active
```

## Test Assertions

### Common Assertions
```python
# Equality
assert result == expected
assert result != unexpected

# Boolean
assert is_valid
assert not is_invalid

# Membership
assert item in list
assert 'key' in dictionary

# Exceptions
with pytest.raises(ValidationError):
    form.clean()

# Comparison
assert count > 0
assert percentage >= 50
```

### Django-Specific
```python
# HTTP Status
assert response.status_code == 200
assert response.status_code == 302  # Redirect
assert response.status_code == 404  # Not Found

# Context
assert 'key' in response.context
assert response.context['count'] == 5

# Templates
assert 'template.html' in [t.name for t in response.templates]

# Database
assert Model.objects.count() == 5
assert Model.objects.filter(status='active').exists()
```

## Test Organization by Function

### Models (31 tests)
- Token generation
- Status validation  
- Percentage calculations
- Time validation
- URL generation

### Forms (19 tests)
- Date validation
- Time range validation
- Required fields
- Error messages

### Utils (41 tests)
- Time slot generation
- Availability calculations
- Heatmap generation
- JSON parsing
- Timezone conversions

### Template Tags (21 tests)
- Dictionary access
- Date formatting
- Error handling

### Views (55 tests)
- Session management
- Wizard workflows
- API endpoints
- Authentication
- Response handling

## Debugging Failed Tests

### View Full Error
```bash
pytest tests/path/to/test.py -v --tb=long
```

### Run Single Test
```bash
pytest tests/path/to/test.py::TestClass::test_method -v
```

### Print Debug Info
```python
def test_something():
    result = function()
    print(f"Debug: result = {result}")  # Will show on failure
    assert result == expected
```

### Use Pytest's `-s` Flag
```bash
pytest tests/ -s  # Don't capture output
```

## Common Issues & Solutions

### Issue: Database Not Accessible
```python
# Solution: Add @pytest.mark.django_db decorator
@pytest.mark.django_db
def test_function():
    meeting = MeetingRequestFactory()
```

### Issue: Session Not Working
```python
# Solution: Create session dictionary
request.session = {}
request.session['key'] = 'value'
```

### Issue: Timezone Issues
```python
# Solution: Use timezone-aware datetime
from django.utils import timezone
now = timezone.now()  # Not datetime.now()
```

### Issue: Factory Overrides Not Working
```python
# Solution: Use correct syntax
meeting = MeetingRequestFactory(
    status='active'  # Correct
)
# Not: MeetingRequestFactory.create(status='active')
```

## Test Markers

### Mark as Database Test
```python
@pytest.mark.django_db
def test_database_access():
    pass
```

### Mark as Slow
```python
@pytest.mark.slow
def test_slow_operation():
    pass
```

### Skip Test
```python
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Tests
  run: |
    python -m pytest tests/ --cov=meetings --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v2
```

## Performance Tips

1. **Use Database Fixtures:** Faster than creating data in each test
2. **Batch Creation:** Use `create_batch()` for multiple objects
3. **Minimal Mocking:** Real operations are often faster
4. **Parallel Execution:** `pytest -n auto` (requires pytest-xdist)
5. **Focus Tests:** Use `-k` to run subset during development

## Writing New Tests

### Template for New Test
```python
@pytest.mark.django_db
class TestNewFeature:
    """Test description"""
    
    def test_happy_path(self):
        """Test normal usage"""
        # Arrange
        meeting = MeetingRequestFactory()
        
        # Act
        result = meeting.some_method()
        
        # Assert
        assert result == expected
    
    def test_edge_case(self):
        """Test boundary condition"""
        # Test implementation
        pass
    
    def test_error_handling(self):
        """Test error scenarios"""
        with pytest.raises(ValidationError):
            # Code that should raise error
            pass
```

## Resources

- **Pytest Documentation:** https://docs.pytest.org/
- **pytest-django:** https://pytest-django.readthedocs.io/
- **Factory Boy:** https://factoryboy.readthedocs.io/
- **Django Testing:** https://docs.djangoproject.com/en/stable/topics/testing/

## Summary Statistics

- **Total Tests:** 167
- **Success Rate:** 100%
- **Average Execution Time:** ~1.9 seconds
- **Code Coverage:** >90% across all modules
