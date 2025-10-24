"""
Unit tests for Meeting Views
Tests for Leader and Member workflow views
"""
import pytest
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.contrib.messages import get_messages
from datetime import timedelta
import json
import uuid

from meetings.models import MeetingRequest, Participant, BusySlot, SuggestedSlot
from meetings.views import get_or_create_creator_id
from tests.factories import (
    MeetingRequestFactory, ParticipantFactory,
    BusySlotFactory, SuggestedSlotFactory
)


@pytest.mark.django_db
class TestGetOrCreateCreatorId:
    """Test get_or_create_creator_id() helper function"""
    
    def test_session_has_existing_creator_id(self, request_factory):
        """Test that existing creator_id is returned"""
        request = request_factory.get('/')
        request.session = {'creator_id': 'existing-id-123'}
        
        creator_id = get_or_create_creator_id(request)
        assert creator_id == 'existing-id-123'
    
    def test_session_has_no_creator_id(self, request_factory):
        """Test that new creator_id is created and stored"""
        request = request_factory.get('/')
        request.session = {}
        
        creator_id = get_or_create_creator_id(request)
        
        assert creator_id != ''
        assert len(creator_id) > 0
        assert request.session['creator_id'] == creator_id
    
    def test_empty_session(self, request_factory):
        """Test with completely empty session"""
        request = request_factory.get('/')
        request.session = {}
        
        creator_id = get_or_create_creator_id(request)
        assert creator_id is not None


@pytest.mark.django_db
class TestHomeView:
    """Test home() view"""
    
    def test_home_get_request(self, client):
        """Test GET request to home page"""
        response = client.get('/')
        assert response.status_code == 200
        assert 'meetings/home.html' in [t.name for t in response.templates]
    
    def test_home_renders_correctly(self, client):
        """Test that home page renders without errors"""
        response = client.get('/')
        assert response.status_code == 200
        assert response.content is not None


@pytest.mark.django_db
class TestDashboardView:
    """Test dashboard() view"""
    
    def test_dashboard_with_no_meetings(self, client):
        """Test dashboard with no meeting requests"""
        response = client.get('/dashboard/')
        assert response.status_code == 200
        assert 'requests' in response.context
        assert len(response.context['requests']) == 0
    
    def test_dashboard_with_meetings(self, client):
        """Test dashboard showing user's meetings"""
        # Create session with creator_id
        session = client.session
        creator_id = str(uuid.uuid4())
        session['creator_id'] = creator_id
        session.save()
        
        # Create meeting requests
        MeetingRequestFactory.create_batch(3, creator_id=creator_id)
        
        response = client.get('/dashboard/')
        assert response.status_code == 200
        assert len(response.context['requests']) == 3
    
    def test_dashboard_shows_response_statistics(self, client):
        """Test that response statistics are calculated"""
        session = client.session
        creator_id = str(uuid.uuid4())
        session['creator_id'] = creator_id
        session.save()
        
        meeting = MeetingRequestFactory(creator_id=creator_id)
        ParticipantFactory.create_batch(3, meeting_request=meeting, has_responded=True)
        ParticipantFactory.create_batch(2, meeting_request=meeting, has_responded=False)
        
        response = client.get('/dashboard/')
        assert response.status_code == 200
        meeting_in_context = response.context['requests'][0]
        assert meeting_in_context.responded_count == 3
        assert meeting_in_context.total_count == 5


@pytest.mark.django_db
class TestCreateRequestStep1:
    """Test create_request_step1() view"""
    
    def test_step1_get_shows_form(self, client):
        """Test GET request shows form"""
        response = client.get('/create/step1/')
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_step1_post_valid_data(self, client):
        """Test POST with valid data creates meeting and redirects"""
        today = timezone.now().date()
        data = {
            'title': 'Test Meeting',
            'description': 'Test Description',
            'duration_minutes': 60,
            'timezone': 'Asia/Ho_Chi_Minh',
            'date_range_start': today + timedelta(days=1),
            'date_range_end': today + timedelta(days=7),
            'work_hours_start': '09:00',
            'work_hours_end': '17:00',
            'step_size_minutes': 30,
            'work_days_only': True,
            'response_deadline': (timezone.now() + timedelta(days=5)).strftime('%Y-%m-%dT%H:%M'),
            'created_by_email': 'test@example.com'
        }
        
        response = client.post('/create/step1/', data)
        assert response.status_code == 302  # Redirect
        assert '/create/step2/' in response.url
        
        # Check meeting was created
        assert MeetingRequest.objects.filter(title='Test Meeting').exists()
    
    def test_step1_post_invalid_data(self, client):
        """Test POST with invalid data shows errors"""
        data = {
            'title': 'Test Meeting',
            # Missing required fields
        }
        
        response = client.post('/create/step1/', data)
        assert response.status_code == 200  # Stays on same page
        assert 'form' in response.context
        assert not response.context['form'].is_valid()
    
    def test_step1_stores_meeting_id_in_session(self, client):
        """Test that meeting ID is stored in session"""
        today = timezone.now().date()
        data = {
            'title': 'Test Meeting',
            'duration_minutes': 60,
            'timezone': 'Asia/Ho_Chi_Minh',
            'date_range_start': today + timedelta(days=1),
            'date_range_end': today + timedelta(days=7),
            'work_hours_start': '09:00',
            'work_hours_end': '17:00',
            'step_size_minutes': 30,
            'work_days_only': True,
        }
        
        response = client.post('/create/step1/', data)
        assert 'meeting_request_id' in client.session


@pytest.mark.django_db
class TestCreateRequestStep2:
    """Test create_request_step2() view"""
    
    def test_step2_without_meeting_id_redirects(self, client):
        """Test that step2 without meeting_id redirects to step1"""
        response = client.get('/create/step2/')
        assert response.status_code == 302
        assert '/create/step1/' in response.url
    
    def test_step2_add_single_participant(self, client):
        """Test adding single participant"""
        meeting = MeetingRequestFactory()
        session = client.session
        session['meeting_request_id'] = str(meeting.id)
        session.save()
        
        data = {
            'action': 'add_participant',
            'name': 'John Doe',
            'email': 'john@example.com',
            'timezone': 'Asia/Ho_Chi_Minh'
        }
        
        response = client.post('/create/step2/', data)
        assert response.status_code == 302
        assert Participant.objects.filter(email='john@example.com').exists()
    
    def test_step2_add_bulk_participants(self, client):
        """Test adding multiple participants at once"""
        meeting = MeetingRequestFactory()
        session = client.session
        session['meeting_request_id'] = str(meeting.id)
        session.save()
        
        bulk_data = """John Doe, john@example.com
Jane Smith, jane@example.com
Bob Wilson, bob@example.com"""
        
        data = {
            'action': 'add_bulk',
            'participants_data': bulk_data
        }
        
        response = client.post('/create/step2/', data)
        assert Participant.objects.filter(meeting_request=meeting).count() == 3
    
    def test_step2_skip_to_step3(self, client):
        """Test skipping participant addition"""
        meeting = MeetingRequestFactory()
        session = client.session
        session['meeting_request_id'] = str(meeting.id)
        session.save()
        
        data = {'action': 'skip'}
        
        response = client.post('/create/step2/', data)
        assert response.status_code == 302
        assert '/create/step3/' in response.url
    
    def test_step2_participant_without_email(self, client):
        """Test adding participant without email (NULL)"""
        meeting = MeetingRequestFactory()
        session = client.session
        session['meeting_request_id'] = str(meeting.id)
        session.save()
        
        bulk_data = "Anonymous User,"
        
        data = {
            'action': 'add_bulk',
            'participants_data': bulk_data
        }
        
        response = client.post('/create/step2/', data)
        # Should create participant with NULL email
        assert Participant.objects.filter(meeting_request=meeting, email=None).exists()


@pytest.mark.django_db
class TestCreateRequestStep3:
    """Test create_request_step3() view"""
    
    def test_step3_without_meeting_id_redirects(self, client):
        """Test that step3 without meeting_id redirects to step1"""
        response = client.get('/create/step3/')
        assert response.status_code == 302
    
    def test_step3_get_shows_preview(self, client):
        """Test GET request shows preview"""
        meeting = MeetingRequestFactory()
        session = client.session
        session['meeting_request_id'] = str(meeting.id)
        session.save()
        
        response = client.get('/create/step3/')
        assert response.status_code == 200
        assert 'meeting_request' in response.context
        assert 'heatmap_data' in response.context
    
    def test_step3_post_finalizes_request(self, client):
        """Test POST request finalizes and redirects"""
        meeting = MeetingRequestFactory(status='draft')
        session = client.session
        session['meeting_request_id'] = str(meeting.id)
        session.save()
        
        response = client.post('/create/step3/', {})
        assert response.status_code == 302
        
        # Check status was updated
        meeting.refresh_from_db()
        assert meeting.status == 'active'
        
        # Check session was cleared
        assert 'meeting_request_id' not in client.session


@pytest.mark.django_db
class TestRequestCreatedView:
    """Test request_created() view"""
    
    def test_request_created_shows_share_url(self, client):
        """Test that success page shows share URL"""
        meeting = MeetingRequestFactory()
        
        # URLs might not be configured, test the view function directly
        from meetings.views import request_created
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get(f'/request/{meeting.id}/created/')
        response = request_created(request, meeting.id)
        
        assert response.status_code == 200
        # Check that the token is in the response (part of share URL)
        assert meeting.token.encode() in response.content or meeting.token in response.content.decode('utf-8')


@pytest.mark.django_db
class TestViewRequestView:
    """Test view_request() view"""
    
    def test_view_request_shows_details(self, client):
        """Test that view request shows all details"""
        meeting = MeetingRequestFactory()
        ParticipantFactory.create_batch(5, meeting_request=meeting, has_responded=True)
        
        response = client.get(f'/request/{meeting.id}/')
        assert response.status_code == 200
        assert 'meeting_request' in response.context
        assert 'participants' in response.context
        assert 'heatmap_data' in response.context
    
    def test_view_request_regenerates_suggestions(self, client):
        """Test that viewing request regenerates suggestions"""
        meeting = MeetingRequestFactory()
        
        response = client.get(f'/request/{meeting.id}/')
        assert response.status_code == 200
        
        # Check that suggestions were generated
        assert SuggestedSlot.objects.filter(meeting_request=meeting).exists()
    
    def test_view_request_locked_status(self, client):
        """Test viewing locked request shows locked slot"""
        meeting = MeetingRequestFactory(status='locked')
        locked_slot = SuggestedSlotFactory(meeting_request=meeting, is_locked=True)
        
        response = client.get(f'/request/{meeting.id}/')
        assert response.status_code == 200
        assert locked_slot in response.context['top_suggestions']


@pytest.mark.django_db
class TestLockSlotView:
    """Test lock_slot() view"""
    
    def test_lock_slot_updates_status(self, client):
        """Test that locking slot updates meeting status"""
        meeting = MeetingRequestFactory(status='active')
        slot = SuggestedSlotFactory(meeting_request=meeting)
        
        response = client.get(f'/request/{meeting.id}/lock/{slot.id}/')
        
        meeting.refresh_from_db()
        assert meeting.status == 'locked'
        
        slot.refresh_from_db()
        assert slot.is_locked is True
    
    def test_lock_slot_deletes_other_slots(self, client):
        """Test that locking deletes other suggested slots"""
        meeting = MeetingRequestFactory()
        slot1 = SuggestedSlotFactory(meeting_request=meeting)
        slot2 = SuggestedSlotFactory(meeting_request=meeting)
        slot3 = SuggestedSlotFactory(meeting_request=meeting)
        
        response = client.get(f'/request/{meeting.id}/lock/{slot1.id}/')
        
        # Only slot1 should remain
        assert SuggestedSlot.objects.filter(meeting_request=meeting).count() == 1
        assert SuggestedSlot.objects.filter(id=slot1.id).exists()


@pytest.mark.django_db
class TestEditRequestView:
    """Test edit_request() view"""
    
    def test_edit_request_ownership_verification(self, client):
        """Test that only owner can edit"""
        meeting = MeetingRequestFactory(creator_id='different-creator')
        
        response = client.get(f'/request/{meeting.id}/edit/')
        assert response.status_code == 403
    
    def test_edit_request_get_shows_form(self, client):
        """Test GET request shows form"""
        session = client.session
        creator_id = str(uuid.uuid4())
        session['creator_id'] = creator_id
        session.save()
        
        meeting = MeetingRequestFactory(creator_id=creator_id)
        
        response = client.get(f'/request/{meeting.id}/edit/')
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_edit_request_post_valid_data(self, client):
        """Test POST with valid data updates meeting"""
        session = client.session
        creator_id = str(uuid.uuid4())
        session['creator_id'] = creator_id
        session.save()
        
        meeting = MeetingRequestFactory(creator_id=creator_id, title='Old Title')
        
        today = timezone.now().date()
        data = {
            'title': 'New Title',
            'duration_minutes': 60,
            'timezone': 'Asia/Ho_Chi_Minh',
            'date_range_start': today + timedelta(days=1),
            'date_range_end': today + timedelta(days=7),
            'work_hours_start': '09:00',
            'work_hours_end': '17:00',
            'step_size_minutes': 30,
            'work_days_only': True,
        }
        
        response = client.post(f'/request/{meeting.id}/edit/', data)
        
        meeting.refresh_from_db()
        assert meeting.title == 'New Title'


@pytest.mark.django_db
class TestRespondToRequestView:
    """Test respond_to_request() view"""
    
    def test_respond_invalid_token(self, client):
        """Test that invalid token returns 403"""
        meeting = MeetingRequestFactory()
        
        response = client.get(f'/r/{meeting.id}/?t=invalid-token')
        assert response.status_code == 403
    
    def test_respond_inactive_request(self, client):
        """Test that inactive request shows closed page"""
        past_time = timezone.now() - timedelta(days=1)
        meeting = MeetingRequestFactory(
            status='active',
            response_deadline=past_time
        )
        
        # URLs might not be configured, test the view function directly
        from meetings.views import respond_to_request
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get(f'/r/{meeting.id}/?t={meeting.token}')
        request.session = {}
        response = respond_to_request(request, meeting.id)
        
        assert response.status_code == 200
        # Check that it shows the closed message (in Vietnamese)
        content_str = response.content.decode('utf-8')
        assert 'đóng' in content_str.lower() or 'closed' in content_str.lower()
    
    def test_respond_get_shows_form(self, client):
        """Test GET request shows response form"""
        meeting = MeetingRequestFactory()
        
        response = client.get(f'/r/{meeting.id}/?t={meeting.token}')
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_respond_post_creates_participant_with_email(self, client):
        """Test POST creates participant with email"""
        meeting = MeetingRequestFactory()
        
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'timezone': 'Asia/Ho_Chi_Minh'
        }
        
        response = client.post(f'/r/{meeting.id}/?t={meeting.token}', data)
        
        assert Participant.objects.filter(email='test@example.com').exists()
        assert response.status_code == 302  # Redirect to select busy times
    
    def test_respond_post_creates_participant_without_email(self, client):
        """Test POST creates participant without email (NULL)"""
        meeting = MeetingRequestFactory()
        
        data = {
            'name': 'Anonymous User',
            'email': '',  # Empty string should convert to NULL
            'timezone': 'Asia/Ho_Chi_Minh'
        }
        
        response = client.post(f'/r/{meeting.id}/?t={meeting.token}', data)
        
        # Should create participant with NULL email
        assert Participant.objects.filter(
            meeting_request=meeting,
            name='Anonymous User',
            email=None
        ).exists()


@pytest.mark.django_db
class TestSaveBusySlotsView:
    """Test save_busy_slots() API endpoint"""
    
    def test_save_busy_slots_no_participant_in_session(self, client):
        """Test that request without participant returns 400"""
        meeting = MeetingRequestFactory()
        
        # Test the view function directly
        from meetings.views import save_busy_slots
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.post(
            f'/r/{meeting.id}/save-slots/',
            data=json.dumps({'busy_slots': []}),
            content_type='application/json'
        )
        request.session = {}  # No participant in session
        
        response = save_busy_slots(request, meeting.id)
        assert response.status_code == 400
    
    def test_save_busy_slots_valid_data(self, client):
        """Test saving valid busy slots"""
        meeting = MeetingRequestFactory()
        participant = ParticipantFactory(meeting_request=meeting)
        
        # Test the view function directly
        from meetings.views import save_busy_slots
        from django.test import RequestFactory
        
        busy_slots_data = [
            {
                'start': '2025-01-15T09:00:00',
                'end': '2025-01-15T10:00:00'
            }
        ]
        
        factory = RequestFactory()
        request = factory.post(
            f'/r/{meeting.id}/save-slots/',
            data=json.dumps({'busy_slots': busy_slots_data}),
            content_type='application/json'
        )
        request.session = {f'participant_{meeting.id}': str(participant.id)}
        
        response = save_busy_slots(request, meeting.id)
        
        assert response.status_code == 200
        assert BusySlot.objects.filter(participant=participant).exists()
        
        participant.refresh_from_db()
        assert participant.has_responded is True
    
    def test_save_busy_slots_clears_existing(self, client):
        """Test that saving clears existing busy slots"""
        meeting = MeetingRequestFactory()
        participant = ParticipantFactory(meeting_request=meeting)
        
        # Create existing busy slots
        BusySlotFactory.create_batch(3, participant=participant)
        assert BusySlot.objects.filter(participant=participant).count() == 3
        
        # Test the view function directly
        from meetings.views import save_busy_slots
        from django.test import RequestFactory
        
        busy_slots_data = [
            {
                'start': '2025-01-15T09:00:00',
                'end': '2025-01-15T10:00:00'
            }
        ]
        
        factory = RequestFactory()
        request = factory.post(
            f'/r/{meeting.id}/save-slots/',
            data=json.dumps({'busy_slots': busy_slots_data}),
            content_type='application/json'
        )
        request.session = {f'participant_{meeting.id}': str(participant.id)}
        
        response = save_busy_slots(request, meeting.id)
        
        # Should only have 1 busy slot (the new one)
        assert BusySlot.objects.filter(participant=participant).count() == 1


@pytest.mark.django_db
class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_api_get_heatmap(self, client):
        """Test heatmap API endpoint"""
        meeting = MeetingRequestFactory()
        
        # Test the view function directly since URLs might not be configured
        from meetings.views import api_get_heatmap
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get(f'/api/heatmap/{meeting.id}/')
        response = api_get_heatmap(request, meeting.id)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'dates' in data
        assert 'time_slots' in data
        assert 'heatmap' in data
    
    def test_api_get_heatmap_custom_timezone(self, client):
        """Test heatmap API with custom timezone parameter"""
        meeting = MeetingRequestFactory()
        
        # Test the view function directly
        from meetings.views import api_get_heatmap
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get(f'/api/heatmap/{meeting.id}/?timezone=America/New_York')
        response = api_get_heatmap(request, meeting.id)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['timezone'] == 'America/New_York'
    
    def test_api_get_suggestions(self, client):
        """Test suggestions API endpoint"""
        meeting = MeetingRequestFactory()
        SuggestedSlotFactory.create_batch(5, meeting_request=meeting)
        
        # Test the view function directly
        from meetings.views import api_get_suggestions
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get(f'/api/suggestions/{meeting.id}/')
        response = api_get_suggestions(request, meeting.id)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'suggestions' in data
        assert isinstance(data['suggestions'], list)
    
    def test_api_get_suggestions_with_parameters(self, client):
        """Test suggestions API with custom parameters"""
        meeting = MeetingRequestFactory()
        
        # Create slots with different availability
        SuggestedSlotFactory(meeting_request=meeting, available_count=9, total_participants=10)
        SuggestedSlotFactory(meeting_request=meeting, available_count=4, total_participants=10)
        
        # Test the view function directly
        from meetings.views import api_get_suggestions
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get(f'/api/suggestions/{meeting.id}/?limit=5&min_pct=50')
        response = api_get_suggestions(request, meeting.id)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        # Should only return suggestions with >= 50% availability
        for suggestion in data['suggestions']:
            assert suggestion['percentage'] >= 50
