from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.common.testing import default_organization, make_organization

from .capabilities import RESOURCES, all_keys, capability_for, get_denied, is_allowed
from .models import ClientConfig


class CapabilityForTests(TestCase):
    def test_method_maps_to_action(self):
        self.assertEqual(capability_for("/api/students/", "GET"), "students.read")
        self.assertEqual(capability_for("/api/students/", "HEAD"), "students.read")
        self.assertEqual(capability_for("/api/students/", "OPTIONS"), "students.read")
        self.assertEqual(capability_for("/api/students/", "POST"), "students.create")
        self.assertEqual(capability_for("/api/students/5/", "PATCH"), "students.update")
        self.assertEqual(capability_for("/api/students/5/", "PUT"), "students.update")
        self.assertEqual(capability_for("/api/students/5/", "DELETE"), "students.delete")

    def test_custom_action_under_prefix_is_gated(self):
        self.assertEqual(capability_for("/api/students/bulk-import/", "POST"), "students.create")

    def test_prefix_matches_whole_segment_only(self):
        self.assertEqual(capability_for("/api/tests/", "GET"), "tests.read")
        self.assertEqual(capability_for("/api/teacher-tasks/", "GET"), "tasks.read")
        self.assertIsNone(capability_for("/api/testsx/", "GET"))
        self.assertEqual(capability_for("/api/students", "GET"), "students.read")

    def test_unregistered_paths_are_never_gated(self):
        for path in ("/api/auth/me/", "/api/notifications/", "/api/devices/events/",
                     "/api/organizations/", "/api/p/handle/", "/admin/", "/"):
            self.assertIsNone(capability_for(path, "GET"), path)

    def test_every_resource_has_prefixes(self):
        for key, resource in RESOURCES.items():
            self.assertTrue(resource.api_prefixes, key)


class IsAllowedTests(TestCase):
    def test_read_denial_blocks_every_action(self):
        denied = frozenset({"materials.read"})
        for action in ("read", "create", "update", "delete"):
            self.assertFalse(is_allowed(denied, f"materials.{action}"))
        self.assertTrue(is_allowed(denied, "students.create"))

    def test_write_denial_keeps_read(self):
        denied = frozenset({"students.create"})
        self.assertTrue(is_allowed(denied, "students.read"))
        self.assertFalse(is_allowed(denied, "students.create"))
        self.assertTrue(is_allowed(denied, "students.update"))


class ClientConfigTests(TestCase):
    def test_no_row_means_nothing_denied(self):
        self.assertEqual(get_denied(make_organization("Fresh")), frozenset())

    def test_denied_round_trip(self):
        org = default_organization()
        ClientConfig.objects.create(organization=org, denied=["materials.read"])
        self.assertEqual(get_denied(org), frozenset({"materials.read"}))

    def test_unknown_key_rejected(self):
        config = ClientConfig(organization=default_organization(), denied=["bogus.read"])
        with self.assertRaises(ValidationError):
            config.full_clean()

    def test_all_keys_cover_resources_times_actions(self):
        self.assertEqual(len(all_keys()), len(RESOURCES) * 4)
