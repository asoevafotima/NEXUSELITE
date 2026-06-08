from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class UserViewTests(TestCase):
    def test_login_register_and_forgot_password_pages_render(self):
        for name in ["login", "register", "forgot_password"]:
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_authenticated_user_is_redirected_away_from_login(self):
        user = get_user_model().objects.create_user(
            username="verified",
            email="verified@example.com",
            password="Testpass123!",
            is_email_verified=True,
        )
        session = self.client.session
        session["user_id"] = user.id
        session["username"] = user.username
        session.save()

        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))
