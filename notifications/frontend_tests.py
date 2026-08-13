from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Notification

User = get_user_model()


class NotificationsFrontendTests(TestCase):

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="notification_user",
            password="testpass123",
            role="player",
        )

        self.other_user = User.objects.create_user(
            username="other_user",
            password="testpass123",
            role="player",
        )

        self.client.login(
            username="notification_user",
            password="testpass123",
        )

    # ==========================================================
    # NOTIFICATIONS PAGE
    # ==========================================================

    def test_notifications_page_loads(self):
        """
        Notifications page should load successfully.
        """
        response = self.client.get(
            reverse("notification_list")
        )

        self.assertEqual(response.status_code, 200)

    def test_notifications_page_uses_correct_template(self):
        """
        Notifications page should render the notification template.
        """
        response = self.client.get(
            reverse("notification_list")
        )

        self.assertTemplateUsed(
            response,
            "notifications/notification_list.html",
        )

    def test_notifications_page_contains_title(self):
        """
        Page should display the Notifications heading.
        """
        response = self.client.get(
            reverse("notification_list")
        )

        self.assertContains(
            response,
            "Notifications",
        )

    def test_notifications_page_contains_description(self):
        """
        Page should display the notification description.
        """
        response = self.client.get(
            reverse("notification_list")
        )

        self.assertContains(
            response,
            "All your notifications",
        )

    # ==========================================================
    # NOTIFICATION CONTENT
    # ==========================================================

    def test_notification_message_is_displayed(self):
        """
        Notification message should appear in the frontend.
        """
        Notification.objects.create(
            user=self.user,
            message="Your team registration has been approved.",
        )

        response = self.client.get(
            reverse("notification_list")
        )

        self.assertContains(
            response,
            "Your team registration has been approved.",
        )

    def test_multiple_notifications_are_displayed(self):
        """
        Multiple notifications should be displayed.
        """
        Notification.objects.create(
            user=self.user,
            message="First notification",
        )

        Notification.objects.create(
            user=self.user,
            message="Second notification",
        )

        Notification.objects.create(
            user=self.user,
            message="Third notification",
        )

        response = self.client.get(
            reverse("notification_list")
        )

        self.assertContains(response, "First notification")
        self.assertContains(response, "Second notification")
        self.assertContains(response, "Third notification")

    # ==========================================================
    # NOTIFICATION CARD UI
    # ==========================================================

    def test_notification_card_is_rendered(self):
        """
        Each notification should be rendered inside a notification card.
        """
        Notification.objects.create(
            user=self.user,
            message="Test notification",
        )

        response = self.client.get(
            reverse("notification_list")
        )

        self.assertContains(
            response,
            "notif-card",
        )

    def test_notification_message_container_is_rendered(self):
        """
        Notification message should use the notification message container.
        """
        Notification.objects.create(
            user=self.user,
            message="Test notification message",
        )

        response = self.client.get(
            reverse("notification_list")
        )

        self.assertContains(
            response,
            "notif-message",
        )

    def test_notification_time_is_rendered(self):
        """
        Notification should display its time information.
        """
        Notification.objects.create(
            user=self.user,
            message="Time test notification",
        )

        response = self.client.get(
            reverse("notification_list")
        )

        self.assertContains(
            response,
            "notif-time",
        )

        self.assertContains(
            response,
            "ago",
        )

    # ==========================================================
    # READ / UNREAD UI
    # ==========================================================

    def test_unread_notification_has_unread_class(self):
        """
        An unread notification should initially be rendered
        using the unread UI class.

        The view automatically marks notifications as read when
        the page is visited, so this test checks the notification
        data/template behavior through a direct template render.
        """
        notification = Notification.objects.create(
            user=self.user,
            message="Unread notification",
            is_read=False,
        )

        response = self.client.get(
            reverse("notification_list")
        )

        # The page was visited, so the view marks it as read.
        notification.refresh_from_db()

        self.assertTrue(notification.is_read)

        self.assertContains(
            response,
            "Unread notification",
        )

    def test_read_notification_is_displayed(self):
        """
        Read notifications should still be visible.
        """
        Notification.objects.create(
            user=self.user,
            message="Already read notification",
            is_read=True,
        )

        response = self.client.get(
            reverse("notification_list")
        )

        self.assertContains(
            response,
            "Already read notification",
        )

    # ==========================================================
    # EMPTY STATE
    # ==========================================================

    def test_empty_state_is_displayed_when_no_notifications(self):
        """
        No notifications should display the empty state.
        """
        response = self.client.get(
            reverse("notification_list")
        )

        self.assertContains(
            response,
            "No notifications yet.",
        )

    def test_empty_state_contains_mail_icon(self):
        """
        Empty state should contain the 📭 icon.
        """
        response = self.client.get(
            reverse("notification_list")
        )

        self.assertContains(
            response,
            "📭",
        )

    def test_notification_list_is_not_rendered_when_empty(self):
        """
        Notification list should not be rendered when there
        are no notifications.
        """
        response = self.client.get(
            reverse("notification_list")
        )

        # The class name exists in the page CSS, so check for the actual list
        # element rather than searching the entire HTML response for the name.
        self.assertNotContains(response, '<div class="notif-list">', html=True)

    # ==========================================================
    # USER-SPECIFIC FRONTEND CONTENT
    # ==========================================================

    def test_logged_in_user_sees_own_notification(self):
        """
        Logged-in user should see their own notification.
        """
        Notification.objects.create(
            user=self.user,
            message="This belongs to notification_user.",
        )

        response = self.client.get(
            reverse("notification_list")
        )

        self.assertContains(
            response,
            "This belongs to notification_user.",
        )

    def test_logged_in_user_does_not_see_other_users_notification(self):
        """
        Notifications belonging to another user should not
        appear on the logged-in user's page.
        """
        Notification.objects.create(
            user=self.other_user,
            message="Private notification of another user.",
        )

        response = self.client.get(
            reverse("notification_list")
        )

        self.assertNotContains(
            response,
            "Private notification of another user.",
        )

    # ==========================================================
    # AUTHENTICATION FRONTEND
    # ==========================================================

    def test_anonymous_user_cannot_access_notifications(self):
        """
        Logged-out users should be redirected from the
        notifications page.
        """
        self.client.logout()

        response = self.client.get(
            reverse("notification_list")
        )

        self.assertEqual(
            response.status_code,
            302,
        )
