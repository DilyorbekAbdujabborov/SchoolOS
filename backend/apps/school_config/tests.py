from datetime import date, time, timedelta
from unittest.mock import patch

# A known Monday — a school day under the default Mon–Sat schedule — so lock tests
# that mock the clock still land on a day the lock is active.
_SCHOOL_DAY = date(2026, 10, 5)

from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.testing import (
    default_organization,
    make_director,
    make_lesson,
    make_school_class,
    make_student,
    make_subject,
    make_teacher,
)

from . import services
from .middleware import SchoolTimeLockMiddleware
from .models import ClassAccessWindow, SchoolDayException, SchoolTimeSettings


class PeriodTimesTests(TestCase):
    def setUp(self):
        self.settings_obj = SchoolTimeSettings.get_solo(default_organization())
        self.settings_obj.start_time = time(8, 0)
        self.settings_obj.period_duration_minutes = 45
        self.settings_obj.short_break_minutes = 5
        self.settings_obj.long_break_after_period = 2
        self.settings_obj.long_break_minutes = 20
        self.settings_obj.save()

    def test_first_period_starts_at_school_start_time(self):
        start, end = self.settings_obj.period_times(1)
        self.assertEqual(start, time(8, 0))
        self.assertEqual(end, time(8, 45))

    def test_period_after_long_break_reflects_break_length(self):
        # period1: 08:00-08:45, then a short break (period 1 != long_break_after_period)
        # period2: 08:50-09:35, then the long break (period 2 == long_break_after_period)
        # period3 starts after the 20-minute long break: 09:55
        start, _end = self.settings_obj.period_times(3)
        self.assertEqual(start, time(9, 55))

    def test_singleton_always_returns_the_same_row(self):
        first = SchoolTimeSettings.get_solo(default_organization())
        second = SchoolTimeSettings.get_solo(default_organization())
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(SchoolTimeSettings.objects.count(), 1)


class SchoolTimeLockMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SchoolTimeLockMiddleware(lambda request: HttpResponse("OK"))
        settings_obj = SchoolTimeSettings.get_solo(default_organization())
        settings_obj.start_time = time(8, 0)
        settings_obj.end_time = time(13, 10)
        settings_obj.save()

    def _authed_request(self, user, path="/api/dashboard/student/"):
        token = str(RefreshToken.for_user(user).access_token)
        return self.factory.get(path, HTTP_AUTHORIZATION=f"Bearer {token}")

    @patch("apps.school_config.middleware.timezone")
    def test_student_locked_out_during_school_hours(self, mock_timezone):
        mock_timezone.localtime.return_value.time.return_value = time(9, 0)
        mock_timezone.localtime.return_value.date.return_value = _SCHOOL_DAY
        student_user, _ = make_student()
        response = self.middleware(self._authed_request(student_user))
        self.assertEqual(response.status_code, 423)

    @patch("apps.school_config.middleware.timezone")
    def test_student_allowed_outside_school_hours(self, mock_timezone):
        mock_timezone.localtime.return_value.time.return_value = time(14, 0)
        mock_timezone.localtime.return_value.date.return_value = _SCHOOL_DAY
        student_user, _ = make_student()
        response = self.middleware(self._authed_request(student_user))
        self.assertEqual(response.status_code, 200)

    @patch("apps.school_config.middleware.timezone")
    def test_student_not_locked_on_a_day_off(self, mock_timezone):
        # 2026-10-04 is a Sunday; default school days are Mon–Sat, so even during
        # school hours the lock must not apply.
        from datetime import date

        mock_now = mock_timezone.localtime.return_value
        mock_now.time.return_value = time(9, 0)
        mock_now.date.return_value = date(2026, 10, 4)
        student_user, _ = make_student()
        response = self.middleware(self._authed_request(student_user))
        self.assertEqual(response.status_code, 200)

    @patch("apps.school_config.middleware.timezone")
    def test_student_locked_on_a_school_day(self, mock_timezone):
        from datetime import date

        mock_now = mock_timezone.localtime.return_value
        mock_now.time.return_value = time(9, 0)
        mock_now.date.return_value = date(2026, 10, 5)  # Monday
        student_user, _ = make_student()
        response = self.middleware(self._authed_request(student_user))
        self.assertEqual(response.status_code, 423)

    @patch("apps.school_config.middleware.timezone")
    def test_director_never_blocked(self, mock_timezone):
        mock_timezone.localtime.return_value.time.return_value = time(9, 0)
        director = make_director()
        response = self.middleware(self._authed_request(director))
        self.assertEqual(response.status_code, 200)

    @patch("apps.school_config.middleware.timezone")
    def test_teacher_never_blocked(self, mock_timezone):
        mock_timezone.localtime.return_value.time.return_value = time(9, 0)
        teacher_user, _ = make_teacher()
        response = self.middleware(self._authed_request(teacher_user))
        self.assertEqual(response.status_code, 200)

    def test_login_endpoint_is_always_exempt(self):
        request = self.factory.post("/api/auth/login/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    @patch("apps.school_config.middleware.timezone")
    def test_me_endpoint_is_exempt_during_school_hours(self, mock_timezone):
        """The frontend resolves the signed-in user on load, so a 423 here left
        the app unable to render anything — not even the locked-out notice."""
        mock_timezone.localtime.return_value.time.return_value = time(9, 0)
        student_user, _ = make_student()
        response = self.middleware(self._authed_request(student_user, path="/api/auth/me/"))
        self.assertEqual(response.status_code, 200)

    @patch("apps.school_config.middleware.timezone")
    def test_change_password_is_exempt_during_school_hours(self, mock_timezone):
        """Bulk-issued students must be able to replace their temporary password
        during the lock, otherwise they can never log in again."""
        mock_timezone.localtime.return_value.time.return_value = time(9, 0)
        student_user, _ = make_student()
        request = self.factory.post(
            "/api/auth/change-password/",
            data="{}",
            content_type="application/json",
            HTTP_AUTHORIZATION=(
                f"Bearer {RefreshToken.for_user(student_user).access_token}"
            ),
        )
        self.assertEqual(self.middleware(request).status_code, 200)

    @patch("apps.school_config.middleware.timezone")
    def test_learning_endpoints_stay_locked_for_students(self, mock_timezone):
        """Guards the other direction: exempting /api/auth/ must not have widened
        the exemption to the rest of the API."""
        mock_timezone.localtime.return_value.time.return_value = time(9, 0)
        mock_timezone.localtime.return_value.date.return_value = _SCHOOL_DAY
        student_user, _ = make_student()
        response = self.middleware(self._authed_request(student_user))
        self.assertEqual(response.status_code, 423)


class ClassAccessWindowTests(TestCase):
    """A teacher opening the platform for their classes during a lesson lifts the
    time lock for those classes until the window expires."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SchoolTimeLockMiddleware(lambda request: HttpResponse("OK"))
        self.settings_obj = SchoolTimeSettings.get_solo(default_organization())
        self.settings_obj.start_time = time(8, 0)
        self.settings_obj.end_time = time(13, 10)
        self.settings_obj.save()

        self.teacher_user, self.teacher = make_teacher()
        self.school_class = make_school_class(class_teacher=self.teacher)
        self.student_user, _ = make_student(school_class=self.school_class)

    def _student_request(self):
        token = str(RefreshToken.for_user(self.student_user).access_token)
        return self.factory.get("/api/dashboard/student/", HTTP_AUTHORIZATION=f"Bearer {token}")

    @patch("apps.school_config.middleware.timezone")
    def test_open_window_lets_the_class_through_during_lock(self, mock_timezone):
        mock_timezone.localtime.return_value.time.return_value = time(9, 0)
        mock_timezone.localtime.return_value.date.return_value = _SCHOOL_DAY
        ClassAccessWindow.objects.create(
            school_class=self.school_class,
            opened_by=self.teacher_user,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.assertEqual(self.middleware(self._student_request()).status_code, 200)

    @patch("apps.school_config.middleware.timezone")
    def test_expired_window_keeps_the_class_locked(self, mock_timezone):
        mock_timezone.localtime.return_value.time.return_value = time(9, 0)
        mock_timezone.localtime.return_value.date.return_value = _SCHOOL_DAY
        ClassAccessWindow.objects.create(
            school_class=self.school_class,
            opened_by=self.teacher_user,
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        self.assertEqual(self.middleware(self._student_request()).status_code, 423)

    @patch("apps.school_config.middleware.timezone")
    def test_other_class_window_does_not_unlock_this_student(self, mock_timezone):
        mock_timezone.localtime.return_value.time.return_value = time(9, 0)
        mock_timezone.localtime.return_value.date.return_value = _SCHOOL_DAY
        other_class = make_school_class()
        ClassAccessWindow.objects.create(
            school_class=other_class,
            opened_by=self.teacher_user,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.assertEqual(self.middleware(self._student_request()).status_code, 423)

    def test_open_anchors_expiry_to_the_current_lesson_end(self):
        subject = make_subject()
        make_lesson(school_class=self.school_class, subject=subject, teacher=self.teacher)
        # make_lesson defaults to 2026-09-21, 09:00–09:45; pretend "now" is 09:10.
        now = timezone.localtime().replace(
            year=2026, month=9, day=21, hour=9, minute=10, second=0, microsecond=0
        )
        with patch("apps.school_config.services.timezone") as mock_tz:
            mock_tz.localtime.return_value = now
            mock_tz.now.return_value = now
            windows = services.open_access(self.teacher_user)

        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0].school_class, self.school_class)
        self.assertEqual(timezone.localtime(windows[0].expires_at).time(), time(9, 45))

    def test_close_removes_the_teacher_windows(self):
        ClassAccessWindow.objects.create(
            school_class=self.school_class,
            opened_by=self.teacher_user,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        removed = services.close_access(self.teacher_user)
        self.assertEqual(removed, 1)
        self.assertFalse(ClassAccessWindow.objects.filter(school_class=self.school_class).exists())

    def test_status_reports_open_state(self):
        ClassAccessWindow.objects.create(
            school_class=self.school_class,
            opened_by=self.teacher_user,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        status = services.access_status(self.teacher_user)
        self.assertTrue(status["open"])
        self.assertIsNotNone(status["expires_at"])
        self.assertEqual(status["classes"][0]["id"], self.school_class.id)

    def test_director_opens_every_class_in_the_school(self):
        other_class = make_school_class()  # not taught by self.teacher
        director = make_director()
        windows = services.open_access(director)
        opened_ids = {w.school_class_id for w in windows}
        self.assertIn(self.school_class.id, opened_ids)
        self.assertIn(other_class.id, opened_ids)

    def test_student_cannot_open_access(self):
        client = APIClient()
        client.force_authenticate(user=self.student_user)
        self.assertEqual(client.post(reverse("class-access")).status_code, 403)

    def test_teacher_can_reach_the_endpoint(self):
        client = APIClient()
        client.force_authenticate(user=self.teacher_user)
        self.assertEqual(client.get(reverse("class-access")).status_code, 200)


class SecondShiftTests(TestCase):
    """The school runs an 08:00 and a 13:00 block, and they are not copies of
    each other: the second block's period 4 is 35 minutes, not 45."""

    def setUp(self):
        self.settings_obj = SchoolTimeSettings.get_solo(default_organization())
        self.settings_obj.start_time = time(8, 0)
        self.settings_obj.period_duration_minutes = 45
        self.settings_obj.short_break_minutes = 5
        self.settings_obj.long_break_after_period = 3
        self.settings_obj.long_break_minutes = 10
        self.settings_obj.second_start_time = time(13, 0)
        self.settings_obj.second_short_period = 4
        self.settings_obj.second_short_period_minutes = 35
        self.settings_obj.save()

    def test_first_shift_matches_the_official_timetable(self):
        expected = [
            (time(8, 0), time(8, 45)),
            (time(8, 50), time(9, 35)),
            (time(9, 40), time(10, 25)),
            (time(10, 35), time(11, 20)),
            (time(11, 25), time(12, 10)),
            (time(12, 15), time(13, 0)),
        ]
        for period, (start, end) in enumerate(expected, start=1):
            self.assertEqual(self.settings_obj.period_times(period, shift=1), (start, end))

    def test_second_shift_matches_the_official_timetable(self):
        expected = [
            (time(13, 0), time(13, 45)),
            (time(13, 50), time(14, 35)),
            (time(14, 40), time(15, 25)),
            (time(15, 35), time(16, 10)),
            (time(16, 15), time(17, 0)),
            (time(17, 5), time(17, 50)),
        ]
        for period, (start, end) in enumerate(expected, start=1):
            self.assertEqual(self.settings_obj.period_times(period, shift=2), (start, end))

    def test_second_shift_period_four_is_thirty_five_minutes(self):
        start, end = self.settings_obj.period_times(4, shift=2)
        self.assertEqual(start, time(15, 35))
        self.assertEqual(end, time(16, 10))
        self.assertNotEqual(
            self.settings_obj.period_duration(4, shift=2),
            self.settings_obj.period_duration(4, shift=1),
        )

    def test_shift_start_falls_back_to_the_first_shift(self):
        self.settings_obj.second_start_time = None
        self.settings_obj.save()
        self.assertEqual(self.settings_obj.shift_start(2), time(8, 0))
        self.assertEqual(self.settings_obj.period_times(4, shift=2), (time(10, 35), time(11, 20)))


class SchoolDayExceptionTests(TestCase):
    """Calendar overrides of the weekly schedule, in both directions."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SchoolTimeLockMiddleware(lambda request: HttpResponse("OK"))
        self.org = default_organization()
        settings_obj = SchoolTimeSettings.get_solo(self.org)
        settings_obj.start_time = time(8, 0)
        settings_obj.end_time = time(13, 10)
        settings_obj.save()
        # A Monday (school day) and a Sunday (day off) to anchor the two directions.
        self.school_day = date(2026, 10, 5)
        self.day_off = date(2026, 10, 4)

    def _authed_request(self, user, path="/api/dashboard/student/"):
        token = str(RefreshToken.for_user(user).access_token)
        return self.factory.get(path, HTTP_AUTHORIZATION=f"Bearer {token}")

    @patch("apps.school_config.middleware.timezone")
    def test_holiday_unlocks_a_normal_school_day(self, mock_timezone):
        SchoolDayException.objects.create(
            organization=self.org, start_date=self.school_day, kind=SchoolDayException.Kind.OFF
        )
        mock_timezone.localtime.return_value.time.return_value = time(9, 0)
        mock_timezone.localtime.return_value.date.return_value = self.school_day
        student_user, _ = make_student()
        response = self.middleware(self._authed_request(student_user))
        self.assertEqual(response.status_code, 200)

    @patch("apps.school_config.middleware.timezone")
    def test_makeup_day_locks_a_normal_day_off(self, mock_timezone):
        SchoolDayException.objects.create(
            organization=self.org, start_date=self.day_off, kind=SchoolDayException.Kind.SCHOOL
        )
        mock_timezone.localtime.return_value.time.return_value = time(9, 0)
        mock_timezone.localtime.return_value.date.return_value = self.day_off
        student_user, _ = make_student()
        response = self.middleware(self._authed_request(student_user))
        self.assertEqual(response.status_code, 423)

    @patch("apps.school_config.middleware.timezone")
    def test_vacation_range_unlocks_every_day_inside_it(self, mock_timezone):
        SchoolDayException.objects.create(
            organization=self.org,
            start_date=date(2026, 10, 5),
            end_date=date(2026, 10, 9),
            kind=SchoolDayException.Kind.OFF,
        )
        mock_timezone.localtime.return_value.time.return_value = time(9, 0)
        mock_timezone.localtime.return_value.date.return_value = date(2026, 10, 7)  # inside
        student_user, _ = make_student()
        response = self.middleware(self._authed_request(student_user))
        self.assertEqual(response.status_code, 200)

    def test_single_day_exception_does_not_leak_past_its_date(self):
        SchoolDayException.objects.create(
            organization=self.org, start_date=self.school_day, kind=SchoolDayException.Kind.OFF
        )
        self.assertIsNone(services._exception_kind(self.org.id, date(2026, 10, 6)))

    def test_is_lock_day_falls_back_to_weekly_pattern_without_exceptions(self):
        settings_obj = SchoolTimeSettings.get_solo(self.org)
        self.assertTrue(services.is_lock_day(settings_obj, self.school_day))
        self.assertFalse(services.is_lock_day(settings_obj, self.day_off))

    def test_exceptions_are_scoped_to_the_organization(self):
        settings_obj = SchoolTimeSettings.get_solo(self.org)
        # An exception for a different org must not affect this one.
        from apps.organizations.models import Organization

        other = Organization.objects.create(name="Other", slug="other-org")
        SchoolDayException.objects.create(
            organization=other, start_date=self.school_day, kind=SchoolDayException.Kind.OFF
        )
        self.assertTrue(services.is_lock_day(settings_obj, self.school_day))
