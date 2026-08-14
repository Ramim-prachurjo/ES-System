"""Template-facing regression tests for the public and authenticated Accounts UI.

These tests use Django's test client: they verify that pages render, expose the
important controls, and maintain role-based navigation without needing a live
browser or external database.
"""

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class PublicAccountsFrontendTest(TestCase):
    def test_landing_page_exposes_primary_navigation(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/landing.html")
        self.assertContains(response, "MARKSMEN")
        self.assertContains(response, reverse("login"))
        self.assertContains(response, reverse("register"))
        self.assertContains(response, reverse("about"))
        self.assertContains(response, reverse("services"))

    def test_about_and_services_are_internal_pages(self):
        pages = (
            ("about", "accounts/about.html", "Where competition meets community."),
            ("services", "accounts/services.html", "Everything needed to run esports."),
        )
        for route_name, template, heading in pages:
            with self.subTest(page=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template)
                self.assertContains(response, heading)
                self.assertContains(response, reverse("home"))

    def test_login_and_register_pages_render_accessible_form_fields(self):
        login_response = self.client.get(reverse("login"))
        self.assertEqual(login_response.status_code, 200)
        self.assertTemplateUsed(login_response, "accounts/login.html")
        self.assertContains(login_response, 'name="username"')
        self.assertContains(login_response, 'name="password"')

        register_response = self.client.get(reverse("register"))
        self.assertEqual(register_response.status_code, 200)
        self.assertTemplateUsed(register_response, "accounts/register.html")
        self.assertContains(register_response, 'name="role"')
        self.assertContains(register_response, "Player")
        self.assertContains(register_response, "Organizer")


class AuthenticatedAccountsFrontendTest(TestCase):
    password = "StrongPassword123!"

    @classmethod
    def setUpTestData(cls):
        cls.player = User.objects.create_user(
            username="frontend_player", password=cls.password, role="player"
        )
        cls.organizer = User.objects.create_user(
            username="frontend_organizer", password=cls.password, role="organizer"
        )

    def test_authenticated_user_is_not_shown_public_entry_pages(self):
        self.client.force_login(self.player)
        for route_name in ("home", "login", "register"):
            with self.subTest(page=route_name):
                response = self.client.get(reverse(route_name))
                self.assertRedirects(response, reverse("dashboard"))

    def test_password_page_has_all_password_controls(self):
        self.client.force_login(self.player)
        response = self.client.get(reverse("change_password"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/change_password.html")
        self.assertContains(response, 'name="old_password"')
        self.assertContains(response, 'name="new_password1"')
        self.assertContains(response, 'name="new_password2"')

    def test_invalid_login_stays_on_login_page_with_form_error(self):
        response = self.client.post(reverse("login"), {
            "username": self.player.username,
            "password": "WrongPassword123!",
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")
        self.assertContains(response, "Please enter a correct username and password")

    def test_logout_returns_user_to_login_page(self):
        self.client.force_login(self.organizer)
        response = self.client.get(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)


class PasswordResetFrontendTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reset_player",
            email="reset@example.com",
            password="StrongPassword123!",
            role="player",
        )

    def test_reset_request_sends_a_secure_email_for_known_account(self):
        response = self.client.post(reverse("password_reset"), {
            "email": self.user.email,
        })

        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Reset your MARKSMEN_es password", mail.outbox[0].subject)
        self.assertIn("password-reset/", mail.outbox[0].body)
