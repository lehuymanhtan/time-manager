# Time Manager - Test Suite

This directory contains comprehensive unit tests for the Time Manager project's **Calculating Overlapping Free Time Slots** feature.

## Test Structure

The tests are organized by function under test:

- **`test_is_participant_available.py`** - Tests for checking individual participant availability (14 test cases)
- **`test_calculate_slot_availability.py`** - Tests for calculating aggregate availability across participants (11 test cases)
- **`test_generate_suggested_slots.py`** - Tests for generating time slot suggestions (18 test cases)
- **`test_get_top_suggestions.py`** - Tests for retrieving top suggestions with filtering (18 test cases)
- **`test_generate_time_slots.py`** - Tests for the time slot generation helper function (8 test cases)
- **`conftest.py`** - Shared pytest fixtures and test utilities

**Total: 69 comprehensive test cases**

## Running the Tests

### Prerequisites

Install test dependencies:

```bash
pip install -r test/requirements-test.txt
```

Or install pytest-django directly:

```bash
pip install pytest pytest-django freezegun pytest-cov
```

### Run All Tests

```bash
pytest test/
```

### Run Specific Test File

```bash
pytest test/test_is_participant_available.py
pytest test/test_calculate_slot_availability.py
pytest test/test_generate_suggested_slots.py
pytest test/test_get_top_suggestions.py
```

### Run with Coverage Report

```bash
pytest test/ --cov=meetings.utils --cov-report=html
```

This will generate an HTML coverage report in `htmlcov/index.html`.

### Run Verbose Mode

```bash
pytest test/ -v
```

### Run Specific Test

```bash
pytest test/test_is_participant_available.py::TestIsParticipantAvailable::test_partial_overlap_at_start
```

## Test Categories

### Phase 1 - Core Logic (High Priority)

#### `is_participant_available()`
Foundation for all availability checks. Tests cover:
- Basic availability (no busy slots)
- Exact match conflicts
- Partial overlaps (start and end)
- Containment scenarios
- Boundary conditions (adjacent slots)
- Multiple conflicts
- Edge cases (cross-day, 1-minute slots)

**Coverage: 14 test cases**

#### `calculate_slot_availability()`
Aggregates availability data across participants. Tests cover:
- No participants/responses
- Full and partial availability
- Mixed response states
- Complex busy patterns
- Large group handling
- Timezone consistency

**Coverage: 11 test cases**

### Phase 2 - Slot Generation (Medium Priority)

#### `generate_suggested_slots()`
Core heatmap algorithm. Tests cover:
- Initial generation vs. updates
- Force recalculation
- Weekend inclusion/exclusion
- Various step sizes and durations
- Extended date ranges
- Timezone handling
- Edge cases (empty ranges, same-day)

**Coverage: 18 test cases**

#### `get_top_suggestions()`
Retrieves and filters top suggestions. Tests cover:
- Default parameters
- Threshold variations (0%, 50%, 100%)
- Limit edge cases (0, 1, negative, large)
- Sorting (by availability and time)
- Percentage calculations
- Complex distributions

**Coverage: 18 test cases**

#### `generate_time_slots()` (Helper)
Time slot generation utility. Tests cover:
- Single and multiple day generation
- Weekend skipping
- Timezone conversions
- Duration and step size validation

**Coverage: 8 test cases**

## Test Design Principles

### Mocking Strategy
- Uses Django's test database (`@pytest.mark.django_db`)
- Factory fixtures for creating model instances
- Timezone-aware datetime handling (UTC storage)

### Fixtures (in `conftest.py`)
- `sample_meeting_request` - Basic meeting request
- `create_meeting_request` - Factory for customized meetings
- `create_participant` - Factory for participants
- `create_busy_slot` - Factory for busy time slots
- `create_suggested_slot` - Factory for suggested slots
- `make_aware_utc` - UTC timezone helper

### Assertions
Tests verify:
- Return types and structures
- Correct counts and calculations
- Participant ID accuracy
- Proper sorting and filtering
- Database state changes
- Boundary condition handling

## Coverage Goals

- **Line coverage**: 100% of function logic
- **Branch coverage**: All conditional paths tested
- **Edge cases**: Boundary values, empty states, maximum values
- **Integration**: Function interactions with dependencies

## Traceability

Each test case maps directly to requirements in `test_design.md`:

| Function | Test Cases | Categories |
|----------|-----------|------------|
| `is_participant_available()` | 14 | Availability, Conflicts, Boundaries, Edge Cases |
| `calculate_slot_availability()` | 11 | Participants, Responses, Patterns, Scale |
| `generate_suggested_slots()` | 18 | Generation, Updates, Date/Time, Timezones |
| `get_top_suggestions()` | 18 | Filtering, Sorting, Limits, Thresholds |
| `generate_time_slots()` | 8 | Helper functions, Time generation |
| **TOTAL** | **69** | **Comprehensive coverage** |

## Example Test Run Output

```
============================= test session starts ==============================
collected 69 items

test/test_is_participant_available.py::TestIsParticipantAvailable::test_participant_with_no_busy_slots PASSED [1%]
test/test_is_participant_available.py::TestIsParticipantAvailable::test_busy_slot_exactly_matching_time_range PASSED [2%]
...
test/test_get_top_suggestions.py::TestGetTopSuggestions::test_empty_meeting_request PASSED [100%]

============================== 69 passed in 2.34s ===============================
```

## Contributing

When adding new tests:
1. Follow the existing naming convention
2. Add appropriate docstrings
3. Use fixtures from `conftest.py`
4. Ensure timezone-aware datetime usage
5. Update this README if adding new test files

## Related Documentation

- **Test Design**: `/test/test_design.md` - Detailed test case specifications
- **Utils Module**: `/meetings/utils.py` - Functions under test
- **Models**: `/meetings/models.py` - Django models used in tests
