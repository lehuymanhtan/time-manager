# Unit Testing Analysis for Time Manager Project

## Table of Contents
1. [Models](#models)
2. [Views](#views)
3. [Forms](#forms)
4. [Utils](#utils)
5. [Template Tags](#template-tags)

---

## Models

### 1. `MeetingRequest.save()`
**Location:** `meetings/models.py`

**Main Functionality:**
- Overrides Django's save method to auto-generate a unique token if not present

**Input Parameters:**
- `*args`, `**kwargs` (standard Django save parameters)

**Expected Return:**
- None (saves object to database)

**Edge Cases:**
- Token already exists
- Token collision (unlikely but possible)
- Multiple saves of same object

**Dependencies to Mock:**
- `secrets.token_urlsafe(32)` - token generation

---

### 2. `MeetingRequest.is_active` (Property)
**Location:** `meetings/models.py`

**Main Functionality:**
- Determines if a meeting request is still accepting responses

**Input Parameters:**
- None (property method)

**Expected Return:**
- Boolean (True if active, False otherwise)

**Edge Cases:**
- Status is not 'active'
- Deadline is None
- Deadline is exactly now
- Deadline is in the past
- Deadline is in the future

**Dependencies to Mock:**
- `timezone.now()` - current time

---

### 3. `MeetingRequest.response_rate` (Property)
**Location:** `meetings/models.py`

**Main Functionality:**
- Calculates percentage of participants who have responded

**Input Parameters:**
- None (property method)

**Expected Return:**
- Integer (0-100, rounded percentage)

**Edge Cases:**
- Zero participants
- All participants responded
- Partial responses
- No responses

**Dependencies to Mock:**
- Database queries (participants.count())

---

### 4. `MeetingRequest.get_share_url()`
**Location:** `meetings/models.py`

**Main Functionality:**
- Generates shareable URL for participants

**Input Parameters:**
- None

**Expected Return:**
- String (URL path)

**Edge Cases:**
- Missing token
- UUID format

**Dependencies to Mock:**
- None

---

### 5. `BusySlot.clean()`
**Location:** `meetings/models.py`

**Main Functionality:**
- Validates that end_time is after start_time

**Input Parameters:**
- None (called on model instance)

**Expected Return:**
- None (raises ValidationError if invalid)

**Edge Cases:**
- start_time == end_time
- start_time > end_time
- start_time < end_time (valid)
- None values

**Dependencies to Mock:**
- None

---

### 6. `SuggestedSlot.availability_percentage` (Property)
**Location:** `meetings/models.py`

**Main Functionality:**
- Calculates percentage of available participants

**Input Parameters:**
- None (property method)

**Expected Return:**
- Float (rounded to 1 decimal place)

**Edge Cases:**
- Zero total participants
- All participants available
- No participants available
- Partial availability

**Dependencies to Mock:**
- None

---

### 7. `SuggestedSlot.heatmap_level` (Property)
**Location:** `meetings/models.py`

**Main Functionality:**
- Returns heatmap intensity level (0-5) based on availability percentage

**Input Parameters:**
- None (property method)

**Expected Return:**
- Integer (0-5)

**Edge Cases:**
- 0% availability (level 0)
- 1-19% (level 1)
- 20-39% (level 2)
- 40-59% (level 3)
- 60-79% (level 4)
- 80%+ (level 5)
- Edge values (exactly 20%, 40%, 60%, 80%, 100%)

**Dependencies to Mock:**
- None

---

## Views

### 8. `get_or_create_creator_id()`
**Location:** `meetings/views.py`

**Main Functionality:**
- Gets or creates a unique creator ID from session

**Input Parameters:**
- `request` (HttpRequest object)

**Expected Return:**
- String (UUID)

**Edge Cases:**
- Session has existing creator_id
- Session has no creator_id
- Empty session

**Dependencies to Mock:**
- `request.session` - session storage
- `uuid.uuid4()` - UUID generation

---

### 9. `home()`
**Location:** `meetings/views.py`

**Main Functionality:**
- Renders landing page

**Input Parameters:**
- `request` (HttpRequest)

**Expected Return:**
- HttpResponse with rendered template

**Edge Cases:**
- GET request
- Different HTTP methods

**Dependencies to Mock:**
- `render()` function

---

### 10. `dashboard()`
**Location:** `meetings/views.py`

**Main Functionality:**
- Shows leader dashboard with their meeting requests

**Input Parameters:**
- `request` (HttpRequest)

**Expected Return:**
- HttpResponse with dashboard template

**Edge Cases:**
- User with no meeting requests
- User with multiple requests
- Session without creator_id
- Responded vs not responded participants

**Dependencies to Mock:**
- `get_or_create_creator_id()`
- `MeetingRequest.objects.filter()`
- `request.build_absolute_uri()`

---

### 11. `create_request_step1()`
**Location:** `meetings/views.py`

**Main Functionality:**
- Step 1 of wizard: Meeting configuration

**Input Parameters:**
- `request` (HttpRequest)

**Expected Return:**
- HttpResponse (GET) or redirect (POST)

**Edge Cases:**
- GET request (show form)
- POST with valid data
- POST with invalid data
- Session handling for meeting_request_id

**Dependencies to Mock:**
- `MeetingRequestForm`
- `get_or_create_creator_id()`
- `timezone.now()`

---

### 12. `create_request_step2()`
**Location:** `meetings/views.py`

**Main Functionality:**
- Step 2 of wizard: Add participants

**Input Parameters:**
- `request` (HttpRequest)

**Expected Return:**
- HttpResponse or redirect

**Edge Cases:**
- No meeting_request_id in session (redirect)
- Add single participant
- Add bulk participants (CSV format)
- Duplicate email addresses
- Empty email (NULL)
- Skip step
- Invalid participant data

**Dependencies to Mock:**
- `ParticipantForm`
- `BulkParticipantForm`
- `Participant.objects.get_or_create()`

---

### 13. `create_request_step3()`
**Location:** `meetings/views.py`

**Main Functionality:**
- Step 3 of wizard: Review and finalize

**Input Parameters:**
- `request` (HttpRequest)

**Expected Return:**
- HttpResponse or redirect

**Edge Cases:**
- No meeting_request_id in session
- GET request (show preview)
- POST request (finalize)
- Session cleanup

**Dependencies to Mock:**
- `get_heatmap_data()`

---

### 14. `request_created()`
**Location:** `meetings/views.py`

**Main Functionality:**
- Success page after creating request, shows share URL

**Input Parameters:**
- `request` (HttpRequest)
- `request_id` (UUID)

**Expected Return:**
- HttpResponse

**Edge Cases:**
- Request doesn't exist (404)
- Building absolute URI

**Dependencies to Mock:**
- `request.build_absolute_uri()`

---

### 15. `view_request()`
**Location:** `meetings/views.py`

**Main Functionality:**
- Leader view of meeting request with full details and suggestions

**Input Parameters:**
- `request` (HttpRequest)
- `request_id` (UUID)

**Expected Return:**
- HttpResponse

**Edge Cases:**
- Request doesn't exist (404)
- No participants
- No responses
- Locked status
- Active status

**Dependencies to Mock:**
- `generate_suggested_slots()`
- `get_top_suggestions()`
- `get_heatmap_data()`

---

### 16. `lock_slot()`
**Location:** `meetings/views.py`

**Main Functionality:**
- Lock a suggested slot as final meeting time

**Input Parameters:**
- `request` (HttpRequest)
- `request_id` (UUID)
- `slot_id` (UUID)

**Expected Return:**
- Redirect to view_request

**Edge Cases:**
- Slot doesn't exist (404)
- Request doesn't exist (404)
- Multiple suggested slots
- Already locked request

**Dependencies to Mock:**
- `SuggestedSlot.objects.filter().delete()`

---

### 17. `edit_request()`
**Location:** `meetings/views.py`

**Main Functionality:**
- Edit meeting request settings

**Input Parameters:**
- `request` (HttpRequest)
- `request_id` (UUID)

**Expected Return:**
- HttpResponse or redirect or 403

**Edge Cases:**
- Ownership verification failure
- GET request
- POST with valid data
- POST with invalid data

**Dependencies to Mock:**
- `get_or_create_creator_id()`
- `MeetingRequestForm`

---

### 18. `delete_request()`
**Location:** `meetings/views.py`

**Main Functionality:**
- Delete a meeting request

**Input Parameters:**
- `request` (HttpRequest)
- `request_id` (UUID)

**Expected Return:**
- HttpResponse (GET) or redirect (POST)

**Edge Cases:**
- Request doesn't exist (404)
- GET request (show confirmation)
- POST request (delete and redirect)
- Cascading deletes (participants, slots, etc.)

**Dependencies to Mock:**
- `MeetingRequest.objects.delete()`

---

### 19. `respond_to_request()`
**Location:** `meetings/views.py`

**Main Functionality:**
- Member view to respond with availability

**Input Parameters:**
- `request` (HttpRequest)
- `request_id` (UUID)

**Expected Return:**
- HttpResponse, redirect, or 403

**Edge Cases:**
- Invalid token (403)
- Request not active (closed page)
- Existing participant
- New participant
- Participant with email
- Participant without email (NULL)
- GET vs POST

**Dependencies to Mock:**
- `ParticipantResponseForm`
- `Participant.objects.get_or_create()`

---

### 20. `select_busy_times()`
**Location:** `meetings/views.py`

**Main Functionality:**
- Member selects their busy time slots on a calendar interface

**Input Parameters:**
- `request` (HttpRequest)
- `request_id` (UUID)

**Expected Return:**
- HttpResponse or redirect

**Edge Cases:**
- No participant_id in session/URL (redirect)
- Participant doesn't exist (404)
- Existing busy slots displayed
- Token validation
- Heatmap serialization

**Dependencies to Mock:**
- `get_heatmap_data()`
- `json.dumps()`

---

### 21. `save_busy_slots()`
**Location:** `meetings/views.py`

**Main Functionality:**
- API endpoint to save participant busy slots

**Input Parameters:**
- `request` (HttpRequest - POST)
- `request_id` (UUID)

**Expected Return:**
- JsonResponse

**Edge Cases:**
- No participant in session (400)
- Invalid JSON
- Empty busy slots
- Multiple busy slots
- Invalid datetime format
- Timezone conversion errors

**Dependencies to Mock:**
- `json.loads()`
- `parse_busy_slots_from_json()`
- `generate_suggested_slots()`
- `timezone.now()`

---

### 22. `response_complete()`
**Location:** `meetings/views.py`

**Main Functionality:**
- Thank you page after member submits response

**Input Parameters:**
- `request` (HttpRequest)
- `request_id` (UUID)

**Expected Return:**
- HttpResponse

**Edge Cases:**
- Participant in session
- No participant in session
- Response statistics calculation

**Dependencies to Mock:**
- `get_top_suggestions()`

---

### 23. `api_get_heatmap()`
**Location:** `meetings/views.py`

**Main Functionality:**
- API endpoint for heatmap data

**Input Parameters:**
- `request` (HttpRequest)
- `request_id` (UUID)

**Expected Return:**
- JsonResponse

**Edge Cases:**
- Request doesn't exist (404)
- Timezone parameter provided
- No timezone parameter (use default)

**Dependencies to Mock:**
- `get_heatmap_data()`

---

### 24. `api_get_suggestions()`
**Location:** `meetings/views.py`

**Main Functionality:**
- API endpoint for top suggestions

**Input Parameters:**
- `request` (HttpRequest)
- `request_id` (UUID)

**Expected Return:**
- JsonResponse

**Edge Cases:**
- Request doesn't exist (404)
- Custom limit parameter
- Custom min_pct parameter
- Default parameters

**Dependencies to Mock:**
- `get_top_suggestions()`

---

## Forms

### 25. `MeetingRequestForm.clean()`
**Location:** `meetings/forms.py`

**Main Functionality:**
- Validate date ranges, work hours, and deadlines

**Input Parameters:**
- None (operates on form data)

**Expected Return:**
- cleaned_data dict or raises ValidationError

**Edge Cases:**
- Past start date ❌
- Past end date ❌
- Past response deadline ❌
- Start date == end date ❌
- End date > 90 days from start ❌
- Work end time <= work start time ❌
- Today's date (should be valid) ✓
- Future dates (should be valid) ✓

**Dependencies to Mock:**
- `timezone.now()` - current time

---

### 26. `BusySlotForm.clean()`
**Location:** `meetings/forms.py`

**Main Functionality:**
- Validate end time is after start time

**Input Parameters:**
- None

**Expected Return:**
- cleaned_data or raises ValidationError

**Edge Cases:**
- end <= start (invalid)
- end > start (valid)
- Missing times

**Dependencies to Mock:**
- None

---

## Utils

### 27. `generate_time_slots()`
**Location:** `meetings/utils.py`

**Main Functionality:**
- Generate all possible time slots based on meeting request configuration

**Input Parameters:**
- `meeting_request` (MeetingRequest object)

**Expected Return:**
- List of (start_datetime_utc, end_datetime_utc) tuples

**Edge Cases:**
- work_days_only=True (skip weekends)
- work_days_only=False (include weekends)
- Different step sizes (15, 30, 60 minutes)
- Different durations
- Different timezones
- Single day range
- Multi-day range
- No valid slots (duration > work hours)

**Dependencies to Mock:**
- `pytz.timezone()`

---

### 28. `is_participant_available()`
**Location:** `meetings/utils.py`

**Main Functionality:**
- Check if participant is available during a time slot

**Input Parameters:**
- `participant` (Participant object)
- `start_time` (datetime)
- `end_time` (datetime)

**Expected Return:**
- Boolean (True if available, False if busy)

**Edge Cases:**
- No busy slots (available)
- Exact time match (busy)
- Partial overlap (busy)
- Before all busy slots (available)
- After all busy slots (available)
- Between busy slots (available)

**Dependencies to Mock:**
- `BusySlot.objects.filter()`

---

### 29. `calculate_slot_availability()`
**Location:** `meetings/utils.py`

**Main Functionality:**
- Calculate how many participants are available for a time slot

**Input Parameters:**
- `meeting_request` (MeetingRequest object)
- `start_time` (datetime)
- `end_time` (datetime)

**Expected Return:**
- Tuple: (available_count, total_count, participant_ids_available)

**Edge Cases:**
- Zero participants
- All participants available
- No participants available
- Partial availability
- Only responded participants counted

**Dependencies to Mock:**
- `is_participant_available()`
- `Participant.objects.filter()`

---

### 30. `generate_suggested_slots()`
**Location:** `meetings/utils.py`

**Main Functionality:**
- Generate or update suggested slots for meeting request

**Input Parameters:**
- `meeting_request` (MeetingRequest object)
- `force_recalculate` (bool, default=False)

**Expected Return:**
- List of SuggestedSlot objects

**Edge Cases:**
- force_recalculate=True (clear existing)
- force_recalculate=False (keep existing)
- No possible slots
- All slots have zero availability
- Mix of availabilities

**Dependencies to Mock:**
- `generate_time_slots()`
- `calculate_slot_availability()`
- `SuggestedSlot.objects.update_or_create()`

---

### 31. `get_top_suggestions()`
**Location:** `meetings/utils.py`

**Main Functionality:**
- Get top suggested slots sorted by availability

**Input Parameters:**
- `meeting_request` (MeetingRequest object)
- `limit` (int, default=10)
- `min_availability_pct` (int, default=50)

**Expected Return:**
- List of SuggestedSlot objects (filtered and limited)

**Edge Cases:**
- No suggestions
- Fewer suggestions than limit
- More suggestions than limit
- All below min_availability_pct
- All above min_availability_pct
- Edge case: exactly min_availability_pct

**Dependencies to Mock:**
- `SuggestedSlot.objects.filter()`

---

### 32. `get_heatmap_data()`
**Location:** `meetings/utils.py`

**Main Functionality:**
- Generate heatmap data for visualization

**Input Parameters:**
- `meeting_request` (MeetingRequest object)
- `participant_timezone` (string, default='Asia/Ho_Chi_Minh')

**Expected Return:**
- Dict with keys: 'dates', 'time_slots', 'heatmap', 'timezone'

**Edge Cases:**
- No suggested slots (generate from config)
- Existing suggested slots
- Different timezones
- Empty meeting request
- Multiple dates
- Single date

**Dependencies to Mock:**
- `SuggestedSlot.objects.filter()`
- `generate_time_slots()`
- `pytz.timezone()`

---

### 33. `merge_overlapping_busy_slots()`
**Location:** `meetings/utils.py`

**Main Functionality:**
- Merge overlapping busy slots

**Input Parameters:**
- `busy_slots` (list of BusySlot objects)

**Expected Return:**
- List of (start, end) tuples (merged)

**Edge Cases:**
- Empty list
- Single slot
- No overlaps
- Adjacent slots (touching)
- Complete overlaps
- Partial overlaps
- Multiple overlaps in sequence

**Dependencies to Mock:**
- None (pure function)

---

### 34. `format_datetime_for_timezone()`
**Location:** `meetings/utils.py`

**Main Functionality:**
- Format datetime for display in specific timezone

**Input Parameters:**
- `dt` (datetime object)
- `timezone_str` (string)

**Expected Return:**
- String (formatted datetime)

**Edge Cases:**
- Naive datetime
- Aware datetime (UTC)
- Aware datetime (other timezone)
- Different timezone_str values

**Dependencies to Mock:**
- `pytz.timezone()`

---

### 35. `parse_busy_slots_from_json()`
**Location:** `meetings/utils.py`

**Main Functionality:**
- Parse busy slots from JSON format (frontend)

**Input Parameters:**
- `json_data` (list of dicts)
- `participant_timezone` (string)

**Expected Return:**
- List of (start_datetime_utc, end_datetime_utc) tuples

**Edge Cases:**
- Empty list
- Missing 'start' or 'end' keys
- Naive datetimes
- Aware datetimes
- ISO format with 'Z'
- ISO format with timezone
- Invalid datetime format

**Dependencies to Mock:**
- `datetime.fromisoformat()`
- `pytz.timezone()`

---

## Template Tags

### 36. `get_item()`
**Location:** `meetings/templatetags/meeting_filters.py`

**Main Functionality:**
- Get item from dictionary in template

**Input Parameters:**
- `dictionary` (dict or None)
- `key` (any hashable type)

**Expected Return:**
- Value from dictionary or None

**Edge Cases:**
- dictionary is None
- key exists
- key doesn't exist
- Empty dictionary

**Dependencies to Mock:**
- None

---

### 37. `format_date_header()`
**Location:** `meetings/templatetags/meeting_filters.py`

**Main Functionality:**
- Format date string for heatmap header

**Input Parameters:**
- `date_str` (string in 'YYYY-MM-DD' format)

**Expected Return:**
- String (e.g., 'T2 15/1' for Monday, January 15)

**Edge Cases:**
- Valid date string
- Invalid date format
- Different weekdays (Mon-Sun)
- Exception handling (returns original string)

**Dependencies to Mock:**
- `datetime.strptime()`

---

## Summary Statistics

### Total Functions to Test: 37

**By Module:**
- Models: 7 functions
- Views: 17 functions
- Forms: 2 functions
- Utils: 9 functions
- Template Tags: 2 functions

**By Complexity:**
- Simple (< 5 test cases): 12 functions
- Medium (5-10 test cases): 18 functions
- Complex (> 10 test cases): 8 functions

**Priority Levels:**

**High Priority (Critical Business Logic):**
1. `generate_time_slots()` - Core scheduling algorithm
2. `is_participant_available()` - Availability checking
3. `calculate_slot_availability()` - Availability calculation
4. `generate_suggested_slots()` - Suggestion generation
5. `get_top_suggestions()` - Suggestion filtering
6. `MeetingRequestForm.clean()` - Date validation
7. `save_busy_slots()` - API endpoint for saving data
8. `respond_to_request()` - Member response workflow
9. `create_request_step2()` - Participant management with bulk upload

**Medium Priority (Important Features):**
1. `get_heatmap_data()` - Visualization
2. `parse_busy_slots_from_json()` - Data parsing
3. `MeetingRequest.is_active` - Request status
4. `lock_slot()` - Finalization workflow
5. `merge_overlapping_busy_slots()` - Optimization
6. `select_busy_times()` - Busy slot selection interface
7. `view_request()` - Main leader dashboard view

**Low Priority (Simple/Utility Functions):**
1. `get_or_create_creator_id()` - Session management
2. `format_date_header()` - Display formatting
3. `get_item()` - Template helper
4. Properties and simple getters

---

## Testing Strategy Recommendations

### 1. **Models Tests**
- Use Django's `TestCase` for database operations
- Use `freezegun` or similar for time-dependent tests
- Test model validation (clean methods)
- Test property calculations
- Test model relationships

### 2. **Views Tests**
- Use Django's `Client` or `RequestFactory`
- Test authentication/authorization
- Test GET vs POST behaviors
- Test session handling
- Test redirects and status codes
- Mock external dependencies

### 3. **Forms Tests**
- Test form validation
- Test clean methods
- Test widget rendering (if custom)
- Test field initialization
- Mock timezone functions

### 4. **Utils Tests**
- Pure unit tests (minimal mocking)
- Test edge cases thoroughly
- Test timezone conversions carefully
- Use parametrized tests for multiple scenarios
- Focus on algorithm correctness

### 5. **Template Tags Tests**
- Use Django's template testing utilities
- Test with various input types
- Test error handling

### 6. **Integration Tests**
- Test complete workflows (create → respond → suggest)
- Test timezone handling end-to-end
- Test database integrity
- Test API endpoints

### 7. **Coverage Goals**
- Minimum: 80% code coverage
- Target: 90%+ for critical business logic
- 100% for pure utility functions

---

## Recommended Testing Tools

1. **pytest-django** - Better test runner than unittest
2. **factory_boy** - Test data factories
3. **freezegun** - Freeze time for testing
4. **pytest-cov** - Coverage reporting
5. **pytest-mock** - Mocking utilities
6. **hypothesis** - Property-based testing (for complex algorithms)
7. **django-test-plus** - Enhanced Django testing utilities

---

## Next Steps

1. Set up testing infrastructure
2. Create test fixtures/factories for models
3. Start with high-priority functions
4. Implement continuous integration (CI)
5. Set up coverage reporting
6. Create test documentation
7. Regular test maintenance and updates
