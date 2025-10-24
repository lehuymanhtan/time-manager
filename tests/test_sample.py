"""
Sample test to verify testing infrastructure is working.
Run with: pytest tests/test_sample.py -v
"""
import pytest
from django.test import Client
from django.utils import timezone


class TestInfrastructure:
    """Test that the testing infrastructure is set up correctly."""
    
    def test_pytest_working(self):
        """Test that pytest is working."""
        assert True
    
    def test_django_client_available(self, client):
        """Test that Django test client is available."""
        assert isinstance(client, Client)
    
    def test_database_access(self, db):
        """Test that database access is working."""
        from meetings.models import MeetingRequest
        count = MeetingRequest.objects.count()
        assert count >= 0
    
    def test_timezone_utility(self):
        """Test that timezone utilities work."""
        now = timezone.now()
        assert now is not None
        assert now.tzinfo is not None
    
    def test_fixtures_loading(self, tz_vietnam, tz_utc):
        """Test that custom fixtures load correctly."""
        assert tz_vietnam.zone == 'Asia/Ho_Chi_Minh'
        assert tz_utc.zone == 'UTC'


class TestFactories:
    """Test that factory classes work correctly."""
    
    def test_meeting_request_factory(self, db):
        """Test MeetingRequestFactory creates valid objects."""
        from tests.factories import MeetingRequestFactory
        
        meeting = MeetingRequestFactory()
        assert meeting.id is not None
        assert meeting.title
        assert meeting.token
        assert meeting.duration_minutes > 0
    
    def test_participant_factory(self, db):
        """Test ParticipantFactory creates valid objects."""
        from tests.factories import ParticipantFactory
        
        participant = ParticipantFactory()
        assert participant.id is not None
        assert participant.name
        assert participant.meeting_request is not None
    
    def test_participant_without_email_factory(self, db):
        """Test ParticipantWithoutEmailFactory creates participant with NULL email."""
        from tests.factories import ParticipantWithoutEmailFactory
        
        participant = ParticipantWithoutEmailFactory()
        assert participant.id is not None
        assert participant.name
        assert participant.email is None
    
    def test_busy_slot_factory(self, db):
        """Test BusySlotFactory creates valid objects."""
        from tests.factories import BusySlotFactory
        
        busy_slot = BusySlotFactory()
        assert busy_slot.id is not None
        assert busy_slot.start_time < busy_slot.end_time
    
    def test_suggested_slot_factory(self, db):
        """Test SuggestedSlotFactory creates valid objects."""
        from tests.factories import SuggestedSlotFactory
        
        slot = SuggestedSlotFactory()
        assert slot.id is not None
        assert slot.start_time < slot.end_time
        assert slot.available_count >= 0
    
    def test_create_meeting_with_participants_helper(self, db):
        """Test the helper function for creating complete meeting setup."""
        from tests.factories import create_meeting_with_participants
        
        meeting, participants = create_meeting_with_participants(
            num_participants=5,
            num_responded=2,
            include_busy_slots=True
        )
        
        assert meeting.id is not None
        assert len(participants) == 5
        assert sum(1 for p in participants if p.has_responded) == 2


class TestMocking:
    """Test that mocking utilities work correctly."""
    
    def test_mock_now_fixture(self, mock_now, tz_utc):
        """Test that mock_now fixture works."""
        from django.utils import timezone as tz
        
        fake_time = timezone.datetime(2025, 1, 1, 12, 0, 0, tzinfo=tz_utc)
        mock_now(fake_time)
        
        assert tz.now() == fake_time
    
    def test_pytest_mock(self, mocker):
        """Test that pytest-mock is working."""
        mock_func = mocker.Mock(return_value=42)
        assert mock_func() == 42
        mock_func.assert_called_once()


@pytest.mark.slow
class TestMarkers:
    """Test that pytest markers are working."""
    
    def test_slow_marker(self):
        """This test is marked as slow."""
        assert True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
