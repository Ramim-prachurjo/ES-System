from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from teams.models import Team, TeamMembership
from tournaments.models import Tournament, TournamentApplication
from venues.models import Venue, VenueBooking


class TournamentIntegrationTests(TestCase):

    def setUp(self):
        self.organizer = CustomUser.objects.create_user(
            username="organizer",
            password="StrongPass123!",
            role="organizer",
        )

        self.player = CustomUser.objects.create_user(
            username="captain",
            password="StrongPass123!",
            role="player",
        )

        self.other_player = CustomUser.objects.create_user(
            username="player2",
            password="StrongPass123!",
            role="player",
        )

        self.venue = Venue.objects.create(
            name="Test Arena",
            city="Dhaka",
            address="Dhaka",
            capacity=100,
            rental_fee=0,
            is_available=True,
        )

    def create_full_team(self, game="valorant"):
        team = Team.objects.create(
            name=f"Team {Team.objects.count() + 1}",
            game=game,
            captain=self.player,
        )

        TeamMembership.objects.create(
            user=self.player,
            team=team,
        )

        required = 5 if game == "valorant" else 4

        for i in range(required - 1):
            user = CustomUser.objects.create_user(
                username=f"{game}_member_{i}",
                password="StrongPass123!",
                role="player",
            )

            TeamMembership.objects.create(
                user=user,
                team=team,
            )

        return team

    def create_tournament(self, games="valorant", status="active"):
        return Tournament.objects.create(
            name=f"Tournament {Tournament.objects.count() + 1}",
            organizer=self.organizer,
            games=games,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 12),
            max_teams=16,
            status=status,
        )

    # IT-TOUR-01
    def test_organizer_can_create_tournament_without_venue(self):
        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse("create_tournament"),
            {
                "name": "Test Tournament",
                "description": "Test",
                "rules": "Rules",
                "needs_venue": "False",
                "venue": "",
                "venue_address": "Dhaka Stadium",
                "games": ["valorant"],
                "start_date": "2026-09-10",
                "end_date": "2026-09-12",
                "registration_deadline": "",
                "max_teams": 16,
                "entry_fee": 0,
                "prize_pool": 1000,
            }
        )

        self.assertEqual(response.status_code, 302)

        tournament = Tournament.objects.get(
            name="Test Tournament"
        )

        self.assertEqual(
            tournament.organizer,
            self.organizer
        )

        self.assertEqual(
            tournament.status,
            "pending"
        )

        self.assertIsNone(tournament.venue)

    # IT-TOUR-02
    def test_player_cannot_create_tournament(self):
        self.client.force_login(self.player)

        self.client.post(
            reverse("create_tournament"),
            {
                "name": "Unauthorized Tournament",
                "needs_venue": "False",
                "venue_address": "Dhaka",
                "games": ["valorant"],
                "start_date": "2026-09-10",
                "end_date": "2026-09-12",
                "max_teams": 16,
                "entry_fee": 0,
                "prize_pool": 0,
            }
        )

        self.assertFalse(
            Tournament.objects.filter(
                name="Unauthorized Tournament"
            ).exists()
        )

    # IT-TOUR-03
    def test_tournament_created_with_venue_creates_booking(self):
        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse("create_tournament"),
            {
                "name": "Venue Tournament",
                "description": "Test",
                "rules": "Rules",
                "needs_venue": "True",
                "venue": self.venue.pk,
                "venue_address": "",
                "games": ["valorant"],
                "start_date": "2026-09-10",
                "end_date": "2026-09-12",
                "registration_deadline": "",
                "max_teams": 16,
                "entry_fee": 0,
                "prize_pool": 1000,
            }
        )

        self.assertEqual(response.status_code, 302)

        tournament = Tournament.objects.get(
            name="Venue Tournament"
        )

        self.assertTrue(
            VenueBooking.objects.filter(
                tournament=tournament,
                venue=self.venue,
            ).exists()
        )

    # IT-TOUR-04
    def test_player_can_view_active_tournament(self):
        tournament = self.create_tournament()

        self.client.force_login(self.player)

        response = self.client.get(
            reverse(
                "tournament_detail",
                args=[tournament.pk]
            )
        )

        self.assertEqual(response.status_code, 200)

    # IT-TOUR-05
    def test_full_team_can_apply_to_matching_tournament(self):
        team = self.create_full_team("valorant")
        tournament = self.create_tournament("valorant")

        self.client.force_login(self.player)

        response = self.client.get(
            reverse(
                "apply_to_tournament",
                args=[tournament.pk, team.pk]
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "tournament_detail",
                args=[tournament.pk]
            )
        )

        application = TournamentApplication.objects.get(
            tournament=tournament,
            team=team
        )

        self.assertEqual(
            application.status,
            "pending"
        )

    # IT-TOUR-06
    def test_incomplete_team_cannot_apply(self):
        team = Team.objects.create(
            name="Incomplete",
            game="valorant",
            captain=self.player,
        )

        TeamMembership.objects.create(
            user=self.player,
            team=team,
        )

        tournament = self.create_tournament("valorant")

        self.client.force_login(self.player)

        self.client.get(
            reverse(
                "apply_to_tournament",
                args=[tournament.pk, team.pk]
            )
        )

        self.assertFalse(
            TournamentApplication.objects.filter(
                tournament=tournament,
                team=team
            ).exists()
        )

    # IT-TOUR-07
    def test_wrong_game_team_cannot_apply(self):
        team = self.create_full_team("pubg")
        tournament = self.create_tournament("valorant")

        self.client.force_login(self.player)

        self.client.get(
            reverse(
                "apply_to_tournament",
                args=[tournament.pk, team.pk]
            )
        )

        self.assertFalse(
            TournamentApplication.objects.filter(
                tournament=tournament,
                team=team
            ).exists()
        )

    # IT-TOUR-08
    def test_duplicate_application_is_rejected(self):
        team = self.create_full_team()
        tournament = self.create_tournament()

        TournamentApplication.objects.create(
            tournament=tournament,
            team=team,
            game="valorant",
            status="pending",
        )

        self.client.force_login(self.player)

        self.client.get(
            reverse(
                "apply_to_tournament",
                args=[tournament.pk, team.pk]
            )
        )

        self.assertEqual(
            TournamentApplication.objects.filter(
                tournament=tournament,
                team=team
            ).count(),
            1
        )

    # IT-TOUR-09
    def test_organizer_can_approve_application(self):
        team = self.create_full_team()
        tournament = self.create_tournament()

        application = TournamentApplication.objects.create(
            tournament=tournament,
            team=team,
            game="valorant",
            status="pending",
        )

        self.client.force_login(self.organizer)

        response = self.client.get(
            reverse(
                "approve_application",
                args=[application.pk]
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "tournament_detail",
                args=[tournament.pk]
            )
        )

        application.refresh_from_db()

        self.assertEqual(
            application.status,
            "approved"
        )

    # IT-TOUR-10
    def test_organizer_can_reject_application(self):
        team = self.create_full_team()
        tournament = self.create_tournament()

        application = TournamentApplication.objects.create(
            tournament=tournament,
            team=team,
            game="valorant",
            status="pending",
        )

        self.client.force_login(self.organizer)

        self.client.get(
            reverse(
                "reject_application",
                args=[application.pk]
            )
        )

        application.refresh_from_db()

        self.assertEqual(
            application.status,
            "rejected"
        )

    # IT-TOUR-11
    def test_non_organizer_cannot_approve_application(self):
        team = self.create_full_team()
        tournament = self.create_tournament()

        application = TournamentApplication.objects.create(
            tournament=tournament,
            team=team,
            game="valorant",
            status="pending",
        )

        self.client.force_login(self.player)

        response = self.client.get(
            reverse(
                "approve_application",
                args=[application.pk]
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

    # IT-TOUR-12
    def test_tournament_full_blocks_new_application(self):
        team = self.create_full_team()
        tournament = self.create_tournament()

        tournament.max_teams = 1
        tournament.save()

        other_team = Team.objects.create(
            name="Other Team",
            game="valorant",
            captain=self.other_player,
        )

        TournamentApplication.objects.create(
            tournament=tournament,
            team=other_team,
            game="valorant",
            status="approved",
        )

        self.client.force_login(self.player)

        self.client.get(
            reverse(
                "apply_to_tournament",
                args=[tournament.pk, team.pk]
            )
        )

        self.assertFalse(
            TournamentApplication.objects.filter(
                tournament=tournament,
                team=team
            ).exists()
        )

    # IT-TOUR-13
    def test_venue_date_conflict_blocks_booking(self):
        VenueBooking.objects.create(
            venue=self.venue,
            booked_by=self.organizer,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 12),
            status="confirmed",
        )

        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse("create_tournament"),
            {
                "name": "Conflict Tournament",
                "description": "Test",
                "rules": "Rules",
                "needs_venue": "True",
                "venue": self.venue.pk,
                "games": ["valorant"],
                "start_date": "2026-09-10",
                "end_date": "2026-09-12",
                "registration_deadline": "",
                "max_teams": 16,
                "entry_fee": 0,
                "prize_pool": 0,
            }
        )

        self.assertEqual(
            Tournament.objects.filter(
                name="Conflict Tournament"
            ).count(),
            0
        )