from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import PlayerProfile
from .forms import RegisterForm, PlayerProfileForm, OrganizerProfileForm

User = get_user_model()


# =====================================================
#               MODEL TESTS
# =====================================================

class CustomUserModelTest(TestCase):

    def test_create_player(self):
        user = User.objects.create_user(
            username="player1",
            password="StrongPass123!",
            role="player"
        )

        self.assertEqual(user.username, "player1")
        self.assertEqual(user.role, "player")

    def test_create_organizer(self):
        user = User.objects.create_user(
            username="organizer1",
            password="StrongPass123!",
            role="organizer"
        )

        self.assertEqual(user.role, "organizer")

    def test_default_role(self):
        user = User.objects.create_user(
            username="defaultuser",
            password="StrongPass123!"
        )

        self.assertEqual(user.role, "player")

    def test_user_string_representation(self):
        user = User.objects.create_user(
            username="ramim",
            password="StrongPass123!",
            role="player"
        )

        self.assertEqual(str(user), "ramim (player)")


class PlayerProfileModelTest(TestCase):

    def test_create_player_profile(self):

        user = User.objects.create_user(
            username="player2",
            password="StrongPass123!",
            role="player"
        )

        profile = PlayerProfile.objects.create(
            user=user,
            ingame_role="assault",
            bio="Professional Player"
        )

        self.assertEqual(profile.user.username, "player2")
        self.assertEqual(profile.ingame_role, "assault")

    def test_player_profile_string(self):

        user = User.objects.create_user(
            username="player3",
            password="StrongPass123!"
        )

        profile = PlayerProfile.objects.create(
            user=user,
            ingame_role="support"
        )

        self.assertEqual(
            str(profile),
            "player3 — support"
        )


# =====================================================
#               REGISTER FORM TESTS
# =====================================================

class RegisterFormTest(TestCase):

    def test_valid_registration_form(self):

        form = RegisterForm(data={
            "username": "newplayer",
            "email": "player@test.com",
            "phone": "01711111111",
            "address": "Dhaka",
            "role": "player",
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!",
        })

        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):

        form = RegisterForm(data={
            "username": "newplayer",
            "email": "player@test.com",
            "role": "player",
            "password1": "StrongPassword123!",
            "password2": "WrongPassword123!",
        })

        self.assertFalse(form.is_valid())

    def test_duplicate_username(self):

        User.objects.create_user(
            username="duplicate",
            password="StrongPass123!"
        )

        form = RegisterForm(data={
            "username": "duplicate",
            "email": "abc@test.com",
            "role": "player",
            "password1": "StrongPassword123!",
            "password2": "StrongPassword123!",
        })

        self.assertFalse(form.is_valid())


# =====================================================
#               PLAYER PROFILE FORM
# =====================================================

class PlayerProfileFormTest(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="playerform",
            password="StrongPass123!",
            role="player",
            email="old@test.com"
        )

        self.profile = PlayerProfile.objects.create(
            user=self.user
        )

    def test_player_profile_form_valid(self):

        form = PlayerProfileForm(
            data={
                "first_name": "Ramim",
                "last_name": "Islam",
                "email": "new@test.com",
                "phone": "01888888888",
                "address": "Dhaka",
                "ingame_role": "support",
                "bio": "Competitive Player"
            },
            instance=self.profile,
            user=self.user
        )

        self.assertTrue(form.is_valid())

    def test_player_profile_save_updates_user(self):

        form = PlayerProfileForm(
            data={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@test.com",
                "phone": "01777777777",
                "address": "Dhaka",
                "ingame_role": "controller",
                "bio": "New Bio"
            },
            instance=self.profile,
            user=self.user
        )

        self.assertTrue(form.is_valid())

        form.save()

        self.user.refresh_from_db()
        self.profile.refresh_from_db()

        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(self.user.email, "john@test.com")
        self.assertEqual(self.profile.ingame_role, "controller")


# =====================================================
#           ORGANIZER PROFILE FORM
# =====================================================

class OrganizerProfileFormTest(TestCase):

    def setUp(self):

        self.organizer = User.objects.create_user(
            username="organizer",
            password="StrongPass123!",
            role="organizer"
        )

    def test_organizer_profile_form(self):

        form = OrganizerProfileForm(
            data={
                "first_name": "Alex",
                "last_name": "Smith",
                "email": "alex@test.com",
                "phone": "01999999999",
                "address": "Dhaka"
            },
            instance=self.organizer
        )

        self.assertTrue(form.is_valid())

    def test_organizer_profile_save(self):

        form = OrganizerProfileForm(
            data={
                "first_name": "David",
                "last_name": "Brown",
                "email": "david@test.com",
                "phone": "01666666666",
                "address": "Chittagong"
            },
            instance=self.organizer
        )

        self.assertTrue(form.is_valid())

        form.save()

        self.organizer.refresh_from_db()

        self.assertEqual(self.organizer.first_name, "David")
        self.assertEqual(self.organizer.address, "Chittagong")


# =====================================================
#          ACCOUNT WORKFLOW / ACCESS TESTS
# =====================================================

class AccountWorkflowTest(TestCase):
    """Exercise the important account journeys through Django's test client."""

    password = "StrongPassword123!"

    @classmethod
    def setUpTestData(cls):
        cls.player = User.objects.create_user(
            username="existing_player", email="existing_player@example.com",
            password=cls.password, role="player"
        )
        cls.organizer = User.objects.create_user(
            username="existing_organizer", password=cls.password, role="organizer"
        )
        cls.admin = User.objects.create_user(
            username="existing_admin", password=cls.password, role="admin"
        )

    def test_player_registration_creates_profile_shows_confirmation_and_redirects_to_login(self):
        response = self.client.post(reverse("register"), {
            "username": "new_player",
            "email": "newplayer@example.com",
            "phone": "01700000000",
            "address": "Dhaka",
            "role": "player",
            "password1": self.password,
            "password2": self.password,
        })

        self.assertRedirects(response, reverse("login"))
        new_user = User.objects.get(username="new_player")
        self.assertEqual(new_user.role, "player")
        self.assertTrue(PlayerProfile.objects.filter(user=new_user).exists())
        self.assertNotEqual(new_user.password, self.password)
        self.assertTrue(new_user.check_password(self.password))
        self.assertIsNone(self.client.session.get("_auth_user_id"))
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("Registration successful" in str(message) for message in messages))

    def test_organizer_registration_does_not_create_player_profile(self):
        response = self.client.post(reverse("register"), {
            "username": "new_organizer",
            "email": "neworganizer@example.com",
            "phone": "01800000000",
            "address": "Dhaka",
            "role": "organizer",
            "password1": self.password,
            "password2": self.password,
        })

        self.assertRedirects(response, reverse("login"))
        new_user = User.objects.get(username="new_organizer")
        self.assertEqual(new_user.role, "organizer")
        self.assertFalse(PlayerProfile.objects.filter(user=new_user).exists())
        self.assertIsNone(self.client.session.get("_auth_user_id"))

    def test_registration_rejects_duplicate_email(self):
        response = self.client.post(reverse("register"), {
            "username": "another_user",
            "email": "existing_player@example.com",
            "role": "player",
            "password1": self.password,
            "password2": self.password,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This email address is already registered.")
        self.assertFalse(User.objects.filter(username="another_user").exists())

    def test_registration_rejects_duplicate_username(self):
        response = self.client.post(reverse("register"), {
            "username": "EXISTING_PLAYER",
            "email": "unique@example.com",
            "role": "player",
            "password1": self.password,
            "password2": self.password,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This username is already registered.")

    def test_invalid_registration_stays_on_register_page(self):
        response = self.client.post(reverse("register"), {
            "username": "bad_registration",
            "email": "not-an-email",
            "role": "player",
            "password1": self.password,
            "password2": "DifferentPassword123!",
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")
        self.assertFalse(User.objects.filter(username="bad_registration").exists())

    def test_dashboard_routes_each_role_to_its_own_area(self):
        cases = (
            (self.player, "accounts/player_dashboard.html"),
            (self.organizer, "accounts/organizer_dashboard.html"),
        )
        for user, template in cases:
            with self.subTest(role=user.role):
                self.client.force_login(user)
                response = self.client.get(reverse("dashboard"))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template)
                self.client.logout()

        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("admin_dashboard"))

    def test_profile_pages_enforce_role_permissions(self):
        self.client.force_login(self.player)
        player_response = self.client.get(reverse("player_profile"))
        self.assertEqual(player_response.status_code, 200)
        self.assertTemplateUsed(player_response, "accounts/player_profile.html")
        self.assertTrue(PlayerProfile.objects.filter(user=self.player).exists())

        organizer_response = self.client.get(reverse("organizer_profile"))
        self.assertRedirects(organizer_response, reverse("dashboard"))

        self.client.force_login(self.organizer)
        player_response = self.client.get(reverse("player_profile"))
        self.assertRedirects(player_response, reverse("dashboard"))

        organizer_response = self.client.get(reverse("organizer_profile"))
        self.assertEqual(organizer_response.status_code, 200)
        self.assertTemplateUsed(organizer_response, "accounts/organizer_profile.html")
