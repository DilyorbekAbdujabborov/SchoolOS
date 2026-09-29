from rest_framework.test import APITestCase

from apps.common.testing import (
    make_director,
    make_lesson,
    make_school_class,
    make_subject,
    make_teacher,
)


class SchoolClassAPITests(APITestCase):
    def test_total_xp_is_exposed_and_read_only(self):
        school_class = make_school_class()
        school_class.total_xp = 75
        school_class.save()

        self.client.force_authenticate(make_director())
        response = self.client.get(f"/api/classes/{school_class.id}/")
        self.assertEqual(response.data["total_xp"], 75)

        self.client.patch(f"/api/classes/{school_class.id}/", {"total_xp": 999}, format="json")
        school_class.refresh_from_db()
        self.assertEqual(school_class.total_xp, 75)

    def test_is_my_homeroom_true_only_for_the_leading_teacher(self):
        teacher_user, teacher = make_teacher()
        other_teacher_user, other_teacher = make_teacher()
        school_class = make_school_class(class_teacher=teacher)
        # Just teaching a lesson in the class (not leading it) is what makes it visible
        # to `other_teacher` at all — and is exactly the case `is_my_homeroom` must reject.
        make_lesson(school_class=school_class, subject=make_subject(), teacher=other_teacher)

        self.client.force_authenticate(teacher_user)
        response = self.client.get(f"/api/classes/{school_class.id}/")
        self.assertTrue(response.data["is_my_homeroom"])

        self.client.force_authenticate(other_teacher_user)
        response = self.client.get(f"/api/classes/{school_class.id}/")
        self.assertFalse(response.data["is_my_homeroom"])
