from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
import json
import logging
import os
from urllib import error, request as urlrequest

logger = logging.getLogger(__name__)


def _platform_help_answer(question):
    """Reliable answers for core MARKSMEN_es journeys; avoids AI guessing."""
    text = question.lower().replace('0', 'o')
    if ('forgot' in text or 'reset' in text) and ('pass' in text or 'password' in text):
        return (
            'To reset a forgotten password: open the Login page, select “Forgot password?”, '
            'enter your account email, then open the secure reset link sent to that email.'
        )
    if 'change' in text and ('pass' in text or 'password' in text):
        return (
            'To change your password while logged in: open the profile icon in the top-right corner, '
            'select “Change Password”, enter your current password and new password, then select “Update Password”.'
        )
    if ('apply' in text or 'application' in text) and ('tournament' in text or 'tournment' in text):
        return (
            'To apply for a tournament: sign in as a player and become captain of a team. Open Discover Tournaments, '
            'open an active tournament that supports your team’s game, then select Apply beside your full team. '
            'Valorant teams need 5 members and PUBG teams need 4 members. Your application will be pending until the organizer reviews it.'
        )
    if 'venue' in text and ('book' in text or 'reserve' in text):
        return (
            'Organizers can book a venue while creating a tournament: select “Need venue: Yes”, choose the date, '
            'select an available venue, and follow the bKash payment slip instructions. The reservation remains pending until admin approval.'
        )
    if ('create' in text or 'make' in text) and 'team' in text:
        return (
            'To create a team: open Create Team, choose PUBG or Valorant, enter the team details, and submit. '
            'You become the captain. Team capacity is 4 for PUBG and 5 for Valorant.'
        )
    return None

from .forms import RegisterForm, LoginForm, PlayerProfileForm, OrganizerProfileForm
from .models import PlayerProfile, CustomUser


# ── Register ────────────────────────────────────────────────────────────────
def landing(request):
    """Public entry point shown before the login page."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/landing.html')


def about(request):
    return render(request, 'accounts/about.html')


def services(request):
    return render(request, 'accounts/services.html')


@login_required
@require_POST
@csrf_protect
def chatbot_response(request):
    """Send a short platform-help question to Gemini without exposing its key."""
    try:
        question = str(json.loads(request.body).get('message', '')).strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Please send a valid question.'}, status=400)

    if not question or len(question) > 700:
        return JsonResponse({'error': 'Please ask one question of up to 700 characters.'}, status=400)

    fixed_answer = _platform_help_answer(question)
    if fixed_answer:
        return JsonResponse({'answer': fixed_answer, 'source': 'platform_help'})

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return JsonResponse({'error': 'The assistant is not configured yet.'}, status=503)

    instructions = (
        'You are MARKSMEN_es Assistant for an esports tournament management platform. '
        'Answer only about accounts, player teams, tournament discovery and applications, '
        'organizer tournaments, venues and bookings, notifications, and password/account help. '
        'Be friendly, brief, accurate, and use simple language. Do not invent live tournament, '
        'payment, booking, account, or personal data.'
    )
    body = json.dumps({
        'systemInstruction': {'parts': [{'text': instructions}]},
        'contents': [{'role': 'user', 'parts': [{'text': question}]}],
        'generationConfig': {'maxOutputTokens': 350, 'temperature': 0.35},
    }).encode('utf-8')
    model = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash')
    gemini_request = urlrequest.Request(
        f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
        data=body,
        headers={'Content-Type': 'application/json', 'x-goog-api-key': api_key},
        method='POST',
    )
    try:
        with urlrequest.urlopen(gemini_request, timeout=18) as response:
            result = json.loads(response.read().decode('utf-8'))
        answer = ''.join(part.get('text', '') for part in result['candidates'][0]['content']['parts']).strip()
        if not answer:
            raise ValueError('No response text returned')
        return JsonResponse({'answer': answer})
    except error.HTTPError as exc:
        logger.warning('Gemini chatbot request failed with HTTP status %s.', exc.code)
        return JsonResponse({'error': 'The assistant is temporarily unavailable. Please try again shortly.'}, status=503)
    except (error.URLError, KeyError, IndexError, ValueError, json.JSONDecodeError):
        logger.warning('Gemini chatbot request failed without an API response.')
        return JsonResponse({'error': 'The assistant is temporarily unavailable. Please try again shortly.'}, status=503)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)

        # auto-create a blank PlayerProfile for new players
        if user.role == 'player':
            PlayerProfile.objects.get_or_create(user=user)

        return redirect('dashboard')

    return render(request, 'accounts/register.html', {'form': form})


# ── Login ────────────────────────────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)

        # safety net — create profile if somehow missing
        if user.role == 'player':
            PlayerProfile.objects.get_or_create(user=user)

        return redirect('dashboard')

    return render(request, 'accounts/login.html', {'form': form})


# ── Logout ───────────────────────────────────────────────────────────────────
def logout_view(request):
    logout(request)
    return redirect('login')


# ── Dashboard ────────────────────────────────────────────────────────────────
@login_required
def dashboard(request):
    if request.user.role == 'organizer':
        return render(request, 'accounts/organizer_dashboard.html')
    elif request.user.role == 'admin':
        return redirect('admin_dashboard')
    else:
        return render(request, 'accounts/player_dashboard.html')


# ── Player profile ───────────────────────────────────────────────────────────
@login_required
def player_profile(request):
    if request.user.role != 'player':
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    # get or create so it never crashes on missing profile
    profile, _ = PlayerProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = PlayerProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('player_profile')
    else:
        form = PlayerProfileForm(instance=profile, user=request.user)

    return render(request, 'accounts/player_profile.html', {
        'form':    form,
        'profile': profile,
    })


# ── Organizer profile ────────────────────────────────────────────────────────
@login_required
def organizer_profile(request):
    if request.user.role not in ('organizer', 'admin'):
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = OrganizerProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('organizer_profile')
    else:
        form = OrganizerProfileForm(instance=request.user)

    return render(request, 'accounts/organizer_profile.html', {'form': form})
@login_required
def view_player_profile(request, user_id):
    from .models import PlayerProfile
    target_user = get_object_or_404(
        __import__('django.contrib.auth', fromlist=['get_user_model']).get_user_model(),
        pk=user_id,
        role='player'
    )
    profile = PlayerProfile.objects.filter(user=target_user).first()
    next_url = request.GET.get('next')
    if not url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
        next_url = reverse('team_list')

    # A captain should never be offered an invite button for a player who is
    # already a member of that captain's team.
    from teams.models import TeamMembership
    invitable_teams = []
    if request.user.role == 'player':
        for team in request.user.captained_teams.all():
            is_member = TeamMembership.objects.filter(team=team, user=target_user).exists()
            if not team.is_full() and not is_member and target_user != request.user:
                invitable_teams.append(team)

    return render(request, 'accounts/view_player_profile.html', {
        'target_user': target_user,
        'profile': profile,
        'invitable_teams': invitable_teams,
        'back_url': next_url,
    })


@login_required
def search_players(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    query = request.GET.get('q', '').strip()
    players = []
    if query:
        players = User.objects.filter(
            username__icontains=query,
            role='player'
        ).select_related('player_profile')
    return render(request, 'accounts/search_players.html', {
        'players': players,
        'query': query,
    })

@login_required
def view_organizer_profile(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, role='organizer')
    return render(request, 'accounts/view_organizer_profile.html', {'user_obj': user})

@login_required
def change_password(request):
    form = PasswordChangeForm(user=request.user)
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # keeps the user logged in after password change
            update_session_auth_hash(request, form.user)
            messages.success(request, "Password changed successfully.")
            return redirect('change_password')
        else:
            # pass errors back — the profile template will show them
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    # always redirect back to the correct profile page
    return render(request, 'accounts/change_password.html', {'form': form})


def _support_page(request, title, intro, sections):
    return render(request, 'accounts/support_page.html', {
        'page_title': title,
        'intro': intro,
        'sections': sections,
    })


def faq(request):
    return _support_page(request, 'Frequently Asked Questions', 'Helpful answers for competing, organizing, and managing your MARKSMEN_es account.', [
        {'heading': 'How do I join a tournament?', 'body': 'Create or join a team for the selected game, open the tournament, and submit an application when registration is available.'},
        {'heading': 'Who can create tournaments?', 'body': 'Registered organizer accounts can create tournaments. New events are reviewed before they become available to players.'},
        {'heading': 'How do venue bookings work?', 'body': 'Organizers can browse venues, submit booking requests, and follow the payment instructions when a venue requires a fee.'},
        {'heading': 'Can a player join more than one team?', 'body': 'Players can join teams according to the game and team rules enforced by the platform. Check your My Team page before accepting an invite.'},
        {'heading': 'Where can I find updates?', 'body': 'Use the notification bell in the header to see tournament, invitation, booking, and account updates.'},
    ])


def terms_conditions(request):
    return _support_page(request, 'Terms & Conditions', 'These terms set clear expectations for respectful, fair participation on MARKSMEN_es.', [
        {'heading': 'Platform use', 'body': 'You must provide accurate account information and use the platform only for lawful esports, team, tournament, and venue-management activities.'},
        {'heading': 'Competitive conduct', 'body': 'Players, captains, and organizers must treat others respectfully. Cheating, harassment, impersonation, or deliberately misleading information may result in account restrictions.'},
        {'heading': 'Tournament and venue decisions', 'body': 'Organizers are responsible for the accuracy of their event details. Venue availability, approvals, fees, and tournament outcomes may be subject to organizer or administrator review.'},
        {'heading': 'Account security', 'body': 'Keep your password private and notify the platform team if you believe your account has been accessed without permission.'},
        {'heading': 'Changes to the service', 'body': 'MARKSMEN_es may update features, procedures, or these terms to improve platform safety, reliability, and competitive integrity.'},
    ])


def privacy_policy(request):
    return _support_page(request, 'Privacy Policy', 'We collect only the information needed to operate accounts, teams, tournaments, venue bookings, and platform communication.', [
        {'heading': 'Information we use', 'body': 'This can include your account details, contact information, player profile details, team activity, tournament applications, and venue-booking information.'},
        {'heading': 'How information is used', 'body': 'Information is used to deliver platform features, verify permissions, communicate updates, manage events, and help keep the community safe.'},
        {'heading': 'Information sharing', 'body': 'Relevant information may be shown to other users when required for platform features, such as team rosters, tournament applications, and organizer communications. We do not sell personal information.'},
        {'heading': 'Security', 'body': 'We use reasonable safeguards to protect account information. You also play an important role by using a strong, unique password.'},
        {'heading': 'Questions about privacy', 'body': 'For questions about this policy or your account information, contact us at apon02931@gmail.com.'},
    ])
