from datetime import date, time, timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.common.testing import (
    default_organization,
    make_director,
    make_lesson,
    make_school_class,
    make_student,
    make_subject,
    make_teacher,
    make_timetable_slot,
)
from apps.school_config.models import SchoolTimeSettings

from .models import Lesson
from .services import generate_lessons_for_week


def _this_weeks_monday() -> date:
    today = timezone.localdate()
    return today - timedelta(days=today.weekday())


class TimetableSlotConstraintTests(TestCase):
    def setUp(self):
        self.subject = make_subject()
        _, self.teacher = make_teacher()
        self.class_a = make_school_class()
        self.class_b = make_school_class()

    def test_double_booking_the_same_class_slot_raises(self):
        make_timetable_slot(
            school_class=self.class_a, subject=self.subject, teacher=self.teacher, period_number=1
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_timetable_slot(
                school_class=self.class_a,
                subject=self.subject,
                teacher=self.teacher,
                period_number=1,
            )

    def test_double_booking_the_same_teacher_slot_raises(self):
        make_timetable_slot(
            school_class=self.class_a, subject=self.subject, teacher=self.teacher, period_number=1
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_timetable_slot(
                school_class=self.class_b,
                subject=self.subject,
                teacher=self.teacher,
                period_number=1,
            )


class GenerateLessonsForWeekTests(TestCase):
    def setUp(self):
        settings_obj = SchoolTimeSettings.get_solo(default_organization())
        settings_obj.start_time = time(8, 0)
        settings_obj.period_duration_minutes = 45
        settings_obj.short_break_minutes = 5
        settings_obj.long_break_after_period = 4
        settings_obj.long_break_minutes = 20
        settings_obj.save()

        self.subject = make_subject()
        _, self.teacher = make_teacher()
        self.school_class = make_school_class()
        # Wednesday (day_of_week=3), period 1.
        self.slot = make_timetable_slot(
            school_class=self.school_class,
            subject=self.subject,
            teacher=self.teacher,
            day_of_week=3,
            period_number=1,
        )

    def test_generates_lesson_on_correct_date_and_time(self):
        monday = _this_weeks_monday()
        lessons = generate_lessons_for_week(monday)

        self.assertEqual(len(lessons), 1)
        lesson = lessons[0]
        self.assertEqual(lesson.date, monday + timedelta(days=2))
        self.assertEqual(lesson.start_time, time(8, 0))
        self.assertEqual(lesson.end_time, time(8, 45))

    def test_running_twice_for_the_same_week_is_idempotent(self):
        monday = _this_weeks_monday()
        generate_lessons_for_week(monday)
        generate_lessons_for_week(monday)
        self.assertEqual(Lesson.objects.count(), 1)

    def test_any_date_in_the_week_normalizes_to_the_same_monday(self):
        monday = _this_weeks_monday()
        wednesday = monday + timedelta(days=2)
        lessons = generate_lessons_for_week(wednesday)
        self.assertEqual(lessons[0].date, wednesday)

    def test_two_classes_on_the_same_day_and_period_dont_collide(self):
        other_class = make_school_class()
        _, other_teacher = make_teacher()
        make_timetable_slot(
            school_class=other_class,
            subject=self.subject,
            teacher=other_teacher,
            day_of_week=3,
            period_number=1,
        )

        lessons = generate_lessons_for_week(_this_weeks_monday())

        self.assertEqual(len(lessons), 2)
        self.assertEqual(Lesson.objects.filter(school_class=self.school_class).count(), 1)
        self.assertEqual(Lesson.objects.filter(school_class=other_class).count(), 1)


class LessonQuerysetScopingAPITests(APITestCase):
    def setUp(self):
        subject = make_subject()
        self.teacher_a_user, self.teacher_a = make_teacher()
        self.teacher_b_user, self.teacher_b = make_teacher()
        self.class_a = make_school_class(class_teacher=self.teacher_a)
        self.class_b = make_school_class()
        self.student_user, _ = make_student(self.class_a)

        self.lesson_a = make_lesson(school_class=self.class_a, subject=subject, teacher=self.teacher_a)
        self.lesson_b = make_lesson(
            school_class=self.class_b,
            subject=subject,
            teacher=self.teacher_b,
            start_time=time(10, 0),
            end_time=time(10, 45),
        )

    def test_director_sees_all_lessons(self):
        self.client.force_authenticate(make_director())
        response = self.client.get("/api/lessons/")
        self.assertEqual(response.data["count"], 2)

    def test_teacher_sees_only_own_or_led_class_lessons(self):
        self.client.force_authenticate(self.teacher_a_user)
        response = self.client.get("/api/lessons/")
        ids = {row["id"] for row in response.data["results"]}
        self.assertEqual(ids, {self.lesson_a.id})

    def test_student_sees_only_their_class_lessons(self):
        self.client.force_authenticate(self.student_user)
        response = self.client.get("/api/lessons/")
        ids = {row["id"] for row in response.data["results"]}
        self.assertEqual(ids, {self.lesson_a.id})


class TimetableSlotAutoTimeTests(APITestCase):
    """The director timetable form posts no times, so the API derives them.

    Two details make this easy to regress:
      * start_time takes part in the unique_teacher_slot constraint, so DRF's
        constraint validator demands it *before* validate() runs — the fill has
        to happen in to_internal_value().
      * the school runs an 08:00 and a 13:00 block with different period
        lengths, so the shift is read off the class's existing slots.
    """

    def setUp(self):
        self.director = make_director()
        self.client.force_authenticate(self.director)
        self.subject = make_subject()
        _, self.teacher = make_teacher()
        self.settings_obj = SchoolTimeSettings.get_solo(default_organization())
        self.settings_obj.start_time = time(8, 0)
        self.settings_obj.end_time = time(17, 50)
        self.settings_obj.period_duration_minutes = 45
        self.settings_obj.short_break_minutes = 5
        self.settings_obj.long_break_after_period = 3
        self.settings_obj.long_break_minutes = 10
        self.settings_obj.second_start_time = time(13, 0)
        self.settings_obj.second_short_period = 4
        self.settings_obj.second_short_period_minutes = 35
        self.settings_obj.save()

    def _post(self, school_class, period, day):
        return self.client.post(
            "/api/timetable-slots/",
            {
                "school_class": school_class.id,
                "day_of_week": day,
                "period_number": period,
                "subject": self.subject.id,
                "teacher": self.teacher.id,
            },
            format="json",
        )

    def test_times_are_derived_for_a_morning_class(self):
        school_class = make_school_class()
        response = self._post(school_class, period=4, day=3)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["start_time"], "10:35:00")
        self.assertEqual(response.data["end_time"], "11:20:00")

    def test_times_are_derived_for_an_afternoon_class(self):
        school_class = make_school_class()
        make_timetable_slot(
            school_class=school_class,
            subject=self.subject,
            teacher=make_teacher()[1],
            day_of_week=1,
            period_number=1,
            start_time=time(13, 0),
            end_time=time(13, 45),
        )
        response = self._post(school_class, period=4, day=3)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["start_time"], "15:35:00")
        self.assertEqual(response.data["end_time"], "16:10:00")

    def test_explicit_times_win_over_derived_ones(self):
        school_class = make_school_class()
        response = self.client.post(
            "/api/timetable-slots/",
            {
                "school_class": school_class.id,
                "day_of_week": 3,
                "period_number": 5,
                "subject": self.subject.id,
                "teacher": self.teacher.id,
                "start_time": "16:15",
                "end_time": "17:00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["start_time"], "16:15:00")

    def test_end_time_before_start_time_is_rejected(self):
        school_class = make_school_class()
        response = self.client.post(
            "/api/timetable-slots/",
            {
                "school_class": school_class.id,
                "day_of_week": 3,
                "period_number": 5,
                "subject": self.subject.id,
                "teacher": self.teacher.id,
                "start_time": "16:00",
                "end_time": "15:00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("end_time", response.data)

    def test_patching_only_the_room_keeps_the_times(self):
        school_class = make_school_class()
        created = self._post(school_class, period=2, day=3)
        self.assertEqual(created.status_code, 201, created.data)
        patched = self.client.patch(
            f"/api/timetable-slots/{created.data['id']}/", {"room": "Xona-9"}, format="json"
        )
        self.assertEqual(patched.status_code, 200, patched.data)
        self.assertEqual(patched.data["start_time"], "08:50:00")
        self.assertEqual(patched.data["end_time"], "09:35:00")
        self.assertEqual(patched.data["room"], "Xona-9")
