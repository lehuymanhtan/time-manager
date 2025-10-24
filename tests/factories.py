"""
Factory classes for creating test data using factory_boy.
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.utils import timezone
import pytz
import secrets

from meetings.models import (
    MeetingRequest,
    Participant,
    BusySlot,
    SuggestedSlot
)

fake = Faker()


class MeetingRequestFactory(DjangoModelFactory):
    """Factory for creating MeetingRequest instances."""
    
    class Meta:
        model = MeetingRequest
    
    title = factory.LazyAttribute(lambda _: fake.sentence(nb_words=5))
    description = factory.LazyAttribute(lambda _: fake.paragraph())
    duration_minutes = 60  # minutes
    step_size_minutes = 30  # minutes
    date_range_start = factory.LazyFunction(lambda: timezone.now().date() + timezone.timedelta(days=1))
    date_range_end = factory.LazyFunction(lambda: timezone.now().date() + timezone.timedelta(days=7))
    work_hours_start = factory.LazyFunction(lambda: timezone.datetime.strptime('09:00', '%H:%M').time())
    work_hours_end = factory.LazyFunction(lambda: timezone.datetime.strptime('17:00', '%H:%M').time())
    work_days_only = True
    timezone = 'Asia/Ho_Chi_Minh'
    response_deadline = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=5))
    status = 'active'
    creator_id = factory.LazyFunction(lambda: str(fake.uuid4()))
    token = factory.LazyFunction(lambda: secrets.token_urlsafe(32))


class ParticipantFactory(DjangoModelFactory):
    """Factory for creating Participant instances."""
    
    class Meta:
        model = Participant
    
    meeting_request = factory.SubFactory(MeetingRequestFactory)
    name = factory.LazyAttribute(lambda _: fake.name())
    email = factory.LazyAttribute(lambda _: fake.email())
    has_responded = False


class ParticipantWithoutEmailFactory(ParticipantFactory):
    """Factory for creating Participant without email (NULL)."""
    email = None


class BusySlotFactory(DjangoModelFactory):
    """Factory for creating BusySlot instances."""
    
    class Meta:
        model = BusySlot
    
    participant = factory.SubFactory(ParticipantFactory)
    start_time = factory.LazyFunction(
        lambda: timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
    )
    end_time = factory.LazyFunction(
        lambda: timezone.now().replace(hour=11, minute=0, second=0, microsecond=0)
    )


class SuggestedSlotFactory(DjangoModelFactory):
    """Factory for creating SuggestedSlot instances."""
    
    class Meta:
        model = SuggestedSlot
    
    meeting_request = factory.SubFactory(MeetingRequestFactory)
    start_time = factory.LazyFunction(
        lambda: timezone.now().replace(hour=14, minute=0, second=0, microsecond=0)
    )
    end_time = factory.LazyFunction(
        lambda: timezone.now().replace(hour=15, minute=0, second=0, microsecond=0)
    )
    available_count = 3
    total_participants = 5


# Helper function to create complete meeting setup
def create_meeting_with_participants(
    num_participants=5,
    num_responded=0,
    include_busy_slots=False
):
    """
    Create a complete meeting request with participants and optionally busy slots.
    
    Args:
        num_participants: Total number of participants to create
        num_responded: Number of participants who have responded
        include_busy_slots: Whether to create busy slots for responded participants
    
    Returns:
        Tuple of (meeting_request, participants_list)
    """
    meeting = MeetingRequestFactory()
    participants = []
    
    for i in range(num_participants):
        participant = ParticipantFactory(
            meeting_request=meeting,
            has_responded=(i < num_responded)
        )
        participants.append(participant)
        
        # Create some busy slots if requested
        if include_busy_slots and i < num_responded:
            BusySlotFactory.create_batch(
                2,
                participant=participant,
                start_time=timezone.now() + timezone.timedelta(hours=i*2),
                end_time=timezone.now() + timezone.timedelta(hours=i*2 + 1)
            )
    
    return meeting, participants
