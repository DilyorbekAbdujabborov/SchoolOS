from datetime import time
from unittest.mock import patch

from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.testing import default_organization, make_director, make_student, make_teacher

from .middleware import SchoolTimeLockMiddleware
from .models import SchoolTimeSettings


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
        student_user, _ = make_student()
        response = self.middleware(self._authed_request(student_user))
        self.assertEqual(response.status_code, 423)

    @patch("apps.school_config.middleware.timezone")
    def test_student_allowed_outside_school_hours(self, mock_timezone):
        mock_timezone.localtime.return_value.time.return_value = time(14, 0)
        student_user, _ = make_student()
        response = self.middleware(self._authed_request(student_user))
        self.assertEqual(response.status_code, 200)

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
        student_user, _ = make_student()
        response = self.middleware(self._authed_request(student_user))
        self.assertEqual(response.status_code, 423)


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
