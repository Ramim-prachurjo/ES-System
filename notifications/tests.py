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


