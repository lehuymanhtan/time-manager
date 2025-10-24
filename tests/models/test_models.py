"""
Unit tests for Meeting Models
Tests for MeetingRequest, Participant, BusySlot, and SuggestedSlot models
"""
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import secrets

from meetings.models import MeetingRequest, Participant, BusySlot, SuggestedSlot
from tests.factories import (
    MeetingRequestFactory, ParticipantFactory, 
    BusySlotFactory, SuggestedSlotFactory
)


@pytest.mark.django_db
class TestMeetingRequestSave:
    """Test MeetingRequest.save() method"""
    
    def test_auto_generate_token_on_save(self):
        """Test that token is auto-generated if not present"""
        meeting = MeetingRequestFactory.build(token='')
        meeting.save()
        assert meeting.token != ''
        assert len(meeting.token) > 0
    
    def test_token_already_exists(self):
        """Test that existing token is not overwritten"""
        existing_token = secrets.token_urlsafe(32)
        meeting = MeetingRequestFactory(token=existing_token)
        meeting.save()
        assert meeting.token == existing_token
    
    def test_multiple_saves_same_object(self):
        """Test that token remains same after multiple saves"""
        meeting = MeetingRequestFactory()
        original_token = meeting.token
        meeting.title = "Updated Title"
        meeting.save()
        assert meeting.token == original_token


@pytest.mark.django_db
class TestMeetingRequestIsActive:
    """Test MeetingRequest.is_active property"""
    
    def test_status_not_active(self):
        """Test that non-active status returns False"""
        meeting = MeetingRequestFactory(status='draft')
        assert meeting.is_active is False
        
        meeting.status = 'locked'
        assert meeting.is_active is False
        
        meeting.status = 'cancelled'
        assert meeting.is_active is False
    
    def test_deadline_is_none(self):
        """Test that None deadline with active status returns True"""
        meeting = MeetingRequestFactory(
            status='active',
            response_deadline=None
        )
        assert meeting.is_active is True
    
    def test_deadline_in_future(self):
        """Test that future deadline returns True"""
        future_time = timezone.now() + timedelta(days=5)
        meeting = MeetingRequestFactory(
            status='active',
            response_deadline=future_time
        )
        assert meeting.is_active is True
    
    def test_deadline_in_past(self):
        """Test that past deadline returns False"""
        past_time = timezone.now() - timedelta(days=1)
        meeting = MeetingRequestFactory(
            status='active',
            response_deadline=past_time
        )
        assert meeting.is_active is False
    
    def test_deadline_exactly_now(self):
        """Test that deadline exactly at current time returns False"""
        # Since the check is >, a deadline exactly at now should return False
        # But due to timing, we use a slightly past deadline
        now = timezone.now()
        meeting = MeetingRequestFactory(
            status='active',
            response_deadline=now - timedelta(microseconds=1)
        )
        assert meeting.is_active is False


@pytest.mark.django_db
class TestMeetingRequestResponseRate:
    """Test MeetingRequest.response_rate property"""
    
    def test_zero_participants(self):
        """Test that zero participants returns 0"""
        meeting = MeetingRequestFactory()
        assert meeting.response_rate == 0
    
    def test_no_responses(self):
        """Test that no responses returns 0"""
        meeting = MeetingRequestFactory()
        ParticipantFactory.create_batch(5, meeting_request=meeting, has_responded=False)
        assert meeting.response_rate == 0
    
    def test_all_responded(self):
        """Test that all responses returns 100"""
        meeting = MeetingRequestFactory()
        ParticipantFactory.create_batch(5, meeting_request=meeting, has_responded=True)
        assert meeting.response_rate == 100
    
    def test_partial_responses(self):
        """Test calculation with partial responses"""
        meeting = MeetingRequestFactory()
        # 3 responded out of 5 = 60%
        ParticipantFactory.create_batch(3, meeting_request=meeting, has_responded=True)
        ParticipantFactory.create_batch(2, meeting_request=meeting, has_responded=False)
        assert meeting.response_rate == 60
    
    def test_rounded_percentage(self):
        """Test that percentage is properly rounded"""
        meeting = MeetingRequestFactory()
        # 2 out of 3 = 66.666... should round to 67
        ParticipantFactory.create_batch(2, meeting_request=meeting, has_responded=True)
        ParticipantFactory.create_batch(1, meeting_request=meeting, has_responded=False)
        assert meeting.response_rate == 67


@pytest.mark.django_db
class TestMeetingRequestGetShareUrl:
    """Test MeetingRequest.get_share_url() method"""
    
    def test_get_share_url(self):
        """Test that share URL is correctly generated"""
        meeting = MeetingRequestFactory()
        expected_url = f"/r/{meeting.id}?t={meeting.token}"
        assert meeting.get_share_url() == expected_url
    
    def test_share_url_includes_uuid(self):
        """Test that UUID is in the share URL"""
        meeting = MeetingRequestFactory()
        url = meeting.get_share_url()
        assert str(meeting.id) in url
    
    def test_share_url_includes_token(self):
        """Test that token is in the share URL"""
        meeting = MeetingRequestFactory()
        url = meeting.get_share_url()
        assert meeting.token in url


@pytest.mark.django_db
class TestBusySlotClean:
    """Test BusySlot.clean() validation"""
    
    def test_start_time_equals_end_time(self):
        """Test that equal start and end times raise ValidationError"""
        time = timezone.now()
        busy_slot = BusySlotFactory.build(start_time=time, end_time=time)
        with pytest.raises(ValidationError):
            busy_slot.clean()
    
    def test_start_time_after_end_time(self):
        """Test that start > end raises ValidationError"""
        start = timezone.now()
        end = start - timedelta(hours=1)
        busy_slot = BusySlotFactory.build(start_time=start, end_time=end)
        with pytest.raises(ValidationError):
            busy_slot.clean()
    
    def test_start_time_before_end_time(self):
        """Test that start < end is valid"""
        start = timezone.now()
        end = start + timedelta(hours=1)
        busy_slot = BusySlotFactory.build(start_time=start, end_time=end)
        # Should not raise exception
        busy_slot.clean()


@pytest.mark.django_db
class TestSuggestedSlotAvailabilityPercentage:
    """Test SuggestedSlot.availability_percentage property"""
    
    def test_zero_total_participants(self):
        """Test that zero total returns 0"""
        slot = SuggestedSlotFactory(available_count=0, total_participants=0)
        assert slot.availability_percentage == 0
    
    def test_all_available(self):
        """Test that all available returns 100"""
        slot = SuggestedSlotFactory(available_count=10, total_participants=10)
        assert slot.availability_percentage == 100.0
    
    def test_no_available(self):
        """Test that none available returns 0"""
        slot = SuggestedSlotFactory(available_count=0, total_participants=10)
        assert slot.availability_percentage == 0.0
    
    def test_partial_availability(self):
        """Test partial availability calculation"""
        slot = SuggestedSlotFactory(available_count=7, total_participants=10)
        assert slot.availability_percentage == 70.0
    
    def test_rounded_to_one_decimal(self):
        """Test that percentage is rounded to 1 decimal place"""
        slot = SuggestedSlotFactory(available_count=2, total_participants=3)
        # 2/3 = 66.666... should round to 66.7
        assert slot.availability_percentage == 66.7


@pytest.mark.django_db
class TestSuggestedSlotHeatmapLevel:
    """Test SuggestedSlot.heatmap_level property"""
    
    def test_zero_percent_returns_level_0(self):
        """Test 0% availability returns level 0"""
        slot = SuggestedSlotFactory(available_count=0, total_participants=10)
        assert slot.heatmap_level == 0
    
    def test_low_percent_returns_level_1(self):
        """Test 1-19% returns level 1"""
        slot = SuggestedSlotFactory(available_count=1, total_participants=10)
        assert slot.heatmap_level == 1
        
        slot = SuggestedSlotFactory(available_count=19, total_participants=100)
        assert slot.heatmap_level == 1
    
    def test_medium_low_returns_level_2(self):
        """Test 20-39% returns level 2"""
        slot = SuggestedSlotFactory(available_count=2, total_participants=10)
        assert slot.heatmap_level == 2
        
        slot = SuggestedSlotFactory(available_count=39, total_participants=100)
        assert slot.heatmap_level == 2
    
    def test_medium_returns_level_3(self):
        """Test 40-59% returns level 3"""
        slot = SuggestedSlotFactory(available_count=4, total_participants=10)
        assert slot.heatmap_level == 3
        
        slot = SuggestedSlotFactory(available_count=59, total_participants=100)
        assert slot.heatmap_level == 3
    
    def test_medium_high_returns_level_4(self):
        """Test 60-79% returns level 4"""
        slot = SuggestedSlotFactory(available_count=6, total_participants=10)
        assert slot.heatmap_level == 4
        
        slot = SuggestedSlotFactory(available_count=79, total_participants=100)
        assert slot.heatmap_level == 4
    
    def test_high_returns_level_5(self):
        """Test 80%+ returns level 5"""
        slot = SuggestedSlotFactory(available_count=8, total_participants=10)
        assert slot.heatmap_level == 5
        
        slot = SuggestedSlotFactory(available_count=100, total_participants=100)
        assert slot.heatmap_level == 5
    
    def test_edge_values(self):
        """Test exact boundary values"""
        # Exactly 20%
        slot = SuggestedSlotFactory(available_count=20, total_participants=100)
        assert slot.heatmap_level == 2
        
        # Exactly 40%
        slot = SuggestedSlotFactory(available_count=40, total_participants=100)
        assert slot.heatmap_level == 3
        
        # Exactly 60%
        slot = SuggestedSlotFactory(available_count=60, total_participants=100)
        assert slot.heatmap_level == 4
        
        # Exactly 80%
        slot = SuggestedSlotFactory(available_count=80, total_participants=100)
        assert slot.heatmap_level == 5
