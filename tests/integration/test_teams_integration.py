from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from notifications.models import Notification

from teams.models import (
    Team,
    TeamMembership,
    TeamInvite,
    JoinRequest,
)


class TeamsIntegrationTests(TestCase):

    def setUp(self):
        self.captain = CustomUser.objects.create_user(
            username="captain",
            password="StrongPass123!",
            role="player",
        )

        self.player = CustomUser.objects.create_user(
            username="player",
            password="StrongPass123!",
            role="player",
        )

        self.player2 = CustomUser.objects.create_user(
            username="player2",
            password="StrongPass123!",
            role="player",
        )

        self.organizer = CustomUser.objects.create_user(
            username="organizer",
            password="StrongPass123!",
            role="organizer",
        )

    def create_team(self, game="valorant"):
        team = Team.objects.create(
            name=f"Team {Team.objects.count() + 1}",
            game=game,
            captain=self.captain,
        )

        TeamMembership.objects.create(
            user=self.captain,
            team=team,
        )

        return team

    # IT-TEAM-01
    def test_create_team_creates_membership_for_captain(self):
        self.client.force_login(self.captain)

        response = self.client.post(
            reverse("create_team"),
            {
                "name": "Alpha",
                "game": "valorant",
            }
        )

        self.assertEqual(response.status_code, 302)

        team = Team.objects.get(name="Alpha")

        self.assertEqual(
            team.captain,
            self.captain
        )

        self.assertTrue(
            TeamMembership.objects.filter(
                user=self.captain,
                team=team
            ).exists()
        )

    # IT-TEAM-02
    def test_player_cannot_create_second_same_game_team(self):
        team = self.create_team("valorant")

        self.client.force_login(self.captain)

        response = self.client.post(
            reverse("create_team"),
            {
                "name": "Second",
                "game": "valorant",
            }
        )

        self.assertEqual(
            Team.objects.filter(
                captain=self.captain,
                game="valorant"
            ).count(),
            1
        )

    # IT-TEAM-03
    def test_player_can_create_team_for_different_game(self):
        self.create_team("valorant")

        self.client.force_login(self.captain)

        response = self.client.post(
            reverse("create_team"),
            {
                "name": "PUBG Team",
                "game": "pubg",
            }
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Team.objects.filter(
                captain=self.captain,
                game="pubg"
            ).exists()
        )

    # IT-TEAM-04
    def test_organizer_cannot_create_team(self):
        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse("create_team"),
            {
                "name": "Wrong Team",
                "game": "valorant",
            }
        )

        self.assertFalse(
            Team.objects.filter(name="Wrong Team").exists()
        )

    # IT-TEAM-05
    def test_captain_can_invite_player(self):
        team = self.create_team()

        self.client.force_login(self.captain)

        response = self.client.post(
            reverse(
                "invite_player",
                args=[team.pk]
            ),
            {
                "username": self.player.username
            }
        )

        self.assertEqual(response.status_code, 302)

        invite = TeamInvite.objects.get(
            team=team,
            invited_user=self.player
        )

        self.assertEqual(
            invite.status,
            "pending"
        )

        self.assertTrue(
            Notification.objects.filter(
                user=self.player
            ).exists()
        )

    # IT-TEAM-06
    def test_non_captain_cannot_invite_player(self):
        team = self.create_team()

        self.client.force_login(self.player)

        self.client.post(
            reverse(
                "invite_player",
                args=[team.pk]
            ),
            {
                "username": self.player2.username
            }
        )

        self.assertFalse(
            TeamInvite.objects.filter(
                team=team,
                invited_user=self.player2
            ).exists()
        )

    # IT-TEAM-07
    def test_cannot_invite_player_already_in_same_game_team(self):
        team = self.create_team()

        other_team = Team.objects.create(
            name="Other",
            game="valorant",
            captain=self.player,
        )

        TeamMembership.objects.create(
            user=self.player,
            team=other_team,
        )

        self.client.force_login(self.captain)

        self.client.post(
            reverse(
                "invite_player",
                args=[team.pk]
            ),
            {
                "username": self.player.username
            }
        )

        self.assertFalse(
            TeamInvite.objects.filter(
                team=team,
                invited_user=self.player
            ).exists()
        )

    # IT-TEAM-08
    def test_player_accepts_invitation_and_becomes_member(self):
        team = self.create_team()

        invite = TeamInvite.objects.create(
            team=team,
            invited_user=self.player,
        )

        self.client.force_login(self.player)

        response = self.client.get(
            reverse(
                "respond_invite",
                args=[invite.pk, "accept"]
            )
        )

        self.assertRedirects(
            response,
            reverse("my_invites")
        )

        self.assertTrue(
            TeamMembership.objects.filter(
                user=self.player,
                team=team
            ).exists()
        )

        invite.refresh_from_db()

        self.assertEqual(
            invite.status,
            "accepted"
        )

        self.assertTrue(
            Notification.objects.filter(
                user=self.captain
            ).exists()
        )

    # IT-TEAM-09
    def test_player_can_reject_invitation(self):
        team = self.create_team()

        invite = TeamInvite.objects.create(
            team=team,
            invited_user=self.player,
        )

        self.client.force_login(self.player)

        self.client.get(
            reverse(
                "respond_invite",
                args=[invite.pk, "reject"]
            )
        )

        invite.refresh_from_db()

        self.assertEqual(
            invite.status,
            "rejected"
        )

        self.assertFalse(
            TeamMembership.objects.filter(
                user=self.player,
                team=team
            ).exists()
        )

    # IT-TEAM-10
    def test_join_by_code_adds_player_to_team(self):
        team = self.create_team()

        self.client.force_login(self.player)

        response = self.client.post(
            reverse("join_by_code"),
            {
                "team_code": team.team_code
            }
        )

        self.assertRedirects(
            response,
            reverse(
                "team_detail",
                args=[team.pk]
            )
        )

        self.assertTrue(
            TeamMembership.objects.filter(
                user=self.player,
                team=team
            ).exists()
        )

    # IT-TEAM-11
    def test_invalid_team_code_does_not_create_membership(self):
        self.client.force_login(self.player)

        self.client.post(
            reverse("join_by_code"),
            {
                "team_code": "INVALID"
            }
        )

        self.assertEqual(
            TeamMembership.objects.filter(
                user=self.player
            ).count(),
            0
        )

    # IT-TEAM-12
    def test_player_can_request_to_join_team(self):
        team = self.create_team()

        self.client.force_login(self.player)

        response = self.client.post(
            reverse(
                "request_to_join",
                args=[team.pk]
            )
        )

        self.assertRedirects(
            response,
            reverse("browse_teams")
        )

        self.assertTrue(
            JoinRequest.objects.filter(
                team=team,
                player=self.player,
                status="pending",
            ).exists()
        )

        self.assertTrue(
            Notification.objects.filter(
                user=self.captain
            ).exists()
        )

    # IT-TEAM-13
    def test_player_cannot_request_to_join_same_game_team(self):
        team = self.create_team()

        existing_team = Team.objects.create(
            name="Existing",
            game="valorant",
            captain=self.player2,
        )

        TeamMembership.objects.create(
            user=self.player,
            team=existing_team,
        )

        self.client.force_login(self.player)

        self.client.post(
            reverse(
                "request_to_join",
                args=[team.pk]
            )
        )

        self.assertFalse(
            JoinRequest.objects.filter(
                team=team,
                player=self.player
            ).exists()
        )

    # IT-TEAM-14
    def test_captain_can_approve_join_request(self):
        team = self.create_team()

        join_request = JoinRequest.objects.create(
            team=team,
            player=self.player,
        )

        self.client.force_login(self.captain)

        response = self.client.get(
            reverse(
                "handle_join_request",
                args=[join_request.pk, "approve"]
            )
        )

        self.assertRedirects(
            response,
            reverse("my_join_requests")
        )

        join_request.refresh_from_db()

        self.assertEqual(
            join_request.status,
            "accepted"
        )

        self.assertTrue(
            TeamMembership.objects.filter(
                user=self.player,
                team=team
            ).exists()
        )

    # IT-TEAM-15
    def test_captain_can_reject_join_request(self):
        team = self.create_team()

        join_request = JoinRequest.objects.create(
            team=team,
            player=self.player,
        )

        self.client.force_login(self.captain)

        self.client.get(
            reverse(
                "handle_join_request",
                args=[join_request.pk, "reject"]
            )
        )

        join_request.refresh_from_db()

        self.assertEqual(
            join_request.status,
            "rejected"
        )

        self.assertFalse(
            TeamMembership.objects.filter(
                user=self.player,
                team=team
            ).exists()
        )

    # IT-TEAM-16
    def test_captain_can_transfer_captaincy(self):
        team = self.create_team()

        TeamMembership.objects.create(
            user=self.player,
            team=team
        )

        self.client.force_login(self.captain)

        response = self.client.get(
            reverse(
                "transfer_captain",
                args=[team.pk, self.player.pk]
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "team_detail",
                args=[team.pk]
            )
        )

        team.refresh_from_db()

        self.assertEqual(
            team.captain,
            self.player
        )

    # IT-TEAM-17
    def test_captain_can_remove_member(self):
        team = self.create_team()

        TeamMembership.objects.create(
            user=self.player,
            team=team
        )

        self.client.force_login(self.captain)

        response = self.client.get(
            reverse(
                "remove_member",
                args=[team.pk, self.player.pk]
            )
        )

        self.assertRedirects(
            response,
            reverse("my_team")
        )

        self.assertFalse(
            TeamMembership.objects.filter(
                user=self.player,
                team=team
            ).exists()
        )

    # IT-TEAM-18
    def test_non_captain_cannot_remove_member(self):
        team = self.create_team()

        TeamMembership.objects.create(
            user=self.player,
            team=team
        )

        self.client.force_login(self.player)

        self.client.get(
            reverse(
                "remove_member",
                args=[team.pk, self.player2.pk]
            )
        )

        self.assertFalse(
            TeamMembership.objects.filter(
                user=self.player2,
                team=team
            ).exists()
        )

    # IT-TEAM-19
    def test_member_can_leave_team(self):
        team = self.create_team()

        TeamMembership.objects.create(
            user=self.player,
            team=team
        )

        self.client.force_login(self.player)

        response = self.client.get(
            reverse(
                "leave_team",
                args=[team.pk]
            )
        )

        self.assertFalse(
            TeamMembership.objects.filter(
                user=self.player,
                team=team
            ).exists()
        )

    # IT-TEAM-20
    def test_last_captain_member_can_disband_team(self):
        team = self.create_team()

        self.client.force_login(self.captain)

        response = self.client.get(
            reverse(
                "leave_team",
                args=[team.pk]
            )
        )

        self.assertFalse(
            Team.objects.filter(pk=team.pk).exists()
        )