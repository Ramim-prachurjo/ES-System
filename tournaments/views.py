import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from teams.models import Team
from venues.models import VenueBooking
from .models import Tournament, TournamentApplication
from .forms import TournamentForm


@login_required
def tournament_list(request):
    game_filter = request.GET.get('game', '').lower()
    if game_filter not in {'pubg', 'valorant'}:
        game_filter = ''

    if request.user.role == 'organizer':
        tournaments = Tournament.objects.filter(
            organizer=request.user
        ) | Tournament.objects.filter(status__in=['active', 'ongoing', 'completed'])
        tournaments = tournaments.distinct().order_by('-created_at')
    elif request.user.role == 'admin':
        tournaments = Tournament.objects.all().order_by('-created_at')
    else:
        tournaments = Tournament.objects.filter(
            status__in=['active', 'ongoing', 'completed']
        ).order_by('-created_at')

    if game_filter:
        tournaments = tournaments.filter(games__contains=game_filter)

    return render(request, 'tournaments/tournament_list.html', {
        'tournaments': tournaments,
        'selected_game': game_filter,
    })


@login_required
def create_tournament(request):
    if request.user.role != 'organizer':
        messages.error(request, "Only organizers can create tournaments.")
        return redirect('tournament_list')

    if request.method == 'POST':
        form = TournamentForm(request.POST)
        if form.is_valid():
            tournament           = form.save(commit=False)
            tournament.organizer = request.user
            tournament.status    = 'pending'

            venue      = form.cleaned_data.get('venue') if form.cleaned_data.get('needs_venue') else None
            start_date = form.cleaned_data.get('start_date')
            end_date   = form.cleaned_data.get('end_date')

            # ── Check if venue is already booked on overlapping dates ──
            if venue and start_date and end_date:

                # Check against standalone venue bookings
                booking_conflict = VenueBooking.objects.filter(
                    venue=venue,
                    status__in=['pending', 'confirmed'],
                    start_date__lte=end_date,
                    end_date__gte=start_date,
                ).exists()

                # Check against other tournaments at same venue
                tournament_conflict = Tournament.objects.filter(
                    venue=venue,
                    status__in=['pending', 'active', 'ongoing'],
                    start_date__lte=end_date,
                    end_date__gte=start_date,
                ).exists()

                if booking_conflict or tournament_conflict:
                    messages.error(
                        request,
                        f"⚠️ '{venue.name}' is already booked between "
                        f"{start_date} and {end_date}. "
                        f"Please choose different dates."
                    )
                    return render(request, 'tournaments/tournament_form.html', {
                        'form': form, 'title': 'Create Tournament',
                    })

            # ── Set payment info based on venue ──
            if venue and venue.requires_payment:
                tournament.venue_payment_required = True
                tournament.venue_payment_amount   = venue.payment_amount
                tournament.venue_payment_code     = f"TRN-{uuid.uuid4().hex[:8].upper()}"
            else:
                tournament.venue_payment_required = False
                tournament.venue_payment_amount   = 0.00
                tournament.venue_payment_code     = ''

            tournament.save()
            if venue:
                amount = venue.rental_fee or venue.payment_amount
                booking = VenueBooking.objects.create(
                    venue=venue, tournament=tournament, booked_by=request.user,
                    start_date=start_date, end_date=end_date, status='pending',
                    payment_required=amount > 0, payment_amount=amount,
                    payment_code=f"{uuid.uuid4().hex[:2].upper()}{uuid.uuid4().int % 1000:03d}",
                )
            messages.success(request, f"Tournament '{tournament.name}' submitted for admin approval.")
            if venue:
                return redirect('venue_booking_payment', pk=booking.pk)

            # Tournaments without a selected venue go straight to their detail page.
            return redirect('tournament_detail', pk=tournament.pk)

    else:
        form = TournamentForm()

    return render(request, 'tournaments/tournament_form.html', {
        'form': form, 'title': 'Create Tournament',
    })


@login_required
def tournament_payment_info(request, pk):
    # Only the organizer who created it can see this page
    tournament = get_object_or_404(Tournament, pk=pk, organizer=request.user)
    return render(request, 'tournaments/tournament_payment.html', {'tournament': tournament})


@login_required
def edit_tournament(request, pk):
    """Organizers can edit their tournaments only while enrollment is open."""
    tournament = get_object_or_404(Tournament, pk=pk)
    if request.user != tournament.organizer:
        messages.error(request, "Only the organizer can edit this tournament.")
        return redirect('tournament_detail', pk=tournament.pk)
    if tournament.enrollment_status == 'closed':
        messages.error(request, "Tournament editing is locked because enrollment has closed.")
        return redirect('tournament_detail', pk=tournament.pk)

    if request.method == 'POST':
        form = TournamentForm(request.POST, instance=tournament)
        if form.is_valid():
            tournament = form.save(commit=False)
            venue = form.cleaned_data.get('venue') if form.cleaned_data.get('needs_venue') else None
            tournament.venue_payment_required = bool(venue and venue.requires_payment)
            tournament.venue_payment_amount = (venue.rental_fee or venue.payment_amount) if venue else 0
            if tournament.venue_payment_required and not tournament.venue_payment_code:
                tournament.venue_payment_code = f"TRN-{uuid.uuid4().hex[:8].upper()}"
            if not tournament.venue_payment_required:
                tournament.venue_payment_code = ''
            tournament.save()

            booking = VenueBooking.objects.filter(tournament=tournament).first()
            if venue:
                amount = venue.rental_fee or venue.payment_amount
                if booking:
                    booking.venue, booking.start_date, booking.end_date = venue, tournament.start_date, tournament.end_date
                    booking.payment_required, booking.payment_amount = amount > 0, amount
                    booking.save()
                else:
                    VenueBooking.objects.create(
                        venue=venue, tournament=tournament, booked_by=request.user,
                        start_date=tournament.start_date, end_date=tournament.end_date,
                        status='pending', payment_required=amount > 0, payment_amount=amount,
                        payment_code=f"{uuid.uuid4().hex[:2].upper()}{uuid.uuid4().int % 1000:03d}",
                    )
            elif booking:
                booking.delete()

            messages.success(request, "Tournament details updated successfully.")
            return redirect('tournament_detail', pk=tournament.pk)
    else:
        form = TournamentForm(instance=tournament)

    return render(request, 'tournaments/tournament_form.html', {
        'form': form, 'title': 'Edit Tournament', 'submit_label': 'Save Changes',
        'back_url': reverse('tournament_detail', kwargs={'pk': tournament.pk}),
    })


@login_required
def tournament_detail(request, pk):
    tournament   = get_object_or_404(Tournament, pk=pk)
    applications = tournament.applications.select_related('team').order_by('applied_at')

    applicable_teams = []
    if request.user.role == 'player':
        tournament_games = tournament.get_games_list()
        captain_teams    = Team.objects.filter(captain=request.user)
        for team in captain_teams:
            if team.game in tournament_games:
                already_applied = TournamentApplication.objects.filter(
                    tournament=tournament, team=team, game=team.game,
                ).exists()
                if not already_applied:
                    applicable_teams.append({
                        'team': team,
                        'is_full': team.is_full(),
                        'current': team.memberships.count(),
                        'max': team.max_size(),
                    })

    return render(request, 'tournaments/tournament_detail.html', {
        'tournament':        tournament,
        'applications':      applications,
        'applicable_teams':  applicable_teams,
    })


@login_required
def apply_to_tournament(request, tournament_id, team_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id, status='active')
    team       = get_object_or_404(Team, pk=team_id, captain=request.user)

    if tournament.enrollment_status == 'closed':
        messages.error(request, "Tournament enrollment is closed.")
        return redirect('tournament_detail', pk=tournament_id)

    if team.game not in tournament.get_games_list():
        messages.error(request, f"This tournament does not support {team.game.title()}.")
        return redirect('tournament_detail', pk=tournament_id)

    if tournament.is_full():
        messages.error(request, "Tournament is full.")
        return redirect('tournament_detail', pk=tournament_id)

    if not team.is_full():
        messages.error(request, f"Your team is incomplete ({team.memberships.count()}/{team.max_size()} members). Complete your team before applying.")
        return redirect('tournament_detail', pk=tournament_id)

    already = TournamentApplication.objects.filter(
        tournament=tournament, team=team, game=team.game,
    ).exists()

    if already:
        messages.error(request, "This team has already applied to this tournament.")
        return redirect('tournament_detail', pk=tournament_id)

    TournamentApplication.objects.create(
        tournament=tournament, team=team, game=team.game, status='pending',
    )
    messages.success(request, f"{team.name} has applied to {tournament.name}!")
    return redirect('tournament_detail', pk=tournament_id)


@login_required
def approve_application(request, application_id):
    application = get_object_or_404(
        TournamentApplication, pk=application_id,
        tournament__organizer=request.user,
    )
    TournamentApplication.objects.filter(pk=application_id).update(status='approved')
    messages.success(request, f"{application.team.name} approved.")
    return redirect('tournament_detail', pk=application.tournament.pk)


@login_required
def reject_application(request, application_id):
    application = get_object_or_404(
        TournamentApplication, pk=application_id,
        tournament__organizer=request.user,
    )
    TournamentApplication.objects.filter(pk=application_id).update(status='rejected')
    messages.error(request, f"{application.team.name} rejected.")
    return redirect('tournament_detail', pk=application.tournament.pk)

