import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Venue, VenueBooking
from .forms import BookingRequestForm

# ── Venues excluded from the standalone booking interface ──
HIDDEN_VENUE_NAMES = ['East West University']


@login_required
def venue_list(request):
    # exclude hidden venues from the organizer-facing list
    venues = Venue.objects.exclude(name__in=HIDDEN_VENUE_NAMES)

    venue_data = []
    for venue in venues:
        bookings = VenueBooking.objects.filter(
            venue=venue,
            status__in=['pending', 'confirmed']
        ).values('start_date', 'end_date', 'status')

        booking_list = []
        for b in bookings:
            booking_list.append({
                'start_date': b['start_date'].strftime('%Y-%m-%d'),
                'end_date':   b['end_date'].strftime('%Y-%m-%d'),
                'status':     b['status'],
            })

        venue_data.append({
            'venue':    venue,
            'bookings': booking_list,
        })

    return render(request, 'venues/venue_list.html', {'venue_data': venue_data})


@login_required
def request_booking(request, venue_id):
    if request.user.role != 'organizer':
        messages.error(request, "Only organizers can request venue bookings.")
        return redirect('venue_list')

    # block direct URL access to hidden venues
    venue = get_object_or_404(Venue, pk=venue_id)
    if venue.name in HIDDEN_VENUE_NAMES:
        messages.error(request, "This venue is not available for standalone bookings.")
        return redirect('venue_list')

    if request.method == 'POST':
        form = BookingRequestForm(request.POST, venue=venue)
        if form.is_valid():
            booking           = form.save(commit=False)
            booking.venue     = venue
            booking.booked_by = request.user
            booking.status    = 'pending'

            if venue.requires_payment:
                booking.payment_required = True
                booking.payment_amount   = venue.payment_amount
                booking.payment_code     = f"VEN-{uuid.uuid4().hex[:8].upper()}"
            else:
                booking.payment_required = False
                booking.payment_amount   = 0.00
                booking.payment_code     = ''

            booking.save()

            if booking.payment_required:
                return redirect('venue_booking_payment', pk=booking.pk)

            messages.success(request, f"Booking request sent for {venue.name}. Awaiting admin approval.")
            return redirect('venue_list')
    else:
        form = BookingRequestForm(venue=venue)

    return render(request, 'venues/request_booking.html', {
        'form':  form,
        'venue': venue,
    })


@login_required
def venue_booking_payment(request, pk):
    booking = get_object_or_404(VenueBooking, pk=pk, booked_by=request.user)
    return render(request, 'venues/venue_booking_payment.html', {'booking': booking})