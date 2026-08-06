from django.test import TestCase
from django.contrib.auth import get_user_model

from .models import (
    Team,
    TeamMembership,
    TeamInvite,
    JoinRequest,
    generate_team_code,
)

from .forms import (
    CreateTeamForm,
    InvitePlayerForm,
    JoinByCodeForm,
)

User = get_user_model()


# ==========================================================
# TEAM MODEL TESTS
# ==========================================================

class TeamModelTest(TestCase):

    def setUp(self):

        self.player = User.objects.create_user(
            username="captain",
            password="StrongPass123!",
            role="player"
        )

    def test_create_team(self):

        team = Team.objects.create(
            name="Alpha",
            game="valorant",
            captain=self.player
        )

        self.assertEqual(team.name, "Alpha")
        self.assertEqual(team.game, "valorant")

    def test_team_string(self):

        team = Team.objects.create(
            name="Warriors",
            game="pubg",
            captain=self.player
        )

        self.assertEqual(
            str(team),
            "Warriors (pubg)"
        )

    def test_team_code_generated(self):

        code = generate_team_code()

        self.assertEqual(len(code), 6)

    def test_team_code_unique_length(self):

        team = Team.objects.create(
            name="TeamOne",
            game="valorant",
            captain=self.player
        )

        self.assertEqual(len(team.team_code), 6)

    def test_valorant_max_size(self):

        team = Team.objects.create(
            name="ValorantTeam",
            game="valorant",
            captain=self.player
        )

        self.assertEqual(team.max_size(), 5)

    def test_pubg_max_size(self):

        team = Team.objects.create(
            name="PUBGTeam",
            game="pubg",
            captain=self.player
        )

        self.assertEqual(team.max_size(), 4)

    def test_team_not_full_initially(self):

        team = Team.objects.create(
            name="Dream",
            game="valorant",
            captain=self.player
        )

        self.assertFalse(team.is_full())


# ==========================================================
# TEAM MEMBERSHIP TESTS
# ==========================================================

class TeamMembershipTest(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="member",
            password="StrongPass123!",
            role="player"
        )

        self.team = Team.objects.create(
            name="Legends",
            game="valorant",
            captain=self.user
        )

    def test_create_membership(self):

        membership = TeamMembership.objects.create(
            user=self.user,
            team=self.team
        )

        self.assertEqual(
            membership.user.username,
            "member"
        )

    def test_membership_string(self):

        membership = TeamMembership.objects.create(
            user=self.user,
            team=self.team
        )

        self.assertEqual(
            str(membership),
            "member → Legends"
        )


# ==========================================================
# TEAM INVITE TESTS
# ==========================================================

class TeamInviteTest(TestCase):

    def setUp(self):

        self.captain = User.objects.create_user(
            username="captain1",
            password="StrongPass123!",
            role="player"
        )

        self.player = User.objects.create_user(
            username="player1",
            password="StrongPass123!",
            role="player"
        )

        self.team = Team.objects.create(
            name="Phoenix",
            game="valorant",
            captain=self.captain
        )

    def test_create_invite(self):

        invite = TeamInvite.objects.create(
            team=self.team,
            invited_user=self.player
        )

        self.assertEqual(invite.status, "pending")

    def test_invite_string(self):

        invite = TeamInvite.objects.create(
            team=self.team,
            invited_user=self.player
        )

        self.assertEqual(
            str(invite),
            "Invite: player1 → Phoenix (pending)"
        )


# ==========================================================
# JOIN REQUEST TESTS
# ==========================================================

class JoinRequestTest(TestCase):

    def setUp(self):

        self.captain = User.objects.create_user(
            username="captain2",
            password="StrongPass123!",
            role="player"
        )

        self.player = User.objects.create_user(
            username="player2",
            password="StrongPass123!",
            role="player"
        )

        self.team = Team.objects.create(
            name="Titans",
            game="pubg",
            captain=self.captain
        )

    def test_join_request_created(self):

        req = JoinRequest.objects.create(
            team=self.team,
            player=self.player
        )

        self.assertEqual(req.status, "pending")

    def test_join_request_string(self):

        req = JoinRequest.objects.create(
            team=self.team,
            player=self.player
        )

        self.assertEqual(
            str(req),
            "player2 → Titans (pending)"
        )


# ==========================================================
# CREATE TEAM FORM TESTS
# ==========================================================

class CreateTeamFormTest(TestCase):

    def test_valid_team_form(self):

        form = CreateTeamForm(data={
            "name": "Galaxy",
            "game": "valorant",
        })

        self.assertTrue(form.is_valid())

    def test_invalid_team_form(self):

        form = CreateTeamForm(data={
            "name": "",
            "game": "",
        })

        self.assertFalse(form.is_valid())


# ==========================================================
# INVITE PLAYER FORM
# ==========================================================

class InvitePlayerFormTest(TestCase):

    def test_valid_invite_form(self):

        form = InvitePlayerForm(data={
            "username": "player123"
        })

        self.assertTrue(form.is_valid())

    def test_invalid_invite_form(self):

        form = InvitePlayerForm(data={
            "username": ""
        })

        self.assertFalse(form.is_valid())


# ==========================================================
# JOIN BY CODE FORM
# ==========================================================

class JoinByCodeFormTest(TestCase):

    def test_valid_join_code(self):

        form = JoinByCodeForm(data={
            "team_code": "ABC123"
        })

        self.assertTrue(form.is_valid())

    def test_invalid_join_code(self):

        form = JoinByCodeForm(data={
            "team_code": ""
        })

        self.assertFalse(form.is_valid())