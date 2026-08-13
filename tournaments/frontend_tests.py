from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from teams.models import Team, TeamMembership
from venues.models import Venue

from .models import Tournament, TournamentApplication


class TournamentFrontendTest(TestCase):
    """
    Frontend/template tests for:

    1. tournament_detail.html
    2. tournament_form.html
    3. tournament_list.html
    4. tournament_payment.html
    """

    @classmethod
    def setUpTestData(cls):

        # --------------------------------------------------------
        # USERS
        # --------------------------------------------------------

        cls.organizer = CustomUser.objects.create_user(
            username="frontend_organizer",
            password="StrongPass123!",
            role="organizer",
        )

        cls.player = CustomUser.objects.create_user(
            username="frontend_player",
            password="StrongPass123!",
            role="player",
        )

        cls.admin = CustomUser.objects.create_user(
            username="frontend_admin",
            password="StrongPass123!",
            role="admin",
        )

        # --------------------------------------------------------
        # VENUE
        # --------------------------------------------------------

        cls.venue = Venue.objects.create(
            name="Frontend Test Arena",
            city="Dhaka",
            address="Test Arena Address",
            capacity=100,
            rental_fee=Decimal("5000.00"),
            description="Frontend test venue",
            is_available=True,
            requires_payment=True,
            payment_amount=Decimal("5000.00"),
        )

        # --------------------------------------------------------
        # TOURNAMENT
        # --------------------------------------------------------

        cls.tournament = Tournament.objects.create(
            name="Frontend Test Tournament",
            description="Frontend tournament description",
            rules="Frontend tournament rules",
            organizer=cls.organizer,
            venue=cls.venue,
            needs_venue=True,
            games="valorant",
            start_date=date(2026, 10, 10),
            end_date=date(2026, 10, 12),
            max_teams=4,
            entry_fee=Decimal("500.00"),
            prize_pool=Decimal("5000.00"),
            status="active",
        )

    # ============================================================
    # 1. TOURNAMENT LIST FRONTEND
    # ============================================================

    def test_tournament_list_uses_correct_template(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("tournament_list")
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "tournaments/tournament_list.html",
        )

    def test_tournament_list_displays_tournament_name(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("tournament_list")
        )

        self.assertContains(
            response,
            "Frontend Test Tournament",
        )

    def test_tournament_list_displays_game(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("tournament_list")
        )

        self.assertContains(
            response,
            "Valorant",
        )

    def test_tournament_list_displays_venue(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("tournament_list")
        )

        self.assertContains(
            response,
            "Frontend Test Arena",
        )

    def test_tournament_list_displays_prize_pool(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("tournament_list")
        )

        self.assertContains(
            response,
            "5000",
        )

    def test_tournament_list_displays_dates(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("tournament_list")
        )

        self.assertContains(
            response,
            "10 Oct 2026",
        )

        self.assertContains(
            response,
            "12 Oct 2026",
        )

    def test_tournament_list_displays_view_button(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("tournament_list")
        )

        self.assertContains(
            response,
            "View",
        )

    def test_organizer_sees_create_tournament_button(self):
        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("tournament_list")
        )

        self.assertContains(
            response,
            "Create Tournament",
        )

    def test_player_does_not_see_create_tournament_button(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("tournament_list")
        )

        self.assertNotContains(
            response,
            "Create Tournament",
        )

    def test_admin_does_not_see_create_tournament_button(self):
        self.client.login(
            username="frontend_admin",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("tournament_list")
        )

        self.assertNotContains(
            response,
            "Create Tournament",
        )

    # ============================================================
    # 2. TOURNAMENT DETAIL FRONTEND
    # ============================================================

    def test_tournament_detail_uses_correct_template(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_detail",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "tournaments/tournament_detail.html",
        )

    def test_tournament_detail_displays_name(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_detail",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "Frontend Test Tournament",
        )

    def test_tournament_detail_displays_game(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_detail",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "Valorant",
        )

    def test_tournament_detail_displays_venue(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_detail",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "Frontend Test Arena",
        )

    def test_tournament_detail_displays_entry_fee(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_detail",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "500",
        )

    def test_tournament_detail_displays_prize_pool(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_detail",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "5000",
        )

    def test_tournament_detail_displays_max_teams(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_detail",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "4",
        )

    def test_tournament_detail_displays_description(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_detail",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "Frontend tournament description",
        )

    def test_tournament_detail_displays_rules(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_detail",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "Frontend tournament rules",
        )

    def test_tournament_detail_displays_status(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_detail",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "Active",
        )

    def test_tournament_detail_displays_back_button(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_detail",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "Back",
        )

    def test_player_sees_apply_section(self):
        self.client.login(
            username="frontend_player",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_detail",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "Apply with your team",
        )

    # ============================================================
    # 3. TOURNAMENT FORM FRONTEND
    # ============================================================

    def test_tournament_form_uses_correct_template(self):
        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("create_tournament")
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "tournaments/tournament_form.html",
        )

    def test_tournament_form_displays_title(self):
        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("create_tournament")
        )

        self.assertContains(
            response,
            "Create Tournament",
        )

    def test_tournament_form_contains_csrf_token(self):
        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("create_tournament")
        )

        self.assertContains(
            response,
            "csrfmiddlewaretoken",
        )

    def test_tournament_form_contains_game_picker(self):
        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("create_tournament")
        )

        self.assertContains(
            response,
            "Choose the game or games for this tournament.",
        )

    def test_tournament_form_contains_valorant_option(self):
        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("create_tournament")
        )

        self.assertContains(
            response,
            "Valorant",
        )

    def test_tournament_form_contains_pubg_option(self):
        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("create_tournament")
        )

        self.assertContains(
            response,
            "PUBG",
        )

    def test_tournament_form_contains_submit_button(self):
        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("create_tournament")
        )

        self.assertContains(
            response,
            "Submit for Approval",
        )

    def test_tournament_form_contains_payment_notice_container(self):
        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("create_tournament")
        )

        self.assertContains(
            response,
            'id="payment-notice"',
        )

    def test_tournament_form_contains_venue_payment_javascript(self):
        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("create_tournament")
        )

        self.assertContains(
            response,
            "requiresPayment",
        )

        self.assertContains(
            response,
            "amount",
        )

    def test_tournament_form_contains_back_link(self):
        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse("create_tournament")
        )

        self.assertContains(
            response,
            "Back to Home",
        )

    # ============================================================
    # 4. TOURNAMENT PAYMENT FRONTEND
    # ============================================================

    def test_tournament_payment_uses_correct_template(self):
        self.tournament.venue_payment_amount = Decimal("5000.00")
        self.tournament.venue_payment_code = "TRN-FRONT01"
        self.tournament.venue_payment_required = True
        self.tournament.save()

        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_payment_info",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "tournaments/tournament_payment.html",
        )

    def test_tournament_payment_displays_tournament_name(self):
        self.tournament.venue_payment_amount = Decimal("5000.00")
        self.tournament.venue_payment_code = "TRN-FRONT02"
        self.tournament.save()

        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_payment_info",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "Frontend Test Tournament",
        )

    def test_tournament_payment_displays_venue_name(self):
        self.tournament.venue_payment_amount = Decimal("5000.00")
        self.tournament.venue_payment_code = "TRN-FRONT03"
        self.tournament.save()

        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_payment_info",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "Frontend Test Arena",
        )

    def test_tournament_payment_displays_amount(self):
        self.tournament.venue_payment_amount = Decimal("5000.00")
        self.tournament.venue_payment_code = "TRN-FRONT04"
        self.tournament.save()

        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_payment_info",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "5000.00",
        )

    def test_tournament_payment_displays_bkash(self):
        self.tournament.venue_payment_amount = Decimal("5000.00")
        self.tournament.venue_payment_code = "TRN-FRONT05"
        self.tournament.save()

        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_payment_info",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "bKash Mobile Banking",
        )

    def test_tournament_payment_displays_biller_id(self):
        self.tournament.venue_payment_amount = Decimal("5000.00")
        self.tournament.venue_payment_code = "TRN-FRONT06"
        self.tournament.save()

        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_payment_info",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "210425",
        )

    def test_tournament_payment_displays_payment_code(self):
        self.tournament.venue_payment_amount = Decimal("5000.00")
        self.tournament.venue_payment_code = "TRN-FRONT07"
        self.tournament.save()

        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_payment_info",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "TRN-FRONT07",
        )

    def test_tournament_payment_displays_payment_instructions(self):
        self.tournament.venue_payment_amount = Decimal("5000.00")
        self.tournament.venue_payment_code = "TRN-FRONT08"
        self.tournament.save()

        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_payment_info",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "How to pay via bKash:",
        )

        self.assertContains(
            response,
            "Pay Bill",
        )

        self.assertContains(
            response,
            "Confirm the payment",
        )

    def test_tournament_payment_displays_admin_verification_warning(self):
        self.tournament.venue_payment_amount = Decimal("5000.00")
        self.tournament.venue_payment_code = "TRN-FRONT09"
        self.tournament.save()

        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_payment_info",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "admin verifies your payment",
        )

    def test_tournament_payment_displays_back_button(self):
        self.tournament.venue_payment_amount = Decimal("5000.00")
        self.tournament.venue_payment_code = "TRN-FRONT10"
        self.tournament.save()

        self.client.login(
            username="frontend_organizer",
            password="StrongPass123!",
        )

        response = self.client.get(
            reverse(
                "tournament_payment_info",
                kwargs={"pk": self.tournament.pk},
            )
        )

        self.assertContains(
            response,
            "View My Tournament",
        )
