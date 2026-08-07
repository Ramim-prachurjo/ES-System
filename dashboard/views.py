from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from venues.models import VenueBooking
from tournaments.models import Tournament
from notifications.models import Notification
from accounts.models import CustomUser
from django.shortcuts import redirect
from django.db.models import Q

def admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'admin':
            messages.error(request, "Admin access only.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_dashboard(request):


    pending_bookings    = VenueBooking.objects.filter(status='pending').select_related('venue', 'booked_by')
    confirmed_bookings  = VenueBooking.objects.filter(status='confirmed').select_related('venue', 'booked_by')
    cancelled_bookings  = VenueBooking.objects.filter(status='cancelled').select_related('venue', 'booked_by')
    pending_tournaments = Tournament.objects.filter(status='pending').select_related('organizer', 'venue')

    # ── SEARCH LOGIC ──
    player_query = request.GET.get('player_q')
    organizer_query = request.GET.get('org_q')

    players = None
    organizers = None

    if player_query:
        players = CustomUser.objects.filter(
        role='player'
        ).filter(
        Q(username__icontains=player_query) |
        Q(first_name__icontains=player_query)
        )
        if players.count() == 1:
            return redirect('view_player_profile', user_id=players.first().id)
    
    

    if organizer_query:
        organizers = CustomUser.objects.filter(
            role='organizer',
            username__icontains=organizer_query
        )

        if organizers.count() == 1:
            return redirect('view_organizer_profile', user_id = organizers.first().id)

    return render(request, 'dashboard/admin_dashboard.html', {
        'pending_bookings':    pending_bookings,
        'confirmed_bookings':  confirmed_bookings,
        'cancelled_bookings':  cancelled_bookings,
        'pending_tournaments': pending_tournaments,
        'players': players,
        'organizers': organizers,
        'player_query': player_query,
        'organizer_query': organizer_query,

    })


@admin_required
def approve_booking(request, booking_id):
    booking = get_object_or_404(VenueBooking, pk=booking_id)
    VenueBooking.objects.filter(pk=booking_id).update(status='confirmed', payment_confirmed=True )

    # ── Notify the organizer ──
    Notification.objects.create(
        user    = booking.booked_by,
        message = (
            f"✅ Your venue booking for '{booking.venue.name}' "
            f"({booking.start_date} → {booking.end_date}) has been confirmed by the admin!"
        ),
    )

    messages.success(request, f"Booking for {booking.venue.name} approved.")
    return redirect('admin_dashboard')


@admin_required
def reject_booking(request, booking_id):
    booking = get_object_or_404(VenueBooking, pk=booking_id)
    VenueBooking.objects.filter(pk=booking_id).update(status='cancelled')

    # ── Notify the organizer ──
    Notification.objects.create(
        user    = booking.booked_by,
        message = (
            f"❌ Your venue booking for '{booking.venue.name}' "
            f"({booking.start_date} → {booking.end_date}) has been rejected by the admin."
        ),
    )

    messages.error(request, f"Booking for {booking.venue.name} rejected.")
    return redirect('admin_dashboard')


@admin_required
def admin_history(request):
    venue_query = request.GET.get('venue', '').strip()
    booking_date = request.GET.get('date', '').strip()
    bookings = VenueBooking.objects.filter(status='confirmed').select_related('venue', 'booked_by')
    tournaments = Tournament.objects.filter(status__in=['active', 'ongoing', 'completed']).select_related('venue', 'organizer')
    if venue_query:
        bookings = bookings.filter(venue__name__icontains=venue_query)
        tournaments = tournaments.filter(venue__name__icontains=venue_query)
    if booking_date:
        bookings = bookings.filter(start_date=booking_date)
        tournaments = tournaments.filter(start_date=booking_date)
    return render(request, 'dashboard/admin_history.html', {
        'bookings': bookings.order_by('-created_at'),
        'tournaments': tournaments.order_by('-created_at'),
        'venue_query': venue_query,
        'booking_date': booking_date,
    })


@admin_required
def approve_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    Tournament.objects.filter(pk=tournament_id).update(status='active', venue_payment_confirmed=True)

    # ── Notify the organizer ──
    Notification.objects.create(
        user    = tournament.organizer,
        message = (
            f"🏆 Your tournament '{tournament.name}' has been approved by the admin "
            f"and is now live!"
        ),
    )

    messages.success(request, f"Tournament '{tournament.name}' approved and now live.")
    return redirect('admin_dashboard')


@admin_required
def reject_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id)
    Tournament.objects.filter(pk=tournament_id).update(status='cancelled')

    # ── Notify the organizer ──
    Notification.objects.create(
        user    = tournament.organizer,
        message = (
            f"❌ Your tournament '{tournament.name}' has been rejected by the admin."
        ),
    )

    messages.error(request, f"Tournament '{tournament.name}' rejected.")
    return redirect('admin_dashboard')


@login_required
def organizer_history(request):
    if request.user.role != 'organizer':
        messages.error(request, "Organizer access only.")
        return redirect('admin_dashboard')

    venue_bookings = VenueBooking.objects.filter(
        booked_by=request.user
    ).select_related('venue').order_by('-created_at')

    tournaments = Tournament.objects.filter(
        organizer=request.user
    ).select_related('venue').order_by('-created_at')

    return render(request, 'dashboard/organizer_history.html', {
        'venue_bookings': venue_bookings,
        'tournaments':    tournaments,
    })


@login_required
def finish_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, pk=tournament_id, organizer=request.user)
    if request.user.role != 'organizer':
        messages.error(request, 'Organizer access only.')
        return redirect('dashboard')
    if tournament.status not in ('active', 'ongoing'):
        messages.error(request, 'Only active or ongoing tournaments can be marked finished.')
    else:
        tournament.status = 'completed'
        tournament.save(update_fields=['status'])
        messages.success(request, f"{tournament.name} is now marked as finished.")
    return redirect('organizer_history')
