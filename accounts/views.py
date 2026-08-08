from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from .forms import RegisterForm, LoginForm, PlayerProfileForm, OrganizerProfileForm
from .models import PlayerProfile, CustomUser


# ── Register ────────────────────────────────────────────────────────────────
def landing(request):
    """Public entry point shown before the login page."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/landing.html')


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
    return render(request, 'accounts/view_player_profile.html', {
        'target_user': target_user,
        'profile': profile,
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
