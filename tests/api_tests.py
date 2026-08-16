"""Contract tests for the application's JSON API endpoints.

These tests use Django's test client and mock the external Gemini request, so
they are deterministic, fast, and never consume production API quota.
"""

import json
import os
from unittest.mock import patch
from urllib.error import HTTPError

from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser


class ChatbotApiTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="api_user",
            email="api_user@example.com",
            password="StrongPassword123!",
            role="player",
        )
        self.url = reverse("chatbot_response")

    def authenticate(self):
        self.client.force_login(self.user)

    def post_json(self, payload):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_requires_authentication(self):
        response = self.post_json({"message": "How do I join a team?"})

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_rejects_non_post_requests_for_authenticated_users(self):
        self.authenticate()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_rejects_invalid_json(self):
        self.authenticate()

        response = self.client.post(
            self.url, data="not-json", content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Please send a valid question.")

    def test_rejects_empty_or_oversized_messages(self):
        self.authenticate()

        empty = self.post_json({"message": ""})
        oversized = self.post_json({"message": "x" * 701})

        self.assertEqual(empty.status_code, 400)
        self.assertEqual(oversized.status_code, 400)

    def test_returns_deterministic_platform_help_json(self):
        self.authenticate()

        response = self.post_json({"message": "How can I apply for a tournament?"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["source"], "platform_help")
        self.assertIn("captain", response.json()["answer"])

    @patch.dict(os.environ, {}, clear=True)
    def test_reports_missing_external_api_configuration(self):
        self.authenticate()

        response = self.post_json({"message": "What is esports?"})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "The assistant is not configured yet.")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch("accounts.views.urlrequest.urlopen")
    def test_maps_upstream_failure_to_safe_json_error(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(
            self.url, 429, "rate limited", {}, None
        )
        self.authenticate()

        response = self.post_json({"message": "What is esports?"})

        self.assertEqual(response.status_code, 503)
        self.assertNotIn("test-key", response.content.decode())
