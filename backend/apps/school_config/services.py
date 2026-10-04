"""Class-access windows: a teacher (their own classes) or a director (the whole
school) temporarily opening the School Time Lock so students can use the platform
during a lesson."""

from datetime import datetime

from django.db.models import Q
from django.utils import timezone

from apps.academics.models import Lesson
from apps.common.permissions import IsDirector
from apps.schools.models import SchoolClass

from .models import ClassAccessWindow, SchoolTimeSettings


def _is_manager(user) -> bool:
    """Owner/admin/director — opens the platform for every class in the school."""
    return user.active_role in IsDirector.allowed_roles


def teacher_classes(profile, organization_id):
    """Every class a teacher can open: ones they lead (`class_teacher`) and ones
    they teach, via either dated lessons or the weekly timetable."""
    return (
        SchoolClass.objects.filter(organization_id=organization_id)
        .filter(
            Q(class_teacher=profile)
            | Q(lessons__teacher=profile)
            | Q(timetable_slots__teacher=profile)
        )
        .distinct()
    )


def accessible_classes(user):
    """The classes `user` may open: the whole school for a manager, otherwise the
    teacher's own classes."""
    organization_id = user.active_organization_id
    if _is_manager(user):
        return SchoolClass.objects.filter(organization_id=organization_id)
    return teacher_classes(user.teacher_profile, organization_id)


def _period_end_from_settings(organization_id, now_time):
    settings_obj = SchoolTimeSettings.objects.filter(organization_id=organization_id).first()
    return settings_obj.current_period_end(now_time) if settings_obj else now_time


def _current_period_expiry(user) -> datetime:
    """When the access window should close: the end of the current period.

    For a teacher this tracks their real lesson where possible — the lesson
    happening now, else their next lesson today. A manager (no lesson of their
    own) and a teacher with no lesson fall back to the lock window's period math.
    """
    organization_id = user.active_organization_id
    now = timezone.localtime()
    today = now.date()
    now_time = now.time()
    end_time = None

    if not _is_manager(user):
        profile = user.teacher_profile
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

    if end_time is None:
        end_time = _period_end_from_settings(organization_id, now_time)

    return now.replace(
        hour=end_time.hour, minute=end_time.minute, second=0, microsecond=0
    )


def open_access(user) -> list[ClassAccessWindow]:
    """Open (or re-open) the platform for the user's classes until the end of the
    current period. Returns the windows that were set."""
    expires_at = _current_period_expiry(user)
    windows = []
    for school_class in accessible_classes(user):
        window, _created = ClassAccessWindow.objects.update_or_create(
            school_class=school_class,
            defaults={"opened_by": user, "expires_at": expires_at},
        )
        windows.append(window)
    return windows


def close_access(user) -> int:
    """Close any access the user has opened on their classes. Returns the number
    of windows removed."""
    class_ids = list(accessible_classes(user).values_list("id", flat=True))
    deleted, _ = ClassAccessWindow.objects.filter(school_class_id__in=class_ids).delete()
    return deleted


def access_status(user) -> dict:
    """The current open/closed state of each of the user's classes, for the UI."""
    now = timezone.now()
    classes = accessible_classes(user).select_related("access_window")
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
