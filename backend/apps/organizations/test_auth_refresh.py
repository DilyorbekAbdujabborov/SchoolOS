"""Regression: `/api/auth/refresh/` must work with only a refresh token.

The multi-tenancy refactor gave `OrganizationTokenRefreshView` a
`permission_classes = [IsAuthenticated]` while the base view runs no
authentication, so every refresh returned 401 — logging users out the moment
their 1-hour access token expired. These tests pin the endpoint open to a valid
refresh token and closed to a bad one.
"""

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.testing import make_director
from apps.organizations.authentication import ORG_CLAIM


class TokenRefreshTests(APITestCase):
    def setUp(self):
        self.user = make_director()
        self.org_id = self.user.active_organization_id
        refresh = RefreshToken.for_user(self.user)
        refresh[ORG_CLAIM] = self.org_id
        self.refresh = str(refresh)

    def test_refresh_succeeds_with_only_the_refresh_token(self):
        # No access token / Authorization header — the whole point of a refresh.
        response = self.client.post(
            "/api/auth/refresh/", {"refresh": self.refresh}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["organization"]["id"], self.org_id)

    def test_refresh_ignores_a_stale_access_token_in_the_header(self):
        response = self.client.post(
            "/api/auth/refresh/",
            {"refresh": self.refresh},
            format="json",
            HTTP_AUTHORIZATION="Bearer not.a.real.token",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_rejects_a_bad_token(self):
        response = self.client.post(
            "/api/auth/refresh/", {"refresh": "garbage"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_requires_a_token(self):
        response = self.client.post("/api/auth/refresh/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutTests(APITestCase):
    def setUp(self):
        self.user = make_director()
        refresh = RefreshToken.for_user(self.user)
        refresh[ORG_CLAIM] = self.user.active_organization_id
        self.refresh = str(refresh)

    def test_logout_blacklists_the_refresh_token(self):
        logout = self.client.post("/api/auth/logout/", {"refresh": self.refresh}, format="json")
        self.assertEqual(logout.status_code, status.HTTP_205_RESET_CONTENT)

        # The blacklisted token can no longer be refreshed.
        refreshed = self.client.post(
            "/api/auth/refresh/", {"refresh": self.refresh}, format="json"
        )
        self.assertEqual(refreshed.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_a_token_is_a_400(self):
        response = self.client.post("/api/auth/logout/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_is_idempotent_for_a_bad_token(self):
        response = self.client.post("/api/auth/logout/", {"refresh": "garbage"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
