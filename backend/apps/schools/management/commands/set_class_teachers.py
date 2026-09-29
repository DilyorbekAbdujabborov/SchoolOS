import json
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.schools.models import SchoolClass
from apps.users.models import TeacherProfile


def class_key(name):
    """Normalise a class label so '9 A', '9-A' and '9A' all collapse to one key."""
    cleaned = re.sub(r"[^0-9A-Za-z]", "", str(name)).upper()
    match = re.match(r"^(\d+)(.*)$", cleaned)
    if not match:
        return cleaned
    number, letters = match.groups()
    return f"{number}-{letters}" if letters else number


def display_name(teacher):
    """Rebuild the full teacher name from the AbstractUser name fields."""
    user = teacher.user
    return f"{user.first_name} {user.last_name}".strip() or user.username


def name_key(name):
    """Order-insensitive teacher-name key.

    The importer stores names as 'I.A. Abdullayeva' (initials first) while the
    schedule says 'Abdullayeva I.A.', so compare sorted, dot-stripped tokens
    instead of the raw string.
    """
    text = re.sub(r"[\u2018\u2019`'\u02bc]", "'", str(name)).lower()
    tokens = [re.sub(r"[.\s]+", "", tok) for tok in text.split()]
    return " ".join(sorted(tok for tok in tokens if tok))


class Command(BaseCommand):
    help = "Assign class teachers (sinf rahbari) from a JSON mapping produced by the schedule export."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Path to the JSON mapping file.")
        parser.add_argument("--dry-run", action="store_true", help="Report without saving.")

    def handle(self, *args, **opts):
        payload = json.loads(Path(opts["file"]).read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise CommandError("Mapping file must contain a JSON list.")

        classes = {}
        for school_class in SchoolClass.objects.all():
            classes.setdefault(class_key(school_class.name), school_class)

        teachers = {}
        for teacher in TeacherProfile.objects.select_related("user").all():
            teachers.setdefault(name_key(display_name(teacher)), teacher)

        assignments, missing_classes, missing_teachers = [], [], []

        with transaction.atomic():
            for row in payload:
                raw_class, raw_teacher = row.get("class"), row.get("teacher")
                school_class = classes.get(class_key(raw_class))
                teacher = teachers.get(name_key(raw_teacher))

                if school_class is None:
                    missing_classes.append(raw_class)
                    continue
                if teacher is None:
                    missing_teachers.append(raw_teacher)
                    continue

                previous = display_name(school_class.class_teacher) if school_class.class_teacher else None
                assignments.append((school_class, teacher, previous, row.get("source", "")))
                if not opts["dry_run"]:
                    school_class.class_teacher = teacher
                    school_class.save(update_fields=["class_teacher", "updated_at"])

            if opts["dry_run"]:
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(f"{'DRY RUN — ' if opts['dry_run'] else ''}sinf rahbari: {len(assignments)}"))
        for school_class, teacher, previous, source in assignments:
            change = "o'zgartirildi" if name_key(previous or "") != name_key(display_name(teacher)) else "o'zgarmadi"
            was = f" (avval: {previous})" if previous and name_key(previous) != name_key(display_name(teacher)) else ""
            self.stdout.write(f"  {school_class.name:8s} -> {display_name(teacher):22s} [{source}] {change}{was}")

        for name in missing_classes:
            self.stdout.write(self.style.WARNING(f"  sinf topilmadi: {name}"))
        for name in missing_teachers:
            self.stdout.write(self.style.WARNING(f"  o'qituvchi topilmadi: {name}"))

        self.stdout.write(
            f"\nJami: {len(assignments)} ta sinf, "
            f"{len({t for _, t, _, _ in assignments})} ta o'qituvchi. "
            f"Sinfsiz qoldi: {len(missing_classes)} ta."
        )
