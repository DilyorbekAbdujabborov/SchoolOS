"""Regression: a director must only ever see their own organization's data.

The multi-tenancy work added an `organization` FK to the org-scoped models and
set it on writes, but the viewsets' director branch returned the whole table —
so a director of one school could read every other school's tests, students,
leaderboard and attendance. These tests pin the isolation closed.
"""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.common.testing import (
    make_director,
    make_organization,
    make_school_class,
    make_student,
    make_subject,
    make_teacher,
)
from apps.learning.models import Test


class DirectorCrossTenantIsolationTests(APITestCase):
    @staticmethod
    def _rows(response):
        """Unwrap the page when the endpoint paginates, else take the list."""
        data = response.data
        return data["results"] if isinstance(data, dict) and "results" in data else data

    def setUp(self):
        self.org_a = make_organization(name="Alpha School")
        self.org_b = make_organization(name="Beta School")

        self.director_a = make_director(organization=self.org_a)

        self.subject = make_subject()
        _, teacher_b = make_teacher(organization=self.org_b)
        self.class_b = make_school_class(organization=self.org_b)
        self.student_b_user, self.student_b = make_student(
            self.class_b,
            organization=self.org_b,
            first_name="BetaOrg",
            last_name="Pupil",
        )
        self.test_b = Test.objects.create(
            title="Beta test",
            subject=self.subject,
            school_class=self.class_b,
            teacher=teacher_b,
            max_xp=100,
            is_published=True,
        )

    def test_director_test_list_excludes_other_org(self):
        self.client.force_authenticate(self.director_a)
        response = self.client.get("/api/tests/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {row["id"] for row in self._rows(response)}
        self.assertNotIn(self.test_b.id, ids)

    def test_director_cannot_retrieve_other_org_test(self):
        self.client.force_authenticate(self.director_a)
        response = self.client.get(f"/api/tests/{self.test_b.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_director_student_list_excludes_other_org(self):
        self.client.force_authenticate(self.director_a)
        response = self.client.get("/api/students/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {row["id"] for row in self._rows(response)}
        self.assertNotIn(self.student_b.id, ids)

    def test_student_leaderboard_excludes_other_org(self):
        self.client.force_authenticate(self.director_a)
        response = self.client.get("/api/leaderboard/students/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {row["name"] for row in self._rows(response)}
        self.assertNotIn("BetaOrg Pupil", names)
