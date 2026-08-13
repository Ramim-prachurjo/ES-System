from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import (
    Team,
    TeamMembership,
    TeamInvite,
    JoinRequest,
)

User = get_user_model()


class TeamsFrontendTests(TestCase):

    def setUp(self):
        self.client = Client()

        self.captain = User.objects.create_user(
            username="captain",
            password="testpass123",
            role="player",
        )

        self.player = User.objects.create_user(
            username="player1",
            password="testpass123",
            role="player",
        )

        self.player2 = User.objects.create_user(
            username="player2",
            password="testpass123",
            role="player",
        )

        self.team = Team.objects.create(
            name="Alpha Squad",
            game="valorant",
            captain=self.captain,
        )

        TeamMembership.objects.create(
            user=self.captain,
            team=self.team,
        )

        self.client.login(
            username="captain",
            password="testpass123",
        )

    # ==========================================================
    # TEAM LIST FRONTEND
    # ==========================================================

    def test_team_list_page_loads(self):
        response = self.client.get(reverse("team_list"))

        self.assertEqual(response.status_code, 200)

    def test_team_list_contains_team_name(self):
        response = self.client.get(reverse("team_list"))

        self.assertContains(response, "Alpha Squad")

    def test_team_list_contains_game(self):
        response = self.client.get(reverse("team_list"))

        self.assertContains(response, "Valorant")

    def test_team_list_contains_captain(self):
        response = self.client.get(reverse("team_list"))

        self.assertContains(response, "captain")

    def test_team_list_contains_view_team_link(self):
        response = self.client.get(reverse("team_list"))

        self.assertContains(
            response,
            reverse("team_detail", kwargs={"pk": self.team.pk}),
        )

    def test_team_list_empty_state(self):
        Team.objects.all().delete()

        response = self.client.get(reverse("team_list"))

        self.assertEqual(response.status_code, 200)

    # ==========================================================
    # CREATE TEAM FRONTEND
    # ==========================================================

    def test_create_team_page_loads(self):
        response = self.client.get(reverse("create_team"))

        self.assertEqual(response.status_code, 200)

    def test_create_team_contains_name_field(self):
        response = self.client.get(reverse("create_team"))

        self.assertContains(response, 'name')

    def test_create_team_contains_game_field(self):
        response = self.client.get(reverse("create_team"))

        self.assertContains(response, 'game')

    def test_player_can_create_team(self):
        self.client.logout()

        self.client.login(
            username="player1",
            password="testpass123",
        )

        response = self.client.post(
            reverse("create_team"),
            {
                "name": "Bravo Squad",
                "game": "pubg",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Team.objects.filter(name="Bravo Squad").exists()
        )

    # ==========================================================
    # TEAM DETAIL FRONTEND
    # ==========================================================

    def test_team_detail_page_loads(self):
        response = self.client.get(
            reverse(
                "team_detail",
                kwargs={"pk": self.team.pk},
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_team_detail_contains_team_information(self):
        response = self.client.get(
            reverse(
                "team_detail",
                kwargs={"pk": self.team.pk},
            )
        )

        self.assertContains(response, "Alpha Squad")
        self.assertContains(response, "Valorant")

    def test_team_detail_contains_members(self):
        response = self.client.get(
            reverse(
                "team_detail",
                kwargs={"pk": self.team.pk},
            )
        )

        self.assertContains(response, "captain")

    def test_captain_can_see_team_code(self):
        response = self.client.get(
            reverse(
                "team_detail",
                kwargs={"pk": self.team.pk},
            )
        )

        self.assertContains(response, self.team.team_code)

    def test_captain_can_see_invite_player(self):
        response = self.client.get(
            reverse(
                "team_detail",
                kwargs={"pk": self.team.pk},
            )
        )

        self.assertContains(response, "Invite")

    # ==========================================================
    # MY TEAM FRONTEND
    # ==========================================================

    def test_my_team_page_loads(self):
        response = self.client.get(reverse("my_team"))

        self.assertEqual(response.status_code, 200)

    def test_my_team_contains_team_name(self):
        response = self.client.get(reverse("my_team"))

        self.assertContains(response, "Alpha Squad")

    def test_my_team_contains_capacity(self):
        response = self.client.get(reverse("my_team"))

        # Captain is currently the only member.
        # Valorant maximum = 5.
        self.assertContains(response, "5")

    def test_captain_sees_view_team_link_in_my_team(self):
        response = self.client.get(reverse("my_team"))

        self.assertContains(response, reverse("team_detail", kwargs={"pk": self.team.pk}))
        self.assertNotContains(response, self.team.team_code)

    # ==========================================================
    # MY INVITES FRONTEND
    # ==========================================================

    def test_my_invites_page_loads(self):
        self.client.logout()

        self.client.login(
            username="player1",
            password="testpass123",
        )

        response = self.client.get(reverse("my_invites"))

        self.assertEqual(response.status_code, 200)

    def test_my_invites_empty_state(self):
        self.client.logout()

        self.client.login(
            username="player1",
            password="testpass123",
        )

        response = self.client.get(reverse("my_invites"))

        self.assertEqual(response.status_code, 200)

    def test_my_invites_displays_invitation(self):
        TeamInvite.objects.create(
            team=self.team,
            invited_user=self.player,
        )

        self.client.logout()

        self.client.login(
            username="player1",
            password="testpass123",
        )

        response = self.client.get(reverse("my_invites"))

        self.assertContains(response, "Alpha Squad")

    # ==========================================================
    # JOIN REQUESTS FRONTEND
    # ==========================================================

    def test_join_requests_page_loads(self):
        response = self.client.get(reverse("my_join_requests"))

        self.assertEqual(response.status_code, 200)

    def test_join_requests_displays_pending_request(self):
        JoinRequest.objects.create(
            team=self.team,
            player=self.player,
        )

        response = self.client.get(reverse("my_join_requests"))

        self.assertContains(response, "player1")

    # ==========================================================
    # BROWSE TEAMS FRONTEND
    # ==========================================================

    def test_browse_teams_page_loads(self):
        self.client.logout()

        self.client.login(
            username="player1",
            password="testpass123",
        )

        response = self.client.get(reverse("browse_teams"))

        self.assertEqual(response.status_code, 200)

    def test_browse_teams_contains_filters(self):
        self.client.logout()

        self.client.login(
            username="player1",
            password="testpass123",
        )

        response = self.client.get(reverse("browse_teams"))

        self.assertContains(response, "Valorant")
        self.assertContains(response, "PUBG")

    def test_browse_teams_contains_join_code(self):
        self.client.logout()

        self.client.login(
            username="player1",
            password="testpass123",
        )

        response = self.client.get(reverse("browse_teams"))

        self.assertEqual(response.status_code, 200)

    def test_browse_teams_game_filter(self):
        self.client.logout()

        self.client.login(
            username="player1",
            password="testpass123",
        )

        response = self.client.get(
            reverse("browse_teams"),
            {"game": "valorant"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha Squad")

    def test_browse_teams_availability_filter(self):
        self.client.logout()

        self.client.login(
            username="player1",
            password="testpass123",
        )

        response = self.client.get(
            reverse("browse_teams"),
            {"availability": "open"},
        )

        self.assertEqual(response.status_code, 200)

    # ==========================================================
    # JOIN BY CODE FRONTEND
    # ==========================================================

    def test_player_can_see_join_code_form(self):
        self.client.logout()

        self.client.login(
            username="player1",
            password="testpass123",
        )

        response = self.client.get(reverse("team_list"))

        self.assertEqual(response.status_code, 200)

    def test_join_by_code_works(self):
        self.client.logout()

        self.client.login(
            username="player1",
            password="testpass123",
        )

        response = self.client.post(
            reverse("join_by_code"),
            {
                "team_code": self.team.team_code,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            TeamMembership.objects.filter(
                user=self.player,
                team=self.team,
            ).exists()
        )

    # ==========================================================
    # REQUEST TO JOIN
    # ==========================================================

    def test_player_can_request_to_join(self):
        self.client.logout()

        self.client.login(
            username="player1",
            password="testpass123",
        )

        response = self.client.post(
            reverse(
                "request_to_join",
                kwargs={"team_id": self.team.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            JoinRequest.objects.filter(
                team=self.team,
                player=self.player,
            ).exists()
        )

    # ==========================================================
    # TEAM INVITATION FRONTEND
    # ==========================================================

    def test_captain_can_invite_player(self):
        response = self.client.post(
            reverse(
                "invite_player",
                kwargs={"team_id": self.team.pk},
            ),
            {
                "username": "player1",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            TeamInvite.objects.filter(
                team=self.team,
                invited_user=self.player,
            ).exists()
        )

    # ==========================================================
    # LEAVE TEAM FRONTEND
    # ==========================================================

    def test_member_can_leave_team(self):
        TeamMembership.objects.create(
            user=self.player,
            team=self.team,
        )

        self.client.logout()

        self.client.login(
            username="player1",
            password="testpass123",
        )

        response = self.client.post(
            reverse(
                "leave_team",
                kwargs={"team_id": self.team.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            TeamMembership.objects.filter(
                user=self.player,
                team=self.team,
            ).exists()
        )

    # ==========================================================
    # CAPACITY
    # ==========================================================

    def test_valorant_team_max_size(self):
        self.assertEqual(self.team.max_size(), 5)

    def test_pubg_team_max_size(self):
        pubg_team = Team.objects.create(
            name="PUBG Warriors",
            game="pubg",
            captain=self.captain,
        )

        self.assertEqual(pubg_team.max_size(), 4)
