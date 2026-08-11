from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from venues.models import Venue, VenueBooking
from venues.forms import VenueForm, BookingRequestForm


class VenueModelTest(TestCase):

    def setUp(self):
        self.venue = Venue.objects.create(
            name="Test Arena",
            city="Dhaka",
            address="Dhaka, Bangladesh",
            capacity=100,
            rental_fee=Decimal("5000.00"),
            description="Test venue",
            is_available=True,
            requires_payment=True,
            payment_amount=Decimal("5000.00"),
        )

    def test_venue_creation(self):
        self.assertEqual(self.venue.name, "Test Arena")
        self.assertEqual(self.venue.city, "Dhaka")
        self.assertEqual(self.venue.capacity, 100)

    def test_venue_string(self):
        self.assertEqual(
            str(self.venue),
            "Test Arena, Dhaka"
        )

    def test_venue_booking_id(self):
        user = CustomUser.objects.create_user(
            username="organizer1",
            password="password123",
            role="organizer",
        )

        booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=user,
            start_date=date(2026, 8, 10),
            end_date=date(2026, 8, 12),
        )

        self.assertEqual(
            booking.booking_id,
            f"BK-{booking.pk:05d}"
        )

    def test_venue_booking_string(self):
        user = CustomUser.objects.create_user(
            username="organizer2",
            password="password123",
            role="organizer",
        )

        booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=user,
            start_date=date(2026, 8, 10),
            end_date=date(2026, 8, 12),
            status="pending",
        )

        self.assertEqual(
            str(booking),
            "Test Arena | 2026-08-10 → 2026-08-12 [pending]"
        )


class VenueFormTest(TestCase):

    def test_valid_venue_form(self):
        form = VenueForm(data={
            "name": "New Arena",
            "address": "Dhaka",
            "city": "Dhaka",
            "capacity": 200,
            "rental_fee": "10000.00",
            "description": "Large arena",
            "is_available": True,
        })

        self.assertTrue(form.is_valid())

    def test_venue_form_missing_name(self):
        form = VenueForm(data={
            "address": "Dhaka",
            "city": "Dhaka",
            "capacity": 200,
            "rental_fee": "10000.00",
            "description": "Large arena",
            "is_available": True,
        })

        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class BookingRequestFormTest(TestCase):

    def setUp(self):
        self.venue = Venue.objects.create(
            name="Booking Arena",
            city="Dhaka",
            capacity=100,
            rental_fee=Decimal("5000.00"),
        )

    def test_valid_booking_dates(self):
        form = BookingRequestForm(
            data={
                "start_date": "2026-08-10",
                "end_date": "2026-08-12",
            },
            venue=self.venue,
        )

        self.assertTrue(form.is_valid())

    def test_end_date_before_start_date(self):
        form = BookingRequestForm(
            data={
                "start_date": "2026-08-15",
                "end_date": "2026-08-10",
            },
            venue=self.venue,
        )

        self.assertFalse(form.is_valid())

    def test_overlapping_booking_is_rejected(self):
        user = CustomUser.objects.create_user(
            username="existing",
            password="password123",
            role="organizer",
        )

        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=user,
            start_date=date(2026, 8, 10),
            end_date=date(2026, 8, 15),
            status="confirmed",
        )

        form = BookingRequestForm(
            data={
                "start_date": "2026-08-12",
                "end_date": "2026-08-18",
            },
            venue=self.venue,
        )

        self.assertFalse(form.is_valid())

    def test_cancelled_booking_does_not_create_conflict(self):
        user = CustomUser.objects.create_user(
            username="cancelled_user",
            password="password123",
            role="organizer",
        )

        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=user,
            start_date=date(2026, 8, 10),
            end_date=date(2026, 8, 15),
            status="cancelled",
        )

        form = BookingRequestForm(
            data={
                "start_date": "2026-08-12",
                "end_date": "2026-08-18",
            },
            venue=self.venue,
        )

        self.assertTrue(form.is_valid())


class VenueViewTest(TestCase):

    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username="admin",
            password="password123",
            role="admin",
        )

        self.organizer = CustomUser.objects.create_user(
            username="organizer",
            password="password123",
            role="organizer",
        )

        self.player = CustomUser.objects.create_user(
            username="player",
            password="password123",
            role="player",
        )

        self.venue = Venue.objects.create(
            name="Main Arena",
            city="Dhaka",
            address="Dhaka",
            capacity=100,
            rental_fee=Decimal("5000.00"),
            is_available=True,
        )

    def test_venue_list_requires_login(self):
        response = self.client.get(
            reverse("venue_list")
        )

        self.assertEqual(response.status_code, 302)

    def test_logged_in_user_can_view_venue_list(self):
        self.client.login(
            username="player",
            password="password123",
        )

        response = self.client.get(
            reverse("venue_list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "venues/venue_list.html"
        )

    def test_admin_can_view_manage_venues(self):
        self.client.login(
            username="admin",
            password="password123",
        )

        response = self.client.get(
            reverse("manage_venues")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "venues/manage_venues.html"
        )

    def test_non_admin_cannot_manage_venues(self):
        self.client.login(
            username="organizer",
            password="password123",
        )

        response = self.client.get(
            reverse("manage_venues")
        )

        self.assertEqual(response.status_code, 302)

    def test_admin_can_open_add_venue_page(self):
        self.client.login(
            username="admin",
            password="password123",
        )

        response = self.client.get(
            reverse("venue_add")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "venues/venue_form.html"
        )

    def test_non_admin_cannot_add_venue(self):
        self.client.login(
            username="organizer",
            password="password123",
        )

        response = self.client.get(
            reverse("venue_add")
        )

        self.assertEqual(response.status_code, 302)

    def test_admin_can_create_venue(self):
        self.client.login(
            username="admin",
            password="password123",
        )

        response = self.client.post(
            reverse("venue_add"),
            {
                "name": "New Venue",
                "address": "New Address",
                "city": "Dhaka",
                "capacity": 250,
                "rental_fee": "8000.00",
                "description": "New test venue",
                "is_available": True,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Venue.objects.filter(
                name="New Venue"
            ).exists()
        )

    def test_admin_can_edit_venue(self):
        self.client.login(
            username="admin",
            password="password123",
        )

        response = self.client.post(
            reverse(
                "venue_edit",
                kwargs={"pk": self.venue.pk},
            ),
            {
                "name": "Updated Arena",
                "address": "Updated Address",
                "city": "Dhaka",
                "capacity": 300,
                "rental_fee": "9000.00",
                "description": "Updated",
                "is_available": True,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.venue.refresh_from_db()

        self.assertEqual(
            self.venue.name,
            "Updated Arena"
        )

    def test_admin_can_delete_venue(self):
        self.client.login(
            username="admin",
            password="password123",
        )

        response = self.client.post(
            reverse(
                "venue_delete",
                kwargs={"pk": self.venue.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Venue.objects.filter(
                pk=self.venue.pk
            ).exists()
        )

    def test_non_admin_cannot_delete_venue(self):
        self.client.login(
            username="organizer",
            password="password123",
        )

        response = self.client.post(
            reverse(
                "venue_delete",
                kwargs={"pk": self.venue.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Venue.objects.filter(
                pk=self.venue.pk
            ).exists()
        )


class VenueBookingViewTest(TestCase):

    def setUp(self):
        self.organizer = CustomUser.objects.create_user(
            username="organizer",
            password="password123",
            role="organizer",
        )

        self.player = CustomUser.objects.create_user(
            username="player",
            password="password123",
            role="player",
        )

        self.venue = Venue.objects.create(
            name="Booking Venue",
            city="Dhaka",
            address="Dhaka",
            capacity=100,
            rental_fee=Decimal("5000.00"),
            is_available=True,
            requires_payment=False,
        )

    def test_booking_page_requires_login(self):
        response = self.client.get(
            reverse(
                "request_booking",
                kwargs={"venue_id": self.venue.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

    def test_organizer_can_open_booking_page(self):
        self.client.login(
            username="organizer",
            password="password123",
        )

        response = self.client.get(
            reverse(
                "request_booking",
                kwargs={"venue_id": self.venue.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "venues/request_booking.html"
        )

    def test_non_organizer_cannot_request_booking(self):
        self.client.login(
            username="player",
            password="password123",
        )

        response = self.client.post(
            reverse(
                "request_booking",
                kwargs={"venue_id": self.venue.pk},
            ),
            {
                "start_date": "2026-08-20",
                "end_date": "2026-08-22",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            VenueBooking.objects.filter(
                venue=self.venue
            ).exists()
        )

    def test_organizer_can_request_booking(self):
        self.client.login(
            username="organizer",
            password="password123",
        )

        response = self.client.post(
            reverse(
                "request_booking",
                kwargs={"venue_id": self.venue.pk},
            ),
            {
                "start_date": "2026-08-20",
                "end_date": "2026-08-22",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            VenueBooking.objects.filter(
                venue=self.venue,
                booked_by=self.organizer,
            ).exists()
        )

    def test_overlapping_booking_is_rejected(self):
        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 8, 20),
            end_date=date(2026, 8, 22),
            status="confirmed",
        )

        self.client.login(
            username="organizer",
            password="password123",
        )

        response = self.client.post(
            reverse(
                "request_booking",
                kwargs={"venue_id": self.venue.pk},
            ),
            {
                "start_date": "2026-08-21",
                "end_date": "2026-08-25",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            VenueBooking.objects.filter(
                venue=self.venue
            ).count(),
            1
        )

    def test_payment_page_requires_login(self):
        booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 8, 20),
            end_date=date(2026, 8, 22),
        )

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                kwargs={"pk": booking.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

    def test_booking_owner_can_view_payment_page(self):
        booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 8, 20),
            end_date=date(2026, 8, 22),
        )

        self.client.login(
            username="organizer",
            password="password123",
        )

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                kwargs={"pk": booking.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "venues/venue_booking_payment.html"
        )

    def test_other_player_cannot_view_payment_page(self):
        booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 8, 20),
            end_date=date(2026, 8, 22),
        )

        self.client.login(
            username="player",
            password="password123",
        )

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                kwargs={"pk": booking.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

    def test_admin_can_view_payment_page(self):
        admin = CustomUser.objects.create_user(
            username="admin",
            password="password123",
            role="admin",
        )

        booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 8, 20),
            end_date=date(2026, 8, 22),
        )

        self.client.login(
            username="admin",
            password="password123",
        )

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                kwargs={"pk": booking.pk},
            )
        )

        self.assertEqual(response.status_code, 200)

