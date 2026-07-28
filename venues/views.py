import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Venue, VenueBooking
from .forms import BookingRequestForm


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