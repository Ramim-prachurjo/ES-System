from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import get_user_model
from .forms import CreateTeamForm, InvitePlayerForm, JoinByCodeForm
from .models import Team, TeamMembership, TeamInvite, JoinRequest
from notifications.models import Notification
from django.db import IntegrityError
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

User = get_user_model()


@login_required
def team_list(request):
    teams = Team.objects.all().select_related('captain')
    query = request.GET.get('q', '').strip()
    if request.user.role == 'organizer' and query:
        teams = teams.filter(name__icontains=query)
    return render(request, 'teams/team_list.html', {
        'teams': teams,
        'query': query,
    })


@login_required
def create_team(request):
    if request.user.role != 'player':
        messages.error(request, "Only players can create teams.")
        return redirect('team_list')

    if request.method == 'POST':
        form = CreateTeamForm(request.POST)
        if form.is_valid():
            game = form.cleaned_data['game']

            already_in = TeamMembership.objects.filter(
                user=request.user,
                team__game=game,
            ).exists()

            if already_in:
                messages.error(request, f"You are already in a {game.title()} team.")
                return render(request, 'teams/create_team.html', {'form': form})

            team = form.save(commit=False)
            team.captain = request.user
            team.save()

            TeamMembership.objects.create(user=request.user, team=team)
            messages.success(request, f"Team '{team.name}' created! Your team code is {team.team_code}")
            return redirect('team_detail', pk=team.pk)
    else:
        form = CreateTeamForm()

    return render(request, 'teams/create_team.html', {'form': form})


@login_required
def team_detail(request, pk):
    team    = get_object_or_404(Team, pk=pk)
    members = team.memberships.select_related('user')
    invites = team.invites.filter(status='pending').select_related('invited_user')
    invite_form = InvitePlayerForm()
    back_url = request.GET.get('next')
    if not url_has_allowed_host_and_scheme(back_url, {request.get_host()}):
        back_url = reverse('browse_teams') if request.user.role == 'player' else reverse('team_list')

    return render(request, 'teams/team_detail.html', {
        'team':        team,
        'members':     members,
        'invites':     invites,
        'invite_form': invite_form,
        'back_url':    back_url,
    })


@login_required
def invite_player(request, team_id):
    team = get_object_or_404(Team, pk=team_id)
    next_url = request.POST.get('next') or reverse('team_detail', kwargs={'pk': team_id})
    if not url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
        next_url = reverse('team_detail', kwargs={'pk': team_id})

    if request.user != team.captain:
        messages.error(request, "Only the captain can invite players.")
        return redirect(next_url)

    if team.is_full():
        messages.error(request, "Team is full.")
        return redirect(next_url)

    if request.method == 'POST':
        form = InvitePlayerForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']

            try:
                invited_user = User.objects.get(username=username, role='player')
            except User.DoesNotExist:
                messages.error(request, f"No player found with username '{username}'.")
                return redirect(next_url)

            if invited_user == request.user:
                messages.error(request, "You can't invite yourself.")
                return redirect(next_url)

            # ✅ FIX: block if already in ANY team for this game
            already_in = TeamMembership.objects.filter(
                user=invited_user,
                team__game=team.game,
            ).exists()

            if already_in:
                messages.error(request, f"{username} is already in a {team.game.title()} team.")
                return redirect(next_url)

            already_invited = TeamInvite.objects.filter(
                team=team,
                invited_user=invited_user,
                status='pending',
            ).exists()

            if already_invited:
                messages.error(request, f"{username} has already been invited.")
                return redirect(next_url)

            TeamInvite.objects.create(team=team, invited_user=invited_user)

            # notify the invited player
            Notification.objects.create(
                user=invited_user,
                message=f"You have been invited to join '{team.name}' ({team.get_game_display()}) by captain {request.user.username}.",
            )

            messages.success(request, f"Invite sent to {username}.")

    return redirect(next_url)


@login_required
def join_by_code(request):
    if request.method == 'POST':
        form = JoinByCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['team_code'].upper().strip()

            try:
                team = Team.objects.get(team_code=code)
            except Team.DoesNotExist:
                messages.error(request, "Invalid team code.")
                return redirect('team_list')

            already_in = TeamMembership.objects.filter(
                user=request.user,
                team__game=team.game,
            ).exists()

            if already_in:
                messages.error(request, f"You are already in a {team.game.title()} team.")
                return redirect('team_list')

            if team.is_full():
                messages.error(request, "This team is already full.")
                return redirect('team_list')

            TeamMembership.objects.create(user=request.user, team=team)
            messages.success(request, f"You joined {team.name}!")
            return redirect('team_detail', pk=team.pk)

    return redirect('team_list')


@login_required
def respond_invite(request, invite_id, action):
    invite = get_object_or_404(TeamInvite, pk=invite_id, invited_user=request.user)

    if action == 'accept':
        # ✅ FIX: strict same-game check before accepting
        already_in = TeamMembership.objects.filter(
            user=request.user,
            team__game=invite.team.game,
        ).exists()

        if already_in:
            messages.error(request, f"You are already in a {invite.team.game.title()} team.")
            invite.status = 'rejected'
            invite.save()
            return redirect('my_invites')

        if invite.team.is_full():
            messages.error(request, "Team is now full.")
            invite.status = 'rejected'
            invite.save()
            return redirect('my_invites')

        TeamMembership.objects.create(user=request.user, team=invite.team)
        invite.status = 'accepted'
        invite.save()

        # notify captain
        Notification.objects.create(
            user=invite.team.captain,
            message=f"{request.user.username} accepted your invite and joined '{invite.team.name}'.",
        )

        messages.success(request, f"You joined {invite.team.name}!")

    elif action == 'reject':
        invite.status = 'rejected'
        invite.save()

        # notify captain
        Notification.objects.create(
            user=invite.team.captain,
            message=f"{request.user.username} declined your invite to '{invite.team.name}'.",
        )

        messages.info(request, f"Invite from {invite.team.name} rejected.")

    return redirect('my_invites')


@login_required
def my_invites(request):
    invites = TeamInvite.objects.filter(
        invited_user=request.user,
        status='pending',
    ).select_related('team', 'team__captain')

    return render(request, 'teams/my_invites.html', {'invites': invites})


@login_required
def transfer_captain(request, team_id, user_id):
    team        = get_object_or_404(Team, pk=team_id)
    new_captain = get_object_or_404(User, pk=user_id)

    if request.user != team.captain:
        messages.error(request, "Only the captain can transfer captaincy.")
        return redirect('team_detail', pk=team_id)

    if not TeamMembership.objects.filter(user=new_captain, team=team).exists():
        messages.error(request, "That player is not in your team.")
        return redirect('team_detail', pk=team_id)

    team.captain = new_captain
    team.save()
    messages.success(request, f"Captaincy transferred to {new_captain.username}.")
    return redirect('team_detail', pk=team_id)


# ── Browse Teams ────────────────────────────────────────────────────────────

@login_required
def browse_teams(request):
    teams = Team.objects.all().select_related('captain').prefetch_related('memberships')

    game_filter         = request.GET.get('game', '')
    availability_filter = request.GET.get('availability', '')

    if game_filter:
        teams = teams.filter(game=game_filter)

    team_data = []
    for team in teams:
        current_size = team.memberships.count()
        max_size     = team.max_size()
        is_full      = current_size >= max_size

        if availability_filter == 'open' and is_full:
            continue

        already_requested = JoinRequest.objects.filter(
            team=team, player=request.user, status='pending',
        ).exists()

        already_member = TeamMembership.objects.filter(
            user=request.user, team=team,
        ).exists()

        in_same_game_team = TeamMembership.objects.filter(
            user=request.user, team__game=team.game,
        ).exists()

        team_data.append({
            'team':              team,
            'current_size':      current_size,
            'max_size':          max_size,
            'is_full':           is_full,
            'already_requested': already_requested,
            'already_member':    already_member,
            'can_apply':         not is_full and not already_requested and not already_member and not in_same_game_team,
        })

    return render(request, 'teams/browse_teams.html', {
        'team_data':           team_data,
        'game_choices':        Team.GAME_CHOICES,
        'game_filter':         game_filter,
        'availability_filter': availability_filter,
    })


@login_required
def request_to_join(request, team_id):

    if request.method != "POST":
        return redirect('browse_teams')

    if request.user.role != 'player':
        messages.error(request, "Only players can request to join a team.")
        return redirect('browse_teams')

    team = get_object_or_404(Team, pk=team_id)

    if request.user == team.captain:
        messages.error(request, "You are the captain of this team.")
        return redirect('browse_teams')

    if TeamMembership.objects.filter(user=request.user, team=team).exists():
        messages.error(request, "You are already a member of this team.")
        return redirect('browse_teams')

    if TeamMembership.objects.filter(user=request.user, team__game=team.game).exists():
        messages.error(request, f"You are already in a {team.game.title()} team.")
        return redirect('browse_teams')

    if team.is_full():
        messages.error(request, "This team is already full.")
        return redirect('browse_teams')

    # ✅ FIXED duplicate check
    existing_request = JoinRequest.objects.filter(team=team, player=request.user).first()

    if existing_request:
        if existing_request.status == 'pending':
            messages.error(request, "You already have a pending request.")
        else:
            messages.error(request, f"You already requested before (status: {existing_request.status}).")
        return redirect('browse_teams')

    # ✅ SAFE CREATE
    try:
        JoinRequest.objects.create(team=team, player=request.user)

        Notification.objects.create(
            user=team.captain,
            message=f"{request.user.username} wants to join your team '{team.name}'.",
        )

        messages.success(request, f"Join request sent to '{team.name}'!")

    except IntegrityError:
        messages.error(request, "Request already exists.")

    return redirect('browse_teams')


@login_required
def my_join_requests(request):
    captained_teams = Team.objects.filter(captain=request.user)
    join_requests   = JoinRequest.objects.filter(
        team__in=captained_teams,
        status='pending',
    ).select_related('player', 'team')

    return render(request, 'teams/join_requests.html', {
        'join_requests': join_requests,
    })


@login_required
def handle_join_request(request, req_id, action):
    join_req = get_object_or_404(JoinRequest, pk=req_id, team__captain=request.user)

    if action == 'approve':
        if join_req.team.is_full():
            messages.error(request, "Team is now full, can't approve.")
            join_req.status = 'rejected'
            join_req.save()
            Notification.objects.create(
                user=join_req.player,
                message=f"Your request to join '{join_req.team.name}' was rejected because the team is now full.",
            )
            return redirect('my_join_requests')

        if TeamMembership.objects.filter(
            user=join_req.player, team__game=join_req.team.game
        ).exists():
            messages.error(request, f"{join_req.player.username} is already in a {join_req.team.game.title()} team.")
            join_req.status = 'rejected'
            join_req.save()
            return redirect('my_join_requests')

        TeamMembership.objects.create(user=join_req.player, team=join_req.team)
        join_req.status = 'accepted'
        join_req.save()

        Notification.objects.create(
            user=join_req.player,
            message=f"✅ Your request to join '{join_req.team.name}' was approved! Welcome to the team.",
        )
        messages.success(request, f"{join_req.player.username} added to {join_req.team.name}.")

    elif action == 'reject':
        join_req.status = 'rejected'
        join_req.save()

        Notification.objects.create(
            user=join_req.player,
            message=f"❌ Your request to join '{join_req.team.name}' was rejected by the captain.",
        )
        messages.info(request, f"Request from {join_req.player.username} rejected.")

    return redirect('my_join_requests')


# ── My Team ─────────────────────────────────────────────────────────────────

@login_required
def my_team(request):
    """
    Player sees all teams they are enrolled in (one per game max).
    Captain can remove members from here.
    """
    memberships = TeamMembership.objects.filter(
        user=request.user
    ).select_related('team', 'team__captain')

    player_query = request.GET.get('player_q', '').strip()
    team_data = []
    for ms in memberships:
        team    = ms.team
        members = TeamMembership.objects.filter(team=team).select_related('user')
        player_results = User.objects.none()
        if player_query and request.user == team.captain and not team.is_full():
            player_results = User.objects.filter(
                role='player', username__icontains=player_query
            ).exclude(
                pk=request.user.pk
            ).exclude(
                memberships__team__game=team.game
            ).exclude(
                received_invites__team=team,
                received_invites__status='pending',
            ).distinct()[:8]
        team_data.append({
            'team':       team,
            'members':    members,
            'is_captain': request.user == team.captain,
            'current':    members.count(),
            'max':        team.max_size(),
            'player_results': player_results,
        })

    return render(request, 'teams/my_team.html', {
        'team_data': team_data,
        'player_query': player_query,
    })


@login_required
def rename_team(request, team_id):
    """Allow only the current captain to rename their own team."""
    team = get_object_or_404(Team, pk=team_id)
    next_url = request.POST.get('next') or reverse('team_detail', kwargs={'pk': team_id})
    if not url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
        next_url = reverse('team_detail', kwargs={'pk': team_id})

    if request.user != team.captain:
        messages.error(request, "Only the team captain can change the team name.")
        return redirect(next_url)

    if request.method != 'POST':
        return redirect(next_url)

    new_name = request.POST.get('name', '').strip()
    if len(new_name) < 2 or len(new_name) > 100:
        messages.error(request, "Team name must be between 2 and 100 characters.")
    elif Team.objects.exclude(pk=team.pk).filter(name__iexact=new_name).exists():
        messages.error(request, "That team name is already being used.")
    elif new_name == team.name:
        messages.info(request, "Your team already has that name.")
    else:
        team.name = new_name
        team.save(update_fields=['name'])
        messages.success(request, "Team name updated successfully.")

    return redirect(next_url)


@login_required
def remove_member(request, team_id, user_id):
    """
    Captain removes a member from their team.
    """
    team       = get_object_or_404(Team, pk=team_id)
    to_remove  = get_object_or_404(User, pk=user_id)

    if request.user != team.captain:
        messages.error(request, "Only the captain can remove members.")
        return redirect('my_team')

    if to_remove == team.captain:
        messages.error(request, "You can't remove yourself as captain.")
        return redirect('my_team')

    membership = get_object_or_404(TeamMembership, user=to_remove, team=team)
    membership.delete()

    Notification.objects.create(
        user=to_remove,
        message=f"You have been removed from '{team.name}' by the captain.",
    )

    messages.success(request, f"{to_remove.username} removed from {team.name}.")
    return redirect('my_team')


@login_required
def leave_team(request, team_id):
    team       = get_object_or_404(Team, pk=team_id)
    membership = get_object_or_404(TeamMembership, user=request.user, team=team)

    if request.user == team.captain:
        # only allow if they are the last member (disband)
        if team.memberships.count() > 1:
            messages.error(request, "Transfer captaincy before leaving.")
            return redirect('my_team')
        # last member — delete the whole team
        team.delete()
        messages.success(request, f"Team disbanded.")
        return redirect('team_list')

    membership.delete()

    Notification.objects.create(
        user=team.captain,
        message=f"{request.user.username} has left your team '{team.name}'.",
    )

    messages.success(request, f"You left {team.name}.")
    return redirect('browse_teams')
