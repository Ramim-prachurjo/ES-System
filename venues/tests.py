from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser

from .models import Venue, VenueBooking
from .forms import VenueForm, BookingRequestForm


# ============================================================
# MODEL TESTS
# ============================================================

class VenueModelTest(TestCase):

    def setUp(self):
        self.venue = Venue.objects.create(
            name="Test Arena",
            city="Dhaka",
            address="Dhaka, Bangladesh",
            capacity=100,
            rental_fee=Decimal("5000.00"),
            description="A test gaming venue",
            is_available=True,
            requires_payment=True,
            payment_amount=Decimal("5000.00"),
        )

    def test_venue_creation(self):
        self.assertEqual(self.venue.name, "Test Arena")
        self.assertEqual(self.venue.city, "Dhaka")
        self.assertEqual(self.venue.capacity, 100)
        self.assertTrue(self.venue.is_available)

    def test_venue_str(self):
        self.assertEqual(
            str(self.venue),
            "Test Arena, Dhaka"
        )

    def test_venue_payment_fields(self):
        self.assertTrue(self.venue.requires_payment)
        self.assertEqual(
            self.venue.payment_amount,
            Decimal("5000.00")
        )

    def test_venue_default_values(self):
        venue = Venue.objects.create(
            name="Free Arena",
            city="Dhaka",
            address="Test Address",
            capacity=50,
        )

        self.assertEqual(
            venue.rental_fee,
            Decimal("0.00")
        )
        self.assertFalse(venue.requires_payment)
        self.assertEqual(
            venue.payment_amount,
            Decimal("0.00")
        )
        self.assertTrue(venue.is_available)


class VenueBookingModelTest(TestCase):

    def setUp(self):
        self.organizer = CustomUser.objects.create_user(
            username="organizer",
            password="testpass123",
            role="organizer",
        )

        self.venue = Venue.objects.create(
            name="Booking Arena",
            city="Dhaka",
            address="Test Address",
            capacity=100,
            rental_fee=Decimal("5000.00"),
            is_available=True,
            requires_payment=True,
            payment_amount=Decimal("5000.00"),
        )

        self.booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 8, 20),
            end_date=date(2026, 8, 22),
            status="pending",
            payment_required=True,
            payment_amount=Decimal("5000.00"),
            payment_code="AB123",
        )

    def test_booking_creation(self):
        self.assertEqual(
            self.booking.venue,
            self.venue
        )

        self.assertEqual(
            self.booking.booked_by,
            self.organizer
        )

        self.assertEqual(
            self.booking.status,
            "pending"
        )

    def test_booking_id_format(self):
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

    def test_booking_payment_fields(self):
        self.assertTrue(
            self.booking.payment_required
        )

        self.assertEqual(
            self.booking.payment_amount,
            Decimal("5000.00")
        )

        self.assertEqual(
            self.booking.payment_code,
            "AB123"
        )

        self.assertFalse(
            self.booking.payment_confirmed
        )

    def test_cancelled_booking_status(self):
        self.booking.status = "cancelled"
        self.booking.save()

        self.booking.refresh_from_db()

        self.assertEqual(
            self.booking.status,
            "cancelled"
        )


# ============================================================
# FORM TESTS
# ============================================================

class VenueFormTest(TestCase):

    def test_valid_venue_form(self):
        form = VenueForm(
            data={
                "name": "New Arena",
                "address": "Dhaka",
                "city": "Dhaka",
                "capacity": 100,
                "rental_fee": "5000.00",
                "description": "Gaming arena",
                "is_available": True,
            }
        )

        self.assertTrue(
            form.is_valid(),
            form.errors
        )

    def test_venue_name_is_required(self):
        form = VenueForm(
            data={
                "name": "",
                "address": "Dhaka",
                "city": "Dhaka",
                "capacity": 100,
                "rental_fee": "5000.00",
                "description": "",
                "is_available": True,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_venue_capacity_is_required(self):
        form = VenueForm(
            data={
                "name": "Arena",
                "address": "Dhaka",
                "city": "Dhaka",
                "capacity": "",
                "rental_fee": "5000.00",
                "description": "",
                "is_available": True,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("capacity", form.errors)


class BookingRequestFormTest(TestCase):

    def setUp(self):
        self.venue = Venue.objects.create(
            name="Form Arena",
            city="Dhaka",
            address="Dhaka",
            capacity=100,
            rental_fee=Decimal("5000.00"),
            is_available=True,
        )

    def test_valid_booking_dates(self):
        form = BookingRequestForm(
            data={
                "start_date": "2026-08-20",
                "end_date": "2026-08-22",
            },
            venue=self.venue,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors
        )

    def test_end_date_before_start_date(self):
        form = BookingRequestForm(
            data={
                "start_date": "2026-08-25",
                "end_date": "2026-08-20",
            },
            venue=self.venue,
        )

        self.assertFalse(form.is_valid())

    def test_same_start_and_end_date_is_valid(self):
        form = BookingRequestForm(
            data={
                "start_date": "2026-08-20",
                "end_date": "2026-08-20",
            },
            venue=self.venue,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors
        )

    def test_overlapping_booking_is_rejected(self):
        organizer = CustomUser.objects.create_user(
            username="bookingorganizer",
            password="testpass123",
            role="organizer",
        )

        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=organizer,
            start_date=date(2026, 8, 20),
            end_date=date(2026, 8, 22),
            status="confirmed",
        )

        form = BookingRequestForm(
            data={
                "start_date": "2026-08-21",
                "end_date": "2026-08-23",
            },
            venue=self.venue,
        )

        self.assertFalse(form.is_valid())

    def test_non_overlapping_booking_is_valid(self):
        organizer = CustomUser.objects.create_user(
            username="anotherorganizer",
            password="testpass123",
            role="organizer",
        )

        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=organizer,
            start_date=date(2026, 8, 20),
            end_date=date(2026, 8, 22),
            status="confirmed",
        )

        form = BookingRequestForm(
            data={
                "start_date": "2026-08-23",
                "end_date": "2026-08-25",
            },
            venue=self.venue,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors
        )

    def test_cancelled_booking_does_not_create_conflict(self):
        organizer = CustomUser.objects.create_user(
            username="cancelledorganizer",
            password="testpass123",
            role="organizer",
        )

        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=organizer,
            start_date=date(2026, 8, 20),
            end_date=date(2026, 8, 22),
            status="cancelled",
        )

        form = BookingRequestForm(
            data={
                "start_date": "2026-08-20",
                "end_date": "2026-08-22",
            },
            venue=self.venue,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors
        )


# ============================================================
# VIEW TESTS
# ============================================================

class VenueViewTest(TestCase):

    def setUp(self):
        # ----------------------------------------------------
        # USERS
        # ----------------------------------------------------

        self.admin = CustomUser.objects.create_user(
            username="admin",
            password="testpass123",
            role="admin",
        )

        self.organizer = CustomUser.objects.create_user(
            username="organizer",
            password="testpass123",
            role="organizer",
        )

        self.other_organizer = CustomUser.objects.create_user(
            username="otherorganizer",
            password="testpass123",
            role="organizer",
        )

        self.player = CustomUser.objects.create_user(
            username="player",
            password="testpass123",
            role="player",
        )

        # ----------------------------------------------------
        # VENUES
        # ----------------------------------------------------

        self.venue = Venue.objects.create(
            name="Main Arena",
            city="Dhaka",
            address="Main Street, Dhaka",
            capacity=100,
            rental_fee=Decimal("5000.00"),
            description="Main gaming venue",
            is_available=True,
            requires_payment=True,
            payment_amount=Decimal("5000.00"),
        )

        self.free_venue = Venue.objects.create(
            name="Free Arena",
            city="Dhaka",
            address="Free Street",
            capacity=50,
            rental_fee=Decimal("0.00"),
            description="Free venue",
            is_available=True,
            requires_payment=False,
            payment_amount=Decimal("0.00"),
        )

        self.hidden_venue = Venue.objects.create(
            name="East West University",
            city="Dhaka",
            address="Aftabnagar",
            capacity=200,
            rental_fee=Decimal("0.00"),
            is_available=True,
            requires_payment=False,
            payment_amount=Decimal("0.00"),
        )

        # ----------------------------------------------------
        # BOOKING
        # ----------------------------------------------------

        self.booking = VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 8, 20),
            end_date=date(2026, 8, 22),
            status="pending",
            payment_required=True,
            payment_amount=Decimal("5000.00"),
            payment_code="AB123",
        )

    # ========================================================
    # MANAGE VENUES
    # ========================================================

    def test_admin_can_manage_venues(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("manage_venues")
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "venues/manage_venues.html"
        )

    def test_non_admin_cannot_manage_venues(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse("manage_venues")
        )

        self.assertRedirects(
            response,
            reverse("dashboard")
        )

    def test_player_cannot_manage_venues(self):
        self.client.force_login(self.player)

        response = self.client.get(
            reverse("manage_venues")
        )

        self.assertRedirects(
            response,
            reverse("dashboard")
        )

    # ========================================================
    # ADD VENUE
    # ========================================================

    def test_admin_can_open_add_venue_page(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("venue_add")
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "venues/venue_form.html"
        )

    def test_non_admin_cannot_add_venue(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse("venue_add")
        )

        self.assertRedirects(
            response,
            reverse("dashboard")
        )

    def test_admin_can_add_venue(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("venue_add"),
            {
                "name": "New Test Arena",
                "address": "New Address",
                "city": "Dhaka",
                "capacity": 150,
                "rental_fee": "7500.00",
                "description": "New venue",
                "is_available": True,
            }
        )

        self.assertRedirects(
            response,
            reverse("manage_venues")
        )

        venue = Venue.objects.get(
            name="New Test Arena"
        )

        self.assertEqual(
            venue.rental_fee,
            Decimal("7500.00")
        )

        self.assertTrue(
            venue.requires_payment
        )

        self.assertEqual(
            venue.payment_amount,
            Decimal("7500.00")
        )

    # ========================================================
    # EDIT VENUE
    # ========================================================

    def test_admin_can_edit_venue(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "venue_edit",
                kwargs={"pk": self.venue.pk}
            ),
            {
                "name": "Updated Arena",
                "address": "Updated Address",
                "city": "Dhaka",
                "capacity": 200,
                "rental_fee": "9000.00",
                "description": "Updated venue",
                "is_available": True,
            }
        )

        self.assertRedirects(
            response,
            reverse("manage_venues")
        )

        self.venue.refresh_from_db()

        self.assertEqual(
            self.venue.name,
            "Updated Arena"
        )

        self.assertEqual(
            self.venue.capacity,
            200
        )

        self.assertEqual(
            self.venue.rental_fee,
            Decimal("9000.00")
        )

        self.assertTrue(
            self.venue.requires_payment
        )

    def test_non_admin_cannot_edit_venue(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse(
                "venue_edit",
                kwargs={"pk": self.venue.pk}
            )
        )

        self.assertRedirects(
            response,
            reverse("dashboard")
        )

    # ========================================================
    # DELETE VENUE
    # ========================================================

    def test_admin_can_delete_venue(self):
        self.client.force_login(self.admin)

        venue_id = self.venue.pk

        response = self.client.post(
            reverse(
                "venue_delete",
                kwargs={"pk": venue_id}
            )
        )

        self.assertRedirects(
            response,
            reverse("manage_venues")
        )

        self.assertFalse(
            Venue.objects.filter(
                pk=venue_id
            ).exists()
        )

    def test_non_admin_cannot_delete_venue(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse(
                "venue_delete",
                kwargs={"pk": self.venue.pk}
            )
        )

        self.assertRedirects(
            response,
            reverse("dashboard")
        )

    def test_admin_delete_nonexistent_venue_returns_404(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "venue_delete",
                kwargs={"pk": 999999}
            )
        )

        self.assertEqual(
            response.status_code,
            404
        )

    # ========================================================
    # VENUE LIST
    # ========================================================

    def test_logged_in_user_can_view_venue_list(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse("venue_list")
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "venues/venue_list.html"
        )

    def test_venue_list_hides_east_west_university(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse("venue_list")
        )

        venue_data = response.context["venue_data"]

        venue_names = [
            item["venue"].name
            for item in venue_data
        ]

        self.assertNotIn(
            "East West University",
            venue_names
        )

        self.assertIn(
            "Main Arena",
            venue_names
        )

    def test_venue_list_contains_booking_information(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse("venue_list")
        )

        venue_data = response.context["venue_data"]

        main_arena_data = next(
            item for item in venue_data
            if item["venue"] == self.venue
        )

        self.assertEqual(
            len(main_arena_data["bookings"]),
            1
        )

        self.assertEqual(
            main_arena_data["bookings"][0]["status"],
            "pending"
        )

    # ========================================================
    # REQUEST BOOKING
    # ========================================================

    def test_organizer_can_open_booking_page(self):
        self.client.force_login(self.organizer)

        # Use free venue so existing self.booking
        # does not cause a conflict.
        response = self.client.get(
            reverse(
                "request_booking",
                kwargs={
                    "venue_id": self.free_venue.pk
                }
            )
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "venues/request_booking.html"
        )

    def test_player_cannot_request_booking(self):
        self.client.force_login(self.player)

        response = self.client.get(
            reverse(
                "request_booking",
                kwargs={
                    "venue_id": self.venue.pk
                }
            )
        )

        self.assertRedirects(
            response,
            reverse("venue_list")
        )

    def test_hidden_venue_cannot_be_booked(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse(
                "request_booking",
                kwargs={
                    "venue_id": self.hidden_venue.pk
                }
            )
        )

        self.assertRedirects(
            response,
            reverse("venue_list")
        )

    def test_organizer_can_request_free_venue(self):
        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse(
                "request_booking",
                kwargs={
                    "venue_id": self.free_venue.pk
                }
            ),
            {
                "start_date": "2026-09-01",
                "end_date": "2026-09-03",
            }
        )

        self.assertRedirects(
            response,
            reverse("venue_list")
        )

        booking = VenueBooking.objects.get(
            venue=self.free_venue,
            booked_by=self.organizer,
        )

        self.assertEqual(
            booking.status,
            "pending"
        )

        self.assertFalse(
            booking.payment_required
        )

    def test_organizer_booking_requires_payment_for_paid_venue(self):
        # Delete existing booking first so dates don't conflict.
        self.booking.delete()

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
            }
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
            self.venue.payment_amount
        )

        self.assertTrue(
            booking.payment_code
        )

        self.assertRedirects(
            response,
            reverse(
                "venue_booking_payment",
                kwargs={"pk": booking.pk}
            )
        )

    def test_booking_conflict_is_rejected(self):
        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse(
                "request_booking",
                kwargs={
                    "venue_id": self.venue.pk
                }
            ),
            {
                "start_date": "2026-08-21",
                "end_date": "2026-08-23",
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        # No second booking should be created.
        self.assertEqual(
            VenueBooking.objects.filter(
                venue=self.venue
            ).count(),
            1
        )

    def test_cancelled_booking_does_not_create_conflict(self):
        self.booking.status = "cancelled"
        self.booking.save()

        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse(
                "request_booking",
                kwargs={
                    "venue_id": self.venue.pk
                }
            ),
            {
                "start_date": "2026-08-20",
                "end_date": "2026-08-22",
            }
        )

        # Payment is required, therefore redirect to payment page.
        new_booking = VenueBooking.objects.exclude(
            pk=self.booking.pk
        ).get(
            venue=self.venue
        )

        self.assertRedirects(
            response,
            reverse(
                "venue_booking_payment",
                kwargs={"pk": new_booking.pk}
            )
        )

        self.assertEqual(
            VenueBooking.objects.filter(
                venue=self.venue
            ).count(),
            2
        )

    # ========================================================
    # PAYMENT SLIP
    # ========================================================

    def test_booking_owner_can_view_payment_slip(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                kwargs={
                    "pk": self.booking.pk
                }
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

    def test_admin_can_view_payment_slip(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                kwargs={
                    "pk": self.booking.pk
                }
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
        self.client.force_login(
            self.other_organizer
        )

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                kwargs={
                    "pk": self.booking.pk
                }
            )
        )

        self.assertRedirects(
            response,
            reverse("dashboard")
        )

    def test_player_cannot_view_payment_slip(self):
        self.client.force_login(self.player)

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                kwargs={
                    "pk": self.booking.pk
                }
            )
        )

        self.assertRedirects(
            response,
            reverse("dashboard")
        )

    def test_nonexistent_booking_payment_page_returns_404(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                kwargs={"pk": 999999}
            )
        )

        self.assertEqual(
            response.status_code,
            404
        )

    # ========================================================
    # LOGIN PROTECTION
    # ========================================================

    def test_manage_venues_requires_login(self):
        response = self.client.get(
            reverse("manage_venues")
        )

        self.assertEqual(
            response.status_code,
            302
        )

    def test_venue_list_requires_login(self):
        response = self.client.get(
            reverse("venue_list")
        )

        self.assertEqual(
            response.status_code,
            302
        )

    def test_request_booking_requires_login(self):
        response = self.client.get(
            reverse(
                "request_booking",
                kwargs={
                    "venue_id": self.venue.pk
                }
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

    def test_payment_page_requires_login(self):
        response = self.client.get(
            reverse(
                "venue_booking_payment",
                kwargs={
                    "pk": self.booking.pk
                }
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )