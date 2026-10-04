from django.urls import reverse
from rest_framework.test import APITestCase

from .models import DemoRequest


class DemoRequestEndpointTests(APITestCase):
    """The public landing-page demo form: anyone may post, no auth, validated."""

    def setUp(self):
        self.url = reverse("demo-request-create")

    def test_anonymous_can_submit(self):
        response = self.client.post(
            self.url,
            {"name": "Ali Valiyev", "phone": "+998 90 123 45 67", "school_name": "5-maktab"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("detail", response.data)
        lead = DemoRequest.objects.get()
        self.assertEqual(lead.name, "Ali Valiyev")
        self.assertEqual(lead.status, DemoRequest.Status.NEW)

    def test_status_is_not_settable_by_the_caller(self):
        self.client.post(
            self.url,
            {"name": "Ali Valiyev", "phone": "+998901234567", "status": "closed"},
            format="json",
        )
        self.assertEqual(DemoRequest.objects.get().status, DemoRequest.Status.NEW)

    def test_short_name_is_rejected(self):
        response = self.client.post(
            self.url, {"name": "A", "phone": "+998901234567"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.data["errors"])
        self.assertFalse(DemoRequest.objects.exists())

    def test_bad_phone_is_rejected(self):
        response = self.client.post(
            self.url, {"name": "Ali Valiyev", "phone": "12"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("phone", response.data["errors"])
        self.assertFalse(DemoRequest.objects.exists())
