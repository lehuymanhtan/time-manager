"""
Views for Meeting Time Scheduler
Handles Leader and Member workflows
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from datetime import datetime, timedelta
import json

from .models import MeetingRequest, Participant, BusySlot, SuggestedSlot
from .forms import (
    MeetingRequestForm, ParticipantForm, BulkParticipantForm,
    BusySlotForm, ParticipantResponseForm
)
from .utils import (
    generate_suggested_slots, get_top_suggestions, get_heatmap_data,
    parse_busy_slots_from_json
)


# =============================================================================
# HOME & DASHBOARD
# =============================================================================

def home(request):
    """Landing page"""
    return render(request, 'meetings/home.html')


def dashboard(request):
    """Leader dashboard showing all their meeting requests"""
    # For MVP, show all recent requests
    # In production, filter by user authentication
    recent_requests = MeetingRequest.objects.all()[:20]
    
    return render(request, 'meetings/dashboard.html', {
        'requests': recent_requests
    })


# =============================================================================
# LEADER WORKFLOW - CREATE REQUEST (3-STEP WIZARD)
# =============================================================================

def create_request_step1(request):
    """Step 1: Meeting configuration"""
    if request.method == 'POST':
        form = MeetingRequestForm(request.POST)
        if form.is_valid():
            meeting_request = form.save()
            # Store ID in session for next steps
            request.session['meeting_request_id'] = str(meeting_request.id)
            return redirect('create_request_step2')
    else:
        # Set default values
        initial = {
            'date_range_start': timezone.now().date(),
            'date_range_end': timezone.now().date() + timedelta(days=7),
            'duration_minutes': 60,
            'timezone': 'Asia/Ho_Chi_Minh',
            'work_hours_start': '09:00',
            'work_hours_end': '18:00',
            'step_size_minutes': 30,
            'work_days_only': True,
        }
        form = MeetingRequestForm(initial=initial)
    
    return render(request, 'meetings/create_step1.html', {'form': form})


def create_request_step2(request):
    """Step 2: Add participants (optional)"""
    meeting_request_id = request.session.get('meeting_request_id')
    if not meeting_request_id:
        return redirect('create_request_step1')
    
    meeting_request = get_object_or_404(MeetingRequest, id=meeting_request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_participant':
            form = ParticipantForm(request.POST)
            if form.is_valid():
                participant = form.save(commit=False)
                participant.meeting_request = meeting_request
                participant.save()
                messages.success(request, f'Đã thêm {participant.name or participant.email}')
                return redirect('create_request_step2')
        
        elif action == 'add_bulk':
            bulk_form = BulkParticipantForm(request.POST)
            if bulk_form.is_valid():
                data = bulk_form.cleaned_data['participants_data']
                count = 0
                for line in data.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) == 2:
                        name, email = parts
                    elif len(parts) == 1:
                        name = ''
                        email = parts[0]
                    else:
                        continue
                    
                    Participant.objects.get_or_create(
                        meeting_request=meeting_request,
                        email=email,
                        defaults={'name': name}
                    )
                    count += 1
                
                messages.success(request, f'Đã thêm {count} người tham gia')
                return redirect('create_request_step2')
        
        elif action == 'next':
            return redirect('create_request_step3')
        
        elif action == 'skip':
            return redirect('create_request_step3')
    
    participants = meeting_request.participants.all()
    form = ParticipantForm()
    bulk_form = BulkParticipantForm()
    
    return render(request, 'meetings/create_step2.html', {
        'meeting_request': meeting_request,
        'participants': participants,
        'form': form,
        'bulk_form': bulk_form,
    })


def create_request_step3(request):
    """Step 3: Review and finalize"""
    meeting_request_id = request.session.get('meeting_request_id')
    if not meeting_request_id:
        return redirect('create_request_step1')
    
    meeting_request = get_object_or_404(MeetingRequest, id=meeting_request_id)
    
    # Generate initial empty heatmap structure
    heatmap_data = get_heatmap_data(meeting_request)
    
    if request.method == 'POST':
        # Finalize and show share link
        meeting_request.status = 'active'
        meeting_request.save()
        
        # Clear session
        del request.session['meeting_request_id']
        
        return redirect('request_created', request_id=meeting_request.id)
    
    return render(request, 'meetings/create_step3.html', {
        'meeting_request': meeting_request,
        'heatmap_data': heatmap_data,
    })


def request_created(request, request_id):
    """Success page after creating request"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    share_url = request.build_absolute_uri(meeting_request.get_share_url())
    
    return render(request, 'meetings/request_created.html', {
        'meeting_request': meeting_request,
        'share_url': share_url,
    })


# =============================================================================
# LEADER WORKFLOW - VIEW & MANAGE REQUEST
# =============================================================================

def view_request(request, request_id):
    """Leader view of a meeting request with full details and suggestions"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    # Get participants and response status
    participants = meeting_request.participants.all()
    responded = participants.filter(has_responded=True)
    not_responded = participants.filter(has_responded=False)
    
    # Generate/update suggestions
    generate_suggested_slots(meeting_request, force_recalculate=True)
    
    # Get top suggestions
    top_suggestions = get_top_suggestions(meeting_request, limit=10)
    
    # Get heatmap data
    heatmap_data = get_heatmap_data(meeting_request)
    
    return render(request, 'meetings/view_request.html', {
        'meeting_request': meeting_request,
        'participants': participants,
        'responded': responded,
        'not_responded': not_responded,
        'top_suggestions': top_suggestions,
        'heatmap_data': heatmap_data,
    })


def lock_slot(request, request_id, slot_id):
    """Lock a suggested slot as the final meeting time"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    slot = get_object_or_404(SuggestedSlot, id=slot_id, meeting_request=meeting_request)
    
    # Unlock all other slots
    SuggestedSlot.objects.filter(meeting_request=meeting_request).update(is_locked=False)
    
    # Lock this slot
    slot.is_locked = True
    slot.save()
    
    # Update meeting request status
    meeting_request.status = 'locked'
    meeting_request.save()
    
    messages.success(request, 'Đã chốt khung giờ họp!')
    return redirect('view_request', request_id=request_id)


# =============================================================================
# MEMBER WORKFLOW - RESPOND TO REQUEST
# =============================================================================

def respond_to_request(request, request_id):
    """Member view - fill in their availability"""
    # Get token from query params
    token = request.GET.get('t')
    
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    # Verify token
    if meeting_request.token != token:
        return HttpResponseForbidden('Invalid token')
    
    # Check if still active
    if not meeting_request.is_active:
        return render(request, 'meetings/request_closed.html', {
            'meeting_request': meeting_request
        })
    
    # Get or create participant from session
    participant_id = request.session.get(f'participant_{request_id}')
    if participant_id:
        participant = Participant.objects.filter(id=participant_id).first()
    else:
        participant = None
    
    if request.method == 'POST':
        form = ParticipantResponseForm(request.POST)
        if form.is_valid():
            # Get or create participant
            if not participant:
                participant = Participant.objects.create(
                    meeting_request=meeting_request,
                    name=form.cleaned_data['name'],
                    email=form.cleaned_data['email'],
                    timezone=form.cleaned_data['timezone']
                )
                request.session[f'participant_{request_id}'] = str(participant.id)
            else:
                # Update participant info
                participant.name = form.cleaned_data['name']
                participant.email = form.cleaned_data['email']
                participant.timezone = form.cleaned_data['timezone']
                participant.save()
            
            # Redirect to calendar selection
            return redirect('select_busy_times', request_id=request_id)
    else:
        initial = {}
        if participant:
            initial = {
                'name': participant.name,
                'email': participant.email,
                'timezone': participant.timezone,
            }
        form = ParticipantResponseForm(initial=initial)
    
    return render(request, 'meetings/respond_step1.html', {
        'meeting_request': meeting_request,
        'form': form,
        'token': token,
    })


def select_busy_times(request, request_id):
    """Member selects their busy time slots"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    # Get participant from session
    participant_id = request.session.get(f'participant_{request_id}')
    if not participant_id:
        return redirect('respond_to_request', request_id=request_id)
    
    participant = get_object_or_404(Participant, id=participant_id)
    
    # Get existing busy slots
    busy_slots = participant.busy_slots.all()
    
    # Get heatmap data in participant's timezone
    heatmap_data = get_heatmap_data(meeting_request, participant.timezone)
    
    return render(request, 'meetings/select_busy_times.html', {
        'meeting_request': meeting_request,
        'participant': participant,
        'busy_slots': busy_slots,
        'heatmap_data': heatmap_data,
    })


@csrf_exempt
@require_http_methods(["POST"])
def save_busy_slots(request, request_id):
    """API endpoint to save participant's busy slots"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    # Get participant from session
    participant_id = request.session.get(f'participant_{request_id}')
    if not participant_id:
        return JsonResponse({'error': 'No participant found'}, status=400)
    
    participant = get_object_or_404(Participant, id=participant_id)
    
    try:
        data = json.loads(request.body)
        busy_slots_data = data.get('busy_slots', [])
        
        # Clear existing busy slots
        participant.busy_slots.all().delete()
        
        # Parse and create new busy slots
        slots = parse_busy_slots_from_json(busy_slots_data, participant.timezone)
        
        for start_utc, end_utc in slots:
            BusySlot.objects.create(
                participant=participant,
                start_time=start_utc,
                end_time=end_utc
            )
        
        # Mark participant as responded
        participant.has_responded = True
        participant.responded_at = timezone.now()
        participant.save()
        
        # Regenerate suggestions
        generate_suggested_slots(meeting_request, force_recalculate=True)
        
        return JsonResponse({
            'success': True,
            'message': 'Đã lưu thành công'
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)


def response_complete(request, request_id):
    """Thank you page after member submits response"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    participant_id = request.session.get(f'participant_{request_id}')
    participant = None
    
    if participant_id:
        participant = Participant.objects.filter(id=participant_id).first()
    
    # Get updated heatmap
    heatmap_data = get_heatmap_data(
        meeting_request, 
        participant.timezone if participant else meeting_request.timezone
    )
    
    # Get top suggestions
    top_suggestions = get_top_suggestions(meeting_request, limit=5)
    
    return render(request, 'meetings/response_complete.html', {
        'meeting_request': meeting_request,
        'participant': participant,
        'heatmap_data': heatmap_data,
        'top_suggestions': top_suggestions,
    })


# =============================================================================
# API ENDPOINTS
# =============================================================================

def api_get_heatmap(request, request_id):
    """API endpoint to get heatmap data"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    timezone_param = request.GET.get('timezone', meeting_request.timezone)
    
    heatmap_data = get_heatmap_data(meeting_request, timezone_param)
    
    return JsonResponse(heatmap_data)


def api_get_suggestions(request, request_id):
    """API endpoint to get top suggestions"""
    meeting_request = get_object_or_404(MeetingRequest, id=request_id)
    
    limit = int(request.GET.get('limit', 10))
    min_pct = int(request.GET.get('min_pct', 50))
    
    suggestions = get_top_suggestions(meeting_request, limit=limit, min_availability_pct=min_pct)
    
    data = []
    for suggestion in suggestions:
        data.append({
            'id': str(suggestion.id),
            'start_time': suggestion.start_time.isoformat(),
            'end_time': suggestion.end_time.isoformat(),
            'available_count': suggestion.available_count,
            'total_participants': suggestion.total_participants,
            'percentage': suggestion.availability_percentage,
            'heatmap_level': suggestion.heatmap_level,
        })
    
    return JsonResponse({'suggestions': data})
