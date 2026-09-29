"""One-off import of the school's real schedule and roster data.

Reads the JSON produced by the local .xls/.xlsx parser and creates
Subject / SchoolClass / TeacherProfile+User / TimetableSlot / Lesson / StudentProfile
rows. Idempotent: re-running updates nothing and creates no duplicates.

Credentials for every account it creates are written to a CSV for the director.
"""

import csv
import json
import re
import secrets
import string
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.academics.models import Lesson, Subject, TimetableSlot
from apps.schools.models import SchoolClass
from apps.users.models import TeacherProfile, User
from apps.users.models import StudentProfile

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
EMAIL_DOMAIN = "schoolos.uz"
NAME_STRIP = "‘’ʼ`\"'"


def norm_class(raw):
    """'4-A' / '4 A' / '4a'  ->  ('4', 'A').  Returns (number, letter) or (number, '')."""
    text = re.sub(r"[^0-9A-Za-z]+", "", str(raw)).upper()
    match = re.match(r"^(\d+)(.*)$", text)
    if not match:
        return text, ""
    return match.group(1), match.group(2)


def class_key(raw):
    number, letter = norm_class(raw)
    return f"{number}-{letter}" if letter else number


def roster_class_name(raw):
    """Name for a class that only the roster knows about — the school writes these '4-A'."""
    number, letter = norm_class(raw)
    return f"{number}-{letter}" if letter else number


def ascii_slug(name):
    for ch in NAME_STRIP:
        name = name.replace(ch, "")
    return re.sub(r"[^a-z0-9]+", ".", name.lower()).strip(".")


def split_name(full_name):
    parts = full_name.split()
    if len(parts) == 1:
        return parts[0], ""
    return " ".join(parts[1:]), parts[0]


def restrict(path):
    """Credentials are plain text — keep them readable only by the server user."""
    path.chmod(0o600)


def temp_password(length=10):
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


class Command(BaseCommand):
    help = "Import real school schedule + roster data from the parser's JSON export."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Path to export.json")
        parser.add_argument("--stage", choices=["core", "students"], default="core")
        parser.add_argument("--credentials", default=None, help="Where to write the login CSV")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        path = Path(opts["file"])
        if not path.is_file():
            raise CommandError(f"File not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        dry_run = opts["dry_run"]
        csv_path = Path(opts["credentials"] or f"/tmp/schoolos-credentials-{opts['stage']}.csv")

        if dry_run:
            with transaction.atomic():
                result = self.import_core(data)
                if opts["stage"] == "students":
                    students = self.import_students(data, result["classes"])
                transaction.set_rollback(True)
            self.stdout.write(self.style.WARNING("DRY RUN — hech narsa saqlanmadi"))
            self.report_core(result, data)
            if opts["stage"] == "students":
                self.report_students(students)
            return

        with transaction.atomic():
            result = self.import_core(data)
        self.report_core(result, data)

        # Only write when accounts were actually created — a re-run must never
        # blank out a credentials file that was already handed to the director.
        if result["accounts"]:
            self.write_csv(csv_path, result["accounts"])
            self.stdout.write(self.style.SUCCESS(f"\nO'qituvchi login CSV: {csv_path}"))
        else:
            self.stdout.write("\nO'qituvchi loginlari allaqachon mavjud — CSV o'zgartirilmadi.")

        if opts["stage"] == "students":
            student_csv = csv_path.with_name(f"{csv_path.stem}-students.csv")
            with transaction.atomic():
                students = self.import_students(data, result["classes"])
            self.report_students(students)
            if students["accounts"]:
                self.write_csv(student_csv, students["accounts"])
                self.stdout.write(self.style.SUCCESS(f"O'quvchi login CSV: {student_csv}"))

    # ------------------------------------------------------------------ core
    def import_core(self, data):
        existing = {c.name for c in SchoolClass.objects.all()}
        classes = {}

        for entry in data["classes"]:
            name = entry["name"].strip()
            obj, created = SchoolClass.objects.get_or_create(name=name)
            if created:
                existing.add(name)
            classes[class_key(name)] = obj

        for raw in data.get("roster_classes", []):
            key = class_key(raw)
            if key in classes:
                continue
            name = roster_class_name(raw)
            obj, created = SchoolClass.objects.get_or_create(name=name)
            if created:
                existing.add(name)
            classes[key] = obj

        subjects = {}
        for name in data["subjects"]:
            obj, _ = Subject.objects.get_or_create(name=name)
            subjects[name] = obj

        teachers, accounts = {}, []
        for entry in data["teachers"]:
            full_name = entry["teacher"].strip()
            email = f"{ascii_slug(full_name)}@{EMAIL_DOMAIN}"
            if User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)
                teacher, _ = TeacherProfile.objects.get_or_create(user=user)
            else:
                password = temp_password()
                initials, surname = split_name(full_name)
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    role=User.Role.TEACHER,
                    first_name=initials,
                    last_name=surname,
                    must_change_password=True,
                )
                teacher, _ = TeacherProfile.objects.get_or_create(user=user)
                accounts.append({
                    "role": "O'qituvchi",
                    "ism_familiya": full_name,
                    "login": email,
                    "parol": password,
                    "sinf": "",
                })
            teachers[full_name] = teacher

        slots = 0
        for entry in data["slots"]:
            school_class = classes[class_key(entry["class"])]
            _, created = TimetableSlot.objects.update_or_create(
                school_class=school_class,
                day_of_week=entry["day_of_week"],
                period_number=entry["period"],
                defaults={
                    "subject": subjects[entry["subject"]],
                    "teacher": teachers[entry["teacher"]],
                    "start_time": entry["start"],
                    "end_time": entry["end"],
                    "room": entry.get("room", ""),
                },
            )
            slots += int(created)

        lessons = 0
        for entry in data["lessons"]:
            school_class = classes[class_key(entry["class"])]
            _, created = Lesson.objects.update_or_create(
                school_class=school_class,
                date=date.fromisoformat(entry["date"]),
                start_time=entry["start"],
                defaults={
                    "subject": subjects[entry["subject"]],
                    "teacher": teachers[entry["teacher"]],
                    "end_time": entry["end"],
                    "room": entry.get("room", ""),
                },
            )
            lessons += int(created)

        return {
            "classes": classes, "subjects": subjects, "teachers": teachers,
            "accounts": accounts, "slots_new": slots, "lessons_new": lessons,
            "counts": {
                "classes": SchoolClass.objects.count(),
                "subjects": Subject.objects.count(),
                "teachers": TeacherProfile.objects.count(),
                "slots": TimetableSlot.objects.count(),
                "lessons": Lesson.objects.count(),
            },
        }

    # -------------------------------------------------------------- students
    def import_students(self, data, classes):
        created, accounts, missing = 0, [], []
        used_emails = set(User.objects.values_list("email", flat=True))

        for entry in data.get("students", []):
            key = class_key(entry["class"])
            school_class = classes.get(key)
            if school_class is None:
                missing.append(f"{entry['full_name']} ({entry['class']})")
                continue

            full_name = " ".join(entry["full_name"].split())
            email = f"{slugify(full_name)[:24]}@{EMAIL_DOMAIN}"
            if email in used_emails:
                email = f"{slugify(full_name)[:18]}{secrets.randbelow(9000) + 1000}@{EMAIL_DOMAIN}"
            used_emails.add(email)

            if User.objects.filter(email=email).exists():
                continue

            password = temp_password()
            first_name, _, last_name = full_name.partition(" ")
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                role=User.Role.STUDENT,
                first_name=first_name,
                last_name=last_name,
                must_change_password=True,
            )
            StudentProfile.objects.create(
                user=user,
                school_class=school_class,
                birth_date=date.fromisoformat(entry["birth_date"]) if entry.get("birth_date") else None,
                phone_number=entry.get("phone", "")[:20],
            )
            accounts.append({
                "role": "O'quvchi",
                "ism_familiya": full_name,
                "login": email,
                "parol": password,
                "sinf": school_class.name,
            })
            created += 1

        return {"created": created, "accounts": accounts, "missing": missing}

    # ---------------------------------------------------------------- report
    def report_core(self, result, data):
        counts = result["counts"]
        self.stdout.write("\n=== Yaratildi / mavzusi ===")
        self.stdout.write(f"  sinf        : {counts['classes']}")
        self.stdout.write(f"  fan         : {counts['subjects']}")
        self.stdout.write(f"  o'qituvchi  : {counts['teachers']}  (yangilangan login: {len(result['accounts'])})")
        self.stdout.write(f"  jadval slot : {counts['slots']}  (yangisi: {result['slots_new']})")
        self.stdout.write(f"  dars        : {counts['lessons']}  (yangi: {result['lessons_new']})")
        skipped = sum(1 for l in data["lessons"] if l["teacher"] == "")
        if skipped:
            self.stdout.write(f"  o'qitsiz kataklar: {skipped}")

    def report_students(self, students):
        self.stdout.write(f"\n=== O'quvchilar ===")
        self.stdout.write(f"  yaratildi   : {students['created']}")
        self.stdout.write(f"  jami o'quvchi: {User.objects.filter(role=User.Role.STUDENT).count()}")
        if students["missing"]:
            self.stdout.write(self.style.WARNING(f"  sinf topilmadi ({len(students['missing'])}):"))
            for name in students["missing"][:10]:
                self.stdout.write(f"    - {name}")

    # ------------------------------------------------------------------- csv
    def write_csv(self, path, accounts):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["role", "ism_familiya", "login", "parol", "sinf"])
            writer.writeheader()
            writer.writerows(accounts)
        restrict(path)

    def append_csv(self, path, accounts):
        if not accounts:
            return
        with path.open("a", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["role", "ism_familiya", "login", "parol", "sinf"])
            writer.writerows(accounts)
        restrict(path)

