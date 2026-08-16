from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from venues.models import Venue, VenueBooking


class VenueIntegrationTests(TestCase):

    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username="admin",
            password="StrongPass123!",
            role="admin",
        )

        self.organizer = CustomUser.objects.create_user(
            username="organizer",
            password="StrongPass123!",
            role="organizer",
        )

        self.player = CustomUser.objects.create_user(
            username="player",
            password="StrongPass123!",
            role="player",
        )

        self.venue = Venue.objects.create(
            name="Arena",
            city="Dhaka",
            address="Dhaka",
            capacity=100,
            rental_fee=0,
            is_available=True,
        )

    # IT-VEN-01
    def test_admin_can_create_venue(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("venue_add"),
            {
                "name": "New Arena",
                "address": "Dhaka",
                "city": "Dhaka",
                "capacity": 200,
                "rental_fee": "5000",
                "description": "Gaming arena",
                "is_available": True,
            }
        )

        self.assertRedirects(
            response,
            reverse("manage_venues")
        )

        venue = Venue.objects.get(
            name="New Arena"
        )

        self.assertEqual(
            venue.rental_fee,
            5000
        )

        self.assertTrue(
            venue.requires_payment
        )

    # IT-VEN-02
    def test_non_admin_cannot_create_venue(self):
        self.client.force_login(self.organizer)

        self.client.post(
            reverse("venue_add"),
            {
                "name": "Unauthorized Arena",
                "address": "Dhaka",
                "city": "Dhaka",
                "capacity": 100,
                "rental_fee": 0,
                "description": "",
                "is_available": True,
            }
        )

        self.assertFalse(
            Venue.objects.filter(
                name="Unauthorized Arena"
            ).exists()
        )

    # IT-VEN-03
    def test_organizer_can_request_free_venue(self):
        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse(
                "request_booking",
                args=[self.venue.pk]
            ),
            {
                "start_date": "2026-09-10",
                "end_date": "2026-09-12",
            }
        )

        self.assertRedirects(
            response,
            reverse("venue_list")
        )

        booking = VenueBooking.objects.get(
            venue=self.venue,
            booked_by=self.organizer
        )

        self.assertEqual(
            booking.status,
            "pending"
        )

        self.assertFalse(
            booking.payment_required
        )

    # IT-VEN-04
    def test_player_cannot_request_venue(self):
        self.client.force_login(self.player)

        self.client.post(
            reverse(
                "request_booking",
                args=[self.venue.pk]
            ),
            {
                "start_date": "2026-09-10",
                "end_date": "2026-09-12",
            }
        )

        self.assertFalse(
            VenueBooking.objects.filter(
                venue=self.venue,
                booked_by=self.player
            ).exists()
        )

    # IT-VEN-05
    def test_overlapping_booking_is_rejected(self):
        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 12),
            status="confirmed",
        )

        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse(
                "request_booking",
                args=[self.venue.pk]
            ),
            {
                "start_date": "2026-09-11",
                "end_date": "2026-09-13",
            }
        )

        self.assertEqual(
            VenueBooking.objects.filter(
                venue=self.venue
            ).count(),
            1
        )

    # IT-VEN-06
    def test_invalid_date_range_is_rejected(self):
        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse(
                "request_booking",
                args=[self.venue.pk]
            ),
            {
                "start_date": "2026-09-15",
                "end_date": "2026-09-10",
            }
        )

        self.assertEqual(
            VenueBooking.objects.filter(
                venue=self.venue
            ).count(),
            0
        )

    # IT-VEN-07
    def test_paid_venue_creates_payment_information(self):
        self.venue.rental_fee = 5000
        self.venue.payment_amount = 5000
        self.venue.requires_payment = True
        self.venue.save()

        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse(
                "request_booking",
                args=[self.venue.pk]
            ),
            {
                "start_date": "2026-09-20",
                "end_date": "2026-09-22",
            }
        )

        booking = VenueBooking.objects.get(
            venue=self.venue
        )

        self.assertTrue(
            booking.payment_required
        )

        self.assertEqual(
            booking.payment_amount,
            5000
        )

        self.assertTrue(
            booking.payment_code
        )

        self.assertRedirects(
            response,
            reverse(
                "venue_booking_payment",
                args=[booking.pk]
            )
        )

    # IT-VEN-08
    def test_booking_owner_can_view_payment_page(self):
        self.venue.rental_fee = 5000
        self.venue.payment_amount = 5000
        self.venue.requires_payment = True
        self.venue.save()

        booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 9, 20),
            end_date=date(2026, 9, 22),
            status="pending",
            payment_required=True,
            payment_amount=5000,
            payment_code="AB123",
        )

        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                args=[booking.pk]
            )
        )

        self.assertEqual(
            response.status_code,
            200
        )

    # IT-VEN-09
    def test_other_user_cannot_view_booking_payment(self):
        booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 9, 20),
            end_date=date(2026, 9, 22),
            status="pending",
        )

        self.client.force_login(self.player)

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                args=[booking.pk]
            )
        )

        self.assertRedirects(
            response,
            reverse("dashboard")
        )

    # IT-VEN-10
    def test_admin_can_view_other_users_booking_payment(self):
        booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 9, 20),
            end_date=date(2026, 9, 22),
            status="pending",
        )

        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                args=[booking.pk]
            )
        )

        self.assertEqual(
            response.status_code,
            200
        )