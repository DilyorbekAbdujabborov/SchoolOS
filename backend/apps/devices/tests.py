from django.test import TestCase

from apps.common.testing import default_organization, make_organization

from .models import Bridge, Device


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
