"""Turning normalized terminal events into attendance.

The cloud ingest is vendor-neutral: it receives already-normalized items from a
bridge (osid, time, direction) and never speaks any device protocol. It
deduplicates, resolves the osid to a `User` *within the bridge's organization*
(so one school's terminal can never touch another school's people), stores the
`AccessEvent`, and — for students — updates the day's `DailyAttendance` and
notifies them.
"""

import logging
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext_lazy as _

from apps.notifications.models import Notification
from apps.notifications.services import notify
from apps.organizations.models import OrganizationMembership
from apps.school_config.models import SchoolTimeSettings
from apps.users.models import User

from .models import AccessEvent, DailyAttendance, Device

logger = logging.getLogger(__name__)

#: How long after school start a check-in still counts as on-time.
GRACE = timedelta(minutes=5)


def _resolve_user(organization, osid: str):
    return (
        User.objects.filter(
            osid=osid,
            organization_memberships__organization=organization,
            organization_memberships__status=OrganizationMembership.Status.ACTIVE,
        )
        .distinct()
        .first()
    )


def _status_for(organization, first_in_at) -> str:
    if first_in_at is None:
        return DailyAttendance.Status.ABSENT
    settings = SchoolTimeSettings.objects.filter(organization=organization).first()
    if settings is None:
        return DailyAttendance.Status.PRESENT
    local = timezone.localtime(first_in_at)
    start = settings.start_time
    second = settings.second_start_time
    if second is not None and second > start:
        # Classes don't record their shift, so pick it from the arrival time:
        # anything past the midpoint between the two starts belongs to shift 2.
        day = local.date()
        midpoint = datetime.combine(day, start) + (
            datetime.combine(day, second) - datetime.combine(day, start)
        ) / 2
        if local.replace(tzinfo=None) >= midpoint:
            start = settings.shift_start(2)
    threshold = (datetime.combine(local.date(), start) + GRACE).time()
    if local.time() <= threshold:
        return DailyAttendance.Status.PRESENT
    return DailyAttendance.Status.LATE


def _apply_daily_attendance(organization, student, event_time, direction) -> None:
    date = timezone.localtime(event_time).date()
    record, _created = DailyAttendance.objects.get_or_create(
        organization=organization, student=student, date=date
    )
    if direction == AccessEvent.Direction.IN and record.first_in_at is None:
        record.first_in_at = event_time
    elif direction == AccessEvent.Direction.OUT:
        record.last_out_at = event_time
    if record.first_in_at is None and record.last_out_at is not None:
        # The entry wasn't recognized but the exit was — they were on site.
        record.status = DailyAttendance.Status.PRESENT
    else:
        record.status = _status_for(organization, record.first_in_at)
    record.save()


def _notify(user, direction, event_time) -> None:
    when = timezone.localtime(event_time).strftime("%H:%M")
    if direction == AccessEvent.Direction.IN:
        title, body = _("Maktabga kirdi"), _("Kirish vaqti: %(t)s") % {"t": when}
    else:
        title, body = _("Maktabdan chiqdi"), _("Chiqish vaqti: %(t)s") % {"t": when}
    notify(recipient=user, title=title, body=str(body), category=Notification.Category.ATTENDANCE)


def _normalize_time(raw_time) -> datetime:
    """Aware datetime for any accepted input. A naive value is the school's local
    time (TIME_ZONE); offsets are kept so the instant is exact."""
    event_time = raw_time if isinstance(raw_time, datetime) else parse_datetime(raw_time)
    if timezone.is_naive(event_time):
        event_time = timezone.make_aware(event_time)
    return event_time


def _dedup_key(device, event_time, osid) -> str:
    # Keyed on the UTC instant, so the same moment written with different
    # offsets ("...03:03Z" vs "...08:03+05:00") is one event.
    instant = event_time.astimezone(dt_timezone.utc).isoformat()
    return f"{device.id}:{instant}:{osid}"


def _is_duplicate(dedup_key) -> bool:
    return AccessEvent.objects.filter(dedup_key=dedup_key).exists()


def ingest_events(bridge, items: list[dict]) -> dict:
    """Ingest a batch of normalized events from `bridge`.

    Returns `{"accepted", "duplicate", "unmatched", "failed"}` lists keyed by
    dedup_key: accepted = osid resolved to a user in this org; unmatched = unknown
    device/osid or an osid from another org (event still stored, `user=None`);
    duplicate = already seen (including a concurrent request that won the race);
    failed = this item hit an error and was rolled back whole, so the bridge's
    retry processes it again instead of finding a half-applied duplicate.
    """
    organization = bridge.organization
    result = {"accepted": [], "duplicate": [], "unmatched": [], "failed": []}

    for item in items:
        device = Device.objects.filter(
            organization=organization, serial=item["device_serial"]
        ).first()
        osid = str(item["osid"])
        direction = item.get("direction") or AccessEvent.Direction.UNKNOWN

        if device is None:
            result["unmatched"].append(f"no-device:{item['device_serial']}:{osid}")
            continue

        event_time = _normalize_time(item["event_time"])
        dedup_key = _dedup_key(device, event_time, osid)
        if _is_duplicate(dedup_key):
            result["duplicate"].append(dedup_key)
            continue

        user = _resolve_user(organization, osid)
        try:
            # One item = one unit: event row, attendance and the notification row
            # commit together or not at all.
            with transaction.atomic():
                AccessEvent.objects.create(
                    organization=organization,
                    device=device,
                    user=user,
                    raw_osid=osid,
                    event_time=event_time,
                    direction=direction,
                    verify_mode=item.get("verify_mode", ""),
                    raw=item.get("raw", {}),
                    dedup_key=dedup_key,
                )
                student = getattr(user, "student_profile", None) if user else None
                if student is not None and direction in (
                    AccessEvent.Direction.IN,
                    AccessEvent.Direction.OUT,
                ):
                    _apply_daily_attendance(organization, student, event_time, direction)
                    _notify(user, direction, event_time)
        except IntegrityError:
            # Lost the race to a concurrent request carrying the same event.
            result["duplicate"].append(dedup_key)
            continue
        except Exception:
            logger.exception("Device event ingest failed for %s", dedup_key)
            result["failed"].append(dedup_key)
            continue

        result["accepted" if user is not None else "unmatched"].append(dedup_key)

    return result
