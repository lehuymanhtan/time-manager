"""
Pytest configuration and fixtures for the Time Manager project.
"""
import pytest
from django.conf import settings
from django.test import Client, RequestFactory
from django.utils import timezone
import pytz


@pytest.fixture
def client():
    """Django test client."""
    return Client()


@pytest.fixture
def request_factory():
    """Django request factory for creating request objects."""
    return RequestFactory()


@pytest.fixture
def authenticated_client(client):
    """Client with an authenticated session."""
    session = client.session
    session['creator_id'] = 'test-creator-id-123'
    session.save()
    return client


@pytest.fixture
def tz_vietnam():
    """Vietnam timezone object."""
    return pytz.timezone('Asia/Ho_Chi_Minh')


@pytest.fixture
def tz_utc():
    """UTC timezone object."""
    return pytz.UTC


@pytest.fixture
def mock_now(monkeypatch):
    """
    Fixture to mock timezone.now() with a specific datetime.
    Returns a function that accepts a datetime to use as 'now'.
    """
    def _mock_now(dt):
        monkeypatch.setattr(timezone, 'now', lambda: dt)
        return dt
    return _mock_now


@pytest.fixture
def sample_datetime_vietnam(tz_vietnam):
    """Sample datetime in Vietnam timezone."""
    return timezone.datetime(2025, 1, 15, 9, 0, tzinfo=tz_vietnam)


@pytest.fixture
def sample_datetime_utc(tz_utc):
    """Sample datetime in UTC."""
    return timezone.datetime(2025, 1, 15, 2, 0, tzinfo=tz_utc)  # 9:00 Vietnam = 2:00 UTC


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Automatically enable database access for all tests.
    Remove this if you want to explicitly mark tests with @pytest.mark.django_db
    """
    pass


@pytest.fixture
def api_client():
    """Client for API testing."""
    return Client(content_type='application/json')
