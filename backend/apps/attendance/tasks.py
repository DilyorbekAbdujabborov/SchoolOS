from datetime import timedelta

from celery import shared_task
from django.db.models import Count
from django.utils import timezone

from apps.academics.models import Lesson
from apps.notifications.models import Notification
from apps.notifications.services import notify

from .models import AttendanceReminder

# Celery Beat re-runs this task every couple of minutes (see
# CELERY_BEAT_SCHEDULE); the reminder window only needs to be wider than that
# interval so a lesson's "10 minutes before the end" moment is never skipped
# between two runs. AttendanceReminder stops the same lesson being pinged twice.
REMINDER_LEAD = timedelta(minutes=10)
REMINDER_WINDOW = timedelta(minutes=5)


@shared_task
def remind_unmarked_attendance() -> int:
    """Sends the lesson's teacher a nudge ~10 minutes before the lesson ends
    when its attendance has never been taken, so they don't lose the window.
    Returns how many lessons were reminded this run.
    """
    now = timezone.localtime()
    remind_at = now + REMINDER_LEAD
    window_start = remind_at.time()
    window_end = (remind_at + REMINDER_WINDOW).time()

    lessons = (
        Lesson.objects.filter(date=now.date(), end_time__gte=window_start, end_time__lt=window_end)
        .annotate(students_count=Count("school_class__students"))
        .filter(
            students_count__gt=0,
            attendance_records__isnull=True,
            attendance_reminder__isnull=True,
        )
        .select_related("subject", "school_class", "teacher__user")
    )

    reminded = 0
    for lesson in lessons:
        notify(
            recipient=lesson.teacher.user,
            title=f"⏰ {lesson.subject.name} davomati olinmadi",
            body=(
                f"{lesson.school_class.name} sinfida {lesson.start_time:%H:%M}–{lesson.end_time:%H:%M} "
                f"darsi tugashiga 10 daqiqa qoldi, lekin davomat hali olinmagan.\n\n"
                "Dars tugaguniga qadar davomatni belgilang — aks holda "
                "'davomat olinmagan' deb qayd etiladi."
            ),
            category=Notification.Category.ATTENDANCE,
        )
        AttendanceReminder.objects.create(lesson=lesson)
        reminded += 1

    return reminded
