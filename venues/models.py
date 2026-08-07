from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField
import uuid


class Venue(models.Model):
    name             = models.CharField(max_length=150)
    city             = models.CharField(max_length=100, blank=True)
    address          = models.TextField(blank=True)
    capacity         = models.PositiveIntegerField()
    rental_fee       = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description      = models.TextField(blank=True)
    photo            = CloudinaryField('venue_photo', blank=True, null=True)
    is_available     = models.BooleanField(default=True)
    requires_payment = models.BooleanField(default=False)
    payment_amount   = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.name}, {self.city}"


class VenueBooking(models.Model):

    BOOKING_STATUS = [
        ('pending',   'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    venue      = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='bookings')
    tournament = models.OneToOneField('tournaments.Tournament', on_delete=models.CASCADE, related_name='venue_booking', null=True, blank=True)
    booked_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='venue_bookings')
    start_date = models.DateField()
    end_date   = models.DateField()
    status     = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    # ── Payment fields (mirrors tournament payment flow) ──
    payment_required  = models.BooleanField(default=False)
    payment_amount    = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_code      = models.CharField(max_length=20, blank=True)
    payment_confirmed = models.BooleanField(default=False)

    @property
    def booking_id(self):
        return f"BK-{self.pk:05d}"

    def __str__(self):
        return f"{self.venue.name} | {self.start_date} → {self.end_date} [{self.status}]"
