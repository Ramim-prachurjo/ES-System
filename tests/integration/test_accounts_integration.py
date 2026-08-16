from django.test import TestCase
from django.urls import reverse
from django.core import mail

from accounts.models import CustomUser, PlayerProfile


class AccountsIntegrationTests(TestCase):

    def setUp(self):
        self.player_data = {
            "username": "player1",
            "email": "player1@example.com",
            "phone": "01700000000",
            "address": "Dhaka",
            "role": "player",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }

    # IT-ACC-01
    def test_player_registration_creates_user_and_profile(self):
        response = self.client.post(
            reverse("register"),
            self.player_data
        )

        self.assertRedirects(response, reverse("dashboard"))

        user = CustomUser.objects.get(username="player1")

        self.assertEqual(user.role, "player")
        self.assertEqual(user.email, "player1@example.com")
        self.assertTrue(
            PlayerProfile.objects.filter(user=user).exists()
        )

    # IT-ACC-02
    def test_organizer_registration_creates_organizer(self):
        data = self.player_data.copy()
        data.update({
            "username": "organizer1",
            "email": "organizer@example.com",
            "role": "organizer",
        })

        response = self.client.post(
            reverse("register"),
            data
        )

        self.assertRedirects(response, reverse("dashboard"))

        user = CustomUser.objects.get(username="organizer1")

        self.assertEqual(user.role, "organizer")
        self.assertFalse(
            PlayerProfile.objects.filter(user=user).exists()
        )

    # IT-ACC-03
    def test_registered_player_is_logged_in(self):
        self.client.post(
            reverse("register"),
            self.player_data
        )

        self.assertTrue(self.client.session.get("_auth_user_id"))

    # IT-ACC-04
    def test_player_login_redirects_to_dashboard(self):
        user = CustomUser.objects.create_user(
            username="player1",
            password="StrongPass123!",
            role="player",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "player1",
                "password": "StrongPass123!",
            }
        )

        self.assertRedirects(response, reverse("dashboard"))

    # IT-ACC-05
    def test_organizer_login_redirects_to_dashboard(self):
        CustomUser.objects.create_user(
            username="org1",
            password="StrongPass123!",
            role="organizer",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "org1",
                "password": "StrongPass123!",
            }
        )

        self.assertRedirects(response, reverse("dashboard"))

    # IT-ACC-06
    def test_player_profile_update_updates_user_and_profile(self):
        user = CustomUser.objects.create_user(
            username="player1",
            password="StrongPass123!",
            role="player",
            email="old@example.com",
        )

        PlayerProfile.objects.create(user=user)

        self.client.force_login(user)

        response = self.client.post(
            reverse("player_profile"),
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "01800000000",
                "address": "Dhaka",
                "ingame_role": "assault",
                "bio": "Competitive player",
            }
        )

        self.assertRedirects(
            response,
            reverse("player_profile")
        )

        user.refresh_from_db()
        profile = user.player_profile

        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.email, "john@example.com")
        self.assertEqual(user.phone, "01800000000")
        self.assertEqual(user.address, "Dhaka")

        self.assertEqual(profile.ingame_role, "assault")
        self.assertEqual(profile.bio, "Competitive player")

    # IT-ACC-07
    def test_player_cannot_access_organizer_profile(self):
        user = CustomUser.objects.create_user(
            username="player1",
            password="StrongPass123!",
            role="player",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse("organizer_profile")
        )

        self.assertRedirects(
            response,
            reverse("dashboard")
        )

    # IT-ACC-08
    def test_organizer_can_update_profile(self):
        user = CustomUser.objects.create_user(
            username="org1",
            password="StrongPass123!",
            role="organizer",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse("organizer_profile"),
            {
                "first_name": "Organizer",
                "last_name": "One",
                "email": "org@example.com",
                "phone": "01900000000",
                "address": "Dhaka",
            }
        )

        self.assertRedirects(
            response,
            reverse("organizer_profile")
        )

        user.refresh_from_db()

        self.assertEqual(user.first_name, "Organizer")
        self.assertEqual(user.email, "org@example.com")
        self.assertEqual(user.phone, "01900000000")

    # IT-ACC-09
    def test_password_change_keeps_user_logged_in(self):
        user = CustomUser.objects.create_user(
            username="player1",
            password="OldPass123!",
            role="player",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse("change_password"),
            {
                "old_password": "OldPass123!",
                "new_password1": "NewPass123!",
                "new_password2": "NewPass123!",
            }
        )

        self.assertRedirects(
            response,
            reverse("change_password")
        )

        user.refresh_from_db()

        self.assertTrue(
            user.check_password("NewPass123!")
        )

        # Session should remain authenticated
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

    # IT-ACC-10
    def test_logout_logs_user_out(self):
        user = CustomUser.objects.create_user(
            username="player1",
            password="StrongPass123!",
            role="player",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse("logout")
        )

        self.assertRedirects(
            response,
            reverse("login")
        )

        response = self.client.get(
            reverse("dashboard")
        )

        self.assertEqual(response.status_code, 302)

    # IT-ACC-11
    def test_password_reset_sends_email(self):
        user = CustomUser.objects.create_user(
            username="player1",
            email="player@example.com",
            password="StrongPass123!",
            role="player",
        )

        response = self.client.post(
            reverse("password_reset"),
            {
                "email": "player@example.com"
            }
        )

        self.assertEqual(response.status_code, 302)

        self.assertEqual(len(mail.outbox), 1)

        self.assertIn(
            "password",
            mail.outbox[0].subject.lower()
        )

    # IT-ACC-12
    def test_chatbot_requires_login(self):
        response = self.client.post(
            reverse("chatbot_response"),
            data='{"message":"How do I change my password?"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 302)

    # IT-ACC-13
    def test_fixed_platform_help_answer_works_without_gemini(self):
        user = CustomUser.objects.create_user(
            username="player1",
            password="StrongPass123!",
            role="player",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse("chatbot_response"),
            data='{"message":"How do I change my password?"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            data["source"],
            "platform_help"
        )