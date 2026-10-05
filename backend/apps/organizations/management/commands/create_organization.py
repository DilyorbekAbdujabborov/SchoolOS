"""Provision a real (paying/onboarding) organization and its first director.

Unlike ``seed_demo_org`` (fixed, shareable demo credentials), this creates one
tenant for an actual school/club and a single director account on a *generated*
temporary password that is printed exactly once. The director is forced to
change it on first login (``must_change_password=True``), mirroring the
bulk-import flow — the plaintext is never stored or shown again.

Idempotent on the organization and the director: rerunning with the same
``--slug`` keeps the org, and reusing the same ``--director-email`` keeps that
account (its password is only (re)generated with ``--reset-password``). The
``<slug>`` becomes the tenant's entrance at ``<slug>.<TENANT_BASE_DOMAIN>``; the
SSL sync job covers that host automatically within one interval.

Example::

    python manage.py create_organization \
        --name "Toshloq tumani 44-sonli umumiy o'rta ta'lim maktabi" \
        --slug toshloq-44 \
        --director-first Anorxan --director-last Nurmatova
"""

import secrets
import string

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import StudentProfile, TeacherProfile, User


def _generate_temp_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = "Create a real organization (tenant) and its first director account."

    def add_arguments(self, parser):
        parser.add_argument("--name", required=True, help="Organization display name.")
        parser.add_argument(
            "--slug",
            required=True,
            help="Tenant slug; becomes <slug>.<TENANT_BASE_DOMAIN>. Lowercase, hyphens.",
        )
        parser.add_argument(
            "--type",
            default=Organization.Type.SCHOOL,
            choices=[c[0] for c in Organization.Type.choices],
            help="Organization type (default: SCHOOL).",
        )
        parser.add_argument("--director-first", required=True, help="Director first name.")
        parser.add_argument("--director-last", required=True, help="Director last name.")
        parser.add_argument(
            "--director-email",
            default=None,
            help="Director login email. Defaults to direktor@<slug>.<TENANT_BASE_DOMAIN>.",
        )
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="If an account already exists, generate a new temporary password.",
        )
        parser.add_argument(
            "--with-sample-accounts",
            action="store_true",
            help="Also create one teacher, a class and one student so every role has a login.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        raw_slug = options["slug"].strip().lower()
        slug = slugify(raw_slug)
        if slug != raw_slug:
            raise CommandError(
                f"Invalid slug '{options['slug']}'. Use lowercase letters, digits and hyphens "
                f"(suggested: '{slug}')."
            )

        from django.conf import settings

        base = (getattr(settings, "TENANT_BASE_DOMAIN", "") or "").strip().rstrip(".")
        email = options["director_email"] or (f"direktor@{slug}.{base}" if base else f"direktor@{slug}.local")

        org, org_created = Organization.objects.get_or_create(
            slug=slug,
            defaults={"name": options["name"], "type": options["type"]},
        )
        if not org_created and org.name != options["name"]:
            # Keep the row, but let an operator correct the display name.
            org.name = options["name"]
            org.save(update_fields=["name"])

        reset = options["reset_password"]

        # (label, user, temporary_password_or_None) for the printed summary.
        results = []

        director, dir_pw = self._provision_user(
            org, email, User.Role.DIRECTOR, OrganizationMembership.Role.DIRECTOR,
            options["director_first"], options["director_last"], reset,
        )
        results.append(("Director", director, dir_pw))

        if options["with_sample_accounts"]:
            from apps.schools.models import SchoolClass

            teacher, teacher_pw = self._provision_user(
                org, f"ustoz@{slug}.{base}" if base else f"ustoz@{slug}.local",
                User.Role.TEACHER, OrganizationMembership.Role.TEACHER,
                "O'qituvchi", "Namuna", reset,
            )
            teacher_profile, _ = TeacherProfile.objects.get_or_create(user=teacher)
            results.append(("Teacher", teacher, teacher_pw))

            school_class, _ = SchoolClass.objects.get_or_create(
                name="1-A", organization=org,
                defaults={"class_teacher": teacher_profile},
            )
            if school_class.class_teacher_id is None:
                school_class.class_teacher = teacher_profile
                school_class.save(update_fields=["class_teacher"])

            student, student_pw = self._provision_user(
                org, f"oquvchi@{slug}.{base}" if base else f"oquvchi@{slug}.local",
                User.Role.STUDENT, OrganizationMembership.Role.STUDENT,
                "O'quvchi", "Namuna", reset,
            )
            StudentProfile.objects.get_or_create(
                user=student, defaults={"school_class": school_class}
            )
            results.append(("Student", student, student_pw))

        host = f"{slug}.{base}" if base else slug
        self.stdout.write(self.style.SUCCESS(
            f"Organization {'created' if org_created else 'exists'}: "
            f"'{org.name}' (slug={org.slug}, type={org.type})"
        ))
        self.stdout.write(f"  Entrance: https://{host}/")
        any_generated = False
        for label, user, temp_password in results:
            self.stdout.write(f"  {label}: {user.first_name} {user.last_name} <{user.email}>")
            if temp_password is not None:
                any_generated = True
                self.stdout.write(self.style.WARNING(
                    f"    Temporary password (shown ONCE): {temp_password}"
                ))
            else:
                self.stdout.write("    already existed; password unchanged (--reset-password to regenerate).")
        if any_generated:
            self.stdout.write("  Each new account must change its password on first login.")

    def _provision_user(self, org, email, user_role, membership_role, first, last, reset):
        """Create-or-update one account pinned to ``org``; return (user, temp_password_or_None)."""
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "role": user_role,
                "first_name": first,
                "last_name": last,
                "must_change_password": True,
                "is_active": True,
            },
        )

        temp_password = None
        if created or reset:
            temp_password = _generate_temp_password()
            user.set_password(temp_password)
            user.must_change_password = True

        user.first_name = first
        user.last_name = last
        user.role = user_role
        user.is_active = True
        user.active_organization = org
        user.save()

        OrganizationMembership.objects.update_or_create(
            user=user, organization=org,
            defaults={"role": membership_role,
                      "status": OrganizationMembership.Status.ACTIVE},
        )
        return user, temp_password
