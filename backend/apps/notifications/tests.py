from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.common.testing import make_director, make_teacher

from .models import Notification, PushSubscription
from .push import send_web_push
from .services import notify


class NotifyServiceTests(TestCase):
    def test_notify_creates_a_web_notification(self):
        recipient = make_director()
        notification = notify(recipient=recipient, title="Salom", body="Test xabar")

        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notification.recipient, recipient)
        self.assertEqual(notification.title, "Salom")

    def test_notify_does_not_raise_when_recipient_has_no_linked_telegram_account(self):
        recipient = make_director()
        # No TelegramAccount exists for `recipient` — the Telegram push must be a
        # silent no-op, never an exception that would break the calling feature.
        notify(recipient=recipient, title="Salom", body="Test xabar")


class NotificationMarkReadAPITests(APITestCase):
    def setUp(self):
        self.owner_user, _ = make_teacher()
        self.other_user, _ = make_teacher()
        self.notification = notify(recipient=self.owner_user, title="Salom", body="Test")

    def test_owner_can_mark_their_notification_read(self):
        self.client.force_authenticate(self.owner_user)
        response = self.client.patch(f"/api/notifications/{self.notification.id}/mark-read/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_another_user_cannot_see_or_mark_someone_elses_notification(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.patch(f"/api/notifications/{self.notification.id}/mark-read/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class WebPushTests(TestCase):
    def test_send_web_push_is_a_no_op_without_vapid_keys(self):
        recipient = make_director()
        PushSubscription.objects.create(
            user=recipient, endpoint="https://example.com/ep", p256dh="p", auth="a"
        )
        # No VAPID key configured in test settings → must return silently without
        # ever importing pywebpush or raising.
        send_web_push(recipient, "Salom", "Test")

    @override_settings(VAPID_PRIVATE_KEY="dummy")
    def test_notify_tolerates_push_failures(self):
        recipient = make_director()
        PushSubscription.objects.create(
            user=recipient, endpoint="https://example.com/ep", p256dh="p", auth="a"
        )
        # pywebpush will choke on the dummy key / fake endpoint, but notify() must
        # still create the DB row — the push channel is best-effort.
        notification = notify(recipient=recipient, title="Salom", body="Test")
        self.assertEqual(Notification.objects.filter(pk=notification.pk).count(), 1)


class PushSubscriptionAPITests(APITestCase):
    def setUp(self):
        self.user = make_director()
        self.payload = {
            "endpoint": "https://push.example.com/abc123",
            "keys": {"p256dh": "BPublicKey", "auth": "AuthSecret"},
        }

    def test_subscribe_requires_authentication(self):
        response = self.client.post("/api/push/subscribe/", self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_subscribe_stores_the_endpoint_for_the_caller(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/push/subscribe/", self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        sub = PushSubscription.objects.get(endpoint=self.payload["endpoint"])
        self.assertEqual(sub.user, self.user)
        self.assertEqual(sub.p256dh, "BPublicKey")

    def test_subscribing_twice_updates_rather_than_duplicates(self):
        self.client.force_authenticate(self.user)
        self.client.post("/api/push/subscribe/", self.payload, format="json")
        self.client.post("/api/push/subscribe/", self.payload, format="json")
        self.assertEqual(
            PushSubscription.objects.filter(endpoint=self.payload["endpoint"]).count(), 1
        )

    def test_subscribe_rejects_a_payload_missing_keys(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            "/api/push/subscribe/",
            {"endpoint": "https://push.example.com/x", "keys": {"p256dh": "only"}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsubscribe_removes_the_endpoint(self):
        self.client.force_authenticate(self.user)
        self.client.post("/api/push/subscribe/", self.payload, format="json")
        response = self.client.post(
            "/api/push/unsubscribe/", {"endpoint": self.payload["endpoint"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PushSubscription.objects.filter(endpoint=self.payload["endpoint"]).exists())

    def test_vapid_key_endpoint_returns_the_configured_public_key(self):
        self.client.force_authenticate(self.user)
        with override_settings(VAPID_PUBLIC_KEY="PUBKEY123"):
            response = self.client.get("/api/push/vapid-key/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["public_key"], "PUBKEY123")
