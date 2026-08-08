from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from accounts.models import CustomUser
from teams.models import Team, TeamMembership
from venues.models import Venue, VenueBooking

from .models import Tournament, TournamentApplication
from .forms import TournamentForm

# ============================================================
# TOURNAMENT MODEL TESTS
# ============================================================

class TournamentModelTest(TestCase):

    def setUp(self):
        self.organizer = CustomUser.objects.create_user(
            username="organizer",
            password="StrongPass123!",
            role="organizer",
        )

        self.tournament = Tournament.objects.create(
            name="Test Valorant Tournament",
            description="Test tournament",
            rules="Standard rules",
            organizer=self.organizer,
            games="valorant",
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 12),
            max_teams=4,
            entry_fee=Decimal("500.00"),
            prize_pool=Decimal("5000.00"),
        )

    def test_tournament_created_with_pending_status(self):
        self.assertEqual(
            self.tournament.status,
            "pending"
        )

    def test_get_games_list_single_game(self):
        self.assertEqual(
            self.tournament.get_games_list(),
            ["valorant"]
        )

    def test_get_games_list_multiple_games(self):
        self.tournament.games = "valorant,pubg"
        self.tournament.save()

        self.assertEqual(
            self.tournament.get_games_list(),
            ["valorant", "pubg"]
        )

    def test_get_games_display(self):
        self.tournament.games = "valorant,pubg"
        self.tournament.save()

        self.assertEqual(
            self.tournament.get_games_display(),
            "Valorant, PUBG"
        )

    def test_tournament_is_not_full_initially(self):
        self.assertFalse(
            self.tournament.is_full()
        )

    def test_tournament_is_full_when_max_teams_approved(self):
        for i in range(4):
            team = Team.objects.create(
                name=f"Team {i}",
                game="valorant",
                captain=self.organizer,
            )

            TournamentApplication.objects.create(
                tournament=self.tournament,
                team=team,
                game="valorant",
                status="approved",
            )

        self.assertTrue(
            self.tournament.is_full()
        )

    def test_pending_application_does_not_make_tournament_full(self):
        for i in range(4):
            team = Team.objects.create(
                name=f"Pending Team {i}",
                game="valorant",
                captain=self.organizer,
            )

            TournamentApplication.objects.create(
                tournament=self.tournament,
                team=team,
                game="valorant",
                status="pending",
            )

        self.assertFalse(
            self.tournament.is_full()
        )

    def test_enrollment_status_active_before_start_date(self):
        self.tournament.start_date = date.today() + timedelta(days=10)
        self.tournament.registration_deadline = None
        self.tournament.save()

        self.assertEqual(
            self.tournament.enrollment_status,
            "active"
        )

    def test_enrollment_status_closed_on_start_date(self):
        self.tournament.start_date = date.today()
        self.tournament.registration_deadline = None
        self.tournament.save()

        self.assertEqual(
            self.tournament.enrollment_status,
            "closed"
        )

    def test_enrollment_status_closed_after_registration_deadline(self):
        self.tournament.registration_deadline = (
            timezone.now() - timedelta(days=1)
        )
        self.tournament.save()

        self.assertEqual(
            self.tournament.enrollment_status,
            "closed"
        )

    def test_enrollment_status_active_before_registration_deadline(self):
        self.tournament.registration_deadline = (
            timezone.now() + timedelta(days=1)
        )
        self.tournament.save()

        self.assertEqual(
            self.tournament.enrollment_status,
            "active"
        )

    def test_tournament_string_representation(self):
        self.assertEqual(
            str(self.tournament),
            "Test Valorant Tournament"
        )


# ============================================================
# TOURNAMENT APPLICATION MODEL TESTS
# ============================================================

class TournamentApplicationModelTest(TestCase):

    def setUp(self):
        self.organizer = CustomUser.objects.create_user(
            username="organizer",
            password="StrongPass123!",
            role="organizer",
        )

        self.team = Team.objects.create(
            name="Test Team",
            game="valorant",
            captain=self.organizer,
        )

        self.tournament = Tournament.objects.create(
            name="Application Tournament",
            organizer=self.organizer,
            games="valorant",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 3),
            max_teams=5,
        )

    def test_application_created_with_pending_status(self):
        application = TournamentApplication.objects.create(
            tournament=self.tournament,
            team=self.team,
            game="valorant",
        )

        self.assertEqual(
            application.status,
            "pending"
        )

    def test_application_string_representation(self):
        application = TournamentApplication.objects.create(
            tournament=self.tournament,
            team=self.team,
            game="valorant",
        )

        self.assertEqual(
            str(application),
            "Test Team → Application Tournament [valorant] (pending)"
        )

    def test_application_can_be_approved(self):
        application = TournamentApplication.objects.create(
            tournament=self.tournament,
            team=self.team,
            game="valorant",
        )

        application.status = "approved"
        application.save()

        application.refresh_from_db()

        self.assertEqual(
            application.status,
            "approved"
        )

    def test_application_can_be_rejected(self):
        application = TournamentApplication.objects.create(
            tournament=self.tournament,
            team=self.team,
            game="valorant",
        )

        application.status = "rejected"
        application.save()

        application.refresh_from_db()

        self.assertEqual(
            application.status,
            "rejected"
        )


# ============================================================
# TOURNAMENT FORM TESTS
# ============================================================

class TournamentFormTest(TestCase):

    def setUp(self):
        self.venue = Venue.objects.create(
            name="Test Arena",
            city="Dhaka",
            address="Test Street, Dhaka",
            capacity=100,
            rental_fee=Decimal("5000.00"),
            description="Test venue",
            is_available=True,
            requires_payment=True,
            payment_amount=Decimal("5000.00"),
        )

        self.valid_data = {
            "name": "Form Test Tournament",
            "description": "Test description",
            "rules": "Test rules",
            "needs_venue": True,
            "venue": self.venue.pk,
            "venue_address": "",
            "games": ["valorant"],
            "start_date": "2026-10-10",
            "end_date": "2026-10-12",
            "registration_deadline": "",
            "max_teams": 8,
            "entry_fee": "500.00",
            "prize_pool": "5000.00",
        }

    def test_valid_tournament_form(self):
        form = TournamentForm(data=self.valid_data)

        self.assertTrue(
            form.is_valid(),
            form.errors
        )

    def test_end_date_before_start_date_is_invalid(self):
        data = self.valid_data.copy()
        data["start_date"] = "2026-10-15"
        data["end_date"] = "2026-10-10"

        form = TournamentForm(data=data)

        self.assertFalse(
            form.is_valid()
        )

        self.assertIn(
            "End date must be after start date.",
            form.non_field_errors()
        )

    def test_venue_required_when_needs_venue_is_true(self):
        data = self.valid_data.copy()
        data["venue"] = ""

        form = TournamentForm(data=data)

        self.assertFalse(
            form.is_valid()
        )

        self.assertIn(
            "venue",
            form.errors
        )

    def test_address_required_when_no_venue_is_selected(self):
        data = self.valid_data.copy()

        data["needs_venue"] = False
        data["venue"] = ""
        data["venue_address"] = ""

        form = TournamentForm(data=data)

        self.assertFalse(
            form.is_valid()
        )

        self.assertIn(
            "venue_address",
            form.errors
        )

    def test_no_venue_allows_address(self):
        data = self.valid_data.copy()

        data["needs_venue"] = False
        data["venue"] = ""
        data["venue_address"] = "123 Independent Road, Dhaka"

        form = TournamentForm(data=data)

        self.assertTrue(
            form.is_valid(),
            form.errors
        )

        self.assertIsNone(
            form.cleaned_data["venue"]
        )

    def test_unavailable_venue_is_not_valid(self):
        self.venue.is_available = False
        self.venue.save()

        data = self.valid_data.copy()
        data["venue"] = self.venue.pk

        form = TournamentForm(data=data)

        self.assertFalse(
            form.is_valid()
        )

        self.assertIn(
            "venue",
            form.errors
        )

    def test_venue_with_existing_booking_is_invalid(self):
        organizer = CustomUser.objects.create_user(
            username="bookinguser",
            password="StrongPass123!",
            role="organizer",
        )

        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=organizer,
            start_date=date(2026, 10, 11),
            end_date=date(2026, 10, 13),
            status="confirmed",
            payment_required=True,
            payment_amount=Decimal("5000.00"),
        )

        form = TournamentForm(data=self.valid_data)

        self.assertFalse(
            form.is_valid()
        )

        self.assertIn(
            "venue",
            form.errors
        )

    def test_multiple_games_are_stored_as_comma_separated_string(self):
        data = self.valid_data.copy()
        data["games"] = ["valorant", "pubg"]

        form = TournamentForm(data=data)

        self.assertTrue(
            form.is_valid(),
            form.errors
        )

        self.assertEqual(
            form.cleaned_data["games"],
            "valorant,pubg"
        )

# ============================================================
# TOURNAMENT VIEW TESTS
# ============================================================

class TournamentViewTest(TestCase):

    def setUp(self):
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

        self.admin = CustomUser.objects.create_user(
            username="admin",
            password="StrongPass123!",
            role="admin",
        )

        self.venue = Venue.objects.create(
            name="Test Arena",
            city="Dhaka",
            address="Test Arena Address",
            capacity=100,
            rental_fee=Decimal("5000.00"),
            description="Test venue",
            is_available=True,
            requires_payment=True,
            payment_amount=Decimal("5000.00"),
        )

        self.tournament = Tournament.objects.create(
            name="Test Tournament",
            description="Tournament description",
            rules="Tournament rules",
            organizer=self.organizer,
            venue=self.venue,
            needs_venue=True,
            games="valorant",
            start_date=date(2026, 10, 10),
            end_date=date(2026, 10, 12),
            max_teams=4,
            entry_fee=Decimal("500.00"),
            prize_pool=Decimal("5000.00"),
            status="active",
        )

    # --------------------------------------------------------
    # TOURNAMENT LIST
    # --------------------------------------------------------

    def test_tournament_list_requires_login(self):
        response = self.client.get(
            reverse("tournament_list")
        )

        self.assertEqual(
            response.status_code,
            302
        )

    def test_player_can_view_tournament_list(self):
        self.client.login(
            username="player",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse("tournament_list")
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "tournaments/tournament_list.html"
        )

        self.assertContains(
            response,
            "Test Tournament"
        )

    def test_organizer_can_view_tournament_list(self):
        self.client.login(
            username="organizer",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse("tournament_list")
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertContains(
            response,
            "Test Tournament"
        )

    def test_admin_can_view_all_tournaments(self):
        self.client.login(
            username="admin",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse("tournament_list")
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertContains(
            response,
            "Test Tournament"
        )

    # --------------------------------------------------------
    # CREATE TOURNAMENT ACCESS
    # --------------------------------------------------------

    def test_create_tournament_requires_login(self):
        response = self.client.get(
            reverse("create_tournament")
        )

        self.assertEqual(
            response.status_code,
            302
        )

    def test_organizer_can_open_create_tournament_page(self):
        self.client.login(
            username="organizer",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse("create_tournament")
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "tournaments/tournament_form.html"
        )

    def test_player_cannot_create_tournament(self):
        self.client.login(
            username="player",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse("create_tournament")
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertRedirects(
            response,
            reverse("tournament_list")
        )

    def test_admin_cannot_create_tournament(self):
        self.client.login(
            username="admin",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse("create_tournament")
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertRedirects(
            response,
            reverse("tournament_list")
        )

    # --------------------------------------------------------
    # CREATE TOURNAMENT WITHOUT VENUE
    # --------------------------------------------------------

    def test_organizer_can_create_tournament_without_venue(self):
        self.client.login(
            username="organizer",
            password="StrongPass123!"
        )

        data = {
            "name": "No Venue Tournament",
            "description": "Tournament without platform venue",
            "rules": "Standard rules",
            "needs_venue": "False",
            "venue": "",
            "venue_address": "123 Independent Road, Dhaka",
            "games": ["valorant"],
            "start_date": "2026-11-10",
            "end_date": "2026-11-12",
            "registration_deadline": "",
            "max_teams": 8,
            "entry_fee": "500.00",
            "prize_pool": "5000.00",
        }

        response = self.client.post(
            reverse("create_tournament"),
            data
        )

        self.assertEqual(
            response.status_code,
            302
        )

        tournament = Tournament.objects.get(
            name="No Venue Tournament"
        )

        self.assertEqual(
            tournament.organizer,
            self.organizer
        )

        self.assertEqual(
            tournament.status,
            "pending"
        )

        self.assertFalse(
            tournament.needs_venue
        )

        self.assertIsNone(
            tournament.venue
        )

        self.assertEqual(
            tournament.venue_address,
            "123 Independent Road, Dhaka"
        )

        self.assertFalse(
            VenueBooking.objects.filter(
                tournament=tournament
            ).exists()
        )

    # --------------------------------------------------------
    # CREATE TOURNAMENT WITH VENUE
    # --------------------------------------------------------

    def test_organizer_can_create_tournament_with_venue(self):
        self.client.login(
            username="organizer",
            password="StrongPass123!"
        )

        data = {
            "name": "Venue Tournament",
            "description": "Tournament with venue",
            "rules": "Standard rules",
            "needs_venue": "True",
            "venue": self.venue.pk,
            "venue_address": "",
            "games": ["valorant"],
            "start_date": "2026-11-20",
            "end_date": "2026-11-22",
            "registration_deadline": "",
            "max_teams": 8,
            "entry_fee": "500.00",
            "prize_pool": "5000.00",
        }

        response = self.client.post(
            reverse("create_tournament"),
            data
        )

        self.assertEqual(
            response.status_code,
            302
        )

        tournament = Tournament.objects.get(
            name="Venue Tournament"
        )

        self.assertEqual(
            tournament.organizer,
            self.organizer
        )

        self.assertEqual(
            tournament.status,
            "pending"
        )

        self.assertEqual(
            tournament.venue,
            self.venue
        )

        booking = VenueBooking.objects.get(
            tournament=tournament
        )

        self.assertEqual(
            booking.venue,
            self.venue
        )

        self.assertEqual(
            booking.booked_by,
            self.organizer
        )

        self.assertEqual(
            booking.status,
            "pending"
        )

    def test_venue_payment_information_is_generated(self):
        self.client.login(
            username="organizer",
            password="StrongPass123!"
        )

        data = {
            "name": "Payment Tournament",
            "description": "Payment test",
            "rules": "Standard rules",
            "needs_venue": "True",
            "venue": self.venue.pk,
            "venue_address": "",
            "games": ["valorant"],
            "start_date": "2026-12-01",
            "end_date": "2026-12-03",
            "registration_deadline": "",
            "max_teams": 8,
            "entry_fee": "500.00",
            "prize_pool": "5000.00",
        }

        self.client.post(
            reverse("create_tournament"),
            data
        )

        tournament = Tournament.objects.get(
            name="Payment Tournament"
        )

        self.assertTrue(
            tournament.venue_payment_required
        )

        self.assertEqual(
            tournament.venue_payment_amount,
            self.venue.payment_amount
        )

        self.assertTrue(
            tournament.venue_payment_code.startswith("TRN-")
        )

    # --------------------------------------------------------
    # VENUE CONFLICT
    # --------------------------------------------------------

    def test_create_tournament_rejects_conflicting_booking(self):
        self.client.login(
            username="organizer",
            password="StrongPass123!"
        )

        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 11, 15),
            status="confirmed",
            payment_required=True,
            payment_amount=Decimal("5000.00"),
        )

        data = {
            "name": "Conflict Tournament",
            "description": "Conflict test",
            "rules": "Standard rules",
            "needs_venue": "True",
            "venue": self.venue.pk,
            "venue_address": "",
            "games": ["valorant"],
            "start_date": "2026-11-12",
            "end_date": "2026-11-14",
            "registration_deadline": "",
            "max_teams": 8,
            "entry_fee": "500.00",
            "prize_pool": "5000.00",
        }

        response = self.client.post(
            reverse("create_tournament"),
            data
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "tournaments/tournament_form.html"
        )

        self.assertFalse(
            Tournament.objects.filter(
                name="Conflict Tournament"
            ).exists()
        )

    # --------------------------------------------------------
    # PAYMENT INFORMATION
    # --------------------------------------------------------

    def test_organizer_can_view_own_payment_information(self):
        self.client.login(
            username="organizer",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "tournament_payment_info",
                kwargs={"pk": self.tournament.pk}
            )
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "tournaments/tournament_payment.html"
        )

        self.assertContains(
            response,
            "Test Tournament"
        )

    def test_other_user_cannot_view_payment_information(self):
        self.client.login(
            username="player",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "tournament_payment_info",
                kwargs={"pk": self.tournament.pk}
            )
        )

        self.assertEqual(
            response.status_code,
            404
        )

    # --------------------------------------------------------
    # TOURNAMENT DETAIL
    # --------------------------------------------------------

    def test_logged_in_user_can_view_tournament_detail(self):
        self.client.login(
            username="player",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "tournament_detail",
                kwargs={"pk": self.tournament.pk}
            )
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "tournaments/tournament_detail.html"
        )

        self.assertContains(
            response,
            "Test Tournament"
        )

    def test_tournament_detail_requires_login(self):
        response = self.client.get(
            reverse(
                "tournament_detail",
                kwargs={"pk": self.tournament.pk}
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

    # --------------------------------------------------------
    # TOURNAMENT APPLICATION
    # --------------------------------------------------------

    def test_captain_can_apply_to_tournament(self):
        captain = CustomUser.objects.create_user(
            username="captain",
            password="StrongPass123!",
            role="player",
        )

        team = Team.objects.create(
            name="Complete Team",
            game="valorant",
            captain=captain,
        )

        # Valorant requires 5 members
        for i in range(5):
            user = captain

            if i > 0:
                user = CustomUser.objects.create_user(
                    username=f"member{i}",
                    password="StrongPass123!",
                    role="player",
                )

            TeamMembership.objects.create(
                user=user,
                team=team,
            )

        self.client.login(
            username="captain",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "apply_to_tournament",
                kwargs={
                    "tournament_id": self.tournament.pk,
                    "team_id": team.pk,
                }
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertTrue(
            TournamentApplication.objects.filter(
                tournament=self.tournament,
                team=team,
                game="valorant",
                status="pending",
            ).exists()
        )

    def test_non_captain_cannot_apply_with_team(self):
        captain = CustomUser.objects.create_user(
            username="captain2",
            password="StrongPass123!",
            role="player",
        )

        other_player = CustomUser.objects.create_user(
            username="otherplayer",
            password="StrongPass123!",
            role="player",
        )

        team = Team.objects.create(
            name="Captain Team",
            game="valorant",
            captain=captain,
        )

        self.client.login(
            username="otherplayer",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "apply_to_tournament",
                kwargs={
                    "tournament_id": self.tournament.pk,
                    "team_id": team.pk,
                }
            )
        )

        self.assertEqual(
            response.status_code,
            404
        )

    def test_incomplete_team_cannot_apply(self):
        captain = CustomUser.objects.create_user(
            username="incompletecaptain",
            password="StrongPass123!",
            role="player",
        )

        team = Team.objects.create(
            name="Incomplete Team",
            game="valorant",
            captain=captain,
        )

        # Only captain = incomplete
        TeamMembership.objects.create(
            user=captain,
            team=team,
        )

        self.client.login(
            username="incompletecaptain",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "apply_to_tournament",
                kwargs={
                    "tournament_id": self.tournament.pk,
                    "team_id": team.pk,
                }
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertFalse(
            TournamentApplication.objects.filter(
                tournament=self.tournament,
                team=team,
            ).exists()
        )

    def test_team_with_wrong_game_cannot_apply(self):
        captain = CustomUser.objects.create_user(
            username="pubgcaptain",
            password="StrongPass123!",
            role="player",
        )

        team = Team.objects.create(
            name="PUBG Team",
            game="pubg",
            captain=captain,
        )

        for i in range(4):
            user = captain

            if i > 0:
                user = CustomUser.objects.create_user(
                    username=f"pubgmember{i}",
                    password="StrongPass123!",
                    role="player",
                )

            TeamMembership.objects.create(
                user=user,
                team=team,
            )

        self.client.login(
            username="pubgcaptain",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "apply_to_tournament",
                kwargs={
                    "tournament_id": self.tournament.pk,
                    "team_id": team.pk,
                }
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertFalse(
            TournamentApplication.objects.filter(
                tournament=self.tournament,
                team=team,
            ).exists()
        )

    def test_duplicate_application_is_rejected(self):
        captain = CustomUser.objects.create_user(
            username="duplicatecaptain",
            password="StrongPass123!",
            role="player",
        )

        team = Team.objects.create(
            name="Duplicate Team",
            game="valorant",
            captain=captain,
        )

        for i in range(5):
            user = captain

            if i > 0:
                user = CustomUser.objects.create_user(
                    username=f"duplicatemember{i}",
                    password="StrongPass123!",
                    role="player",
                )

            TeamMembership.objects.create(
                user=user,
                team=team,
            )

        TournamentApplication.objects.create(
            tournament=self.tournament,
            team=team,
            game="valorant",
            status="pending",
        )

        self.client.login(
            username="duplicatecaptain",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "apply_to_tournament",
                kwargs={
                    "tournament_id": self.tournament.pk,
                    "team_id": team.pk,
                }
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertEqual(
            TournamentApplication.objects.filter(
                tournament=self.tournament,
                team=team,
                game="valorant",
            ).count(),
            1
        )

    # --------------------------------------------------------
    # APPROVE / REJECT APPLICATION
    # --------------------------------------------------------

    def test_organizer_can_approve_application(self):
        captain = CustomUser.objects.create_user(
            username="applycaptain",
            password="StrongPass123!",
            role="player",
        )

        team = Team.objects.create(
            name="Application Team",
            game="valorant",
            captain=captain,
        )

        application = TournamentApplication.objects.create(
            tournament=self.tournament,
            team=team,
            game="valorant",
            status="pending",
        )

        self.client.login(
            username="organizer",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "approve_application",
                kwargs={
                    "application_id": application.pk
                }
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        application.refresh_from_db()

        self.assertEqual(
            application.status,
            "approved"
        )

    def test_organizer_can_reject_application(self):
        captain = CustomUser.objects.create_user(
            username="rejectcaptain",
            password="StrongPass123!",
            role="player",
        )

        team = Team.objects.create(
            name="Reject Team",
            game="valorant",
            captain=captain,
        )

        application = TournamentApplication.objects.create(
            tournament=self.tournament,
            team=team,
            game="valorant",
            status="pending",
        )

        self.client.login(
            username="organizer",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "reject_application",
                kwargs={
                    "application_id": application.pk
                }
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        application.refresh_from_db()

        self.assertEqual(
            application.status,
            "rejected"
        )

    def test_other_organizer_cannot_approve_application(self):
        other_organizer = CustomUser.objects.create_user(
            username="otherorganizer",
            password="StrongPass123!",
            role="organizer",
        )

        captain = CustomUser.objects.create_user(
            username="approvalcaptain",
            password="StrongPass123!",
            role="player",
        )

        team = Team.objects.create(
            name="Approval Team",
            game="valorant",
            captain=captain,
        )

        application = TournamentApplication.objects.create(
            tournament=self.tournament,
            team=team,
            game="valorant",
            status="pending",
        )

        self.client.login(
            username="otherorganizer",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "approve_application",
                kwargs={
                    "application_id": application.pk
                }
            )
        )

        self.assertEqual(
            response.status_code,
            404
        )

        application.refresh_from_db()

        self.assertEqual(
            application.status,
            "pending"
        )

    def test_other_organizer_cannot_reject_application(self):
        other_organizer = CustomUser.objects.create_user(
            username="otherorganizer2",
            password="StrongPass123!",
            role="organizer",
        )

        captain = CustomUser.objects.create_user(
            username="rejectcaptain2",
            password="StrongPass123!",
            role="player",
        )

        team = Team.objects.create(
            name="Reject Protection Team",
            game="valorant",
            captain=captain,
        )

        application = TournamentApplication.objects.create(
            tournament=self.tournament,
            team=team,
            game="valorant",
            status="pending",
        )

        self.client.login(
            username="otherorganizer2",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "reject_application",
                kwargs={
                    "application_id": application.pk
                }
            )
        )

        self.assertEqual(
            response.status_code,
            404
        )

        application.refresh_from_db()

        self.assertEqual(
            application.status,
            "pending"
        )
