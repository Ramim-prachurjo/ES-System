from django.test import TestCase

from django.urls import reverse

from accounts.models import CustomUser
from .models import Notification


class NotificationModelTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpass123",
            role="player",
        )

    def test_notification_creation(self):
        notification = Notification.objects.create(
            user=self.user,
            message="You were approved!",
        )

        self.assertEqual(
            notification.user,
            self.user
        )

        self.assertEqual(
            notification.message,
            "You were approved!"
        )

        self.assertFalse(
            notification.is_read
        )

 def test_notification_default_is_unread(self):
        notification = Notification.objects.create(
            user=self.user,
            message="New notification",
        )

        self.assertFalse(
            notification.is_read
        )

    def test_notification_can_be_marked_as_read(self):
        notification = Notification.objects.create(
            user=self.user,
            message="You were approved!",
        )

        notification.is_read = True
        notification.save()

        notification.refresh_from_db()

        self.assertTrue(
            notification.is_read
        )
  def test_notification_str_unread(self):
        notification = Notification.objects.create(
            user=self.user,
            message="You were approved!",
            is_read=False,
        )

        self.assertEqual(
            str(notification),
            "To testuser: You were approved! [unread]"
        )

    def test_notification_str_read(self):
        notification = Notification.objects.create(
            user=self.user,
            message="You were approved!",
            is_read=True,
        )

        self.assertEqual(
            str(notification),
            "To testuser: You were approved! [read]"
        )

 def test_long_message_is_truncated_in_str(self):
        message = "A" * 100

        notification = Notification.objects.create(
            user=self.user,
            message=message,
        )

        result = str(notification)

        self.assertEqual(
            result,
            f"To testuser: {'A' * 40} [unread]"
        )

 def test_notifications_are_ordered_newest_first(self):
        first = Notification.objects.create(
            user=self.user,
            message="First notification",
        )

        second = Notification.objects.create(
            user=self.user,
            message="Second notification",
        )

        notifications = Notification.objects.all()

        self.assertEqual(
            notifications.first(),
            second
        )

        self.assertEqual(
            notifications.last(),
            first
        )


class NotificationViewTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser",
            password="testpass123",
            role="player",
        )

        self.other_user = CustomUser.objects.create_user(
            username="otheruser",
            password="testpass123",
            role="player",
        )

    def test_notification_list_requires_login(self):
        response = self.client.get(
            reverse("notification_list")
        )

        self.assertEqual(
            response.status_code,
            302
        )

 def test_logged_in_user_can_view_notifications(self):
        self.client.force_login(
            self.user
        )

        response = self.client.get(
            reverse("notification_list")
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertTemplateUsed(
            response,
            "notifications/notification_list.html"
        )

    def test_user_only_sees_own_notifications(self):
        own_notification = Notification.objects.create(
            user=self.user,
            message="Your notification",
        )

        other_notification = Notification.objects.create(
            user=self.other_user,
            message="Other user's notification",
        )

        self.client.force_login(
            self.user
        )

        response = self.client.get(
            reverse("notification_list")
        )

        notifications = response.context["notifications"]

        self.assertIn(
            own_notification,
            notifications
        )

        self.assertNotIn(
            other_notification,
            notifications
        )

 def test_visiting_notification_list_marks_unread_as_read(self):
        notification = Notification.objects.create(
            user=self.user,
            message="Unread notification",
            is_read=False,
        )

        self.client.force_login(
            self.user
        )

        self.client.get(
            reverse("notification_list")
        )

        notification.refresh_from_db()

        self.assertTrue(
            notification.is_read
        )

def test_already_read_notification_remains_read(self):
        notification = Notification.objects.create(
            user=self.user,
            message="Already read",
            is_read=True,
        )

        self.client.force_login(
            self.user
        )

        self.client.get(
            reverse("notification_list")
        )

        notification.refresh_from_db()

        self.assertTrue(
            notification.is_read
        )

 def test_all_unread_notifications_are_marked_read(self):
        notification1 = Notification.objects.create(
            user=self.user,
            message="Notification 1",
            is_read=False,
        )

        notification2 = Notification.objects.create(
            user=self.user,
            message="Notification 2",
            is_read=False,
        )

        notification3 = Notification.objects.create(
            user=self.user,
            message="Notification 3",
            is_read=False,
        )

        self.client.force_login(
            self.user
        )

        self.client.get(
            reverse("notification_list")
        )

        notification1.refresh_from_db()
        notification2.refresh_from_db()
        notification3.refresh_from_db()

        self.assertTrue(
            notification1.is_read
        )

        self.assertTrue(
            notification2.is_read
        )

        self.assertTrue(
            notification3.is_read
        )

