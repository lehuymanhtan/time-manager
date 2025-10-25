"""
Quick reference for test execution and examples
"""

# =============================================================================
# QUICK START GUIDE
# =============================================================================

# 1. Install dependencies
"""
pip install -r test/requirements-test.txt
"""

# 2. Run all tests
"""
pytest test/
"""

# 3. Run with coverage
"""
pytest test/ --cov=meetings.utils --cov-report=html
"""

# =============================================================================
# TEST FILE ORGANIZATION
# =============================================================================

# test_is_participant_available.py - 14 tests
"""
Tests for checking if a single participant is available during a time slot

Key test scenarios:
- No busy slots (available)
- Exact match conflict
- Partial overlaps (start/end)
- Containment (busy within check, check within busy)
- Boundary conditions (adjacent times)
- Multiple conflicts
- Edge cases (1-minute slot, cross-day)

Example test:
    def test_partial_overlap_at_start(...)
        # Busy 08:30-09:30, checking 09:00-10:00
        # Expected: False (overlap detected)
"""

# test_calculate_slot_availability.py - 11 tests
"""
Tests for calculating aggregate availability across all participants

Key test scenarios:
- No participants/responses
- All available/all busy/partial availability
- Mixed response states
- Complex busy patterns
- Boundary testing
- Large groups (100 participants)
- Timezone consistency

Example test:
    def test_partial_availability(...)
        # 10 participants: 7 available, 3 busy
        # Expected: (7, 10, [list of 7 IDs])
"""

# test_generate_suggested_slots.py - 18 tests
"""
Tests for generating suggested time slots (heatmap algorithm)

Key test scenarios:
- Initial generation
- Update vs force recalculate
- No participants/responses
- Weekend inclusion/exclusion
- Various step sizes (15min, 30min, 60min)
- Various durations (15min to 8 hours)
- Extended date ranges (multi-week)
- Timezone handling
- Edge cases (empty range, same day)

Example test:
    def test_weekend_exclusion(...)
        # Jan 1-7 2024, work_days_only=True
        # Expected: 5 slots (Mon-Fri only)
"""

# test_get_top_suggestions.py - 18 tests
"""
Tests for retrieving top suggestions with filtering and sorting

Key test scenarios:
- Default parameters (limit=10, min=50%)
- All above/below threshold
- Exact threshold boundaries
- Zero/100% thresholds
- Limit variations (0, 1, negative, large)
- Sorting by availability then time
- No suggestions available
- Percentage calculations
- Decimal thresholds

Example test:
    def test_sorting_time(...)
        # Slots: 60%@14:00, 80%@10:00, 80%@09:00, 60%@13:00
        # Expected order: 80%@09:00, 80%@10:00, 60%@13:00, 60%@14:00
"""

# test_generate_time_slots.py - 8 tests
"""
Tests for helper function that generates time slot tuples

Key test scenarios:
- Single/multiple day generation
- Weekend skipping
- Timezone conversions
- Duration validation
- Step size verification

Example test:
    def test_timezone_conversion(...)
        # 9 AM America/New_York
        # Expected: 14:00 UTC (EST is UTC-5)
"""

# =============================================================================
# COMMON TEST PATTERNS
# =============================================================================

# Pattern 1: Create meeting request with participants
"""
meeting_request = create_meeting_request(
    duration_minutes=60,
    step_size_minutes=30,
    date_range_start=date(2024, 1, 1),
    date_range_end=date(2024, 1, 1),
    work_hours_start=time(9, 0),
    work_hours_end=time(17, 0)
)

participant = create_participant(meeting_request, has_responded=True)
"""

# Pattern 2: Create busy slots
"""
start_time = pytz.UTC.localize(datetime(2024, 1, 1, 9, 0))
end_time = pytz.UTC.localize(datetime(2024, 1, 1, 10, 0))
create_busy_slot(participant, start_time, end_time)
"""

# Pattern 3: Create suggested slots
"""
create_suggested_slot(
    meeting_request,
    start_time,
    end_time,
    available_count=7,
    total_participants=10
)
"""

# =============================================================================
# USEFUL PYTEST COMMANDS
# =============================================================================

# Run specific test file
"""
pytest test/test_is_participant_available.py
"""

# Run specific test class
"""
pytest test/test_is_participant_available.py::TestIsParticipantAvailable
"""

# Run specific test method
"""
pytest test/test_is_participant_available.py::TestIsParticipantAvailable::test_partial_overlap_at_start
"""

# Run with verbose output
"""
pytest test/ -v
"""

# Run with extra verbose output (show test names)
"""
pytest test/ -vv
"""

# Run and stop at first failure
"""
pytest test/ -x
"""

# Run and show local variables on failure
"""
pytest test/ -l
"""

# Run with coverage and missing lines
"""
pytest test/ --cov=meetings.utils --cov-report=term-missing
"""

# Run specific tests matching pattern
"""
pytest test/ -k "partial_overlap"
"""

# Run in quiet mode (less output)
"""
pytest test/ -q
"""

# =============================================================================
# COVERAGE ANALYSIS
# =============================================================================

# Generate HTML coverage report
"""
pytest test/ --cov=meetings.utils --cov-report=html
# Open htmlcov/index.html in browser
"""

# Show coverage in terminal
"""
pytest test/ --cov=meetings.utils --cov-report=term
"""

# Show missing lines
"""
pytest test/ --cov=meetings.utils --cov-report=term-missing
"""

# =============================================================================
# DEBUGGING TESTS
# =============================================================================

# Use pytest's built-in debugger
"""
pytest test/ --pdb  # Drop into debugger on failure
"""

# Print output during tests
"""
pytest test/ -s  # Don't capture stdout/stderr
"""

# Show which tests will run without executing
"""
pytest test/ --collect-only
"""

# =============================================================================
# TEST EXECUTION EXAMPLES
# =============================================================================

# Example 1: Run all tests for is_participant_available
"""
$ pytest test/test_is_participant_available.py -v

test_is_participant_available.py::TestIsParticipantAvailable::test_participant_with_no_busy_slots PASSED
test_is_participant_available.py::TestIsParticipantAvailable::test_busy_slot_exactly_matching_time_range PASSED
test_is_participant_available.py::TestIsParticipantAvailable::test_partial_overlap_at_start PASSED
...
14 passed in 1.23s
"""

# Example 2: Run with coverage
"""
$ pytest test/ --cov=meetings.utils --cov-report=term-missing

---------- coverage: platform linux, python 3.10.0 -----------
Name                    Stmts   Miss  Cover   Missing
-----------------------------------------------------
meetings/utils.py         156      0   100%
-----------------------------------------------------
TOTAL                     156      0   100%

69 passed in 3.45s
"""

# Example 3: Run specific test with verbose output
"""
$ pytest test/test_get_top_suggestions.py::TestGetTopSuggestions::test_sorting_time -v

test_get_top_suggestions.py::TestGetTopSuggestions::test_sorting_time PASSED [100%]

========================== 1 passed in 0.45s ==========================
"""

# =============================================================================
# FIXTURES REFERENCE
# =============================================================================

# Available fixtures from conftest.py:
"""
- utc: UTC timezone instance
- sample_meeting_request: Basic meeting request
- create_meeting_request: Factory for custom meetings
- create_participant: Factory for participants
- create_busy_slot: Factory for busy slots
- create_suggested_slot: Factory for suggested slots
- make_aware_utc: Helper to make datetime UTC-aware
"""

# Using fixtures in tests:
"""
def test_example(create_meeting_request, create_participant):
    meeting = create_meeting_request(duration_minutes=60)
    participant = create_participant(meeting, has_responded=True)
    # ... test logic
"""
