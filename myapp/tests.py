from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from .models import Category, Resume


class PublicPageSmokeTests(TestCase):
    def test_public_pages_render_successfully(self):
        urls = [
            reverse("home"),
            reverse("aboutas"),
            reverse("studio"),
            reverse("login"),
            reverse("register"),
            reverse("forgot_password"),
            reverse("resource_page", args=["faq"]),
            reverse("resource_page", args=["blog"]),
            reverse("resource_page", args=["support"]),
            reverse("resource_page", args=["security"]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_protected_pages_redirect_anonymous_user(self):
        urls = [
            reverse("homeview"),
            reverse("history"),
            reverse("feedback"),
            reverse("profile"),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)


class AuthenticatedPageSmokeTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.specialist_group = Group.objects.create(name="Specialist")
        self.customer_group = Group.objects.create(name="Customer")

        self.specialist = user_model.objects.create_user(
            username="specialist",
            email="specialist@example.com",
            password="Testpass123!",
            is_email_verified=True,
        )
        self.specialist.groups.add(self.specialist_group)

        self.customer = user_model.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="Testpass123!",
            is_email_verified=True,
        )
        self.customer.groups.add(self.customer_group)

        self.category = Category.objects.create(name="Design")
        self.resume = Resume.objects.create(
            user=self.specialist,
            full_name="Test Specialist",
            category=self.category,
            skills="Figma, UI",
            price="100.00",
        )

    def login_with_session(self, user):
        session = self.client.session
        session["user_id"] = user.id
        session["username"] = user.username
        session.save()

    def test_authenticated_user_can_open_core_pages(self):
        self.login_with_session(self.customer)

        urls = [
            reverse("homeview"),
            reverse("history"),
            reverse("profile"),
            reverse("feedback"),
            reverse("resume_detail", args=[self.resume.pk]),
            reverse("order_add", args=[self.resume.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_specialist_can_open_resume_management_pages(self):
        self.login_with_session(self.specialist)

        urls = [
            reverse("resume_add"),
            reverse("resume_edit", args=[self.resume.pk]),
            reverse("resume_delete", args=[self.resume.pk]),
            reverse("review_add", args=[self.resume.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
