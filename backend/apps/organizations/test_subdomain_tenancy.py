"""Subdomain multi-tenancy: `<org-slug>.tochna.uz` is that org's entrance.

The subdomain is authoritative — a request on `alfa.tochna.uz` acts in org alfa
whatever the token claims, and a non-member is refused. These tests go through
the real JWT auth path (not `force_authenticate`), since the whole point is the
TenantMiddleware + authentication interplay.
"""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.common.testing import (
    add_membership,
    make_director,
    make_organization,
    make_school_class,
    make_student,
)
from apps.organizations.tenancy import tenant_slug_from_host

PASSWORD = "pass12345"  # apps.common.testing.make_user sets this


class TenantSlugParsingTests(APITestCase):
    def test_single_label_subdomain_is_the_slug(self):
        self.assertEqual(tenant_slug_from_host("alfa.tochna.uz", "tochna.uz"), "alfa")
        self.assertEqual(tenant_slug_from_host("ALFA.Tochna.UZ:443", "tochna.uz"), "alfa")

    def test_reserved_and_bare_and_foreign_hosts_are_none(self):
        for host in ["app.tochna.uz", "www.tochna.uz", "tochna.uz", "a.b.tochna.uz",
                     "crm.sharqsoft.uz", "", None]:
            self.assertIsNone(tenant_slug_from_host(host, "tochna.uz"), msg=host)


class SubdomainLoginTests(APITestCase):
    def _login(self, email, host):
        return self.client.post(
            "/api/auth/login/",
            {"email": email, "password": PASSWORD},
            format="json",
            HTTP_HOST=host,
        )

    def test_login_on_subdomain_pins_its_org_without_a_body_field(self):
        org = make_organization(name="Alfa", slug="alfa")
        director = make_director(organization=org)
        response = self._login(director.email, "alfa.tochna.uz")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["organization"]["slug"], "alfa")

    def test_login_on_a_foreign_subdomain_is_refused(self):
        make_organization(name="Alfa", slug="alfa")
        beta = make_organization(name="Beta", slug="beta")
        outsider = make_director(organization=beta)  # not a member of alfa
        response = self._login(outsider.email, "alfa.tochna.uz")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_on_main_host_redirects_to_the_org_subdomain(self):
        org = make_organization(name="Alfa", slug="alfa")
        director = make_director(organization=org)
        for host in ["tochna.uz", "app.tochna.uz", "www.tochna.uz"]:
            response = self._login(director.email, host)
            self.assertEqual(response.status_code, status.HTTP_200_OK, msg=host)
            self.assertEqual(response.data["redirect_to"], "alfa.tochna.uz", msg=host)

    def test_login_on_the_tenant_subdomain_has_no_redirect(self):
        org = make_organization(name="Alfa", slug="alfa")
        director = make_director(organization=org)
        response = self._login(director.email, "alfa.tochna.uz")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["redirect_to"])


class SubdomainRequestScopingTests(APITestCase):
    def setUp(self):
        self.org_a = make_organization(name="Alfa", slug="alfa")
        self.org_b = make_organization(name="Beta", slug="beta")

        # One director who belongs to BOTH organizations.
        self.director = make_director(organization=self.org_a)
        add_membership(self.director, self.org_b)

        self.student_a_user, self.student_a = make_student(
            make_school_class(organization=self.org_a, name="A-1"),
            organization=self.org_a,
            first_name="Alfa",
            last_name="Pupil",
        )
        self.student_b_user, self.student_b = make_student(
            make_school_class(organization=self.org_b, name="B-1"),
            organization=self.org_b,
            first_name="Beta",
            last_name="Pupil",
        )

    def _token(self, host):
        response = self.client.post(
            "/api/auth/login/",
            {"email": self.director.email, "password": PASSWORD},
            format="json",
            HTTP_HOST=host,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        return response.data["access"]

    def _student_ids(self, host, token):
        response = self.client.get(
            "/api/students/", HTTP_HOST=host, HTTP_AUTHORIZATION=f"Bearer {token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        return {row["id"] for row in response.data["results"]}

    def test_subdomain_scopes_the_student_list(self):
        token = self._token("alfa.tochna.uz")  # token's claim = org A
        ids_on_a = self._student_ids("alfa.tochna.uz", token)
        self.assertIn(self.student_a.id, ids_on_a)
        self.assertNotIn(self.student_b.id, ids_on_a)

    def test_same_token_on_the_other_subdomain_acts_in_that_org(self):
        token = self._token("alfa.tochna.uz")  # claim = org A …
        ids_on_b = self._student_ids("beta.tochna.uz", token)  # … but host = org B wins
        self.assertIn(self.student_b.id, ids_on_b)
        self.assertNotIn(self.student_a.id, ids_on_b)

    def test_foreign_subdomain_is_forbidden(self):
        gamma = make_organization(name="Gamma", slug="gamma")  # director not a member
        token = self._token("alfa.tochna.uz")
        response = self.client.get(
            "/api/students/",
            HTTP_HOST="gamma.tochna.uz",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        _ = gamma

    def test_reserved_host_falls_back_to_the_token_org(self):
        token = self._token("alfa.tochna.uz")
        ids = self._student_ids("app.tochna.uz", token)  # no tenant -> token's org A
        self.assertIn(self.student_a.id, ids)
        self.assertNotIn(self.student_b.id, ids)


class CreateOrganizationSlugFilterTests(APITestCase):
    """The org slug is a subdomain, so creation must reject illegal/reserved slugs."""

    def _create(self, director, slug):
        self.client.force_authenticate(director)
        return self.client.post(
            "/api/organizations/",
            {"name": "X", "slug": slug, "type": "SCHOOL", "timezone": "Asia/Tashkent"},
            format="json",
        )

    def test_reserved_slug_rejected(self):
        director = make_director()
        response = self._create(director, "app")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("slug", response.data.get("errors", response.data))

    def test_illegal_characters_rejected(self):
        director = make_director()
        for bad in ["Up_per", "-x", "x-", "a.b"]:
            response = self._create(director, bad)
            self.assertEqual(
                response.status_code, status.HTTP_400_BAD_REQUEST, msg=f"accepted {bad!r}"
            )
