from rest_framework import status
from rest_framework.test import APITestCase

from apps.common.testing import make_director, make_teacher
from apps.notifications.models import Notification

from .models import TeacherTask, TeacherTaskAssignment


class TeacherTaskAPITests(APITestCase):
    def setUp(self):
        self.director = make_director()
        self.teacher_user, self.teacher = make_teacher()
        self.other_teacher_user, self.other_teacher = make_teacher()

    def test_director_can_assign_a_task_to_one_teacher(self):
        self.client.force_authenticate(self.director)
        response = self.client.post(
            "/api/teacher-tasks/",
            {"title": "Hisobot topshiring", "description": "Choraklik hisobot", "category": "REPORT", "teacher": self.teacher.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        task = TeacherTask.objects.get()
        self.assertFalse(task.is_broadcast)
        self.assertEqual(task.assignments.count(), 1)
        self.assertEqual(task.assignments.get().teacher, self.teacher)
        self.assertTrue(Notification.objects.filter(recipient=self.teacher_user, category=Notification.Category.TASK_ASSIGNED).exists())
        self.assertFalse(Notification.objects.filter(recipient=self.other_teacher_user).exists())

    def test_director_can_broadcast_a_task_to_every_teacher(self):
        self.client.force_authenticate(self.director)
        response = self.client.post(
            "/api/teacher-tasks/",
            {"title": "Yig'ilish", "category": "MEETING", "send_to_all": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        task = TeacherTask.objects.get()
        self.assertTrue(task.is_broadcast)
        self.assertEqual(task.assignments.count(), 2)
        self.assertTrue(Notification.objects.filter(recipient=self.teacher_user).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.other_teacher_user).exists())

    def test_must_choose_a_teacher_or_send_to_all(self):
        self.client.force_authenticate(self.director)
        response = self.client.post("/api/teacher-tasks/", {"title": "Vazifa"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_choose_both_a_teacher_and_send_to_all(self):
        self.client.force_authenticate(self.director)
        response = self.client.post(
            "/api/teacher-tasks/",
            {"title": "Vazifa", "teacher": self.teacher.id, "send_to_all": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_teacher_cannot_create_a_task(self):
        self.client.force_authenticate(self.teacher_user)
        response = self.client.post(
            "/api/teacher-tasks/", {"title": "Vazifa", "teacher": self.teacher.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_only_sees_their_own_assignments(self):
        self.client.force_authenticate(self.director)
        self.client.post(
            "/api/teacher-tasks/", {"title": "Faqat menga", "teacher": self.teacher.id}, format="json"
        )
        self.client.post(
            "/api/teacher-tasks/", {"title": "Faqat boshqasiga", "teacher": self.other_teacher.id}, format="json"
        )

        self.client.force_authenticate(self.teacher_user)
        response = self.client.get("/api/my-tasks/")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Faqat menga")

    def test_teacher_can_mark_their_assignment_done(self):
        self.client.force_authenticate(self.director)
        self.client.post(
            "/api/teacher-tasks/", {"title": "Vazifa", "teacher": self.teacher.id}, format="json"
        )
        assignment = TeacherTaskAssignment.objects.get(teacher=self.teacher)

        self.client.force_authenticate(self.teacher_user)
        response = self.client.patch(f"/api/my-tasks/{assignment.id}/mark-done/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assignment.refresh_from_db()
        self.assertTrue(assignment.is_done)
        self.assertIsNotNone(assignment.completed_at)

    def test_teacher_cannot_mark_another_teachers_assignment_done(self):
        self.client.force_authenticate(self.director)
        self.client.post(
            "/api/teacher-tasks/", {"title": "Vazifa", "teacher": self.teacher.id}, format="json"
        )
        assignment = TeacherTaskAssignment.objects.get(teacher=self.teacher)

        self.client.force_authenticate(self.other_teacher_user)
        response = self.client.patch(f"/api/my-tasks/{assignment.id}/mark-done/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
