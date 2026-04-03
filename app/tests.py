from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.test.utils import override_settings

from .models import NewsArticle, UserProfile


@override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage"
)
class CorePageTests(TestCase):
    def setUp(self):
        NewsArticle.objects.create(
            headline="Test headline",
            title="Test headline",
            summary="Test summary",
            url="https://example.com/story",
            image_url="https://example.com/image.jpg",
            source="The Hindu",
            category="home",
        )

    @patch("app.news.refresh_category")
    def test_home_page_renders(self, _refresh_category):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Top Headlines")

    def test_profile_requires_login(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)


@override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage"
)
class SignupFlowTests(TestCase):
    def test_signup_creates_user_and_profile(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "tester",
                "email": "tester@example.com",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="tester").exists())
        self.assertTrue(UserProfile.objects.filter(user__username="tester").exists())

    def test_signup_rejects_weak_password(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "weakuser",
                "email": "weak@example.com",
                "password1": "12345678",
                "password2": "12345678",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "password")
