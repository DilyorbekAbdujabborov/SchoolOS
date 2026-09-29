from rest_framework import status
from rest_framework.test import APITestCase

from apps.common.testing import (
    make_director,
    make_school_class,
    make_student,
    make_subject,
    make_teacher,
)
from apps.gamification.models import XPTransaction
from apps.gamification.services import award_xp
from apps.learning.models import Activity, Test
from apps.schools.models import SchoolClass


class DirectorDashboardTests(APITestCase):
    def setUp(self):
        self.subject = make_subject()
        _, self.teacher = make_teacher()
        self.school_class = make_school_class()
        _, self.student = make_student(self.school_class)

    def test_reports_test_activity_and_xp_totals(self):
        Test.objects.create(
            title="T1", subject=self.subject, school_class=self.school_class, teacher=self.teacher
        )
        Activity.objects.create(
            title="A1", subject=self.subject, school_class=self.school_class, teacher=self.teacher,
            activity_type=Activity.ActivityType.ASSIGNMENT,
        )
        award_xp(
            student=self.student, amount=30, source=XPTransaction.Source.TEST,
            related_object=None, reason="x",
        )

        self.client.force_authenticate(make_director())
        response = self.client.get("/api/dashboard/director/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_tests"], 1)
        self.assertEqual(response.data["total_activities"], 1)
        self.assertEqual(response.data["total_xp_awarded"], 30)
        self.assertEqual(response.data["top_class"]["name"], self.school_class.name)
        self.assertEqual(response.data["top_class"]["total_xp"], 30)

    def test_reports_null_top_class_when_no_classes_exist(self):
        SchoolClass.objects.all().delete()

        self.client.force_authenticate(make_director())
        response = self.client.get("/api/dashboard/director/")

        self.assertIsNone(response.data["top_class"])

    def test_teacher_cannot_access_director_dashboard(self):
        teacher_user, _profile = make_teacher()
        self.client.force_authenticate(teacher_user)
        response = self.client.get("/api/dashboard/director/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ClassReportTests(APITestCase):
    """The teacher/director class progress report and its anonymized AI summary."""

    def setUp(self):
        from django.core.cache import cache

        from apps.attendance.models import Attendance
        from apps.common.testing import make_lesson
        from apps.learning.models import TestAttempt

        cache.clear()
        self.teacher_user, self.teacher = make_teacher()
        self.school_class = make_school_class(class_teacher=self.teacher)
        self.subject = make_subject("Matematika")
        _, self.strong = make_student(self.school_class, first_name="Ali", last_name="Valiyev")
        _, self.weak = make_student(self.school_class, first_name="Bobur", last_name="Karimov")

        from django.utils import timezone

        now = timezone.now()
        for index, (student, score) in enumerate([(self.strong, 92.0), (self.weak, 38.0)]):
            test = Test.objects.create(
                title=f"T{index}", subject=self.subject, school_class=self.school_class, teacher=self.teacher
            )
            TestAttempt.objects.create(
                test=test, student=student, status=TestAttempt.Status.SUBMITTED, submitted_at=now, score_percent=score
            )

        lesson = make_lesson(
            school_class=self.school_class, subject=self.subject, teacher=self.teacher, lesson_date=timezone.localdate()
        )
        Attendance.objects.create(lesson=lesson, student=self.strong, status=Attendance.Status.PRESENT)
        Attendance.objects.create(lesson=lesson, student=self.weak, status=Attendance.Status.ABSENT)

    def _report(self, user):
        self.client.force_authenticate(user)
        return self.client.get(f"/api/reports/classes/{self.school_class.id}/")

    def test_class_teacher_sees_per_student_stats_and_status(self):
        response = self._report(self.teacher_user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rows = {row["full_name"]: row for row in response.data["students"]}
        self.assertEqual(rows["Ali Valiyev"]["status"], "GOOD")
        self.assertEqual(rows["Ali Valiyev"]["attendance_rate"], 100)
        self.assertEqual(rows["Bobur Karimov"]["status"], "RISK")
        self.assertEqual(rows["Bobur Karimov"]["weak_subjects"], [{"subject": "Matematika", "avg": 38.0, "results": 1}])
        self.assertEqual(response.data["summary"]["test_avg"], 65.0)
        self.assertEqual(response.data["summary"]["at_risk"], 1)

    def test_director_sees_any_class(self):
        self.assertEqual(self._report(make_director()).status_code, status.HTTP_200_OK)

    def test_unrelated_teacher_and_students_cannot_see_it(self):
        other_teacher, _ = make_teacher()
        student_user, _ = make_student(self.school_class)
        self.assertEqual(self._report(other_teacher).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self._report(student_user).status_code, status.HTTP_403_FORBIDDEN)

    def test_ai_summary_never_sends_names_and_restores_them(self):
        from unittest.mock import patch

        self.client.force_authenticate(self.teacher_user)
        with patch("apps.dashboard.reports.call_gemini", return_value="E'tibor: S2 testdan past ball oldi.") as ai:
            response = self.client.post(f"/api/reports/classes/{self.school_class.id}/ai-summary/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prompt = ai.call_args.kwargs["prompt"]
        self.assertNotIn("Bobur", prompt)
        self.assertNotIn("Valiyev", prompt)
        self.assertIn("S2:", prompt)
        self.assertEqual(response.data["summary"], "E'tibor: Bobur Karimov testdan past ball oldi.")

    def test_ai_summary_is_cached_until_refreshed(self):
        from unittest.mock import patch

        self.client.force_authenticate(self.teacher_user)
        url = f"/api/reports/classes/{self.school_class.id}/ai-summary/"
        with patch("apps.dashboard.reports.call_gemini", return_value="Xulosa") as ai:
            self.client.post(url)
            self.client.post(url)
            self.assertEqual(ai.call_count, 1)
            self.client.post(url, {"refresh": True}, format="json")
            self.assertEqual(ai.call_count, 2)

    def test_ai_unavailable_returns_503(self):
        from unittest.mock import patch

        self.client.force_authenticate(self.teacher_user)
        with patch("apps.dashboard.reports.call_gemini", return_value=None):
            response = self.client.post(f"/api/reports/classes/{self.school_class.id}/ai-summary/")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
