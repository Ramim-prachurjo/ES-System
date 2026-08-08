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



# ==========================================================
#                 TEAM VIEW TESTS
# ==========================================================

from django.urls import reverse


class TeamViewTest(TestCase):

    def setUp(self):
        self.player = User.objects.create_user(
            username="player1",
            password="StrongPass123!",
            role="player"
        )

        self.organizer = User.objects.create_user(
            username="organizer1",
            password="StrongPass123!",
            role="organizer"
        )

        self.team = Team.objects.create(
            name="Alpha Squad",
            game="valorant",
            captain=self.player
        )

        TeamMembership.objects.create(
            user=self.player,
            team=self.team
        )

        self.client.login(
            username="player1",
            password="StrongPass123!"
        )

    # ------------------------------------------------------
    # TEAM LIST
    # ------------------------------------------------------

    def test_team_list_authenticated(self):
        response = self.client.get(
            reverse("team_list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "teams/team_list.html"
        )

        self.assertContains(
            response,
            "Alpha Squad"
        )

    # ------------------------------------------------------
    # CREATE TEAM
    # ------------------------------------------------------

    def test_create_team_get(self):
        response = self.client.get(
            reverse("create_team")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "teams/create_team.html"
        )

    def test_create_team_successfully(self):
        response = self.client.post(
            reverse("create_team"),
            {
                "name": "New Warriors",
                "game": "pubg",
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        team = Team.objects.get(
            name="New Warriors"
        )

        self.assertEqual(
            team.captain,
            self.player
        )

        self.assertEqual(
            team.game,
            "pubg"
        )

        # Captain should automatically become
        # a team member.
        self.assertTrue(
            TeamMembership.objects.filter(
                user=self.player,
                team=team
            ).exists()
        )

    def test_non_player_cannot_create_team(self):
        self.client.logout()

        self.client.login(
            username="organizer1",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse("create_team")
        )

        self.assertRedirects(
            response,
            reverse("team_list")
        )

        self.assertEqual(
            Team.objects.filter(
                name="Organizer Team"
            ).count(),
            0
        )

    def test_player_cannot_create_second_team_for_same_game(self):
        response = self.client.post(
            reverse("create_team"),
            {
                "name": "Another Valorant Team",
                "game": "valorant",
            }
        )

        # The view renders the form again instead
        # of creating another team.
        self.assertEqual(
            response.status_code,
            200
        )

        self.assertFalse(
            Team.objects.filter(
                name="Another Valorant Team"
            ).exists()
        )

    # ------------------------------------------------------
    # TEAM DETAIL
    # ------------------------------------------------------

    def test_team_detail(self):
        response = self.client.get(
            reverse(
                "team_detail",
                kwargs={"pk": self.team.pk}
            )
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "teams/team_detail.html"
        )

        self.assertEqual(
            response.context["team"],
            self.team
        )

        self.assertContains(
            response,
            "Alpha Squad"
        )

    # ------------------------------------------------------
    # JOIN BY CODE
    # ------------------------------------------------------

    def test_join_team_using_valid_code(self):

        new_player = User.objects.create_user(
            username="joinplayer",
            password="StrongPass123!",
            role="player"
        )

        self.client.logout()

        self.client.login(
            username="joinplayer",
            password="StrongPass123!"
        )

        response = self.client.post(
            reverse("join_by_code"),
            {
                "team_code": self.team.team_code
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertTrue(
            TeamMembership.objects.filter(
                user=new_player,
                team=self.team
            ).exists()
        )

        self.assertRedirects(
            response,
            reverse(
                "team_detail",
                kwargs={"pk": self.team.pk}
            )
        )

    def test_join_team_using_invalid_code(self):

        new_player = User.objects.create_user(
            username="invalidcode",
            password="StrongPass123!",
            role="player"
        )

        self.client.logout()

        self.client.login(
            username="invalidcode",
            password="StrongPass123!"
        )

        response = self.client.post(
            reverse("join_by_code"),
            {
                "team_code": "INVALID"
            }
        )

        self.assertRedirects(
            response,
            reverse("team_list")
        )

        self.assertEqual(
            TeamMembership.objects.filter(
                user=new_player
            ).count(),
            0
        )

    def test_join_team_same_game_rejected(self):

        another_player = User.objects.create_user(
            username="alreadyjoined",
            password="StrongPass123!",
            role="player"
        )

        existing_team = Team.objects.create(
            name="Existing Team",
            game="valorant",
            captain=another_player
        )

        TeamMembership.objects.create(
            user=another_player,
            team=existing_team
        )

        self.client.logout()

        self.client.login(
            username="alreadyjoined",
            password="StrongPass123!"
        )

        response = self.client.post(
            reverse("join_by_code"),
            {
                "team_code": self.team.team_code
            }
        )

        self.assertRedirects(
            response,
            reverse("team_list")
        )

        self.assertFalse(
            TeamMembership.objects.filter(
                user=another_player,
                team=self.team
            ).exists()
        )

    # ------------------------------------------------------
    # BROWSE TEAMS
    # ------------------------------------------------------

    def test_browse_teams(self):

        response = self.client.get(
            reverse("browse_teams")
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "teams/browse_teams.html"
        )

        self.assertContains(
            response,
            "Alpha Squad"
        )

    def test_browse_teams_game_filter(self):

        pubg_team = Team.objects.create(
            name="PUBG Warriors",
            game="pubg",
            captain=self.player
        )

        response = self.client.get(
            reverse("browse_teams"),
            {
                "game": "pubg"
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertContains(
            response,
            "PUBG Warriors"
        )

        self.assertNotContains(
            response,
            "Alpha Squad"
        )

    # ------------------------------------------------------
    # MY TEAM
    # ------------------------------------------------------

    def test_my_team(self):

        response = self.client.get(
            reverse("my_team")
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "teams/my_team.html"
        )

        team_data = response.context["team_data"]

        self.assertEqual(
            len(team_data),
            1
        )

        self.assertEqual(
            team_data[0]["team"],
            self.team
        )

        self.assertTrue(
            team_data[0]["is_captain"]
        )

    # ------------------------------------------------------
    # LOGIN PROTECTION
    # ------------------------------------------------------

    def test_team_list_requires_login(self):

        self.client.logout()

        response = self.client.get(
            reverse("team_list")
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertIn(
            "/accounts/login/",
            response.url
        )

    def test_create_team_requires_login(self):

        self.client.logout()

        response = self.client.get(
            reverse("create_team")
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertIn(
            "/accounts/login/",
            response.url
        )
# ==========================================================
#                 TEAM INVITATION VIEW TESTS
# ==========================================================

class TeamInvitationViewTest(TestCase):

    def setUp(self):
        self.captain = User.objects.create_user(
            username="captain",
            password="StrongPass123!",
            role="player"
        )

        self.player = User.objects.create_user(
            username="player",
            password="StrongPass123!",
            role="player"
        )

        self.team = Team.objects.create(
            name="Invite Team",
            game="valorant",
            captain=self.captain
        )

        TeamMembership.objects.create(
            user=self.captain,
            team=self.team
        )

        self.client.login(
            username="captain",
            password="StrongPass123!"
        )

    # ------------------------------------------------------
    # SEND INVITATION
    # ------------------------------------------------------

    def test_captain_can_invite_player(self):

        response = self.client.post(
            reverse(
                "invite_player",
                kwargs={"team_id": self.team.id}
            ),
            {
                "username": "player"
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertTrue(
            TeamInvite.objects.filter(
                team=self.team,
                invited_user=self.player,
                status="pending"
            ).exists()
        )

    # ------------------------------------------------------
    # INVITE NON-EXISTING USER
    # ------------------------------------------------------

    def test_invite_nonexistent_player(self):

        response = self.client.post(
            reverse(
                "invite_player",
                kwargs={"team_id": self.team.id}
            ),
            {
                "username": "doesnotexist"
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertFalse(
            TeamInvite.objects.filter(
                team=self.team
            ).exists()
        )

    # ------------------------------------------------------
    # CAPTAIN CANNOT INVITE THEMSELVES
    # ------------------------------------------------------

    def test_captain_cannot_invite_self(self):

        response = self.client.post(
            reverse(
                "invite_player",
                kwargs={"team_id": self.team.id}
            ),
            {
                "username": "captain"
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertFalse(
            TeamInvite.objects.filter(
                team=self.team,
                invited_user=self.captain
            ).exists()
        )

    # ------------------------------------------------------
    # CANNOT INVITE EXISTING MEMBER
    # ------------------------------------------------------

    def test_cannot_invite_existing_member(self):

        existing_member = User.objects.create_user(
            username="member",
            password="StrongPass123!",
            role="player"
        )

        TeamMembership.objects.create(
            user=existing_member,
            team=self.team
        )

        response = self.client.post(
            reverse(
                "invite_player",
                kwargs={"team_id": self.team.id}
            ),
            {
                "username": "member"
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertFalse(
            TeamInvite.objects.filter(
                team=self.team,
                invited_user=existing_member
            ).exists()
        )

    # ------------------------------------------------------
    # DUPLICATE INVITATION
    # ------------------------------------------------------

    def test_duplicate_invitation_not_created(self):

        TeamInvite.objects.create(
            team=self.team,
            invited_user=self.player
        )

        response = self.client.post(
            reverse(
                "invite_player",
                kwargs={"team_id": self.team.id}
            ),
            {
                "username": "player"
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertEqual(
            TeamInvite.objects.filter(
                team=self.team,
                invited_user=self.player
            ).count(),
            1
        )

    # ------------------------------------------------------
    # NON-CAPTAIN CANNOT SEND INVITATION
    # ------------------------------------------------------

    def test_non_captain_cannot_invite(self):

        self.client.logout()

        self.client.login(
            username="player",
            password="StrongPass123!"
        )

        response = self.client.post(
            reverse(
                "invite_player",
                kwargs={"team_id": self.team.id}
            ),
            {
                "username": "captain"
            }
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertFalse(
            TeamInvite.objects.filter(
                team=self.team,
                invited_user=self.captain
            ).exists()
        )

    # ------------------------------------------------------
    # VIEW INVITATIONS
    # ------------------------------------------------------

    def test_my_invites(self):

        invite = TeamInvite.objects.create(
            team=self.team,
            invited_user=self.player
        )

        self.client.logout()

        self.client.login(
            username="player",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse("my_invites")
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "teams/my_invites.html"
        )

        self.assertContains(
            response,
            "Invite Team"
        )

    # ------------------------------------------------------
    # ACCEPT INVITATION
    # ------------------------------------------------------

    def test_player_can_accept_invitation(self):

        invite = TeamInvite.objects.create(
            team=self.team,
            invited_user=self.player
        )

        self.client.logout()

        self.client.login(
            username="player",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "respond_invite",
                kwargs={
                    "invite_id": invite.id,
                    "action": "accept"
                }
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        invite.refresh_from_db()

        self.assertEqual(
            invite.status,
            "accepted"
        )

        self.assertTrue(
            TeamMembership.objects.filter(
                user=self.player,
                team=self.team
            ).exists()
        )

    # ------------------------------------------------------
    # REJECT INVITATION
    # ------------------------------------------------------

    def test_player_can_reject_invitation(self):

        invite = TeamInvite.objects.create(
            team=self.team,
            invited_user=self.player
        )

        self.client.logout()

        self.client.login(
            username="player",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "respond_invite",
                kwargs={
                    "invite_id": invite.id,
                    "action": "reject"
                }
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        invite.refresh_from_db()

        self.assertEqual(
            invite.status,
            "rejected"
        )

        self.assertFalse(
            TeamMembership.objects.filter(
                user=self.player,
                team=self.team
            ).exists()
        )

    # ------------------------------------------------------
    # INVALID INVITATION ACTION
    # ------------------------------------------------------

    def test_invalid_invitation_action(self):

        invite = TeamInvite.objects.create(
            team=self.team,
            invited_user=self.player
        )

        self.client.logout()

        self.client.login(
            username="player",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "respond_invite",
                kwargs={
                    "invite_id": invite.id,
                    "action": "invalid"
                }
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        invite.refresh_from_db()

        self.assertEqual(
            invite.status,
            "pending"
        )

    # ------------------------------------------------------
    # CANNOT ACCEPT SOMEONE ELSE'S INVITATION
    # ------------------------------------------------------

    def test_other_player_cannot_accept_invitation(self):

     other_player = User.objects.create_user(
        username="otherplayer",
        password="StrongPass123!",
        role="player"
     )

     invite = TeamInvite.objects.create(
        team=self.team,
        invited_user=self.player
     )

     self.client.logout()

     self.client.login(
        username="otherplayer",
        password="StrongPass123!"
     )

     response = self.client.get(
        reverse(
            "respond_invite",
            kwargs={
                "invite_id": invite.id,
                "action": "accept"
            }
        )
    )

    # The view hides invitations belonging to another user.
     self.assertEqual(
        response.status_code,
        404
    )

     invite.refresh_from_db()

    # The original invitation must remain pending.
     self.assertEqual(
        invite.status,
        "pending"
    )

    # The unauthorized user must not become a member.
     self.assertFalse(
        TeamMembership.objects.filter(
            user=other_player,
            team=self.team
        ).exists()
    )

 # ==========================================================
#       JOIN REQUEST / TEAM MANAGEMENT VIEW TESTS
# ==========================================================

class TeamManagementViewTest(TestCase):

    def setUp(self):
        self.captain = User.objects.create_user(
            username="captain",
            password="StrongPass123!",
            role="player"
        )

        self.member = User.objects.create_user(
            username="member",
            password="StrongPass123!",
            role="player"
        )

        self.player = User.objects.create_user(
            username="requestplayer",
            password="StrongPass123!",
            role="player"
        )

        self.team = Team.objects.create(
            name="Management Team",
            game="valorant",
            captain=self.captain
        )

        TeamMembership.objects.create(
            user=self.captain,
            team=self.team
        )

        TeamMembership.objects.create(
            user=self.member,
            team=self.team
        )

        self.client.login(
            username="requestplayer",
            password="StrongPass123!"
        )

    # ------------------------------------------------------
    # REQUEST TO JOIN
    # ------------------------------------------------------

def test_player_can_request_to_join(self):

    response = self.client.post(
        reverse(
            "request_to_join",
            kwargs={"team_id": self.team.id}
        )
    )

    self.assertEqual(
        response.status_code,
        302
    )

    self.assertTrue(
        JoinRequest.objects.filter(
            team=self.team,
            player=self.player,
            status="pending"
        ).exists()
    )
    # ------------------------------------------------------
    # DUPLICATE JOIN REQUEST
    # ------------------------------------------------------

    def test_duplicate_join_request_not_created(self):

        JoinRequest.objects.create(
            team=self.team,
            player=self.player
        )

        response = self.client.get(
            reverse(
                "request_to_join",
                kwargs={"team_id": self.team.id}
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertEqual(
            JoinRequest.objects.filter(
                team=self.team,
                player=self.player
            ).count(),
            1
        )

    # ------------------------------------------------------
    # ALREADY MEMBER CANNOT REQUEST
    # ------------------------------------------------------

    def test_existing_member_cannot_request_to_join(self):

        self.client.logout()

        self.client.login(
            username="member",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "request_to_join",
                kwargs={"team_id": self.team.id}
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertFalse(
            JoinRequest.objects.filter(
                team=self.team,
                player=self.member
            ).exists()
        )

    # ------------------------------------------------------
    # VIEW MY JOIN REQUESTS
    # ------------------------------------------------------

def test_my_join_requests(self):

    JoinRequest.objects.create(
        team=self.team,
        player=self.player
    )

    self.client.logout()

    self.client.login(
        username="captain",
        password="StrongPass123!"
    )

    response = self.client.get(
        reverse("my_join_requests")
    )

    self.assertEqual(
        response.status_code,
        200
    )

    self.assertTemplateUsed(
        response,
        "teams/join_requests.html"
    )

    self.assertContains(
        response,
        "Management Team"
    )

    # ------------------------------------------------------
    # CAPTAIN ACCEPTS JOIN REQUEST
    # ------------------------------------------------------

def test_captain_can_accept_join_request(self):

    join_request = JoinRequest.objects.create(
        team=self.team,
        player=self.player
    )

    self.client.logout()

    self.client.login(
        username="captain",
        password="StrongPass123!"
    )

    response = self.client.get(
        reverse(
            "handle_join_request",
            kwargs={
                "req_id": join_request.id,
                "action": "approve"
            }
        )
    )

    self.assertEqual(
        response.status_code,
        302
    )

    join_request.refresh_from_db()

    self.assertEqual(
        join_request.status,
        "accepted"
    )

    self.assertTrue(
        TeamMembership.objects.filter(
            user=self.player,
            team=self.team
        ).exists()
    )
    # ------------------------------------------------------
    # CAPTAIN REJECTS JOIN REQUEST
    # ------------------------------------------------------

    def test_captain_can_reject_join_request(self):

        join_request = JoinRequest.objects.create(
            team=self.team,
            player=self.player
        )

        self.client.logout()

        self.client.login(
            username="captain",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "handle_join_request",
                kwargs={
                    "req_id": join_request.id,
                    "action": "reject"
                }
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        join_request.refresh_from_db()

        self.assertEqual(
            join_request.status,
            "rejected"
        )

        self.assertFalse(
            TeamMembership.objects.filter(
                user=self.player,
                team=self.team
            ).exists()
        )

    # ------------------------------------------------------
    # NON-CAPTAIN CANNOT HANDLE REQUEST
    # ------------------------------------------------------

    def test_non_captain_cannot_handle_join_request(self):

        join_request = JoinRequest.objects.create(
            team=self.team,
            player=self.player
        )

        self.client.logout()

        self.client.login(
            username="member",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "handle_join_request",
                kwargs={
                    "req_id": join_request.id,
                    "action": "accept"
                }
            )
        )

        self.assertIn(
            response.status_code,
            [302, 403, 404]
        )

        join_request.refresh_from_db()

        self.assertEqual(
            join_request.status,
            "pending"
        )

    # ------------------------------------------------------
    # PLAYER LEAVES TEAM
    # ------------------------------------------------------

    def test_member_can_leave_team(self):

        self.client.logout()

        self.client.login(
            username="member",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "leave_team",
                kwargs={"team_id": self.team.id}
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertFalse(
            TeamMembership.objects.filter(
                user=self.member,
                team=self.team
            ).exists()
        )

    # ------------------------------------------------------
    # CAPTAIN CANNOT LEAVE TEAM
    # ------------------------------------------------------

    def test_captain_cannot_leave_team(self):

        self.client.logout()

        self.client.login(
            username="captain",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "leave_team",
                kwargs={"team_id": self.team.id}
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertTrue(
            TeamMembership.objects.filter(
                user=self.captain,
                team=self.team
            ).exists()
        )

    # ------------------------------------------------------
    # CAPTAIN REMOVES MEMBER
    # ------------------------------------------------------

    def test_captain_can_remove_member(self):

        self.client.logout()

        self.client.login(
            username="captain",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "remove_member",
                kwargs={
                    "team_id": self.team.id,
                    "user_id": self.member.id
                }
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.assertFalse(
            TeamMembership.objects.filter(
                user=self.member,
                team=self.team
            ).exists()
        )

    # ------------------------------------------------------
    # NON-CAPTAIN CANNOT REMOVE MEMBER
    # ------------------------------------------------------

    def test_non_captain_cannot_remove_member(self):

        self.client.logout()

        self.client.login(
            username="member",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "remove_member",
                kwargs={
                    "team_id": self.team.id,
                    "user_id": self.captain.id
                }
            )
        )

        self.assertIn(
            response.status_code,
            [302, 403, 404]
        )

        self.assertTrue(
            TeamMembership.objects.filter(
                user=self.captain,
                team=self.team
            ).exists()
        )

    # ------------------------------------------------------
    # TRANSFER CAPTAIN
    # ------------------------------------------------------

    def test_captain_can_transfer_captaincy(self):

        self.client.logout()

        self.client.login(
            username="captain",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "transfer_captain",
                kwargs={
                    "team_id": self.team.id,
                    "user_id": self.member.id
                }
            )
        )

        self.assertEqual(
            response.status_code,
            302
        )

        self.team.refresh_from_db()

        self.assertEqual(
            self.team.captain,
            self.member
        )

    # ------------------------------------------------------
    # NON-CAPTAIN CANNOT TRANSFER CAPTAINCY
    # ------------------------------------------------------

    def test_non_captain_cannot_transfer_captaincy(self):

        self.client.logout()

        self.client.login(
            username="member",
            password="StrongPass123!"
        )

        response = self.client.get(
            reverse(
                "transfer_captain",
                kwargs={
                    "team_id": self.team.id,
                    "user_id": self.player.id
                }
            )
        )

        self.assertIn(
            response.status_code,
            [302, 403, 404]
        )

        self.team.refresh_from_db()

        self.assertEqual(
            self.team.captain,
            self.captain
        )    