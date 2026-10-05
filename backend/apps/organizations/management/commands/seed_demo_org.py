"""Seed a self-contained demo organization for prospective-school trials.

Creates a "Demo maktab" organization (slug ``demo``) with one account per role
(director / teacher / student) on fixed, shareable credentials, plus a class of
sample students so the UI is not empty. Idempotent: rerunning refreshes the
passwords and leaves existing rows in place. The credentials here are the ones
printed on the public demo one-pager, so keep the two in sync.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.organizations.models import Organization, OrganizationMembership
from apps.schools.models import SchoolClass
from apps.users.models import StudentProfile, TeacherProfile, User

DEMO_PASSWORD = "demo1234"
ORG_NAME = "Demo maktab"
ORG_SLUG = "demo"
CLASS_NAME = "9-A"

# (email, username, first_name, last_name)
DIRECTOR = ("direktor@demo.uz", "direktor.demo", "Dilnoza", "Karimova")
TEACHER = ("ustoz@demo.uz", "ustoz.demo", "Jasur", "Tohirov")
STUDENT = ("oquvchi@demo.uz", "oquvchi.demo", "Aziza", "Yusupova")

# Extra classmates so lists / ratings are not empty.
CLASSMATES = [
    ("Bekzod", "Rahimov"),
    ("Malika", "Sobirova"),
    ("Sardor", "Umarov"),
    ("Nigora", "Qodirova"),
    ("Jahongir", "Aliyev"),
]


class Command(BaseCommand):
    help = "Create/refresh the public demo organization, accounts and sample data."

    @transaction.atomic
    def handle(self, *args, **options):
        org, _ = Organization.objects.get_or_create(
            slug=ORG_SLUG,
            defaults={"name": ORG_NAME, "type": Organization.Type.SCHOOL},
        )

        director = self._account(org, User.Role.DIRECTOR,
                                 OrganizationMembership.Role.DIRECTOR, *DIRECTOR)

        teacher = self._account(org, User.Role.TEACHER,
                                OrganizationMembership.Role.TEACHER, *TEACHER)
        teacher_profile, _ = TeacherProfile.objects.get_or_create(user=teacher)

        school_class, _ = SchoolClass.objects.get_or_create(
            name=CLASS_NAME, organization=org,
            defaults={"class_teacher": teacher_profile},
        )
        if school_class.class_teacher_id is None:
            school_class.class_teacher = teacher_profile
            school_class.save(update_fields=["class_teacher"])

        student = self._account(org, User.Role.STUDENT,
                                 OrganizationMembership.Role.STUDENT, *STUDENT)
        StudentProfile.objects.get_or_create(
            user=student, defaults={"school_class": school_class}
        )

        for i, (first, last) in enumerate(CLASSMATES, start=1):
            classmate = self._account(
                org, User.Role.STUDENT, OrganizationMembership.Role.STUDENT,
                f"oquvchi{i}@demo.uz", f"oquvchi{i}.demo", first, last,
            )
            StudentProfile.objects.get_or_create(
                user=classmate, defaults={"school_class": school_class}
            )

        self.stdout.write(self.style.SUCCESS(
            f"Demo org '{org.name}' (slug={org.slug}) tayyor. "
            f"Login (parol: {DEMO_PASSWORD}): "
            f"{DIRECTOR[0]} / {TEACHER[0]} / {STUDENT[0]}"
        ))

    def _account(self, org, user_role, membership_role, email, username,
                 first_name, last_name):
        """Create-or-refresh a user, pin the org, and ensure an ACTIVE membership."""
        user, _ = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username,
                "role": user_role,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        user.username = username
        user.role = user_role
        user.first_name = first_name
        user.last_name = last_name
        user.must_change_password = False
        user.is_active = True
        user.active_organization = org
        user.set_password(DEMO_PASSWORD)
        user.save()

        OrganizationMembership.objects.update_or_create(
            user=user, organization=org,
            defaults={"role": membership_role,
                      "status": OrganizationMembership.Status.ACTIVE},
        )
        return user
