from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from venues.models import Venue, VenueBooking


class VenueManagementFrontendTests(TestCase):
    """Frontend/template tests for the admin venue management interface."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            username="frontend_admin",
            email="admin@test.com",
            password="TestPass123!",
            role="admin",
        )

        cls.venue = Venue.objects.create(
            name="Test Arena",
            city="Dhaka",
            address="123 Test Street, Dhaka",
            capacity=500,
            rental_fee=Decimal("5000.00"),
            description="A test tournament venue.",
            is_available=True,
        )

    def test_admin_management_page_loads(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("manage_venues"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "venues/manage_venues.html")

    def test_management_page_displays_venue_information(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("manage_venues"))

        self.assertContains(response, self.venue.name)
        self.assertContains(response, self.venue.address)
        self.assertContains(response, str(self.venue.capacity))
        self.assertContains(response, "5000.00")

    def test_management_page_contains_add_venue_link(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("manage_venues"))

        self.assertContains(
            response,
            reverse("venue_add"),
        )

    def test_management_page_contains_edit_link(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("manage_venues"))

        self.assertContains(
            response,
            reverse("venue_edit", args=[self.venue.pk]),
        )

    def test_management_page_contains_delete_link(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("manage_venues"))

        self.assertContains(
            response,
            reverse("venue_delete", args=[self.venue.pk]),
        )

    def test_add_venue_page_renders_form(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("venue_add"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "venues/venue_form.html")

        self.assertContains(response, "Add New Venue")
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="city"')
        self.assertContains(response, 'name="address"')
        self.assertContains(response, 'name="capacity"')
        self.assertContains(response, 'name="rental_fee"')
        self.assertContains(response, 'name="description"')
        self.assertContains(response, 'name="photo"')
        self.assertContains(response, 'name="is_available"')

    def test_edit_venue_page_displays_existing_data(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("venue_edit", args=[self.venue.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "venues/venue_form.html")

        self.assertContains(response, "Update Venue")
        self.assertContains(response, self.venue.name)
        self.assertContains(response, self.venue.city)
        self.assertContains(response, self.venue.address)

    def test_delete_confirmation_page_displays_venue_name(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("venue_delete", args=[self.venue.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "venues/venue_delete.html")
        self.assertContains(response, self.venue.name)
        self.assertContains(response, "This cannot be undone.")

    def test_delete_page_contains_cancel_link(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("venue_delete", args=[self.venue.pk])
        )

        self.assertContains(
            response,
            reverse("manage_venues"),
        )


class VenueListFrontendTests(TestCase):
    """Frontend/template tests for the organizer-facing venue list."""

    @classmethod
    def setUpTestData(cls):
        cls.organizer = CustomUser.objects.create_user(
            username="frontend_organizer",
            email="organizer@test.com",
            password="TestPass123!",
            role="organizer",
        )

        cls.available_venue = Venue.objects.create(
            name="Available Arena",
            city="Dhaka",
            address="Available Street, Dhaka",
            capacity=300,
            rental_fee=Decimal("3000.00"),
            description="Available tournament venue.",
            is_available=True,
        )

        cls.unavailable_venue = Venue.objects.create(
            name="Unavailable Arena",
            city="Dhaka",
            address="Unavailable Street, Dhaka",
            capacity=200,
            rental_fee=Decimal("2500.00"),
            description="Currently unavailable venue.",
            is_available=False,
        )

        cls.hidden_venue = Venue.objects.create(
            name="East West University",
            city="Dhaka",
            address="Aftabnagar, Dhaka",
            capacity=1000,
            rental_fee=Decimal("0.00"),
            description="Hidden venue.",
            is_available=True,
        )

    def test_venue_list_page_loads(self):
        self.client.force_login(self.organizer)

        response = self.client.get(reverse("venue_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "venues/venue_list.html")

    def test_available_venue_is_displayed(self):
        self.client.force_login(self.organizer)

        response = self.client.get(reverse("venue_list"))

        self.assertContains(response, self.available_venue.name)
        self.assertContains(response, self.available_venue.address)
        self.assertContains(
            response,
            str(self.available_venue.capacity),
        )

    def test_available_venue_contains_booking_link(self):
        self.client.force_login(self.organizer)

        response = self.client.get(reverse("venue_list"))

        self.assertContains(
            response,
            reverse(
                "request_booking",
                args=[self.available_venue.pk],
            ),
        )
        self.assertContains(response, "Request Booking")

    def test_unavailable_venue_is_displayed_without_booking_link(self):
        self.client.force_login(self.organizer)

        response = self.client.get(reverse("venue_list"))

        self.assertContains(response, self.unavailable_venue.name)
        self.assertContains(response, "Currently unavailable")

        self.assertNotContains(
            response,
            reverse(
                "request_booking",
                args=[self.unavailable_venue.pk],
            ),
        )

    def test_hidden_east_west_university_is_not_displayed(self):
        self.client.force_login(self.organizer)

        response = self.client.get(reverse("venue_list"))

        self.assertNotContains(response, "East West University")

    def test_venue_description_is_displayed(self):
        self.client.force_login(self.organizer)

        response = self.client.get(reverse("venue_list"))

        self.assertContains(
            response,
            self.available_venue.description,
        )


class VenueBookingFrontendTests(TestCase):
    """Frontend/template tests for booking request and payment pages."""

    @classmethod
    def setUpTestData(cls):
        cls.organizer = CustomUser.objects.create_user(
            username="booking_organizer",
            email="booking@test.com",
            password="TestPass123!",
            role="organizer",
        )

        cls.other_organizer = CustomUser.objects.create_user(
            username="other_booking_organizer",
            email="other@test.com",
            password="TestPass123!",
            role="organizer",
        )

        cls.admin = CustomUser.objects.create_user(
            username="booking_admin",
            email="bookingadmin@test.com",
            password="TestPass123!",
            role="admin",
        )

        cls.venue = Venue.objects.create(
            name="Booking Arena",
            city="Dhaka",
            address="Booking Street, Dhaka",
            capacity=400,
            rental_fee=Decimal("4000.00"),
            description="Venue for booking tests.",
            is_available=True,
            requires_payment=True,
            payment_amount=Decimal("4000.00"),
        )

        cls.booking = VenueBooking.objects.create(
            venue=cls.venue,
            booked_by=cls.organizer,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            status="pending",
            payment_required=True,
            payment_amount=Decimal("4000.00"),
            payment_code="AB123",
        )

    def test_booking_request_page_loads(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse(
                "request_booking",
                args=[self.venue.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "venues/request_booking.html",
        )

    def test_booking_request_page_displays_venue_information(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse(
                "request_booking",
                args=[self.venue.pk],
            )
        )

        self.assertContains(response, self.venue.name)
        self.assertContains(response, self.venue.address)
        self.assertContains(
            response,
            str(self.venue.capacity),
        )

    def test_booking_request_page_contains_date_fields(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse(
                "request_booking",
                args=[self.venue.pk],
            )
        )

        self.assertContains(response, 'name="start_date"')
        self.assertContains(response, 'name="end_date"')

    def test_booking_payment_page_loads_for_owner(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                args=[self.booking.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "venues/venue_booking_payment.html",
        )

    def test_payment_page_displays_booking_information(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                args=[self.booking.pk],
            )
        )

        self.assertContains(
            response,
            self.booking.booking_id,
        )
        self.assertContains(
            response,
            self.booking.payment_code,
        )
        self.assertContains(
            response,
            self.booking.venue.name,
        )
        self.assertContains(
            response,
            str(self.booking.payment_amount),
        )

    def test_payment_page_displays_payment_instructions(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                args=[self.booking.pk],
            )
        )

        self.assertContains(response, "bKash payment instructions")
        self.assertContains(response, "Send Money")
        self.assertContains(response, self.booking.payment_code)
        self.assertContains(
            response,
            "+880 18 4351 8567",
        )

    def test_payment_page_displays_organizer_information(self):
        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                args=[self.booking.pk],
            )
        )

        self.assertContains(
            response,
            self.organizer.email,
        )

    def test_admin_can_view_payment_page(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                args=[self.booking.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "venues/venue_booking_payment.html",
        )

    def test_other_organizer_cannot_view_payment_page(self):
        self.client.force_login(self.other_organizer)

        response = self.client.get(
            reverse(
                "venue_booking_payment",
                args=[self.booking.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("dashboard"),
        )