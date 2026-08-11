from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from .models import Venue, VenueBooking
from .forms import VenueForm, BookingRequestForm


class VenueModelTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="organizer",
            password="testpass123",
            role="organizer",
        )

        self.venue = Venue.objects.create(
            name="Test Arena",
            city="Dhaka",
            address="Test Address",
            capacity=100,
            rental_fee=Decimal("5000.00"),
            description="Test venue",
            is_available=True,
        )

    def test_venue_creation(self):
        self.assertEqual(self.venue.name, "Test Arena")
        self.assertEqual(self.venue.city, "Dhaka")
        self.assertEqual(self.venue.capacity, 100)
        self.assertEqual(self.venue.rental_fee, Decimal("5000.00"))
        self.assertTrue(self.venue.is_available)

    def test_venue_str(self):
        self.assertEqual(
            str(self.venue),
            "Test Arena, Dhaka"
        )


class VenueBookingModelTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="organizer",
            password="testpass123",
            role="organizer",
        )

        self.venue = Venue.objects.create(
            name="Test Arena",
            city="Dhaka",
            address="Test Address",
            capacity=100,
            rental_fee=Decimal("5000.00"),
            is_available=True,
        )

        self.booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user,
            start_date=date(2026, 8, 15),
            end_date=date(2026, 8, 17),
            status="pending",
        )

    def test_booking_creation(self):
        self.assertEqual(self.booking.venue, self.venue)
        self.assertEqual(self.booking.booked_by, self.user)
        self.assertEqual(self.booking.status, "pending")

    def test_booking_id_generation(self):
        self.assertEqual(
            self.booking.booking_id,
            f"BK-{self.booking.pk:05d}"
        )

    def test_booking_str(self):
        expected = (
            f"{self.venue.name} | "
            f"{self.booking.start_date} → "
            f"{self.booking.end_date} "
            f"[{self.booking.status}]"
        )

        self.assertEqual(
            str(self.booking),
            expected
        )

    def test_payment_defaults(self):
        self.assertFalse(self.booking.payment_required)
        self.assertEqual(
            self.booking.payment_amount,
            Decimal("0.00")
        )
        self.assertEqual(self.booking.payment_code, "")
        self.assertFalse(self.booking.payment_confirmed)


class VenueFormTest(TestCase):

    def test_valid_venue_form(self):
        form = VenueForm(
            data={
                "name": "New Arena",
                "city": "Dhaka",
                "address": "Test Address",
                "capacity": 200,
                "rental_fee": "10000.00",
                "description": "Gaming venue",
                "is_available": True,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_required_venue_fields(self):
        form = VenueForm(data={})

        self.assertFalse(form.is_valid())

        self.assertIn("name", form.errors)
        self.assertIn("capacity", form.errors)


class BookingRequestFormTest(TestCase):

    def setUp(self):
        self.venue = Venue.objects.create(
            name="Booking Arena",
            city="Dhaka",
            address="Test Address",
            capacity=100,
            rental_fee=Decimal("5000.00"),
            is_available=True,
        )

        self.user = CustomUser.objects.create_user(
            username="organizer",
            password="testpass123",
            role="organizer",
        )

    def test_valid_booking_dates(self):
        form = BookingRequestForm(
            data={
                "start_date": "2026-08-15",
                "end_date": "2026-08-17",
            },
            venue=self.venue,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_end_date_before_start_date(self):
        form = BookingRequestForm(
            data={
                "start_date": "2026-08-20",
                "end_date": "2026-08-15",
            },
            venue=self.venue,
        )

        self.assertFalse(form.is_valid())

        self.assertIn(
            "End date must be on or after the start date.",
            str(form.errors)
        )

    def test_overlapping_booking_is_rejected(self):
        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user,
            start_date=date(2026, 8, 15),
            end_date=date(2026, 8, 20),
            status="confirmed",
        )

        form = BookingRequestForm(
            data={
                "start_date": "2026-08-18",
                "end_date": "2026-08-22",
            },
            venue=self.venue,
        )

        self.assertFalse(form.is_valid())

        self.assertIn(
            "These dates overlap with an existing booking",
            str(form.errors)
        )

    def test_non_overlapping_booking_is_accepted(self):
        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user,
            start_date=date(2026, 8, 15),
            end_date=date(2026, 8, 20),
            status="confirmed",
        )

        form = BookingRequestForm(
            data={
                "start_date": "2026-08-21",
                "end_date": "2026-08-25",
            },
            venue=self.venue,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_cancelled_booking_does_not_create_conflict(self):
        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.user,
            start_date=date(2026, 8, 15),
            end_date=date(2026, 8, 20),
            status="cancelled",
        )

        form = BookingRequestForm(
            data={
                "start_date": "2026-08-18",
                "end_date": "2026-08-22",
            },
            venue=self.venue,
        )

        self.assertTrue(form.is_valid(), form.errors)


class VenueViewTest(TestCase):

    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username="admin",
            password="adminpass123",
            role="admin",
        )

        self.organizer = CustomUser.objects.create_user(
            username="organizer",
            password="organizerpass123",
            role="organizer",
        )

        self.other_organizer = CustomUser.objects.create_user(
            username="otherorganizer",
            password="otherpass123",
            role="organizer",
        )

        self.player = CustomUser.objects.create_user(
            username="player",
            password="playerpass123",
            role="player",
        )

        self.venue = Venue.objects.create(
            name="Test Arena",
            city="Dhaka",
            address="Test Address",
            capacity=100,
            rental_fee=Decimal("5000.00"),
            is_available=True,
        )

        self.hidden_venue = Venue.objects.create(
            name="East West University",
            city="Dhaka",
            address="EWU Address",
            capacity=500,
            rental_fee=Decimal("10000.00"),
            is_available=True,
        )

    def test_admin_can_manage_venues(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("manage_venues")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "venues/manage_venues.html"
        )

    def test_non_admin_cannot_manage_venues(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse("manage_venues")
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse("dashboard")
        )

    def test_admin_can_add_venue(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("venue_add"),
            {
                "name": "New Venue",
                "city": "Dhaka",
                "address": "New Address",
                "capacity": 300,
                "rental_fee": "7000.00",
                "description": "New venue",
                "is_available": True,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Venue.objects.filter(
                name="New Venue"
            ).exists()
        )

    def test_non_admin_cannot_add_venue(self):
        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse("venue_add"),
            {
                "name": "Unauthorized Venue",
                "city": "Dhaka",
                "address": "Address",
                "capacity": 100,
                "rental_fee": "5000.00",
                "description": "Test",
                "is_available": True,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Venue.objects.filter(
                name="Unauthorized Venue"
            ).exists()
        )

    def test_admin_can_edit_venue(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "venue_edit",
                kwargs={"pk": self.venue.pk}
            ),
            {
                "name": "Updated Arena",
                "city": "Dhaka",
                "address": "Updated Address",
                "capacity": 200,
                "rental_fee": "8000.00",
                "description": "Updated description",
                "is_available": True,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.venue.refresh_from_db()

        self.assertEqual(
            self.venue.name,
            "Updated Arena"
        )

        self.assertEqual(
            self.venue.capacity,
            200
        )

    def test_admin_can_delete_venue(self):
        self.client.force_login(self.admin)

        venue_id = self.venue.pk

        response = self.client.post(
            reverse(
                "venue_delete",
                kwargs={"pk": venue_id}
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Venue.objects.filter(
                pk=venue_id
            ).exists()
        )

    def test_non_admin_cannot_delete_venue(self):
        self.client.force_login(self.organizer)

        venue_id = self.venue.pk

        response = self.client.post(
            reverse(
                "venue_delete",
                kwargs={"pk": venue_id}
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Venue.objects.filter(
                pk=venue_id
            ).exists()
        )

    def test_venue_list_hides_east_west_university(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse("venue_list")
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "Test Arena"
        )

        self.assertNotContains(
            response,
            "East West University"
        )

    def test_organizer_can_open_booking_page(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse(
                "request_booking",
                kwargs={"venue_id": self.venue.pk}
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "venues/request_booking.html"
        )

    def test_player_cannot_request_booking(self):
        self.client.force_login(self.player)

        response = self.client.get(
            reverse(
                "request_booking",
                kwargs={"venue_id": self.venue.pk}
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            response.url,
            reverse("venue_list")
        )

    def test_hidden_venue_cannot_be_booked_directly(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse(
                "request_booking",
                kwargs={
                    "venue_id": self.hidden_venue.pk
                }
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            response.url,
            reverse("venue_list")
        )

    def test_organizer_can_request_booking(self):
        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse(
                "request_booking",
                kwargs={
                    "venue_id": self.venue.pk
                }
            ),
            {
                "start_date": "2026-09-01",
                "end_date": "2026-09-03",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            VenueBooking.objects.filter(
                venue=self.venue,
                booked_by=self.organizer,
                start_date=date(2026, 9, 1),
                end_date=date(2026, 9, 3),
            ).exists()
        )

    def test_booking_conflict_is_rejected(self):
        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 5),
            status="confirmed",
        )

        self.client.force_login(self.other_organizer)

        response = self.client.post(
            reverse(
                "request_booking",
                kwargs={
                    "venue_id": self.venue.pk
                }
            ),
            {
                "start_date": "2026-09-03",
                "end_date": "2026-09-07",
            },
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "venues/request_booking.html"
        )

        self.assertEqual(
            VenueBooking.objects.filter(
                venue=self.venue
            ).count(),
            1
        )

    def test_payment_information_is_generated(self):
        self.venue.requires_payment = True
        self.venue.payment_amount = Decimal("5000.00")
        self.venue.save()

        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse(
                "request_booking",
                kwargs={
                    "venue_id": self.venue.pk
                }
            ),
            {
                "start_date": "2026-10-01",
                "end_date": "2026-10-03",
            },
        )

        booking = VenueBooking.objects.get(
            venue=self.venue,
            booked_by=self.organizer,
        )

        self.assertTrue(
            booking.payment_required
        )

        self.assertEqual(
            booking.payment_amount,
            Decimal("5000.00")
        )

        self.assertTrue(
            booking.payment_code
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertEqual(
            response.url,
            reverse(
                "venue_booking_payment",
                kwargs={"pk": booking.pk}
            )
        )

    def test_booking_owner_can_view_payment_slip(self):
        self.venue.requires_payment = True
        self.venue.payment_amount = Decimal("5000.00")
        self.venue.save()

        booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 11, 1),
            end_date=date(2026, 11, 3),
            status="pending",
            payment_required=True,
            payment_amount=Decimal("5000.00"),
            payment_code="AB123",
        )

        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                kwargs={"pk": booking.pk}
            )
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "venues/venue_booking_payment.html"
        )

    def test_other_organizer_cannot_view_payment_slip(self):
        booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 11, 12),
            status="pending",
            payment_required=True,
            payment_amount=Decimal("5000.00"),
            payment_code="XY789",
        )

        self.client.force_login(
            self.other_organizer
        )

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                kwargs={"pk": booking.pk}
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertEqual(
            response.url,
            reverse("dashboard")
        )

    def test_admin_can_view_payment_slip(self):
        booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 12, 1),
            end_date=date(2026, 12, 3),
            status="pending",
            payment_required=True,
            payment_amount=Decimal("5000.00"),
            payment_code="AD123",
        )

        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                kwargs={"pk": booking.pk}
            )
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "venues/venue_booking_payment.html"
        )

    def test_booking_id_format(self):
        booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2027, 1, 1),
            end_date=date(2027, 1, 3),
            status="pending",
        )

        self.assertEqual(
            booking.booking_id,
            f"BK-{booking.pk:05d}"
        )

    def test_cancelled_booking_does_not_block_new_booking(self):
        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2027, 2, 1),
            end_date=date(2027, 2, 5),
            status="cancelled",
        )

        form = BookingRequestForm(
            data={
                "start_date": "2027-02-03",
                "end_date": "2027-02-07",
            },
            venue=self.venue,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors
        )

    def test_admin_delete_nonexistent_venue_returns_404(self):
        self.client.force_login(
            self.admin
        )

        response = self.client.post(
            reverse(
                "venue_delete",
                kwargs={"pk": 99999}
            )
        )

        self.assertEqual(
            response.status_code,
            404
        )

