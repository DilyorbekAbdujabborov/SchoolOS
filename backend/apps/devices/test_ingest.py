from datetime import datetime, time

from django.test import TestCase
from django.utils import timezone

from apps.common.testing import default_organization, make_organization, make_student
from apps.notifications.models import Notification
from apps.school_config.models import SchoolTimeSettings

from .models import AccessEvent, Bridge, DailyAttendance, Device
from .services import ingest_events


def _aware(h, m):
    return timezone.make_aware(datetime(2026, 10, 9, h, m))


class IngestEventsTests(TestCase):
    def setUp(self):
        self.org = default_organization()
        self.bridge = Bridge.objects.create(organization=self.org, name="b")
        self.device = Device.objects.create(
            bridge=self.bridge, serial="DEV-1", direction=Device.Direction.BOTH
        )
        self.user, self.student = make_student()

    def _item(self, osid=None, h=8, m=3, direction="IN"):
        return {
            "device_serial": "DEV-1",
            "osid": osid or self.user.osid,
            "event_time": _aware(h, m).isoformat(),
            "direction": direction,
            "verify_mode": "face",
            "raw": {"src": "test"},
        }

    def test_in_event_creates_access_event_and_daily_attendance_present(self):
        SchoolTimeSettings.objects.create(organization=self.org, start_time=time(8, 0))
        result = ingest_events(self.bridge, [self._item(h=8, m=3)])

        self.assertEqual(len(result["accepted"]), 1)
        self.assertEqual(AccessEvent.objects.count(), 1)
        da = DailyAttendance.objects.get(student=self.student)
        self.assertEqual(da.status, DailyAttendance.Status.PRESENT)
        self.assertIsNotNone(da.first_in_at)

    def test_late_when_first_in_after_grace(self):
        SchoolTimeSettings.objects.create(organization=self.org, start_time=time(8, 0))
        ingest_events(self.bridge, [self._item(h=8, m=30)])
        da = DailyAttendance.objects.get(student=self.student)
        self.assertEqual(da.status, DailyAttendance.Status.LATE)

    def test_missing_school_time_settings_defaults_present(self):
        SchoolTimeSettings.objects.filter(organization=self.org).delete()
        ingest_events(self.bridge, [self._item(h=9, m=0)])
        da = DailyAttendance.objects.get(student=self.student)
        self.assertEqual(da.status, DailyAttendance.Status.PRESENT)

    def test_out_event_sets_last_out(self):
        ingest_events(self.bridge, [self._item(h=8, m=0, direction="IN")])
        ingest_events(self.bridge, [self._item(h=13, m=0, direction="OUT")])
        da = DailyAttendance.objects.get(student=self.student)
        self.assertIsNotNone(da.last_out_at)

    def test_duplicate_dedup_key_ingested_once(self):
        item = self._item(h=8, m=3)
        ingest_events(self.bridge, [item])
        result = ingest_events(self.bridge, [item])
        self.assertEqual(AccessEvent.objects.count(), 1)
        self.assertEqual(len(result["duplicate"]), 1)

    def test_unknown_osid_stored_with_user_none(self):
        result = ingest_events(self.bridge, [self._item(osid="9999999999")])
        self.assertEqual(len(result["unmatched"]), 1)
        event = AccessEvent.objects.get()
        self.assertIsNone(event.user)
        self.assertEqual(event.raw_osid, "9999999999")

    def test_cross_org_osid_not_matched(self):
        other_user, _ = make_student(organization=make_organization("Other School"))
        result = ingest_events(self.bridge, [self._item(osid=other_user.osid)])
        self.assertEqual(len(result["unmatched"]), 1)
        self.assertIsNone(AccessEvent.objects.get().user)

    def test_in_event_notifies_student(self):
        before = Notification.objects.filter(recipient=self.user).count()
        ingest_events(self.bridge, [self._item(h=8, m=3)])
        after = Notification.objects.filter(recipient=self.user).count()
        self.assertEqual(after, before + 1)


class SecondShiftTests(TestCase):
    def setUp(self):
        self.org = default_organization()
        self.bridge = Bridge.objects.create(organization=self.org, name="b")
        Device.objects.create(bridge=self.bridge, serial="DEV-1")
        self.user, self.student = make_student()
        SchoolTimeSettings.objects.create(
            organization=self.org, start_time=time(8, 0), second_start_time=time(13, 0)
        )

    def _ingest(self, h, m):
        ingest_events(
            self.bridge,
            [{"device_serial": "DEV-1", "osid": self.user.osid,
              "event_time": _aware(h, m).isoformat(), "direction": "IN"}],
        )
        return DailyAttendance.objects.get(student=self.student).status

    def test_second_shift_arrival_before_its_start_is_present(self):
        self.assertEqual(self._ingest(12, 55), DailyAttendance.Status.PRESENT)

    def test_second_shift_arrival_after_grace_is_late(self):
        self.assertEqual(self._ingest(13, 30), DailyAttendance.Status.LATE)

    def test_first_shift_late_still_late(self):
        self.assertEqual(self._ingest(8, 30), DailyAttendance.Status.LATE)


class IngestRobustnessTests(TestCase):
    def setUp(self):
        self.org = default_organization()
        self.bridge = Bridge.objects.create(organization=self.org, name="b")
        self.device = Device.objects.create(bridge=self.bridge, serial="DEV-1")
        self.user, self.student = make_student()

    def _item(self, event_time, direction="IN"):
        return {"device_serial": "DEV-1", "osid": self.user.osid,
                "event_time": event_time, "direction": direction}

    def test_same_instant_different_offsets_dedup(self):
        ingest_events(self.bridge, [self._item("2026-10-09T03:03:00+00:00")])
        result = ingest_events(self.bridge, [self._item("2026-10-09T08:03:00+05:00")])
        self.assertEqual(AccessEvent.objects.count(), 1)
        self.assertEqual(len(result["duplicate"]), 1)

    def test_naive_time_treated_as_local(self):
        ingest_events(self.bridge, [self._item("2026-10-09T08:03:00")])
        event = AccessEvent.objects.get()
        self.assertTrue(timezone.is_aware(event.event_time))
        self.assertEqual(timezone.localtime(event.event_time).hour, 8)

    def test_concurrent_duplicate_insert_reported_not_raised(self):
        # Simulates a racing request that inserted the same event between our
        # exists() check and create(): the unique dedup_key must not 500.
        from unittest import mock

        item = self._item(_aware(8, 3).isoformat())
        ingest_events(self.bridge, [item])
        with mock.patch("apps.devices.services._is_duplicate", return_value=False):
            result = ingest_events(self.bridge, [item])
        self.assertEqual(len(result["duplicate"]), 1)
        self.assertEqual(AccessEvent.objects.count(), 1)

    def test_notify_failure_rolls_back_item_so_retry_reprocesses(self):
        from unittest import mock

        item = self._item(_aware(8, 3).isoformat())
        with mock.patch("apps.devices.services.notify", side_effect=RuntimeError("db blip")):
            result = ingest_events(self.bridge, [item])
        self.assertEqual(len(result["failed"]), 1)
        self.assertEqual(AccessEvent.objects.count(), 0)

        before = Notification.objects.filter(recipient=self.user).count()
        result = ingest_events(self.bridge, [item])
        self.assertEqual(len(result["accepted"]), 1)
        self.assertEqual(Notification.objects.filter(recipient=self.user).count(), before + 1)

    def test_lone_out_marks_present(self):
        ingest_events(self.bridge, [self._item(_aware(13, 0).isoformat(), direction="OUT")])
        da = DailyAttendance.objects.get(student=self.student)
        self.assertEqual(da.status, DailyAttendance.Status.PRESENT)
