"""Delete all school content (students, lessons, timetable) while keeping
director/teacher accounts, classes, subjects and school config. Used to reset
the DB for a fresh real-data import."""

from django.core.management.base import BaseCommand

from apps.users.models import StudentProfile, User


class Command(BaseCommand):
    help = "Remove students + timetable/lessons; keep directors, teachers, classes, subjects, config."

    def handle(self, *args, **options):
        from apps.academics.models import DailyScheduleDigest, Lesson, TimetableSlot

        students = User.objects.filter(role=User.Role.STUDENT)
        self.stdout.write(f"Students to delete: {students.count()}")
        students.delete()

        orphan_profiles = StudentProfile.objects.all()
        self.stdout.write(f"Orphan student profiles: {orphan_profiles.count()}")
        orphan_profiles.delete()

        lessons = Lesson.objects.all()
        self.stdout.write(f"Lessons to delete: {lessons.count()}")
        lessons.delete()

        # Teachers are kept by this command, so their digests are not cascaded
        # away with the students. Left behind, a kept teacher's row would still
        # suppress today's 07:00 push after a reset.
        digests = DailyScheduleDigest.objects.all()
        self.stdout.write(f"Daily schedule digests to delete: {digests.count()}")
        digests.delete()

        slots = TimetableSlot.objects.all()
        self.stdout.write(f"Timetable slots to delete: {slots.count()}")
        slots.delete()

        self.stdout.write(self.style.SUCCESS("Cleanup done."))