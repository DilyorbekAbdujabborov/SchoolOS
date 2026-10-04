"""Seed one fully-filled example student.

Demonstrates the enriched `StudentProfile` (PINFL, passport, middle name,
gender, address, region) using the shape of the national IT-City / digital.uz
person registry. The data here is the registry's own sample record, not a real
person. Idempotent: re-running updates the same account.

    python manage.py seed_example_student
"""

from django.core.management.base import BaseCommand

from apps.organizations.models import Organization, OrganizationMembership
from apps.schools.models import SchoolClass
from apps.users.models import StudentProfile, User

EMAIL = "dilyorbek.abdujabborov@example.com"
USERNAME = "dilyorbek.abdujabborov"
PASSWORD = "student123"
CLASS_NAME = "11-A"
HANDLE = "dilyorbekdev"

# Mapped from the digital.uz person payload (sample record).
PROFILE = {
    "first_name": "Dilyorbek",
    "last_name": "Abdujabborov",
    "middle_name": "Abduqahhor o'g'li",
    "pinfl": "12345678901234",
    "passport_number": "DD1234567",
    "gender": StudentProfile.Gender.MALE,
    "birth_date": "2000-12-28",
    "phone_number": "+998901234567",
    "address": "Qayerdur",
    "region": "Qayerdur",
}


class Command(BaseCommand):
    help = "Create or refresh an example student with every identity field filled."

    def handle(self, *args, **options):
        school_class, _ = SchoolClass.objects.get_or_create(name=CLASS_NAME)

        user, _created = User.objects.get_or_create(
            username=USERNAME,
            defaults={
                "email": EMAIL,
                "role": User.Role.STUDENT,
                "first_name": PROFILE["first_name"],
                "last_name": PROFILE["last_name"],
            },
        )
        user.email = EMAIL
        user.role = User.Role.STUDENT
        user.first_name = PROFILE["first_name"]
        user.last_name = PROFILE["last_name"]
        # Give the example account a live public profile at /p/dilyorbekdev/.
        if not User.objects.exclude(pk=user.pk).filter(handle=HANDLE).exists():
            user.handle = HANDLE
            user.is_profile_public = True
        user.set_password(PASSWORD)
        user.must_change_password = False
        user.save()

        # Attach to an organization so the example shows up in the director's
        # (org-scoped) student list and its gamification resolves. Picks the
        # first organization — on crm that is the single "Maktab" org.
        organization = Organization.objects.order_by("id").first()
        if organization is not None:
            OrganizationMembership.objects.update_or_create(
                user=user,
                organization=organization,
                defaults={
                    "role": OrganizationMembership.Role.STUDENT,
                    "status": OrganizationMembership.Status.ACTIVE,
                },
            )
            if user.active_organization_id != organization.id:
                user.active_organization = organization
                user.save(update_fields=["active_organization"])

        profile, _ = StudentProfile.objects.update_or_create(
            user=user,
            defaults={
                "school_class": school_class,
                "middle_name": PROFILE["middle_name"],
                "pinfl": PROFILE["pinfl"],
                "passport_number": PROFILE["passport_number"],
                "gender": PROFILE["gender"],
                "birth_date": PROFILE["birth_date"],
                "phone_number": PROFILE["phone_number"],
                "address": PROFILE["address"],
                "region": PROFILE["region"],
            },
        )

        self.stdout.write(self.style.SUCCESS(f"Example student ready — login: {EMAIL} / {PASSWORD}"))
        self.stdout.write(
            "  {} {} ({}) · PINFL {} · {} · {}".format(
                profile.user.first_name,
                profile.user.last_name,
                profile.get_gender_display(),
                profile.pinfl,
                profile.passport_number,
                profile.region,
            )
        )
