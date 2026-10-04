"""Class-access windows: a teacher temporarily opening the School Time Lock for
their classes so students can use the platform during a lesson."""

from datetime import datetime

from django.db.models import Q
from django.utils import timezone

from apps.academics.models import Lesson
from apps.schools.models import SchoolClass

from .models import ClassAccessWindow, SchoolTimeSettings


def teacher_classes(profile, organization_id):
    """Every class the teacher can open: ones they lead (`class_teacher`) and
    ones they teach, via either dated lessons or the weekly timetable."""
    return (
        SchoolClass.objects.filter(organization_id=organization_id)
        .filter(
            Q(class_teacher=profile)
            | Q(lessons__teacher=profile)
            | Q(timetable_slots__teacher=profile)
        )
        .distinct()
    )


def _current_period_expiry(profile, organization_id) -> datetime:
    """When the access window should close: the end of the current period.

    Preference order, so the window tracks the real lesson wherever possible:
      1. the teacher's lesson happening right now → its end time,
      2. the teacher's next lesson today → its end time,
      3. the lock window's own end time (SchoolTimeSettings).
    """
    now = timezone.localtime()
    today = now.date()
    now_time = now.time()

    current = (
        Lesson.objects.filter(
            teacher=profile, date=today, start_time__lte=now_time, end_time__gt=now_time
        )
        .order_by("end_time")
        .first()
    )
    if current:
        end_time = current.end_time
    else:
        upcoming = (
            Lesson.objects.filter(teacher=profile, date=today, start_time__gt=now_time)
            .order_by("start_time")
            .first()
        )
        if upcoming:
            end_time = upcoming.end_time
        else:
            settings_obj = SchoolTimeSettings.objects.filter(
                organization_id=organization_id
            ).first()
            end_time = (
                settings_obj.current_period_end(now_time) if settings_obj else now_time
            )

    return now.replace(
        hour=end_time.hour, minute=end_time.minute, second=0, microsecond=0
    )


def open_access_for_teacher(user) -> list[ClassAccessWindow]:
    """Open (or re-open) the platform for all of the teacher's classes until the
    end of the current period. Returns the windows that were set."""
    profile = user.teacher_profile
    organization_id = user.active_organization_id
    expires_at = _current_period_expiry(profile, organization_id)

    windows = []
    for school_class in teacher_classes(profile, organization_id):
        window, _created = ClassAccessWindow.objects.update_or_create(
            school_class=school_class,
            defaults={"opened_by": user, "expires_at": expires_at},
        )
        windows.append(window)
    return windows


def close_access_for_teacher(user) -> int:
    """Close any access the teacher has opened on their classes. Returns the
    number of windows removed."""
    profile = user.teacher_profile
    organization_id = user.active_organization_id
    class_ids = list(teacher_classes(profile, organization_id).values_list("id", flat=True))
    deleted, _ = ClassAccessWindow.objects.filter(school_class_id__in=class_ids).delete()
    return deleted


def teacher_access_status(user) -> dict:
    """The current open/closed state of each of the teacher's classes, for the UI."""
    profile = user.teacher_profile
    organization_id = user.active_organization_id
    now = timezone.now()

    classes = teacher_classes(profile, organization_id).select_related("access_window")
    rows = []
    latest_expiry = None
    for school_class in classes:
        window = getattr(school_class, "access_window", None)
        active = bool(window and window.expires_at > now)
        expires_at = window.expires_at if active else None
        if active and (latest_expiry is None or expires_at > latest_expiry):
            latest_expiry = expires_at
        rows.append(
            {"id": school_class.id, "name": school_class.name, "expires_at": expires_at}
        )

    return {
        "open": latest_expiry is not None,
        "expires_at": latest_expiry,
        "classes": rows,
    }


def class_is_open(school_class_id) -> bool:
    """Whether a student's class currently has an active access window."""
    if not school_class_id:
        return False
    return ClassAccessWindow.objects.filter(
        school_class_id=school_class_id, expires_at__gt=timezone.now()
    ).exists()
