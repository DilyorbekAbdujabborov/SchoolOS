from django.test import TestCase
from rest_framework import exceptions
from rest_framework.test import APIRequestFactory

from apps.common.testing import default_organization, make_organization

from .authentication import BridgeTokenAuthentication
from .models import Bridge, Device
from .permissions import IsBridge


class BridgeTokenTests(TestCase):
    def test_issue_token_sets_hash_and_returns_plaintext(self):
        bridge = Bridge.objects.create(organization=default_organization(), name="b1")
        token = bridge.issue_token()
        self.assertTrue(token)
        self.assertTrue(bridge.token_hash)
        self.assertNotEqual(bridge.token_hash, token)

    def test_issue_token_is_verifiable_and_not_stored_in_clear(self):
        from django.contrib.auth.hashers import check_password

        bridge = Bridge.objects.create(organization=default_organization(), name="b2")
        token = bridge.issue_token()
        self.assertTrue(check_password(token, bridge.token_hash))
        self.assertFalse(check_password("wrong-token", bridge.token_hash))


class DeviceTests(TestCase):
    def test_device_inherits_organization_from_bridge(self):
        org = make_organization("Device Org")
        bridge = Bridge.objects.create(organization=org, name="b3")
        device = Device.objects.create(bridge=bridge, serial="SER-1", vendor="hikvision")
        self.assertEqual(device.organization_id, org.id)

    def test_device_direction_defaults_to_both(self):
        bridge = Bridge.objects.create(organization=default_organization(), name="b4")
        device = Device.objects.create(bridge=bridge, serial="SER-2")
        self.assertEqual(device.direction, Device.Direction.BOTH)


class BridgeAuthenticationTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def _request(self, token=None):
        headers = {}
        if token is not None:
            headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return self.factory.post("/api/devices/events/", **headers)

    def test_valid_token_resolves_bridge_and_org(self):
        org = make_organization("Auth Org")
        bridge = Bridge.objects.create(organization=org, name="b")
        token = bridge.issue_token()
        request = self._request(token)

        result = BridgeTokenAuthentication().authenticate(request)

        self.assertIsNotNone(result)
        self.assertEqual(request.bridge, bridge)
        self.assertEqual(request.organization_id, org.id)

    def test_no_header_returns_none(self):
        self.assertIsNone(BridgeTokenAuthentication().authenticate(self._request()))

    def test_unknown_token_rejected(self):
        with self.assertRaises(exceptions.AuthenticationFailed):
            BridgeTokenAuthentication().authenticate(self._request("not-a-real-token"))

    def test_revoked_bridge_rejected(self):
        bridge = Bridge.objects.create(organization=default_organization(), name="b")
        token = bridge.issue_token()
        bridge.is_active = False
        bridge.save(update_fields=["is_active"])
        with self.assertRaises(exceptions.AuthenticationFailed):
            BridgeTokenAuthentication().authenticate(self._request(token))

    def test_is_bridge_permission(self):
        request = self._request()
        self.assertFalse(IsBridge().has_permission(request, view=None))
        request.bridge = Bridge.objects.create(organization=default_organization(), name="b")
        self.assertTrue(IsBridge().has_permission(request, view=None))
