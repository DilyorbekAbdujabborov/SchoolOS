from apps.notifications.models import Notification
from apps.notifications.services import notify
from apps.users.models import TeacherProfile

from .models import TeacherTask, TeacherTaskAssignment


def assign_task(
    task: TeacherTask, *, teacher: TeacherProfile | None, send_to_all: bool
) -> list[TeacherTaskAssignment]:
    """Fan `task` out to its recipients — one specific teacher, or every teacher — creating
    an assignment (and a notification) for each. `send_to_all` XOR `teacher` is enforced by
    `TeacherTaskWriteSerializer.validate` before this is ever called.
    """
    teachers = TeacherProfile.objects.all() if send_to_all else [teacher]
    assignments = [TeacherTaskAssignment.objects.create(task=task, teacher=t) for t in teachers]

    for assignment in assignments:
        notify(
            recipient=assignment.teacher.user,
            title=f"Yangi vazifa: {task.title}",
            body=task.description or task.get_category_display(),
            category=Notification.Category.TASK_ASSIGNED,
        )

    return assignments
