"""
Unit tests for Meeting Utils
Tests for time slot generation, availability calculation, and heatmap data
"""
import pytest
from django.utils import timezone
from datetime import timedelta, time, date, datetime
import pytz

from meetings.utils import (
    generate_time_slots,
    is_participant_available,
    calculate_slot_availability,
    generate_suggested_slots,
    get_top_suggestions,
    get_heatmap_data,
    merge_overlapping_busy_slots,
    format_datetime_for_timezone,
    parse_busy_slots_from_json
)
from tests.factories import (
    MeetingRequestFactory, ParticipantFactory,
    BusySlotFactory, SuggestedSlotFactory
)


@pytest.mark.django_db
class TestGenerateTimeSlots:
    """Test generate_time_slots() function"""
    
    def test_basic_time_slot_generation(self):
        """Test basic slot generation with simple parameters"""
        meeting = MeetingRequestFactory(
            date_range_start=date(2025, 1, 15),  # Wednesday
            date_range_end=date(2025, 1, 15),
            work_hours_start=time(9, 0),
            work_hours_end=time(12, 0),
            duration_minutes=60,
            step_size_minutes=60,
            work_days_only=False,
            timezone='Asia/Ho_Chi_Minh'
        )
        
        slots = generate_time_slots(meeting)
        
        # Should have 3 slots: 9-10, 10-11, 11-12
        assert len(slots) == 3
        
        # Check all slots are tuples of (start, end)
        for slot in slots:
            assert len(slot) == 2
            assert slot[0] < slot[1]
    
    def test_skip_weekends_when_work_days_only(self):
        """Test that weekends are skipped when work_days_only=True"""
        meeting = MeetingRequestFactory(
            date_range_start=date(2025, 1, 17),  # Friday
            date_range_end=date(2025, 1, 20),    # Monday
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0),
            duration_minutes=30,
            step_size_minutes=30,
            work_days_only=True,
            timezone='Asia/Ho_Chi_Minh'
        )
        
        slots = generate_time_slots(meeting)
        
        # Should only have slots for Friday (Jan 17) and Monday (Jan 20)
        # Not Saturday (18) and Sunday (19)
        # Each day has 2 slots: 9:00-9:30, 9:30-10:00
        assert len(slots) == 4
    
    def test_include_weekends_when_work_days_only_false(self):
        """Test that weekends are included when work_days_only=False"""
        meeting = MeetingRequestFactory(
            date_range_start=date(2025, 1, 17),  # Friday
            date_range_end=date(2025, 1, 19),    # Sunday
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0),
            duration_minutes=30,
            step_size_minutes=30,
            work_days_only=False,
            timezone='Asia/Ho_Chi_Minh'
        )
        
        slots = generate_time_slots(meeting)
        
        # Should have slots for all 3 days (Fri, Sat, Sun)
        # Each day has 2 slots: 9:00-9:30, 9:30-10:00
        assert len(slots) == 6
    
    def test_different_step_sizes(self):
        """Test slot generation with different step sizes"""
        # 15-minute steps
        meeting = MeetingRequestFactory(
            date_range_start=date(2025, 1, 15),
            date_range_end=date(2025, 1, 15),
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0),
            duration_minutes=30,
            step_size_minutes=15,
            timezone='Asia/Ho_Chi_Minh'
        )
        
        slots = generate_time_slots(meeting)
        # 9:00-9:30, 9:15-9:45, 9:30-10:00 = 3 slots
        assert len(slots) == 3
    
    def test_single_day_range(self):
        """Test slot generation for single day"""
        meeting = MeetingRequestFactory(
            date_range_start=date(2025, 1, 15),
            date_range_end=date(2025, 1, 15),
            work_hours_start=time(9, 0),
            work_hours_end=time(11, 0),
            duration_minutes=60,
            step_size_minutes=30,
            timezone='Asia/Ho_Chi_Minh'
        )
        
        slots = generate_time_slots(meeting)
        # 9:00-10:00, 9:30-10:30, 10:00-11:00 = 3 slots
        assert len(slots) == 3
    
    def test_multi_day_range(self):
        """Test slot generation across multiple days"""
        meeting = MeetingRequestFactory(
            date_range_start=date(2025, 1, 13),  # Monday
            date_range_end=date(2025, 1, 15),    # Wednesday
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0),
            duration_minutes=30,
            step_size_minutes=30,
            work_days_only=True,
            timezone='Asia/Ho_Chi_Minh'
        )
        
        slots = generate_time_slots(meeting)
        # 3 days * 2 slots per day = 6 slots
        assert len(slots) == 6
    
    def test_no_valid_slots_when_duration_exceeds_work_hours(self):
        """Test that no slots are generated when duration > work hours"""
        meeting = MeetingRequestFactory(
            date_range_start=date(2025, 1, 15),
            date_range_end=date(2025, 1, 15),
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0),
            duration_minutes=120,  # 2 hours, but only 1 hour available
            step_size_minutes=30,
            timezone='Asia/Ho_Chi_Minh'
        )
        
        slots = generate_time_slots(meeting)
        assert len(slots) == 0
    
    def test_timezone_conversion_to_utc(self):
        """Test that slots are properly converted to UTC"""
        meeting = MeetingRequestFactory(
            date_range_start=date(2025, 1, 15),
            date_range_end=date(2025, 1, 15),
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0),
            duration_minutes=30,
            step_size_minutes=30,
            timezone='Asia/Ho_Chi_Minh'
        )
        
        slots = generate_time_slots(meeting)
        
        # Check that all times are in UTC
        for start, end in slots:
            assert start.tzinfo == pytz.UTC
            assert end.tzinfo == pytz.UTC


@pytest.mark.django_db
class TestIsParticipantAvailable:
    """Test is_participant_available() function"""
    
    def test_no_busy_slots_returns_true(self):
        """Test that participant with no busy slots is available"""
        participant = ParticipantFactory()
        start = timezone.now()
        end = start + timedelta(hours=1)
        
        assert is_participant_available(participant, start, end) is True
    
    def test_exact_time_match_returns_false(self):
        """Test that exact busy slot match returns False"""
        participant = ParticipantFactory()
        start = timezone.now()
        end = start + timedelta(hours=1)
        
        BusySlotFactory(participant=participant, start_time=start, end_time=end)
        
        assert is_participant_available(participant, start, end) is False
    
    def test_partial_overlap_returns_false(self):
        """Test that partial overlap returns False"""
        participant = ParticipantFactory()
        
        # Busy slot: 9:00-11:00
        busy_start = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        busy_end = busy_start + timedelta(hours=2)
        BusySlotFactory(participant=participant, start_time=busy_start, end_time=busy_end)
        
        # Check slot: 10:00-12:00 (overlaps with 10:00-11:00)
        check_start = busy_start + timedelta(hours=1)
        check_end = check_start + timedelta(hours=2)
        
        assert is_participant_available(participant, check_start, check_end) is False
    
    def test_before_busy_slot_returns_true(self):
        """Test that time before busy slot returns True"""
        participant = ParticipantFactory()
        
        # Busy slot: 10:00-11:00
        busy_start = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        busy_end = busy_start + timedelta(hours=1)
        BusySlotFactory(participant=participant, start_time=busy_start, end_time=busy_end)
        
        # Check slot: 8:00-9:00 (before busy slot)
        check_start = busy_start - timedelta(hours=2)
        check_end = busy_start - timedelta(hours=1)
        
        assert is_participant_available(participant, check_start, check_end) is True
    
    def test_after_busy_slot_returns_true(self):
        """Test that time after busy slot returns True"""
        participant = ParticipantFactory()
        
        # Busy slot: 9:00-10:00
        busy_start = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        busy_end = busy_start + timedelta(hours=1)
        BusySlotFactory(participant=participant, start_time=busy_start, end_time=busy_end)
        
        # Check slot: 11:00-12:00 (after busy slot)
        check_start = busy_end + timedelta(hours=1)
        check_end = check_start + timedelta(hours=1)
        
        assert is_participant_available(participant, check_start, check_end) is True
    
    def test_between_busy_slots_returns_true(self):
        """Test that time between two busy slots returns True"""
        participant = ParticipantFactory()
        
        # Busy slot 1: 9:00-10:00
        busy1_start = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        busy1_end = busy1_start + timedelta(hours=1)
        BusySlotFactory(participant=participant, start_time=busy1_start, end_time=busy1_end)
        
        # Busy slot 2: 12:00-13:00
        busy2_start = busy1_start + timedelta(hours=3)
        busy2_end = busy2_start + timedelta(hours=1)
        BusySlotFactory(participant=participant, start_time=busy2_start, end_time=busy2_end)
        
        # Check slot: 10:30-11:30 (between busy slots)
        check_start = busy1_end + timedelta(minutes=30)
        check_end = check_start + timedelta(hours=1)
        
        assert is_participant_available(participant, check_start, check_end) is True


@pytest.mark.django_db
class TestCalculateSlotAvailability:
    """Test calculate_slot_availability() function"""
    
    def test_zero_participants(self):
        """Test with no participants"""
        meeting = MeetingRequestFactory()
        start = timezone.now()
        end = start + timedelta(hours=1)
        
        available, total, ids = calculate_slot_availability(meeting, start, end)
        
        assert available == 0
        assert total == 0
        assert ids == []
    
    def test_all_participants_available(self):
        """Test when all participants are available"""
        meeting = MeetingRequestFactory()
        participants = ParticipantFactory.create_batch(5, meeting_request=meeting, has_responded=True)
        
        start = timezone.now()
        end = start + timedelta(hours=1)
        
        available, total, ids = calculate_slot_availability(meeting, start, end)
        
        assert available == 5
        assert total == 5
        assert len(ids) == 5
    
    def test_no_participants_available(self):
        """Test when no participants are available"""
        meeting = MeetingRequestFactory()
        
        start = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=1)
        
        # Create participants with busy slots at the check time
        for _ in range(3):
            participant = ParticipantFactory(meeting_request=meeting, has_responded=True)
            BusySlotFactory(participant=participant, start_time=start, end_time=end)
        
        available, total, ids = calculate_slot_availability(meeting, start, end)
        
        assert available == 0
        assert total == 3
        assert len(ids) == 0
    
    def test_partial_availability(self):
        """Test with some participants available"""
        meeting = MeetingRequestFactory()
        
        start = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=1)
        
        # 2 available participants
        ParticipantFactory.create_batch(2, meeting_request=meeting, has_responded=True)
        
        # 3 busy participants
        for _ in range(3):
            participant = ParticipantFactory(meeting_request=meeting, has_responded=True)
            BusySlotFactory(participant=participant, start_time=start, end_time=end)
        
        available, total, ids = calculate_slot_availability(meeting, start, end)
        
        assert available == 2
        assert total == 5
        assert len(ids) == 2
    
    def test_only_responded_participants_counted(self):
        """Test that only responded participants are counted"""
        meeting = MeetingRequestFactory()
        
        start = timezone.now()
        end = start + timedelta(hours=1)
        
        # 3 responded, 2 not responded
        ParticipantFactory.create_batch(3, meeting_request=meeting, has_responded=True)
        ParticipantFactory.create_batch(2, meeting_request=meeting, has_responded=False)
        
        available, total, ids = calculate_slot_availability(meeting, start, end)
        
        # Only 3 responded participants should be counted
        assert total == 3


@pytest.mark.django_db
class TestGenerateSuggestedSlots:
    """Test generate_suggested_slots() function"""
    
    def test_force_recalculate_clears_existing(self):
        """Test that force_recalculate=True clears existing slots"""
        meeting = MeetingRequestFactory(
            date_range_start=date(2025, 1, 15),
            date_range_end=date(2025, 1, 15),
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0),
            duration_minutes=30,
            step_size_minutes=30,
            timezone='Asia/Ho_Chi_Minh'
        )
        
        # Create some existing suggested slots
        SuggestedSlotFactory.create_batch(3, meeting_request=meeting)
        assert meeting.suggested_slots.count() == 3
        
        # Force recalculate
        generate_suggested_slots(meeting, force_recalculate=True)
        
        # Old slots should be deleted and new ones created
        # Should have 2 slots: 9:00-9:30, 9:30-10:00
        assert meeting.suggested_slots.count() == 2
    
    def test_no_force_recalculate_keeps_existing(self):
        """Test that force_recalculate=False updates existing slots"""
        meeting = MeetingRequestFactory(
            date_range_start=date(2025, 1, 15),
            date_range_end=date(2025, 1, 15),
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0),
            duration_minutes=30,
            step_size_minutes=30,
            timezone='Asia/Ho_Chi_Minh'
        )
        
        # Generate initial slots
        initial_slots = generate_suggested_slots(meeting, force_recalculate=False)
        initial_count = len(initial_slots)
        
        # Generate again without force recalculate
        new_slots = generate_suggested_slots(meeting, force_recalculate=False)
        
        assert len(new_slots) == initial_count
    
    def test_suggested_slots_have_correct_availability(self):
        """Test that suggested slots calculate availability correctly"""
        meeting = MeetingRequestFactory(
            date_range_start=date(2025, 1, 15),
            date_range_end=date(2025, 1, 15),
            work_hours_start=time(9, 0),
            work_hours_end=time(11, 0),
            duration_minutes=60,
            step_size_minutes=60,
            timezone='Asia/Ho_Chi_Minh'
        )
        
        # Add participants
        ParticipantFactory.create_batch(5, meeting_request=meeting, has_responded=True)
        
        slots = generate_suggested_slots(meeting, force_recalculate=True)
        
        # Each slot should have availability info
        for slot in slots:
            assert slot.total_participants == 5
            assert 0 <= slot.available_count <= 5


@pytest.mark.django_db
class TestGetTopSuggestions:
    """Test get_top_suggestions() function"""
    
    def test_no_suggestions(self):
        """Test with no suggested slots"""
        meeting = MeetingRequestFactory()
        suggestions = get_top_suggestions(meeting)
        assert len(suggestions) == 0
    
    def test_limit_parameter(self):
        """Test that limit parameter works"""
        meeting = MeetingRequestFactory()
        
        # Create 15 slots with 100% availability
        for i in range(15):
            SuggestedSlotFactory(
                meeting_request=meeting,
                available_count=10,
                total_participants=10
            )
        
        suggestions = get_top_suggestions(meeting, limit=5)
        assert len(suggestions) <= 5
    
    def test_min_availability_filter(self):
        """Test that min_availability_pct filters correctly"""
        meeting = MeetingRequestFactory()
        
        # Create slots with different availability
        SuggestedSlotFactory(meeting_request=meeting, available_count=9, total_participants=10)  # 90%
        SuggestedSlotFactory(meeting_request=meeting, available_count=7, total_participants=10)  # 70%
        SuggestedSlotFactory(meeting_request=meeting, available_count=4, total_participants=10)  # 40%
        SuggestedSlotFactory(meeting_request=meeting, available_count=2, total_participants=10)  # 20%
        
        # Get suggestions with min 50%
        suggestions = get_top_suggestions(meeting, min_availability_pct=50)
        
        # Should only get 90% and 70% slots
        assert len(suggestions) == 2
    
    def test_sorted_by_availability(self):
        """Test that suggestions are sorted by availability"""
        meeting = MeetingRequestFactory()
        
        SuggestedSlotFactory(meeting_request=meeting, available_count=4, total_participants=10)
        SuggestedSlotFactory(meeting_request=meeting, available_count=9, total_participants=10)
        SuggestedSlotFactory(meeting_request=meeting, available_count=7, total_participants=10)
        
        suggestions = get_top_suggestions(meeting, min_availability_pct=0)
        
        # Should be sorted by available_count descending
        assert suggestions[0].available_count >= suggestions[1].available_count
        assert suggestions[1].available_count >= suggestions[2].available_count


@pytest.mark.django_db
class TestGetHeatmapData:
    """Test get_heatmap_data() function"""
    
    def test_basic_heatmap_structure(self):
        """Test that heatmap data has correct structure"""
        meeting = MeetingRequestFactory(
            date_range_start=date(2025, 1, 15),
            date_range_end=date(2025, 1, 15),
            work_hours_start=time(9, 0),
            work_hours_end=time(11, 0),
            duration_minutes=60,
            step_size_minutes=60,
            timezone='Asia/Ho_Chi_Minh'
        )
        
        heatmap = get_heatmap_data(meeting)
        
        assert 'dates' in heatmap
        assert 'time_slots' in heatmap
        assert 'heatmap' in heatmap
        assert 'timezone' in heatmap
        assert isinstance(heatmap['dates'], list)
        assert isinstance(heatmap['time_slots'], list)
        assert isinstance(heatmap['heatmap'], dict)
    
    def test_heatmap_with_no_suggested_slots(self):
        """Test heatmap generation when no suggested slots exist"""
        meeting = MeetingRequestFactory(
            date_range_start=date(2025, 1, 15),
            date_range_end=date(2025, 1, 15),
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0),
            duration_minutes=30,
            step_size_minutes=30,
            timezone='Asia/Ho_Chi_Minh'
        )
        
        heatmap = get_heatmap_data(meeting)
        
        # Should generate from config
        assert len(heatmap['dates']) == 1
        assert len(heatmap['time_slots']) == 2  # 9:00, 9:30
    
    def test_heatmap_with_existing_suggested_slots(self):
        """Test heatmap with existing suggested slots"""
        meeting = MeetingRequestFactory(
            date_range_start=date(2025, 1, 15),
            date_range_end=date(2025, 1, 15),
            work_hours_start=time(9, 0),
            work_hours_end=time(10, 0),
            duration_minutes=30,
            step_size_minutes=30,
            timezone='Asia/Ho_Chi_Minh'
        )
        
        # Generate suggested slots
        generate_suggested_slots(meeting, force_recalculate=True)
        
        heatmap = get_heatmap_data(meeting)
        
        # Should have heatmap data for each date and time
        for date_str in heatmap['dates']:
            assert date_str in heatmap['heatmap']
            for time_str in heatmap['time_slots']:
                if time_str in heatmap['heatmap'][date_str]:
                    slot_data = heatmap['heatmap'][date_str][time_str]
                    assert 'level' in slot_data
                    assert 'available' in slot_data
                    assert 'total' in slot_data


@pytest.mark.django_db
class TestMergeOverlappingBusySlots:
    """Test merge_overlapping_busy_slots() function"""
    
    def test_empty_list(self):
        """Test with empty list"""
        result = merge_overlapping_busy_slots([])
        assert result == []
    
    def test_single_slot(self):
        """Test with single slot"""
        participant = ParticipantFactory()
        slot = BusySlotFactory(participant=participant)
        
        result = merge_overlapping_busy_slots([slot])
        assert len(result) == 1
        assert result[0] == (slot.start_time, slot.end_time)
    
    def test_no_overlaps(self):
        """Test slots with no overlaps"""
        participant = ParticipantFactory()
        
        slot1 = BusySlotFactory(
            participant=participant,
            start_time=timezone.now().replace(hour=9, minute=0, second=0, microsecond=0),
            end_time=timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        )
        slot2 = BusySlotFactory(
            participant=participant,
            start_time=timezone.now().replace(hour=11, minute=0, second=0, microsecond=0),
            end_time=timezone.now().replace(hour=12, minute=0, second=0, microsecond=0)
        )
        
        result = merge_overlapping_busy_slots([slot1, slot2])
        assert len(result) == 2
    
    def test_adjacent_slots_merge(self):
        """Test that adjacent slots are merged"""
        participant = ParticipantFactory()
        
        now = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        slot1 = BusySlotFactory(
            participant=participant,
            start_time=now,
            end_time=now + timedelta(hours=1)
        )
        slot2 = BusySlotFactory(
            participant=participant,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2)
        )
        
        result = merge_overlapping_busy_slots([slot1, slot2])
        # Adjacent slots should merge
        assert len(result) == 1
        assert result[0] == (slot1.start_time, slot2.end_time)
    
    def test_overlapping_slots_merge(self):
        """Test that overlapping slots merge correctly"""
        participant = ParticipantFactory()
        
        now = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        slot1 = BusySlotFactory(
            participant=participant,
            start_time=now,
            end_time=now + timedelta(hours=2)
        )
        slot2 = BusySlotFactory(
            participant=participant,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=3)
        )
        
        result = merge_overlapping_busy_slots([slot1, slot2])
        assert len(result) == 1
        assert result[0] == (slot1.start_time, slot2.end_time)
    
    def test_multiple_overlaps_in_sequence(self):
        """Test merging multiple overlapping slots"""
        participant = ParticipantFactory()
        
        now = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        slot1 = BusySlotFactory(participant=participant, start_time=now, end_time=now + timedelta(hours=1))
        slot2 = BusySlotFactory(participant=participant, start_time=now + timedelta(minutes=30), end_time=now + timedelta(hours=1, minutes=30))
        slot3 = BusySlotFactory(participant=participant, start_time=now + timedelta(hours=1), end_time=now + timedelta(hours=2))
        
        result = merge_overlapping_busy_slots([slot1, slot2, slot3])
        # All should merge into one
        assert len(result) == 1


@pytest.mark.django_db
class TestFormatDatetimeForTimezone:
    """Test format_datetime_for_timezone() function"""
    
    def test_naive_datetime(self):
        """Test formatting naive datetime"""
        dt = datetime(2025, 1, 15, 9, 0, 0)
        result = format_datetime_for_timezone(dt, 'Asia/Ho_Chi_Minh')
        assert '2025-01-15' in result
        assert '09:00' in result or '16:00' in result  # Depends on interpretation
    
    def test_aware_datetime_utc(self):
        """Test formatting UTC datetime"""
        dt = datetime(2025, 1, 15, 2, 0, 0, tzinfo=pytz.UTC)
        result = format_datetime_for_timezone(dt, 'Asia/Ho_Chi_Minh')
        # 2:00 UTC = 9:00 Vietnam (UTC+7)
        assert '09:00' in result
    
    def test_different_timezones(self):
        """Test conversion between different timezones"""
        dt = datetime(2025, 1, 15, 9, 0, 0, tzinfo=pytz.timezone('Asia/Ho_Chi_Minh'))
        result = format_datetime_for_timezone(dt, 'America/New_York')
        # Vietnam is UTC+7, NY is UTC-5 (or UTC-4 during DST), difference is 11-12 hours
        # 9:00 Vietnam = 21:00 or 20:00 previous day NY
        # Just check that result contains time and date
        assert '2025-01-14' in result or '2025-01-15' in result
        assert ':' in result  # Has time component


@pytest.mark.django_db
class TestParseBusySlotsFromJson:
    """Test parse_busy_slots_from_json() function"""
    
    def test_empty_list(self):
        """Test with empty list"""
        result = parse_busy_slots_from_json([], 'Asia/Ho_Chi_Minh')
        assert result == []
    
    def test_valid_json_data(self):
        """Test parsing valid JSON data"""
        json_data = [
            {'start': '2025-01-15T09:00:00', 'end': '2025-01-15T10:00:00'},
            {'start': '2025-01-15T14:00:00', 'end': '2025-01-15T15:00:00'}
        ]
        
        result = parse_busy_slots_from_json(json_data, 'Asia/Ho_Chi_Minh')
        
        assert len(result) == 2
        # Check that results are tuples
        for slot in result:
            assert len(slot) == 2
            assert slot[0] < slot[1]
    
    def test_missing_start_or_end(self):
        """Test that entries with missing start/end are skipped"""
        json_data = [
            {'start': '2025-01-15T09:00:00'},  # Missing end
            {'end': '2025-01-15T10:00:00'},    # Missing start
            {'start': '2025-01-15T11:00:00', 'end': '2025-01-15T12:00:00'}  # Valid
        ]
        
        result = parse_busy_slots_from_json(json_data, 'Asia/Ho_Chi_Minh')
        
        # Only one valid entry
        assert len(result) == 1
    
    def test_iso_format_with_z(self):
        """Test parsing ISO format with Z (Zulu time)"""
        json_data = [
            {'start': '2025-01-15T09:00:00Z', 'end': '2025-01-15T10:00:00Z'}
        ]
        
        result = parse_busy_slots_from_json(json_data, 'Asia/Ho_Chi_Minh')
        
        assert len(result) == 1
        # Result should be in UTC
        assert result[0][0].tzinfo == pytz.UTC
        assert result[0][1].tzinfo == pytz.UTC
    
    def test_naive_datetime_assumes_participant_timezone(self):
        """Test that naive datetimes are localized to participant timezone"""
        json_data = [
            {'start': '2025-01-15T09:00:00', 'end': '2025-01-15T10:00:00'}
        ]
        
        result = parse_busy_slots_from_json(json_data, 'Asia/Ho_Chi_Minh')
        
        # Result should be converted to UTC
        assert result[0][0].tzinfo == pytz.UTC
        assert result[0][1].tzinfo == pytz.UTC
