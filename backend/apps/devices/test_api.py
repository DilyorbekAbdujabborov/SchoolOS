from datetime import datetime

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.common.testing import default_organization, make_organization, make_student

from .models import AccessEvent, Bridge, Device

EVENTS_URL = "/api/devices/events/"
HEARTBEAT_URL = "/api/devices/heartbeat/"


def _iso(h, m):
    return timezone.make_aware(datetime(2026, 10, 9, h, m)).isoformat()


class EventsEndpointTests(APITestCase):
    def setUp(self):
        self.org = default_organization()
        self.bridge = Bridge.objects.create(organization=self.org, name="b")
        self.token = self.bridge.issue_token()
        self.device = Device.objects.create(bridge=self.bridge, serial="DEV-1")
        self.user, self.student = make_student()

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def _item(self, osid=None, direction="IN"):
        return {
            "device_serial": "DEV-1",
            "osid": osid or self.user.osid,
            "event_time": _iso(8, 3),
            "direction": direction,
            "verify_mode": "face",
            "raw": {"src": "test"},
        }

    def test_post_events_with_bridge_token_ingests(self):
        self._auth()
        response = self.client.post(EVENTS_URL, [self._item()], format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["accepted"]), 1)
        self.assertEqual(AccessEvent.objects.count(), 1)

    def test_post_events_without_token_401(self):
        response = self.client.post(EVENTS_URL, [self._item()], format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(AccessEvent.objects.count(), 0)

    def test_bridge_cannot_post_osid_of_another_org(self):
        other_user, _ = make_student(organization=make_organization("Other School"))
        self._auth()
        response = self.client.post(
            EVENTS_URL, [self._item(osid=other_user.osid)], format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["unmatched"]), 1)
        self.assertIsNone(AccessEvent.objects.get().user)


class HeartbeatEndpointTests(APITestCase):
    def setUp(self):
        self.bridge = Bridge.objects.create(organization=default_organization(), name="b")
        self.token = self.bridge.issue_token()
        self.device = Device.objects.create(bridge=self.bridge, serial="DEV-1")

    def test_heartbeat_updates_last_seen(self):
        self.assertIsNone(self.bridge.last_seen_at)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.post(
            HEARTBEAT_URL, {"device_serials": ["DEV-1"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.bridge.refresh_from_db()
        self.assertIsNotNone(self.bridge.last_seen_at)
