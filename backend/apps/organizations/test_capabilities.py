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


from rest_framework.test import APITestCase  # noqa: E402
from rest_framework_simplejwt.tokens import RefreshToken  # noqa: E402

from apps.common.testing import add_membership, make_director  # noqa: E402


class CapabilityGateApiTests(APITestCase):
    def setUp(self):
        self.org_a = default_organization()
        self.org_b = make_organization("School B")
        self.director = make_director()  # active in org_a

    def _auth(self, user, **headers):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", **headers)

    def _deny(self, org, *keys):
        ClientConfig.objects.update_or_create(organization=org, defaults={"denied": list(keys)})

    def test_denied_read_blocks_get_and_post_with_envelope(self):
        self._deny(self.org_a, "materials.read")
        self._auth(self.director)
        for method in ("get", "post"):
            response = getattr(self.client, method)("/api/materials/", {}, format="json")
            self.assertEqual(response.status_code, 403, method)
            self.assertEqual(response.data["error_code"], "capability_denied")
            self.assertEqual(response.data["errors"]["capability"], [f"materials.{'read' if method == 'get' else 'create'}"])

    def test_write_denial_keeps_read(self):
        self._deny(self.org_a, "students.create")
        self._auth(self.director)
        self.assertEqual(self.client.get("/api/students/").status_code, 200)
        response = self.client.post("/api/students/", {}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error_code"], "capability_denied")

    def test_other_org_config_does_not_apply(self):
        self._deny(self.org_b, "students.read")
        self._auth(self.director)
        self.assertEqual(self.client.get("/api/students/").status_code, 200)

    def test_header_switch_applies_target_org_config(self):
        add_membership(self.director, self.org_b, role="DIRECTOR")
        self._deny(self.org_b, "students.read")
        self._auth(self.director, HTTP_X_ORGANIZATION_ID=str(self.org_b.id))
        self.assertEqual(self.client.get("/api/students/").status_code, 403)

    def test_unregistered_route_never_gated(self):
        self._deny(self.org_a, *[f"{r}.read" for r in RESOURCES])
        self._auth(self.director)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)

    def test_anonymous_still_401(self):
        self._deny(self.org_a, "materials.read")
        self.assertEqual(self.client.get("/api/materials/").status_code, 401)


class MeCapabilitiesTests(APITestCase):
    def setUp(self):
        self.org = default_organization()
        self.director = make_director()
        token = str(RefreshToken.for_user(self.director).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_me_lists_denied_for_acting_org(self):
        ClientConfig.objects.create(
            organization=self.org, denied=["students.create", "materials.read"]
        )
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["capabilities"], {"denied": ["materials.read", "students.create"]}
        )

    def test_me_empty_when_no_config(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.data["capabilities"], {"denied": []})
